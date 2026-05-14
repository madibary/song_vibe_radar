import os
import requests
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def get_song_tags(track: str, artist: str) -> str:
    """Fetch the top genre, mood, and style tags for a song from Last.fm.
    Use this to verify whether the genre, mood, or style described in the
    vibe description matches how the song is actually tagged by listeners."""
    try:
        response = requests.get(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "track.getTopTags",
                "artist": artist,
                "track": track,
                "api_key": os.getenv("LAST_FM_API_KEY"),
                "format": "json",
            },
            timeout=5,
        )
        data = response.json()
        tags = data.get("toptags", {}).get("tag", [])
        if not tags:
            return "No tags found for this track on Last.fm."
        top_tags = [t["name"] for t in tags[:10]]
        return f"Last.fm top tags: {', '.join(top_tags)}"
    except Exception:
        logger.exception("Failed to fetch Last.fm tags for %s by %s", track, artist)
        return "Could not fetch tags."
