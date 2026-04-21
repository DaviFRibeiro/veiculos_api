from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.veiculo import Veiculo


class VeiculoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, veiculo_id: int) -> Optional[Veiculo]:
        result = await self.db.execute(
            select(Veiculo).where(Veiculo.id == veiculo_id, Veiculo.ativo == True)
        )
        return result.scalar_one_or_none()

    async def get_by_placa(self, placa: str, exclude_id: Optional[int] = None) -> Optional[Veiculo]:
        query = select(Veiculo).where(Veiculo.placa == placa.upper())
        if exclude_id is not None:
            query = query.where(Veiculo.id != exclude_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        marca: Optional[str] = None,
        ano: Optional[int] = None,
        cor: Optional[str] = None,
        min_preco: Optional[float] = None,
        max_preco: Optional[float] = None,
        page: int = 1,
        size: int = 20,
        order_by: str = "id",
        order_dir: str = "asc",
    ) -> tuple[list[Veiculo], int]:
        query = select(Veiculo).where(Veiculo.ativo == True)

        if marca:
            query = query.where(Veiculo.marca.ilike(f"%{marca}%"))
        if ano:
            query = query.where(Veiculo.ano == ano)
        if cor:
            query = query.where(Veiculo.cor.ilike(f"%{cor}%"))
        if min_preco is not None:
            query = query.where(Veiculo.preco_usd >= min_preco)
        if max_preco is not None:
            query = query.where(Veiculo.preco_usd <= max_preco)

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Ordering
        col = getattr(Veiculo, order_by, Veiculo.id)
        if order_dir.lower() == "desc":
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())

        # Pagination
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def create(self, veiculo: Veiculo) -> Veiculo:
        self.db.add(veiculo)
        await self.db.flush()
        await self.db.refresh(veiculo)
        return veiculo

    async def save(self, veiculo: Veiculo) -> Veiculo:
        await self.db.flush()
        await self.db.refresh(veiculo)
        return veiculo

    async def soft_delete(self, veiculo: Veiculo) -> Veiculo:
        veiculo.ativo = False
        await self.db.flush()
        return veiculo

    async def relatorio_por_marca(self) -> list[tuple[str, int]]:
        result = await self.db.execute(
            select(Veiculo.marca, func.count(Veiculo.id).label("total"))
            .where(Veiculo.ativo == True)
            .group_by(Veiculo.marca)
            .order_by(func.count(Veiculo.id).desc())
        )
        return result.all()
