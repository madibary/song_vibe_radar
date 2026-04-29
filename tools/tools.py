import os
from pydantic import BaseModel, Field
from tavily import TavilyClient
from langchain.tools import tool
import lyricsgenius as genius
import logging

logger = logging.getLogger(__name__)

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))
genius_api = genius.Genius(os.getenv("GENIUS_API_KEY"))
SONGS_NUMBER_lIMIT=5

class GetWordCountInput(BaseModel):
    text:str = Field(description="The text that contains the words to be counted")

class GetLyricsInput(BaseModel):
    track_name:str = Field(description="The name of the track to look lyrics for")
    artist_name:str = Field(description="The name of the artist behind the track")

class GetSongRecommendationsInput(BaseModel):
    track_name:str = Field(description="The name of the track to find recommendations based on")
    artist_name:str = Field(description="The name of the artist of the specified track")

def search_web(query: str) -> str:
    """
    A search engine optimized for AI agents, specifically for retrieving up-to-date
    information from the web.
    Returns a string with the curated answer.
    """
    try:
        response = tavily.search(query=query, include_answer=True, search_depth="advanced")
        return response["answer"]
    #check which exception it can be
    except Exception as e:
        logger.exception("Error fetching from web. query: %s, Error: %s", query, e)
        return ""
        # raise e


@tool("get_word_count", args_schema=GetWordCountInput, return_direct=True)
def get_word_count(text: str) -> str:
    """Returns the number of words in the text."""
    words = text.split()
    return f"Word count: {len(words)}"


def get_track_lyrics(track_name: str, artist_name: str) -> str:
    """
    Retrieves the lyrics of a track from Genius API based on the track name and artist name.
    Returns a string with the lyrics of the track.
    """
    try:
        song = genius_api.search_song(track_name, artist_name)
    except Exception as e:
        logger.exception("Failed to fetch lyrics for %s by %s. Error: %s", track_name, artist_name, e)
        return ""

    if song:
        lyrics = song.lyrics
        words_list = lyrics.split()
        if (len(words_list) > 40):
            first_40_words = words_list[:40]
            result_string = " ".join(first_40_words)
            return result_string
        return lyrics
        
    else:
        logger.info("track not found: %s by %s", track_name, artist_name)
        return ""

