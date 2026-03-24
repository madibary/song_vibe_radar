
import operator
from typing import Annotated,Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    reference_track: dict[str, str]
    unsorted_songs: dict
    best_match: str
    song_data: Annotated[list, operator.add]