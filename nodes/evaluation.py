
import logging
from typing import cast, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage
from helpers.thresholds import EVALUATION_THRESHOLD, SUBGRAPH_EVALUATION_THRESHOLD
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from models.evaluation import model


logger = logging.getLogger(__name__)

class ModelEvaluationOutput(BaseModel):
    score: float = Field(description="Average score from 1-10 based on criteria")
    feedback: str = Field(description="Actionable feedback if the description failed")

system_instructions = """
    ### ROLE
    You are an elitist music critic for a high-end publication.
    Rate the provided "Vibe Description" with rigorous standards.
    The description must be specific, evocative, and accurately reflect the info given about the song.
    You must provide your final answer by calling the ModelEvaluationOutput tool. Do not provide any conversational preamble.
    
    ### SCORING (1-10)
    - 9-10: Exceptional. Highly specific, evocative, emotionally accurate. No generic language. Captures the unique essence of the song.
    - 7-8: Good. Accurate and specific, but may lack depth or have minor generic phrasing.
    - 5-6: Marginal. Some accuracy but too generic, vague, or missing key emotional elements.
    - 1-4: Fail. Inaccurate, hallucinatory, off-base, or completely generic AI-speak.

    ### OUTPUT (JSON)
    {
    "score": [number 1-10],
    "feedback": "List specific improvements needed. Be direct and actionable."
    }

    ### INPUT DATA
    Lyrics: {lyrics}
    Reviews: {reviews}
    Vibe Description: {vibe_description}

"""


def evaluate_recommendation_vibe_description(state: SubgraphState) -> dict:
    song = state["song_data"][0]
    messages = convert_to_messages(state["messages"])
    try:
        response = evaluate_description(song.get("lyrics", ""), song.get("reviews", ""), song.get("vibe_description", ""), messages)
        response_text = generate_response_text(response, SUBGRAPH_EVALUATION_THRESHOLD)
        msg = HumanMessage(content=response_text)
        return {"messages": [msg], "feedback": response.feedback, "score": response.score}

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": [], "feedback": "Evaluation failed due to an error.", "score": 0}


def evaluate_reference_vibe_description(state: AgentState) -> dict:
    song = state["reference_track"]
    messages = convert_to_messages(state["messages"])
    try:
        response = evaluate_description(song.get("lyrics", ""), song.get("reviews", ""), song.get("vibe_description", ""), messages)
        response_text = generate_response_text(response, EVALUATION_THRESHOLD)
        msg = HumanMessage(content=response_text)
        return {"messages": [msg], "reference_feedback": response.feedback, "reference_score": response.score}

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": [], "reference_feedback": "Evaluation failed due to an error.", "reference_score": 0}

def evaluate_description(lyrics: str, reviews: str, vibe_description: str, messages: list) -> ModelEvaluationOutput:
    recent_messages = messages[-6:]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Lyrics: {lyrics}\nReviews: {reviews}\nVibe Description: {vibe_description}")
    model_with_schema = model().with_structured_output(ModelEvaluationOutput, method="function_calling")

    response = model_with_schema.invoke([
        system_prompt,
        song_context,
        *recent_messages,
    ])
    
    response = cast(ModelEvaluationOutput, response)
    return response
        
        

def generate_response_text(response: ModelEvaluationOutput, threshold: float) -> str:
    if response.score >= threshold:
        return f"Description generation APPROVED. score: {response.score}. feedback: {response.feedback}"
    else:
        return f"Retry description generation: {response.feedback}"