from langgraph.graph.state import StateGraph, END
from helpers.thresholds import SUBGRAPH_EVALUATION_THRESHOLD
from nodes.analyze_vibe import analyze_recommendation_vibe
from nodes.evaluation import evaluate_recommendation_vibe_description
from nodes.process_song import process_song
from state.subgraph_state import SubgraphState
from langgraph.types import RetryPolicy


def should_continue_evaluation_loop(state: SubgraphState):    
    if state.get("iterations", 0) > 1:
        return "end"

    if (state.get("score") is not None and state.get("score") >= SUBGRAPH_EVALUATION_THRESHOLD):
        return "end"
    
    return "refine"

def should_reflect(state: SubgraphState):
    vibe_description = state["song_data"][0].get("vibe_description", "")
    if not vibe_description:
        return "end"    
    return "reflect"

subgraph_builder = StateGraph(SubgraphState)

subgraph_builder.add_node("process_song", process_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))

subgraph_builder.add_node("analyze_vibe", analyze_recommendation_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("reflect", evaluate_recommendation_vibe_description, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))

subgraph_builder.set_entry_point("process_song")
subgraph_builder.add_edge("process_song", "analyze_vibe")
subgraph_builder.add_conditional_edges(
    "analyze_vibe",
    should_reflect,
    {
        "reflect": "reflect",
        "end": END
    }
)

subgraph_builder.add_conditional_edges(
    "reflect",
    should_continue_evaluation_loop,
    {
        "refine": "analyze_vibe",
        "end": END
    }
)

subgraph = subgraph_builder.compile()