import os
import logging
from logging.handlers import RotatingFileHandler

# Configure logging early so all modules use the same handlers
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "song_radar.log")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3),
    ],
)

from typing import cast
from dotenv import load_dotenv
from state.agent_state import AgentState
from graphs.main_graph import graph    

load_dotenv()

# Prompt user for initial input
track_name = input("Enter the reference track name: ")
artist_name = input("Enter the artist name: ")

initial_state = {
    "reference_track": {
        "name": track_name,
        "artist": artist_name
    },
    "reference_iterations": 0,
    "reference_feedback": ""
}

for state in graph.stream(cast(AgentState, initial_state), stream_mode="values"):
    if (state["messages"]):
        last_message = state["messages"][-1]
        last_message.pretty_print()
