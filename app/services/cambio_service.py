from app.core.cache import get_usd_brl_rate


async def brl_to_usd(preco_brl: float) -> float:
    """Converts BRL price to USD using cached exchange rate."""
    rate = await get_usd_brl_rate()
    return round(preco_brl / rate, 6)


async def usd_to_brl(preco_usd: float) -> float:
    """Converts USD price to BRL using cached exchange rate."""
    rate = await get_usd_brl_rate()
    return round(preco_usd * rate, 2)
