import logging
import time

from helpers.cache import _get_client

logger = logging.getLogger(__name__)

_IP_LIMIT = 10      # requests per IP per hour
_IP_WINDOW = 3600   # seconds
_DAILY_BUDGET = 200 # total requests per day across all users


def _today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def check_ip_limit(ip: str) -> bool:
    """Return False if this IP has exceeded its hourly limit."""
    try:
        client = _get_client()
        if client is None:
            return True
        key = f"rl:ip:{ip}"
        count = client.incr(key)
        if count == 1:
            client.expire(key, _IP_WINDOW)
        return count <= _IP_LIMIT
    except Exception as e:
        logger.warning("IP rate limit check failed: %s", e)
        return True  # fail open


def check_global_budget() -> bool:
    """Return False if the daily request budget is exhausted."""
    try:
        client = _get_client()
        if client is None:
            return True
        key = f"rl:global:{_today()}"
        count = client.incr(key)
        if count == 1:
            client.expire(key, 86400)
        return count <= _DAILY_BUDGET
    except Exception as e:
        logger.warning("Global budget check failed: %s", e)
        return True  # fail open
