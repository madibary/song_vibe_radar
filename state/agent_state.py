
import operator
from typing import Annotated,Sequence, TypedDict, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    reference_track: dict[str, str]
    unsorted_songs: dict
    sorted_songs: list[dict]
    best_match: str
    reference_score: float
    reference_feedback: str
    reference_iterations: int
    error: str
    song_data: Annotated[list, operator.add]
