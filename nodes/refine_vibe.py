from helpers.vibe_refinement import get_refined_description
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
import logging

logger = logging.getLogger(__name__)


def refine_recommendation_vibe(state: SubgraphState):
    song_data = state["song_data"][0].copy()
    critique = state["messages"][-1].content if state["messages"] else ""
    logger.info("REFINING vibe description for %s", song_data.get('name'))
    logger.debug("Original description for %s: %s", song_data.get('name'), song_data.get('vibe_description'))
    logger.debug("Critique received for %s: %s", song_data.get('name'), critique)
    try:
        response = get_refined_description(song_data["name"], song_data["artist"], song_data["vibe_description"], critique)
        logger.info("Refined description for %s: %s", song_data.get('name'), response)
        song_data["vibe_description"] = response
        return {"song_data": [song_data], "iterations": state["iterations"] + 1, "critique": critique}
    except Exception as e:
        logger.exception("Error refining vibe description of %s by %s: %s", song_data.get('name'), song_data.get('artist'), e)
        raise

def refine_reference_vibe(state: AgentState):
    song_data = state.get("reference_track", {}).copy()
    critique = state.get("reference_critique", "")
    try:
        response = get_refined_description(song_data["name"], song_data["artist"], song_data["vibe_description"], critique)
        song_data["vibe_description"] = response
        return {"reference_track": song_data, "reference_iterations": state["reference_iterations"] + 1, "reference_critique": critique}
    except Exception as e:
        logger.exception("Error refining vibe description of %s by %s: %s", song_data.get('name'), song_data.get('artist'), e)
        raise
