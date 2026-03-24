from dotenv import load_dotenv
from langgraph.graph import StateGraph
from state.agent_state import AgentState
from nodes.context_enricher import map_songs, reduce_enrichment_data
from langgraph.graph.state import StateGraph


from nodes.song_recommendations import get_song_recommendations
from graphs.subgraph import subgraph
from nodes.vector_validation import validate_by_vectors

load_dotenv()


workflow = StateGraph(AgentState)
workflow.add_node("get_song_recommendations", get_song_recommendations)
workflow.add_node("vector_validator", validate_by_vectors)
workflow.add_node("reduce_enrichment_data", reduce_enrichment_data)
workflow.add_node("map_songs", map_songs)
workflow.add_node("music_worker", subgraph)


workflow.set_entry_point("get_song_recommendations")
workflow.add_conditional_edges("get_song_recommendations", map_songs, ["music_worker"])
workflow.add_edge("music_worker", "reduce_enrichment_data")
workflow.add_edge("reduce_enrichment_data", "vector_validator")


graph = workflow.compile()

