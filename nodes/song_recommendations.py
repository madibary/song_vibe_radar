import requests
import json
import os
import uuid
import sys

from state.agent_state import AgentState

SONGS_NUMBER_lIMIT=5

def get_song_recommendations(state: AgentState):
    reference_track = state["reference_track"]
    track_name=reference_track["name"]
    artist_name = reference_track["artist"]
    try:
        response = requests.get(f"https://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist={artist_name}&track={track_name}&api_key={os.getenv("LAST_FM_API_KEY")}&format=json&limit={SONGS_NUMBER_lIMIT}")
    except requests.exceptions.HTTPError as errh:
        print("Eror getting track recommendations")
        print(errh.args[0])
        return {"unsorted_songs": {}}
    track_data = json.loads(response.text)

    # Ensure 'similartracks' and 'track' exist and are non-empty before using them
    if (
        not isinstance(track_data, dict)
        or "similartracks" not in track_data
        or not isinstance(track_data["similartracks"], dict)
        or "track" not in track_data["similartracks"]
        or not track_data["similartracks"]["track"]
    ):
        # No recommendations found; inform the user and exit the program
        print(f"No recommendations found for '{track_name}' by '{artist_name}'. Exiting.")
        sys.exit(0)

    result_tracks = track_data["similartracks"]["track"]
    reduced_tracks = {}
    for track in result_tracks:
        id = str(uuid.uuid4())
        reduced_tracks[id] = {"id": id, "name": track.get("name"), "artist": track.get("artist", {}).get("name")}
    return {"unsorted_songs": reduced_tracks}