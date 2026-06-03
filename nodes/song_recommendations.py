import requests
import json
import os
import uuid
import logging

from langchain_core.messages import HumanMessage
from state.agent_state import AgentState
from typings.node_outputs import SongRecommendationsOutput
from helpers.search_web import search_web
from models.description_generator import model

logger = logging.getLogger(__name__)
SONGS_NUMBER_LIMIT = 5


def _build_tracks_dict(tracks: list[dict]) -> dict:
    result = {}
    for track in tracks:
        name = track.get("name")
        artist = track.get("artist")
        if not name or not artist:
            continue
        track_id = str(uuid.uuid4())
        result[track_id] = {"id": track_id, "name": name, "artist": artist}
    return result


def _web_search_fallback(track_name: str, artist_name: str) -> SongRecommendationsOutput:
    logger.info("Falling back to web search for recommendations: %s by %s", track_name, artist_name)
    raw = search_web(f"{SONGS_NUMBER_LIMIT} songs similar to {track_name} by {artist_name}")
    if not raw:
        return {"unsorted_songs": {}, "error": f"No recommendations found for '{track_name}' by '{artist_name}'."}

    extraction_prompt = (
        f"Extract up to {SONGS_NUMBER_LIMIT} song recommendations from the text below. "
        f"Return ONLY a valid JSON array of objects with 'name' and 'artist' string keys, nothing else. "
        f"Example: [{{\"name\": \"Song Title\", \"artist\": \"Artist Name\"}}]\n\nText:\n{raw}"
    )
    response = model().invoke([HumanMessage(content=extraction_prompt)])

    try:
        songs = json.loads(str(response.content))
    except (ValueError, TypeError):
        logger.warning("Failed to parse LLM song extraction for %s by %s", track_name, artist_name)
        return {"unsorted_songs": {}, "error": f"No recommendations found for '{track_name}' by '{artist_name}'."}

    reduced_tracks = _build_tracks_dict(songs[:SONGS_NUMBER_LIMIT])
    if not reduced_tracks:
        return {"unsorted_songs": {}, "error": f"No recommendations found for '{track_name}' by '{artist_name}'."}

    return {"unsorted_songs": reduced_tracks}


def get_song_recommendations(state: AgentState) -> SongRecommendationsOutput:
    reference_track = state.get("reference_track", {})
    track_name = reference_track.get("name", "")
    artist_name = reference_track.get("artist", "")

    try:
        response = requests.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "track.getsimilar",
                "artist": artist_name,
                "track": track_name,
                "api_key": os.getenv("LAST_FM_API_KEY"),
                "format": "json",
                "limit": SONGS_NUMBER_LIMIT,
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as err:
        raise RuntimeError(f"Error fetching recommendations: {err}") from err

    try:
        track_data = response.json()
    except ValueError:
        track_data = json.loads(response.text)

    if (
        not isinstance(track_data, dict)
        or "similartracks" not in track_data
        or not isinstance(track_data["similartracks"], dict)
        or "track" not in track_data["similartracks"]
        or not track_data["similartracks"]["track"]
    ):
        logger.warning("No Last.fm recommendations for %s by %s, trying web search fallback", track_name, artist_name)
        return _web_search_fallback(track_name, artist_name)

    result_tracks = [
        {"name": t.get("name"), "artist": (t.get("artist") or {}).get("name")}
        for t in track_data["similartracks"]["track"]
    ]
    reduced_tracks = _build_tracks_dict(result_tracks)
    return {"unsorted_songs": reduced_tracks}