import logging
from helpers.cache import cache_set
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState

logger = logging.getLogger(__name__)


def _cache_song_vibe(song: dict) -> None:
    if song.get("_from_cache"):
        return
    name = song.get("name", "")
    artist = song.get("artist", "")
    description = song.get("vibe_description", "")
    if name and artist and description:
        cache_set(name, artist, description)
        logger.info("Cached vibe for %s by %s", name, artist)


def cache_reference_vibe(state: AgentState) -> dict:
    _cache_song_vibe(state.get("reference_track", {}))
    return {}


def cache_recommendation_vibe(state: SubgraphState) -> dict:
    _cache_song_vibe(state["song_data"][0])
    return {}
