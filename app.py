from typing import cast
from state.agent_state import AgentState
from graphs.main_graph import graph    

initial_state = {
    "reference_track": {
        "name": "Blue Jeans",
        "artist": "Hana"
    }
}

for state in graph.stream(cast(AgentState, initial_state), stream_mode="values"):
    if (state["messages"]):
        last_message = state["messages"][-1]
        last_message.pretty_print()
