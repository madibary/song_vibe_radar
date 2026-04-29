
import logging
import json
from typing import cast
from pydantic import BaseModel, Field
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from state.node_outputs import EvaluationNodeOutput, ReferenceEvaluationOutput
from models.evaluation import model


logger = logging.getLogger(__name__)

class ModelEvaluationOutput(BaseModel):
    score: float = Field(description="Average score from 1-10 based on criteria")
    is_passing: bool = Field(description="Whether the description meets the quality bar")
    feedback: str = Field(description="Actionable feedback if the description failed")

system_instructions = """
    ### ROLE
    You are a strict musicologist. Rate the provided "Vibe Description" based on how well it matches the "Source Context" (Lyrics/Reviews).
    You must provide your final answer by calling the ModelEvaluationOutput tool. Do not provide any conversational preamble.
    
    ### SCORING (1-10)
    - 9-10: Perfect. Accurate, professional, and specific.
    - 7-8: Good. Accurate, but maybe a bit generic.
    - 5-6: Needs Work. Minor inaccuracies or very "AI-sounding."
    - 1-4: Fail. Contains lies/hallucinations or is completely off-base.

    ### OUTPUT (JSON)
    {
    "score": [number],
    "is_passing": [true/false, pass if score >= 7],
    "feedback": "If failing, tell the writer exactly what to change."
    }

    ### INPUT DATA
    Lyrics: {lyrics}
    Reviews: {reviews}
    Vibe Description: {vibe_description}

"""


def evaluate_vibe_description(state: SubgraphState) -> EvaluationNodeOutput:
    song = state["song_data"][0]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Lyrics: {song['lyrics']}\nReviews: {song['reviews']}\nVibe Description: {song['vibe_description']}")
    model_with_schema = model.with_structured_output(ModelEvaluationOutput, method="function_calling")
    # Only send the last 6 messages to keep it clean
    messages = convert_to_messages(state["messages"])
    recent_messages = messages[-6:]
    try:
        response = model_with_schema.invoke([
            system_prompt,
            song_context,
            *recent_messages,
        ])

        response = cast(ModelEvaluationOutput, response)
        # Convert to dict if it's a Pydantic object, otherwise use as is
        result_dict = response.model_dump() if hasattr(response, "model_dump") else response
        
        # Create the message. We use json.dumps to keep the message content 
        # as a string for LangGraph's history compatibility.
        msg = AIMessage(content=json.dumps(result_dict, ensure_ascii=False))
        return cast(EvaluationNodeOutput, {"messages": [msg]})

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": [AIMessage(content="ERROR: evaluation failed")]}

def evaluate_reference_vibe_description(state: AgentState) -> ReferenceEvaluationOutput:
    song = state["reference_track"]
    model_with_schema = model.with_structured_output(ModelEvaluationOutput, method="function_calling")
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Lyrics: {song['lyrics']}\nReviews: {song['reviews']}\nVibe Description: {song['vibe_description']}")
    try:
        response = model_with_schema.invoke([
            system_prompt,
            song_context,
        ])
        content = getattr(response, "content", response)

        # content may already be a dict, a pydantic model, or an object with attributes
        if isinstance(content, dict):
            result = content
        else:
            # Try to extract named attributes
            try:
                result = {
                    "score": float(getattr(content, "score")),
                    "is_passing": bool(getattr(content, "is_passing")),
                    "feedback": str(getattr(content, "feedback")),
                }
            except Exception:
                # Fallback: serialize to string under feedback and mark as failing
                result = {"score": 0.0, "is_passing": False, "feedback": str(content)}

        from typing import cast
        return cast(ReferenceEvaluationOutput, {"reference_critique": result})

    except Exception as e:
        logger.exception("Error evaluating reference description of %s by %s", song.get("name"), song.get("artist"))
        # Return a structured failure result
        failure = {"score": 0.0, "is_passing": False, "feedback": "ERROR: evaluation failed"}
        return cast(ReferenceEvaluationOutput, {"reference_critique": failure})