from helpers.vibe_refinement import get_refined_description
from state.subgraph_state import SubgraphState

def refine_vibe(state: SubgraphState):
    song_data = state["song_data"][0].copy()
    critique = state["messages"][-1].content if state["messages"] else ""
    print(f"\n\nREFINING vibe description for {song_data['name']}")
    print(f"Original description for {song_data['name']}: {song_data['vibe_description']}")
    print(f"Critique received for {song_data['name']}: {critique}")
    try:
        response = get_refined_description(song_data["name"], song_data["artist"], song_data["vibe_description"], critique)
        print(f"Refined description for {song_data['name']}: {response}")
        song_data["vibe_description"] = response
        return {"song_data": [song_data], "iterations": state["iterations"] + 1, "critique": critique}
    except Exception as e:
        print(f"Error refining vibe description of {song_data['name']} by {song_data['artist']}: {e}")
        raise e
