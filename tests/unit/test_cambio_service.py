import pytest
from unittest.mock import AsyncMock, patch

from app.services.cambio_service import brl_to_usd, usd_to_brl
from app.core.cache import get_usd_brl_rate, _fetch_from_awesome, _fetch_from_frankfurter


@pytest.mark.asyncio
@patch("app.services.cambio_service.get_usd_brl_rate", return_value=5.0)
async def test_brl_to_usd(mock_rate):
    result = await brl_to_usd(50000.0)
    assert result == 10000.0


@pytest.mark.asyncio
@patch("app.services.cambio_service.get_usd_brl_rate", return_value=5.0)
async def test_usd_to_brl(mock_rate):
    result = await usd_to_brl(10000.0)
    assert result == 50000.0


@pytest.mark.asyncio
@patch("app.services.cambio_service.get_usd_brl_rate", return_value=5.75)
async def test_conversao_arredondamento(mock_rate):
    result = await usd_to_brl(1.0)
    assert result == 5.75


@pytest.mark.asyncio
async def test_get_usd_brl_rate_from_cache():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = "5.50"

    with patch("app.core.cache.get_redis", return_value=mock_redis):
        rate = await get_usd_brl_rate()

    assert rate == 5.50
    mock_redis.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_usd_brl_rate_from_awesome_api():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with patch("app.core.cache.get_redis", return_value=mock_redis), \
         patch("app.core.cache._fetch_from_awesome", return_value=5.20) as mock_awesome:
        rate = await get_usd_brl_rate()

    assert rate == 5.20
    mock_awesome.assert_called_once()


@pytest.mark.asyncio
async def test_get_usd_brl_rate_fallback_to_frankfurter():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with patch("app.core.cache.get_redis", return_value=mock_redis), \
         patch("app.core.cache._fetch_from_awesome", side_effect=Exception("AwesomeAPI down")), \
         patch("app.core.cache._fetch_from_frankfurter", return_value=5.30) as mock_frank:
        rate = await get_usd_brl_rate()

    assert rate == 5.30
    mock_frank.assert_called_once()


@pytest.mark.asyncio
async def test_get_usd_brl_rate_ambos_falham():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("app.core.cache.get_redis", return_value=mock_redis), \
         patch("app.core.cache._fetch_from_awesome", side_effect=Exception("down")), \
         patch("app.core.cache._fetch_from_frankfurter", side_effect=Exception("down")):
        with pytest.raises(RuntimeError, match="cotação do dólar"):
            await get_usd_brl_rate()


@pytest.mark.asyncio
async def test_get_usd_brl_rate_redis_indisponivel():
    """Even if Redis is down, the rate is fetched from the API."""
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = Exception("Redis connection refused")

    with patch("app.core.cache.get_redis", return_value=mock_redis), \
         patch("app.core.cache._fetch_from_awesome", return_value=5.10):
        rate = await get_usd_brl_rate()

    assert rate == 5.10


@pytest.mark.asyncio
async def test_taxa_armazenada_no_cache():
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True

    with patch("app.core.cache.get_redis", return_value=mock_redis), \
         patch("app.core.cache._fetch_from_awesome", return_value=5.25):
        await get_usd_brl_rate()

    mock_redis.set.assert_called_once()
    call_args = mock_redis.set.call_args
    assert call_args[0][1] == "5.25"
