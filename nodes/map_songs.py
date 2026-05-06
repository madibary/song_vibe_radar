import logging
from typing import Union, List
from state.agent_state import AgentState
from langgraph.types import Send
from langgraph.graph import END

logger = logging.getLogger(__name__)

def map_songs(state: AgentState) -> Union[str, List[Send]]:
    if not state.get("unsorted_songs"):
        logger.warning("No songs to map. Ending graph execution.")
        return END
    return [Send("music_worker", {"song_data": [value], "score": None, "feedback": "", "iterations": 0}) for key, value in state["unsorted_songs"].items()]

