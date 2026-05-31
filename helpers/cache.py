import logging
import os
import redis

logger = logging.getLogger(__name__)

_client = None
_unavailable = False


def _get_client():
    global _client, _unavailable
    if _unavailable:
        return None
    if _client is not None:
        return _client
    url = os.getenv("REDIS_URL")
    if not url:
        _unavailable = True
        return None
    try:
        _client = redis.from_url(url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
        _client.ping()
        logger.info("Redis cache connected.")
    except Exception as e:
        logger.warning("Redis unavailable, running without cache: %s", e)
        _unavailable = True
        _client = None
    return _client


def make_key(name: str, artist: str) -> str:
    return f"vibe:{name.lower().strip()}:{artist.lower().strip()}"


def cache_get(name: str, artist: str) -> str | None:
    try:
        client = _get_client()
        if client is None:
            return None
        return client.get(make_key(name, artist))
    except Exception as e:
        logger.warning("Cache get error: %s", e)
        return None


def cache_set(name: str, artist: str, value: str) -> None:
    try:
        client = _get_client()
        if client is None:
            return
        client.set(make_key(name, artist), value, ex=60 * 60 * 24 * 3)
    except Exception as e:
        logger.warning("Cache set error: %s", e)
