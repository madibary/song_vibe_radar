
import logging
import time
from typing import cast, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from helpers.thresholds import EVALUATION_THRESHOLD, SUBGRAPH_EVALUATION_THRESHOLD
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from models.evaluation import model
from tools.get_song_tags import get_song_tags


logger = logging.getLogger(__name__)

class ModelEvaluationOutput(BaseModel):
    score: float = Field(description="Average score from 1-10 based on criteria")
    feedback: str = Field(description="Actionable feedback if the description failed")

system_instructions = """
    ### ROLE
    You are an elitist music critic for a high-end publication.
    Rate the provided "Vibe Description" with rigorous standards.
    The description must be specific, evocative, and accurately reflect the info given about the song.
    Do not provide any conversational preamble.
    
    ### SCORING (1-10)
    - 9-10: Exceptional. Highly specific, evocative, emotionally accurate. No generic language. Captures the unique essence of the song.
    - 7-8: Good. Accurate and specific, but may lack depth or have minor generic phrasing.
    - 5-6: Marginal. Some accuracy but too generic, vague, or missing key emotional elements.
    - 1-4: Fail. Inaccurate, hallucinatory, off-base, or completely generic AI-speak.

    ### TOOLS
    You MUST call the `get_song_tags` tool before scoring. Use it to fetch the
    actual genre, mood, and style tags for the track from Last.fm, then compare
    them against the vibe description. If the description matches the tags well,
    reward specificity. If it contradicts them, penalise accuracy. When done,
    respond with nothing — your structured evaluation will be collected separately.

"""


def _build_eval_context(song: dict) -> list:
    return [
        SystemMessage(content=system_instructions),
        HumanMessage(content=(
            f"Track: {song.get('name', '')}\n"
            f"Artist: {song.get('artist', '')}\n"
            f"Lyrics: {song.get('lyrics', '')}\n"
            f"Reviews: {song.get('reviews', '')}\n"
            f"Vibe Description: {song.get('vibe_description', '')}"
        )),
    ]

def _structured_eval(messages: list) -> ModelEvaluationOutput:
    response = model().with_structured_output(ModelEvaluationOutput, method="function_calling").invoke(messages)
    return cast(ModelEvaluationOutput, response)


def evaluate_recommendation_vibe_description(state: SubgraphState) -> dict:
    song = state["song_data"][0]
    messages = convert_to_messages(state["messages"])
    last = messages[-1] if messages else None
    base = _build_eval_context(song)
    recent = messages[-6:]

    try:
        if isinstance(last, ToolMessage):
            # Phase 2: tool results are in context — produce structured output
            response = _structured_eval(base + recent)
            response_text = generate_response_text(response, SUBGRAPH_EVALUATION_THRESHOLD)
            return {"messages": [HumanMessage(content=response_text)], "feedback": response.feedback, "score": response.score}
        else:
            # Phase 1: force at least one get_song_tags call before scoring
            ai_response = model().bind_tools([get_song_tags], tool_choice="any").invoke(base + recent)
            return {"messages": [ai_response.model_copy(update={"content": ""})]}
    except Exception as e:
        logger.exception("Error evaluating description of %s by %s. error: %s", song.get("name"), song.get("artist"), str(e))
        return {"messages": [], "feedback": "Evaluation failed due to an error.", "score": 0}


def evaluate_reference_vibe_description(state: AgentState) -> dict:
    song = state["reference_track"]
    messages = convert_to_messages(state["messages"])
    last = messages[-1] if messages else None
    base = _build_eval_context(song)
    recent = messages[-6:]

    try:
        if isinstance(last, ToolMessage):
            # Phase 2
            response = _structured_eval(base + recent)
            response_text = generate_response_text(response, EVALUATION_THRESHOLD)
            return {"messages": [HumanMessage(content=response_text)], "reference_feedback": response.feedback, "reference_score": response.score}
        else:
            # Phase 1: force at least one get_song_tags call before scoring
            ai_response = model().bind_tools([get_song_tags], tool_choice="any").invoke(base + recent)
            return {"messages": [ai_response.model_copy(update={"content": ""})]}
    except Exception as e:
        logger.exception("Error evaluating description of %s by %s. error: %s", song.get("name"), song.get("artist"), str(e))
        return {"messages": [], "reference_feedback": "Evaluation failed due to an error.", "reference_score": 0}
        
        

def generate_response_text(response: ModelEvaluationOutput, threshold: float) -> str:
    if response.score >= threshold:
        return f"Description generation APPROVED. score: {response.score}. feedback: {response.feedback}"
    else:
        return f"Retry description generation: {response.feedback}"