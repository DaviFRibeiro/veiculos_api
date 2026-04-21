import logging
from typing import Optional

import httpx
import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[aioredis.Redis] = None

AWESOME_API_URL = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
FRANKFURTER_API_URL = "https://api.frankfurter.app/latest?from=USD&to=BRL"
REDIS_KEY = "usd_brl_rate"


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def _fetch_from_awesome() -> Optional[float]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(AWESOME_API_URL)
        response.raise_for_status()
        data = response.json()
        return float(data["USDBRL"]["bid"])


async def _fetch_from_frankfurter() -> Optional[float]:
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(FRANKFURTER_API_URL)
        response.raise_for_status()
        data = response.json()
        return float(data["rates"]["BRL"])


async def get_usd_brl_rate() -> float:
    """
    Returns the USD to BRL exchange rate.
    Uses Redis cache with TTL. Falls back to Frankfurter API if AwesomeAPI fails.
    """
    redis = get_redis()

    try:
        cached = await redis.get(REDIS_KEY)
        if cached:
            logger.debug("USD rate from cache: %s", cached)
            return float(cached)
    except Exception as e:
        logger.warning("Redis unavailable, fetching fresh rate: %s", e)

    rate: Optional[float] = None

    try:
        rate = await _fetch_from_awesome()
        logger.info("USD rate from AwesomeAPI: %s", rate)
    except Exception as e:
        logger.warning("AwesomeAPI failed (%s), trying Frankfurter fallback", e)

    if rate is None:
        try:
            rate = await _fetch_from_frankfurter()
            logger.info("USD rate from Frankfurter: %s", rate)
        except Exception as e:
            logger.error("All exchange rate sources failed: %s", e)
            raise RuntimeError("Não foi possível obter a cotação do dólar") from e

    try:
        await redis.set(REDIS_KEY, str(rate), ex=settings.USD_CACHE_TTL)
    except Exception as e:
        logger.warning("Could not cache USD rate in Redis: %s", e)

    return rate


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None
