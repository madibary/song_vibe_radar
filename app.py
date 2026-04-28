from typing import cast
from state.agent_state import AgentState
from graphs.main_graph import graph    

# Prompt user for initial input
track_name = input("Enter the reference track name: ")
artist_name = input("Enter the artist name: ")

initial_state = {
    "reference_track": {
        "name": track_name,
        "artist": artist_name
    },
    "reference_iterations": 0,
    "reference_critique": ""
}

for state in graph.stream(cast(AgentState, initial_state), stream_mode="values"):
    if (state["messages"]):
        last_message = state["messages"][-1]
        last_message.pretty_print()
