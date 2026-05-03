import logging
from state.agent_state import AgentState
from langgraph.types import Send
from langgraph.graph import END
from tools.tools import search_web, get_track_lyrics

logger = logging.getLogger(__name__)

def map_songs(state: AgentState):
    if not state.get("unsorted_songs"):
        logger.info("No songs to map. Ending graph execution.")
        return END
    return [Send("music_worker", {"song_data": [value], "is_passing": None, "score": None, "feedback": "", "iterations": 0}) for key, value in state["unsorted_songs"].items()]

def enrich_song(song_data) -> dict:
    search_results = search_web(f"Find reviews for the song {song_data["name"]} by {song_data["artist"]} based on vibe and song energy. keep it short - under 25 words.")
    lyrics_results = get_track_lyrics(song_data["name"], song_data["artist"])
    enriched_data = {"reviews": search_results, "lyrics": lyrics_results}
    return song_data | enriched_data

def enrich_reference_song(state: AgentState):
    reference_song = state["reference_track"]
    enriched_reference_song = enrich_song(reference_song)
    return {"reference_track": enriched_reference_song}

def reduce_enrichment_data(state: AgentState):
    songs = state["unsorted_songs"].copy()
    for song_info in state["song_data"]:
        id = song_info["id"]
        songs[id] = songs[id] | song_info

    return {"unsorted_songs": songs}