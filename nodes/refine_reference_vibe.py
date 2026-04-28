from helpers.vibe_refinement import get_refined_description
from state.agent_state import AgentState

def refine_reference_vibe(state: AgentState):
    song_data = state.get("reference_track", {}).copy()
    critique = state.get("reference_critique", "")
    try:
        response = get_refined_description(song_data["name"], song_data["artist"], song_data["vibe_description"], critique)
        song_data["vibe_description"] = response
        return {"reference_track": song_data, "reference_iterations": state["reference_iterations"] + 1, "reference_critique": critique}
    except Exception as e:
        print(f"Error refining vibe description of {song_data['name']} by {song_data['artist']}: {e}")
        raise e
