
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages # helper function to add messages to the state

class SubgraphState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    song_data: list[dict]
    critique: str
    iterations: int
