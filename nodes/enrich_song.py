from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from helpers.get_lyrics import get_track_lyrics
from helpers.search_web import search_web
import logging

logger = logging.getLogger(__name__)

def enrich_song(song_data: dict) -> dict:
    search_results = search_web(f"Find reviews for the song {song_data.get('name')} by {song_data.get('artist')} based on vibe and song energy. keep it short - under 25 words.")
    lyrics_results = get_track_lyrics(song_data.get("name", ""), song_data.get("artist", ""))
    enriched_data = {"reviews": search_results, "lyrics": lyrics_results}
    return song_data | enriched_data

def enrich_reference_song(state: AgentState) -> dict:
    reference_song = state["reference_track"]
    try:
        enriched_reference_song = enrich_song(reference_song)
        return {"reference_track": enriched_reference_song}
    except Exception as e:
        logger.exception("Error enriching reference song: %s by %s. error: %s", reference_song.get('name'), reference_song.get('artist'), e)
        raise RuntimeError(f"Failed to enrich reference song: {reference_song.get('name')} by {reference_song.get('artist')}") from e

def enrich_recommendation_song(state: SubgraphState) -> dict:
    song_data_only = state["song_data"][0]
    try:
        enriched_data = enrich_song(song_data_only)
        return {"song_data": [enriched_data]}
    except Exception as e:
        logger.exception("Error enriching song: %s by %s. error: %s", song_data_only.get('name'), song_data_only.get('artist'), e)
        return {"song_data": [song_data_only | {"reviews": "", "lyrics": ""}]}