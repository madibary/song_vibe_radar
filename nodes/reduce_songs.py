from state.agent_state import AgentState

def reduce_enrichment_data(state: AgentState) -> dict:
    songs = state["unsorted_songs"].copy()
    for song_info in state["song_data"]:
        id = song_info["id"]
        songs[id] = songs[id] | song_info

    return {"unsorted_songs": songs}