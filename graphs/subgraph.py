from langgraph.graph.state import StateGraph, END
from nodes.evaluation import evaluate_vibe_description
from nodes.process_song import process_song
from state.subgraph_state import SubgraphState
from tools.tools import get_word_count
from nodes.refine_vibe import refine_recommendation_vibe
from langgraph.prebuilt import ToolNode
from langgraph.types import RetryPolicy
from langchain_core.messages import AIMessage

tool_node = ToolNode([get_word_count], handle_tool_errors=True)

def should_continue_evaluation_loop(state: SubgraphState):
    messages = state["messages"]
    last_message = messages[-1]
    
    if state.get("iterations", 0) > 1:
        return "end"

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"

    content = last_message.content
    if "APPROVED" in content:
        return "end"
    
    # If it's not a tool call and not an approval, it's a critique.
    return "refine"



subgraph_builder = StateGraph(SubgraphState)

subgraph_builder.add_node("process_song", process_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("refine_vibe", refine_recommendation_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("reflect", evaluate_vibe_description, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
subgraph_builder.add_node("tools", tool_node)

subgraph_builder.set_entry_point("process_song")
subgraph_builder.add_edge("process_song", "reflect")

subgraph_builder.add_conditional_edges(
    "reflect",
    should_continue_evaluation_loop,
    {
        "tools": "tools",
        "refine": "refine_vibe",
        "end": END
    }
)
subgraph_builder.add_edge("tools", "reflect")
subgraph_builder.add_edge("refine_vibe", "reflect")

subgraph = subgraph_builder.compile()