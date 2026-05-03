import requests
import json
import os
import uuid
import logging

from state.agent_state import AgentState
from typings.node_outputs import SongRecommendationsOutput

logger = logging.getLogger(__name__)
SONGS_NUMBER_LIMIT = 5

def get_song_recommendations(state: AgentState) -> SongRecommendationsOutput:
    reference_track = state.get("reference_track", {})
    track_name = reference_track.get("name", "")
    artist_name = reference_track.get("artist", "")

    try:
        response = requests.get(
            f"https://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist={artist_name}&track={track_name}&api_key={os.getenv('LAST_FM_API_KEY')}&format=json&limit={SONGS_NUMBER_LIMIT}",
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as err:
        # Let the graph retry this transient failure via RetryPolicy
        raise RuntimeError(f"Error fetching recommendations: {err}") from err

    # Parse JSON safely
    try:
        track_data = response.json()
    except ValueError:
        track_data = json.loads(response.text)

    # Ensure 'similartracks' and 'track' exist and are non-empty before using them
    if (
        not isinstance(track_data, dict)
        or "similartracks" not in track_data
        or not isinstance(track_data["similartracks"], dict)
        or "track" not in track_data["similartracks"]
        or not track_data["similartracks"]["track"]
    ):
        # No recommendations found;
        logger.info("No recommendations found for %s by %s", track_name, artist_name)
        return {"unsorted_songs": {}, "error": f"No recommendations found for '{track_name}' by '{artist_name}'."}

    result_tracks = track_data["similartracks"]["track"]
    reduced_tracks = {}
    for track in result_tracks:
        name = track.get("name")
        artist = (track.get("artist") or {}).get("name")
        if not name or not artist:
            continue
        id = str(uuid.uuid4())
        reduced_tracks[id] = {"id": id, "name": name, "artist": artist}
    return {"unsorted_songs": reduced_tracks}