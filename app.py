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

print("🚀 Starting Song Vibe Radar...")

initial_state = {
    "reference_track": {
        "name": track_name,
        "artist": artist_name
    },
    "reference_iterations": 0,
    "reference_feedback": ""
}

final_state = initial_state.copy()
for updates in graph.stream(cast(AgentState, initial_state), stream_mode="updates"):
    for node_name, update in updates.items():
        if update is not None:
            final_state.update(update)
        if node_name == "validate_reference_song":
            print("🔍 Validating reference song...")
        elif node_name == "enrich_reference_song":
            print("📊 Enriching reference song data...")
        elif node_name == "analyze_vibe":
            print("🎵 Generating vibe description...")
        elif node_name == "reflect":
            print("⚖️ Evaluating vibe description...")
        elif node_name == "get_song_recommendations":
            print("🔎 Finding song recommendations...")
        elif node_name == "music_worker":
            print("🎶 Processing recommendations: generating vibes, evaluating, and sorting...")

# Check for errors
if "error" in final_state:
    print(f"❌ Error: {final_state['error']}")
else:
    # Print reference song vibe description
    reference_track = final_state.get("reference_track", {})
    print(f"\n📍 Reference Song: {reference_track.get('name')} by {reference_track.get('artist')}")
    print(f"\n✨ Vibe Description:\n{reference_track.get('vibe_description', 'N/A')}\n")
    
    sorted_songs = final_state.get("sorted_songs", [])
    if not sorted_songs:
        print("😔 No recommendations found.")
    else:
        print("🎉 Top Recommendations:")
        for i, song in enumerate(sorted_songs, 1):
            score = song.get("score", "N/A")
            # Convert score to percentage if it's a number
            if isinstance(score, (int, float)):
                score = f"{round(score * 100)}%"
            print(f"\n{i}. {song['name']} by {song['artist']} (Vibe match: {score})")
            vibe_desc = song.get("vibe_description", "")
            if vibe_desc:
                print(f"   Vibe: {vibe_desc}")
