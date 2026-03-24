from nodes.context_enricher import enrich_song
from state.subgraph_state import SubgraphState
from typing import cast


def process_song(state: SubgraphState) -> SubgraphState:
    song_data_only = state["song_data"][0]
    try:
        enriched_data = enrich_song(song_data_only)
        return cast(SubgraphState, {"song_data": [enriched_data], 
                "critique": state["critique"], 
                "iterations": state["iterations"] + 1})
    except Exception as e:
        print(f"Error enriching song: {song_data_only['name']} by {song_data_only['artist']}. error: {e}")
        raise e
