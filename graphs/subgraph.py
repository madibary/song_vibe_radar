from langgraph.graph.state import StateGraph, END
from nodes.refine_vibe import refine_recommendation_vibe
from nodes.analyze_vibe import analyze_vibe
from nodes.evaluation import evaluate_vibe_description
from nodes.process_song import process_song
from state.subgraph_state import SubgraphState
from langgraph.types import RetryPolicy


def should_continue_evaluation_loop(state: SubgraphState):    
    if state.get("iterations", 0) > 1:
        return "end"

    if state.get("is_passing") is True or (state.get("score") is not None and state.get("score") >= 7):
        return "end"
    
    return "refine"


subgraph_builder = StateGraph(SubgraphState)

subgraph_builder.add_node("process_song", process_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("refine_recommendation_vibe", refine_recommendation_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))

subgraph_builder.add_node("analyze_vibe", analyze_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("reflect", evaluate_vibe_description, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))

subgraph_builder.set_entry_point("process_song")
subgraph_builder.add_edge("process_song", "analyze_vibe")
subgraph_builder.add_edge("analyze_vibe", "reflect")

subgraph_builder.add_conditional_edges(
    "reflect",
    should_continue_evaluation_loop,
    {
        "refine": "analyze_vibe",
        "end": END
    }
)

subgraph = subgraph_builder.compile()