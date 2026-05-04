import json
import os
import requests
from state.agent_state import AgentState
import logging

logger = logging.getLogger(__name__)

def validate_song(state: AgentState):
    reference_track = state.get("reference_track", {})
    track_name = reference_track.get("name", "")
    artist_name = reference_track.get("artist", "")

    try:
        response = requests.get(
            f"https://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={os.getenv('LAST_FM_API_KEY')}&artist={artist_name}&track={track_name}&format=json",
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as err:
        # Let the graph retry this transient failure via RetryPolicy
        raise RuntimeError(f"Error getting track info: {err}") from err

    try:
        track_data = response.json()
    except ValueError:
        track_data = json.loads(response.text)
    
    if not track_data or track_data.get("error"):
        logger.warning("track not found: %s by %s", track_name, artist_name)
        return {"error": f"Track '{track_name}' by '{artist_name}' not found."}
    
    return {"reference_track": state.get("reference_track", {})}