import logging
import re
import os
import lyricsgenius as genius

logger = logging.getLogger(__name__)

_genius_api = None


def _get_genius_api():
    global _genius_api
    if _genius_api is None:
        _genius_api = genius.Genius(os.getenv("GENIUS_API_KEY"), verbose=False)
    return _genius_api


def get_track_lyrics(track_name: str, artist_name: str) -> str:
    """
    Retrieves the lyrics of a track from Genius API based on the track name and artist name.
    Returns a string with the lyrics of the track.
    """
    try:
        song = _get_genius_api().search_song(track_name, artist_name)
    except Exception as e:
        logger.exception("Failed to fetch lyrics for %s by %s. Error: %s", track_name, artist_name, e)
        return ""
    
    if song:
        lyrics = song.lyrics
        # Remove any text inside square brackets (e.g., [Chorus], [Intro])
        lyrics = re.sub(r'\[.*?\]', '', lyrics)

        words_list = lyrics.split()
        if (len(words_list) > 40):
            first_40_words = words_list[:40]
            result_string = " ".join(first_40_words)
            return result_string
        return lyrics
        
    else:
        logger.warning("track lyrics not found: %s by %s", track_name, artist_name)
        return ""