from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.schemas.veiculo import (
    VeiculoCreate,
    VeiculoListResponse,
    VeiculoPatch,
    VeiculoResponse,
    VeiculoUpdate,
)
from app.services import veiculo_service

router = APIRouter(prefix="/veiculos", tags=["Veículos"])


@router.get(
    "",
    response_model=VeiculoListResponse,
    summary="Listar veículos",
    description="Retorna veículos ativos com filtros opcionais e paginação.",
)
async def listar_veiculos(
    marca: Optional[str] = Query(None, description="Filtrar por marca (parcial)"),
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    cor: Optional[str] = Query(None, description="Filtrar por cor (parcial)"),
    min_preco: Optional[float] = Query(None, alias="minPreco", description="Preço mínimo em BRL"),
    max_preco: Optional[float] = Query(None, alias="maxPreco", description="Preço máximo em BRL"),
    page: int = Query(1, ge=1, description="Número da página"),
    size: int = Query(20, ge=1, le=100, description="Itens por página"),
    order_by: str = Query("id", description="Campo para ordenação"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$", description="Direção: asc ou desc"),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return await veiculo_service.listar_veiculos(
        db=db,
        marca=marca,
        ano=ano,
        cor=cor,
        min_preco_brl=min_preco,
        max_preco_brl=max_preco,
        page=page,
        size=size,
        order_by=order_by,
        order_dir=order_dir,
    )


@router.get(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Detalhar veículo",
)
async def obter_veiculo(
    veiculo_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    return await veiculo_service.obter_veiculo(db, veiculo_id)


@router.post(
    "",
    response_model=VeiculoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar veículo (ADMIN)",
)
async def criar_veiculo(
    payload: VeiculoCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await veiculo_service.criar_veiculo(db, payload)


@router.put(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Atualizar veículo completo (ADMIN)",
)
async def atualizar_veiculo(
    veiculo_id: int,
    payload: VeiculoUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await veiculo_service.atualizar_veiculo(db, veiculo_id, payload)


@router.patch(
    "/{veiculo_id}",
    response_model=VeiculoResponse,
    summary="Atualizar veículo parcialmente (ADMIN)",
)
async def atualizar_parcial_veiculo(
    veiculo_id: int,
    payload: VeiculoPatch,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return await veiculo_service.atualizar_parcial_veiculo(db, veiculo_id, payload)


@router.delete(
    "/{veiculo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover veículo - soft delete (ADMIN)",
)
async def remover_veiculo(
    veiculo_id: int,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    await veiculo_service.remover_veiculo(db, veiculo_id)
