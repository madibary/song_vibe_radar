from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import convert_to_messages, AIMessage
from graphs.subgraph import subgraph
from helpers.thresholds import EVALUATION_THRESHOLD
from nodes.analyze_vibe import analyze_reference_vibe
from nodes.evaluation import evaluate_reference_vibe_description
from langgraph.types import RetryPolicy
from nodes.validate_song import validate_song
from state.agent_state import AgentState
from nodes.map_songs import map_songs
from nodes.enrich_song import enrich_reference_song
from nodes.reduce_songs import reduce_enrichment_data
from langgraph.graph.state import StateGraph
from nodes.song_recommendations import get_song_recommendations
from nodes.vector_validation import validate_by_vectors
from tools.get_song_tags import get_song_tags

def is_valid_reference_song(state: AgentState) -> bool:
    if "error" in state:
        return False
    return True

def should_continue_evaluation_loop(state: AgentState) -> str:
    messages = convert_to_messages(state.get("messages", []))
    last = messages[-1] if messages else None

    if isinstance(last, AIMessage) and getattr(last, "tool_calls", []):
        return "tools"

    if state.get("reference_iterations", 0) > 1:
        return "end"

    if state.get("reference_score") is not None and state.get("reference_score") >= EVALUATION_THRESHOLD:
        return "end"

    return "refine"

def should_reduce_songs(state: AgentState) -> str:
    # check if the reduced songs aren't empty
    unsorted_songs = state.get("unsorted_songs", {})
    if not unsorted_songs:
        print ("No recommendations found. Ending graph execution.")
        return "end"
    return "reduce"


workflow = StateGraph(AgentState)

# enrichment and reflection on reference song
workflow.add_node("validate_reference_song", validate_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
workflow.add_node("enrich_reference_song", enrich_reference_song, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
workflow.add_node("analyze_vibe", analyze_reference_vibe, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
workflow.add_node("reflect", evaluate_reference_vibe_description, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
workflow.add_node("evaluation_tools", ToolNode([get_song_tags]))

# enrichment and processing of recommended songs
workflow.add_node("get_song_recommendations", get_song_recommendations, retry_policy=RetryPolicy(max_attempts=2, initial_interval=1.0))
workflow.add_node("vector_validator", validate_by_vectors)
workflow.add_node("reduce_enrichment_data", reduce_enrichment_data)
workflow.add_node("map_songs", map_songs)
workflow.add_node("music_worker", subgraph)


workflow.set_entry_point("validate_reference_song")
workflow.add_conditional_edges("validate_reference_song", is_valid_reference_song, {
    True: "enrich_reference_song",
    False: END
})  
workflow.add_edge("enrich_reference_song", "analyze_vibe")
workflow.add_edge("analyze_vibe", "reflect")
workflow.add_edge("evaluation_tools", "reflect")
workflow.add_conditional_edges(
    "reflect",
    should_continue_evaluation_loop,
    {
        "refine": "analyze_vibe",
        "end": "get_song_recommendations",
        "tools": "evaluation_tools",
    }
)
workflow.add_conditional_edges("get_song_recommendations", map_songs, ["music_worker", END])
workflow.add_conditional_edges("music_worker", should_reduce_songs , {
    "reduce": "reduce_enrichment_data",
    "end": END
})
# workflow.add_edge("music_worker", "reduce_enrichment_data")
workflow.add_edge("reduce_enrichment_data", "vector_validator")


graph = workflow.compile()

