from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.veiculo import Veiculo
from app.repositories.veiculo_repo import VeiculoRepository
from app.schemas.veiculo import (
    VeiculoCreate,
    VeiculoListResponse,
    VeiculoPatch,
    VeiculoResponse,
    VeiculoUpdate,
    RelatorioMarcaResponse,
    RelatorioMarcaItem,
)
from app.services.cambio_service import brl_to_usd, usd_to_brl

VALID_ORDER_FIELDS = {"id", "marca", "modelo", "ano", "cor", "placa", "preco_usd", "criado_em"}


async def _to_response(veiculo: Veiculo) -> VeiculoResponse:
    preco_brl = await usd_to_brl(veiculo.preco_usd)
    return VeiculoResponse(
        id=veiculo.id,
        marca=veiculo.marca,
        modelo=veiculo.modelo,
        ano=veiculo.ano,
        cor=veiculo.cor,
        placa=veiculo.placa,
        preco_usd=veiculo.preco_usd,
        preco_brl=preco_brl,
        ativo=veiculo.ativo,
        criado_em=veiculo.criado_em,
        atualizado_em=veiculo.atualizado_em,
    )


async def listar_veiculos(
    db: AsyncSession,
    marca: Optional[str] = None,
    ano: Optional[int] = None,
    cor: Optional[str] = None,
    min_preco_brl: Optional[float] = None,
    max_preco_brl: Optional[float] = None,
    page: int = 1,
    size: int = 20,
    order_by: str = "id",
    order_dir: str = "asc",
) -> VeiculoListResponse:
    if order_by not in VALID_ORDER_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Campo de ordenação inválido. Opções: {sorted(VALID_ORDER_FIELDS)}",
        )

    # Convert BRL price filter to USD for query
    min_preco_usd = await brl_to_usd(min_preco_brl) if min_preco_brl is not None else None
    max_preco_usd = await brl_to_usd(max_preco_brl) if max_preco_brl is not None else None

    repo = VeiculoRepository(db)
    veiculos, total = await repo.list_all(
        marca=marca,
        ano=ano,
        cor=cor,
        min_preco=min_preco_usd,
        max_preco=max_preco_usd,
        page=page,
        size=size,
        order_by=order_by,
        order_dir=order_dir,
    )

    items = [await _to_response(v) for v in veiculos]
    pages = max(1, (total + size - 1) // size)

    return VeiculoListResponse(items=items, total=total, page=page, size=size, pages=pages)


async def obter_veiculo(db: AsyncSession, veiculo_id: int) -> VeiculoResponse:
    repo = VeiculoRepository(db)
    veiculo = await repo.get_by_id(veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado")
    return await _to_response(veiculo)


async def criar_veiculo(db: AsyncSession, payload: VeiculoCreate) -> VeiculoResponse:
    repo = VeiculoRepository(db)

    existing = await repo.get_by_placa(payload.placa)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Já existe um veículo com a placa {payload.placa}",
        )

    preco_usd = await brl_to_usd(payload.preco_brl)

    veiculo = Veiculo(
        marca=payload.marca,
        modelo=payload.modelo,
        ano=payload.ano,
        cor=payload.cor,
        placa=payload.placa,
        preco_usd=preco_usd,
    )

    veiculo = await repo.create(veiculo)
    return await _to_response(veiculo)


async def atualizar_veiculo(
    db: AsyncSession, veiculo_id: int, payload: VeiculoUpdate
) -> VeiculoResponse:
    repo = VeiculoRepository(db)
    veiculo = await repo.get_by_id(veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado")

    # Check placa uniqueness excluding current vehicle
    if payload.placa != veiculo.placa:
        existing = await repo.get_by_placa(payload.placa, exclude_id=veiculo_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um veículo com a placa {payload.placa}",
            )

    veiculo.marca = payload.marca
    veiculo.modelo = payload.modelo
    veiculo.ano = payload.ano
    veiculo.cor = payload.cor
    veiculo.placa = payload.placa
    veiculo.preco_usd = await brl_to_usd(payload.preco_brl)

    veiculo = await repo.save(veiculo)
    return await _to_response(veiculo)


async def atualizar_parcial_veiculo(
    db: AsyncSession, veiculo_id: int, payload: VeiculoPatch
) -> VeiculoResponse:
    repo = VeiculoRepository(db)
    veiculo = await repo.get_by_id(veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado")

    update_data = payload.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nenhum campo fornecido para atualização",
        )

    if "placa" in update_data and update_data["placa"] != veiculo.placa:
        existing = await repo.get_by_placa(update_data["placa"], exclude_id=veiculo_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um veículo com a placa {update_data['placa']}",
            )

    if "preco_brl" in update_data:
        veiculo.preco_usd = await brl_to_usd(update_data.pop("preco_brl"))

    for field, value in update_data.items():
        setattr(veiculo, field, value)

    veiculo = await repo.save(veiculo)
    return await _to_response(veiculo)


async def remover_veiculo(db: AsyncSession, veiculo_id: int) -> None:
    repo = VeiculoRepository(db)
    veiculo = await repo.get_by_id(veiculo_id)
    if not veiculo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado")
    await repo.soft_delete(veiculo)


async def relatorio_por_marca(db: AsyncSession) -> RelatorioMarcaResponse:
    repo = VeiculoRepository(db)
    rows = await repo.relatorio_por_marca()
    items = [RelatorioMarcaItem(marca=marca, total=total) for marca, total in rows]
    return RelatorioMarcaResponse(
        items=items,
        total_marcas=len(items),
        total_veiculos=sum(i.total for i in items),
    )
