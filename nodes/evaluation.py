
import logging
import re
from langchain_core.messages import convert_to_messages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from state.node_outputs import EvaluationOutput, ReferenceEvaluationOutput
from models.evaluation import model


logger = logging.getLogger(__name__)


system_instructions = """
    ### ROLE
    You are a strict musicologist. Your goal is to review a song's vibe description. 

    ### CRITERIA
    1. Uniqueness: Mood/energy must not be generic.
    2. Objectivity: Uses objective descriptors.

    ### OUTPUT RULES
    - If all criteria pass: Reply with "APPROVED" and nothing else.
    - If any criteria fail: Provide a critique (max 30 words).
    - NEVER state the numerical word count in your final response.

    ### INPUT DATA
    Vibe Description: {vibe_description}

    ### OUTPUT
    [Your critique or "APPROVED" here]
"""


def evaluate_vibe_description(state: SubgraphState) -> EvaluationOutput:
    song = state["song_data"][0]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Vibe Description: {song['vibe_description']}")
    # Only send the last 6 messages to keep it clean
    messages = convert_to_messages(state["messages"])
    recent_messages = messages[-6:]
    try:
        response = model.invoke([
            system_prompt,
            song_context,
            *recent_messages
        ])

        # Extract textual content safely
        content = getattr(response, "content", response)
        content_str = str(content).strip()

        # Normalize APPROVED exactly
        if content_str.upper() == "APPROVED":
            return {"messages": [AIMessage(content="APPROVED")]}

        # Validate critique: max 30 words
        words = re.findall(r"\S+", content_str)
        if len(words) > 30:
            logger.warning("Evaluation critique too long (%d words); truncating.", len(words))
            content_str = " ".join(words[:30])

        return {"messages": [AIMessage(content=content_str)]}

    except Exception as e:
        logger.exception("Error evaluating description of %s by %s", song.get("name"), song.get("artist"))
        # Return a safe, consistent shape so the graph can continue or retry
        return {"messages": [AIMessage(content="ERROR: evaluation failed")]}

def evaluate_reference_vibe_description(state: AgentState) -> ReferenceEvaluationOutput:
    song = state["reference_track"]
    system_prompt = SystemMessage(content=system_instructions)
    song_context = HumanMessage(content=f"Vibe Description: {song['vibe_description']}")
    try:
        response = model.invoke([
            system_prompt,
            song_context,
        ])
        content = getattr(response, "content", response)
        content_str = str(content).strip()
        return {"reference_critique": content_str}

    except Exception as e:
        logger.exception("Error evaluating reference description of %s by %s", song.get("name"), song.get("artist"))
        return {"reference_critique": "ERROR: evaluation failed"}