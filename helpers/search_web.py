import os
from tavily import TavilyClient
import logging

logger = logging.getLogger(__name__)

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))
SONGS_NUMBER_lIMIT=5


def search_web(query: str) -> str:
    """
    A search engine optimized for AI agents, specifically for retrieving up-to-date
    information from the web.
    Returns a string with the curated answer.
    """
    try:
        response = tavily.search(query=query, include_answer=True, search_depth="advanced")
        return response["answer"]
    
    except Exception as e:
        logger.exception("Error fetching from web. query: %s, Error: %s", query, e)
        return ""


