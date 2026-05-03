from typing import cast
from nodes.vibe_analyzer import get_description
from state.agent_state import AgentState
from state.subgraph_state import SubgraphState
from langchain_core.messages import convert_to_messages
import logging
from helpers.formatter import parse_content
from models.description_generator import model

logger = logging.getLogger(__name__)

def analyze_vibe(state: SubgraphState) -> SubgraphState:
    song_data = state["song_data"][0]
    name = song_data["name"]
    artist = song_data["artist"]
    reviews = song_data.get("reviews", "")
    lyrics = song_data.get("lyrics", "")
    
    messages = convert_to_messages(state["messages"])
    recent_messages = messages[-6:]

    model_response = get_description(name, artist, reviews, lyrics, recent_messages)
    content_str = str(model_response.content)
    description = parse_content(content_str)

    enriched_song_data = song_data.copy()
    enriched_song_data["vibe_description"] = description
    return cast(SubgraphState, {"song_data": [enriched_song_data], "messages": [model_response], "iterations": state["iterations"] + 1})

def analyze_reference_vibe(state: AgentState) -> AgentState:
    song_data = state["reference_track"]
    name = song_data["name"]
    artist = song_data["artist"]
    reviews = song_data.get("reviews", "")
    lyrics = song_data.get("lyrics", "")
    
    messages = convert_to_messages(state["messages"])
    recent_messages = messages[-6:]

    model_response = get_description(name, artist, reviews, lyrics, recent_messages)
    content_str = str(model_response.content)
    description = parse_content(content_str)

    enriched_song_data = song_data.copy()
    enriched_song_data["vibe_description"] = description
    return cast(AgentState, {"reference_track": enriched_song_data, "messages": [model_response], "reference_iterations": state["reference_iterations"] + 1})