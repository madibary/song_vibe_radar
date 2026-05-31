import logging
import re
import requests

logger = logging.getLogger(__name__)

_LRCLIB_URL = "https://lrclib.net/api/search"


def get_track_lyrics(track_name: str, artist_name: str) -> str:
    try:
        response = requests.get(
            _LRCLIB_URL,
            params={"q": f"{track_name} {artist_name}"},
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()
    except Exception as e:
        logger.warning("Failed to fetch lyrics for %s by %s: %s", track_name, artist_name, e)
        return ""

    if not results:
        logger.warning("Track lyrics not found: %s by %s", track_name, artist_name)
        return ""

    lyrics = results[0].get("plainLyrics") or ""
    if not lyrics:
        return ""

    lyrics = re.sub(r'\[.*?\]', '', lyrics)
    words = lyrics.split()
    return " ".join(words[:40]) if len(words) > 40 else lyrics
