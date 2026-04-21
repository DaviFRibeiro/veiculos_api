from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.veiculo import RelatorioMarcaResponse
from app.services import veiculo_service

router = APIRouter(prefix="/veiculos/relatorios", tags=["Relatórios"])


@router.get(
    "/por-marca",
    response_model=RelatorioMarcaResponse,
    summary="Relatório de veículos por marca",
    description="Retorna a contagem de veículos ativos agrupados por marca.",
)
async def relatorio_por_marca(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return await veiculo_service.relatorio_por_marca(db)
