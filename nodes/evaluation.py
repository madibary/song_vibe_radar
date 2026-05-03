
import logging
from typing import cast
from pydantic import BaseModel, Field
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
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
    - 9-10: Perfect. Accurate, professional, and specific. No hallucinations.
    - 7-8: Good. Accurate, no hallucinations, but maybe a bit generic.
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


def evaluate_vibe_description(state: SubgraphState):
    song = state["song_data"][0]
    messages = convert_to_messages(state["messages"])
    try:
        response = evaluate_description(song.get("lyrics"), song.get("reviews"), song.get("vibe_description"), messages)
        response_text = generate_response_text(response)
        msg = HumanMessage(content=response_text)
        return {"messages": [msg], "is_passing": response.is_passing, "feedback": response.feedback, "score": response.score}

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": []}


def evaluate_reference_vibe_description(state: AgentState):
    song = state["reference_track"]
    messages = convert_to_messages(state["messages"])
    try:
        response = evaluate_description(song.get("lyrics"), song.get("reviews"), song.get("vibe_description"), messages)
        response_text = generate_response_text(response)
        msg = HumanMessage(content=response_text)
        return {"messages": [msg], "reference_is_passing": response.is_passing, "reference_feedback": response.feedback, "reference_score": response.score}

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": []}

def evaluate_description(lyrics, reviews, vibe_description, messages) -> ModelEvaluationOutput:
    recent_messages = messages[-6:]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Lyrics: {lyrics}\nReviews: {reviews}\nVibe Description: {vibe_description}")
    model_with_schema = model.with_structured_output(ModelEvaluationOutput, method="function_calling")

    response = model_with_schema.invoke([
        system_prompt,
        song_context,
        *recent_messages,
    ])
    
    response = cast(ModelEvaluationOutput, response)
    return response
        
        

def generate_response_text (response) -> str:
    if response.is_passing:
        return f"Description generation APPROVED. score: {response.score}. feedback: {response.feedback}"
    else:
        return f"Retry description generation: {response.feedback}"