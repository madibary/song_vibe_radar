from typing import cast

from nodes.vibe_analyzer import get_description
from state.agent_state import AgentState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from state.subgraph_state import SubgraphState
from langchain_core.messages import convert_to_messages
import logging
from helpers.formatter import parse_content
from models.description_generator import model

logger = logging.getLogger(__name__)

def analyze_recommendation_vibe(state: SubgraphState) -> dict:
    song_data = state["song_data"][0]
    new_messages = analyze_vibe(song_data, state["messages"])
    model_response = new_messages[-1]
    content_str = str(model_response.content)
    description = parse_content(content_str)

    enriched_song_data = song_data.copy()
    enriched_song_data["vibe_description"] = description
    return {"song_data": [enriched_song_data], "messages": new_messages, "iterations": state["iterations"] + 1}

def analyze_reference_vibe(state: AgentState) -> dict:
    song_data = state["reference_track"]
    new_messages = analyze_vibe(song_data, state["messages"])
    last_message = new_messages[-1]
    content_str = str(last_message.content)
    description = parse_content(content_str) 
    
    enriched_song_data = song_data.copy()
    enriched_song_data["vibe_description"] = description
    return {"reference_track": enriched_song_data, "messages": new_messages, "reference_iterations": state["reference_iterations"] + 1}


def analyze_vibe(song_data, messages) -> list[HumanMessage | AIMessage | SystemMessage]:
    name = song_data["name"]
    artist = song_data["artist"]
    reviews = song_data.get("reviews", "")
    lyrics = song_data.get("lyrics", "")
    new_messages = []

    messages = convert_to_messages(messages)
    recent_messages = messages[-6:]

    # if it's the first vibe analysis - provide reviews and lyrics
    if not recent_messages:
        user_input = f"Generate a new vibe description. Reviews: {reviews} \nLyrics: {lyrics}"
        new_messages.append(HumanMessage(content=user_input))
        recent_messages = [HumanMessage(content=user_input)]

    model_response = get_description(name, artist, reviews, lyrics, recent_messages)
    new_messages.append(model_response)
    return new_messages