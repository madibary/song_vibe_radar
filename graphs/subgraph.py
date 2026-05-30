import os
from langgraph.graph.state import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import convert_to_messages, AIMessage
from helpers.thresholds import SUBGRAPH_EVALUATION_THRESHOLD
from nodes.analyze_vibe import analyze_recommendation_vibe
from nodes.evaluation import evaluate_recommendation_vibe_description
from nodes.enrich_song import enrich_recommendation_song
from state.subgraph_state import SubgraphState
from langgraph.types import RetryPolicy
from tools.get_song_tags import get_song_tags


def should_continue_evaluation_loop(state: SubgraphState) -> str:
    messages = convert_to_messages(state.get("messages", []))
    last = messages[-1] if messages else None

    if isinstance(last, AIMessage) and getattr(last, "tool_calls", []):
        return "tools"

    if state.get("iterations", 0) > 1:
        return "end"

    if state.get("score") is not None and state.get("score") >= SUBGRAPH_EVALUATION_THRESHOLD:
        return "end"

    return "refine"

def should_reflect(state: SubgraphState) -> str:
    if os.getenv("EVALUATION_ENABLED", "").lower() != "true":
        return "end"
    vibe_description = state["song_data"][0].get("vibe_description", "")
    if not vibe_description:
        return "end"
    return "reflect"

subgraph_builder = StateGraph(SubgraphState)

subgraph_builder.add_node("enrich_song", enrich_recommendation_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("analyze_vibe", analyze_recommendation_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("reflect", evaluate_recommendation_vibe_description, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("evaluation_tools", ToolNode([get_song_tags]))

subgraph_builder.set_entry_point("enrich_song")
subgraph_builder.add_edge("enrich_song", "analyze_vibe")
subgraph_builder.add_edge("evaluation_tools", "reflect")
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
        "end": END,
        "tools": "evaluation_tools",
    }
)

subgraph = subgraph_builder.compile()