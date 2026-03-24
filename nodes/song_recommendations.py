import requests
import json
import os
import uuid

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
    result_tracks = track_data["similartracks"]["track"]
    reduced_tracks = {}
    # to use less tokens
    for track in result_tracks:
        id = str(uuid.uuid4())
        reduced_tracks[id] = {"id": id, "name": track["name"], "artist": track["artist"]["name"]}
    return {"unsorted_songs": reduced_tracks}