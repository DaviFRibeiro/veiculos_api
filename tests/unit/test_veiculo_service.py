import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services import veiculo_service
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate, VeiculoPatch
from app.models.veiculo import Veiculo


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_veiculo(**kwargs) -> Veiculo:
    _now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    defaults = dict(
        id=1, marca="Toyota", modelo="Corolla", ano=2022,
        cor="Prata", placa="ABC1D23", preco_usd=24000.0, ativo=True,
        criado_em=_now, atualizado_em=_now,
    )
    defaults.update(kwargs)
    v = MagicMock(spec=Veiculo)
    for k, val in defaults.items():
        setattr(v, k, val)
    return v


# ── criar_veiculo ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.veiculo_service.brl_to_usd", return_value=24000.0)
@patch("app.services.veiculo_service.usd_to_brl", return_value=120000.0)
async def test_criar_veiculo_sucesso(mock_usd_to_brl, mock_brl_to_usd):
    db = AsyncMock()
    payload = VeiculoCreate(
        marca="Toyota", modelo="Corolla", ano=2022,
        cor="Prata", placa="ABC1D23", preco_brl=120000.0,
    )

    mock_repo = AsyncMock()
    mock_repo.get_by_placa.return_value = None
    mock_repo.create.return_value = make_veiculo()

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.criar_veiculo(db, payload)

    assert result.placa == "ABC1D23"
    assert result.marca == "Toyota"
    mock_repo.get_by_placa.assert_called_once_with("ABC1D23")
    mock_brl_to_usd.assert_called_once_with(120000.0)


@pytest.mark.asyncio
async def test_criar_veiculo_placa_duplicada():
    db = AsyncMock()
    payload = VeiculoCreate(
        marca="Toyota", modelo="Corolla", ano=2022,
        cor="Prata", placa="ABC1D23", preco_brl=120000.0,
    )

    mock_repo = AsyncMock()
    mock_repo.get_by_placa.return_value = make_veiculo()

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.criar_veiculo(db, payload)

    assert exc_info.value.status_code == 409
    assert "ABC1D23" in exc_info.value.detail


# ── listar_veiculos ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.veiculo_service.brl_to_usd", return_value=0.0)
@patch("app.services.veiculo_service.usd_to_brl", return_value=120000.0)
async def test_listar_veiculos_sem_filtros(mock_usd, mock_brl):
    db = AsyncMock()
    v1 = make_veiculo(id=1, placa="ABC1D23")
    v2 = make_veiculo(id=2, placa="XYZ9A87", marca="Honda", modelo="Civic")

    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = ([v1, v2], 2)

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.listar_veiculos(db)

    assert result.total == 2
    assert len(result.items) == 2
    assert result.page == 1


@pytest.mark.asyncio
@patch("app.services.veiculo_service.brl_to_usd", return_value=10000.0)
@patch("app.services.veiculo_service.usd_to_brl", return_value=50000.0)
async def test_listar_veiculos_filtro_combinado(mock_usd, mock_brl):
    db = AsyncMock()
    v1 = make_veiculo(marca="Honda", cor="Vermelho", ano=2021)

    mock_repo = AsyncMock()
    mock_repo.list_all.return_value = ([v1], 1)

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.listar_veiculos(
            db, marca="Honda", cor="Vermelho", ano=2021,
            min_preco_brl=40000.0, max_preco_brl=60000.0
        )

    assert result.total == 1
    call_kwargs = mock_repo.list_all.call_args.kwargs
    assert call_kwargs["marca"] == "Honda"
    assert call_kwargs["cor"] == "Vermelho"
    assert call_kwargs["ano"] == 2021


@pytest.mark.asyncio
async def test_listar_veiculos_order_by_invalido():
    db = AsyncMock()
    with pytest.raises(HTTPException) as exc_info:
        await veiculo_service.listar_veiculos(db, order_by="campo_inexistente")
    assert exc_info.value.status_code == 422


# ── obter_veiculo ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.veiculo_service.usd_to_brl", return_value=120000.0)
async def test_obter_veiculo_existente(mock_usd):
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_veiculo(id=1)

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.obter_veiculo(db, 1)

    assert result.id == 1


@pytest.mark.asyncio
async def test_obter_veiculo_nao_encontrado():
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.obter_veiculo(db, 999)

    assert exc_info.value.status_code == 404


# ── atualizar_veiculo (PUT) ──────────────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.veiculo_service.brl_to_usd", return_value=20000.0)
@patch("app.services.veiculo_service.usd_to_brl", return_value=100000.0)
async def test_put_veiculo_sucesso(mock_usd, mock_brl):
    db = AsyncMock()
    veiculo = make_veiculo(id=1, placa="ABC1D23")
    payload = VeiculoUpdate(
        marca="Honda", modelo="Civic", ano=2023,
        cor="Azul", placa="ABC1D23", preco_brl=100000.0,
    )

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = veiculo
    mock_repo.get_by_placa.return_value = None
    mock_repo.save.return_value = make_veiculo(marca="Honda", modelo="Civic")

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.atualizar_veiculo(db, 1, payload)

    assert result.marca == "Honda"


@pytest.mark.asyncio
async def test_put_veiculo_nao_encontrado():
    db = AsyncMock()
    payload = VeiculoUpdate(
        marca="Honda", modelo="Civic", ano=2023,
        cor="Azul", placa="ABC1D23", preco_brl=100000.0,
    )
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.atualizar_veiculo(db, 999, payload)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_put_veiculo_placa_duplicada():
    db = AsyncMock()
    veiculo = make_veiculo(id=1, placa="ABC1D23")
    payload = VeiculoUpdate(
        marca="Honda", modelo="Civic", ano=2023,
        cor="Azul", placa="XYZ9A87", preco_brl=100000.0,
    )
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = veiculo
    mock_repo.get_by_placa.return_value = make_veiculo(id=2, placa="XYZ9A87")

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.atualizar_veiculo(db, 1, payload)

    assert exc_info.value.status_code == 409


# ── atualizar_parcial_veiculo (PATCH) ────────────────────────────────────────

@pytest.mark.asyncio
@patch("app.services.veiculo_service.usd_to_brl", return_value=120000.0)
async def test_patch_veiculo_sucesso(mock_usd):
    db = AsyncMock()
    veiculo = make_veiculo(id=1, cor="Prata")
    payload = VeiculoPatch(cor="Azul")

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = veiculo
    mock_repo.save.return_value = make_veiculo(id=1, cor="Azul")

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.atualizar_parcial_veiculo(db, 1, payload)

    assert result.cor == "Azul"


@pytest.mark.asyncio
async def test_patch_veiculo_sem_campos():
    db = AsyncMock()
    payload = VeiculoPatch()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_veiculo(id=1)

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.atualizar_parcial_veiculo(db, 1, payload)

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_patch_veiculo_nao_encontrado():
    db = AsyncMock()
    payload = VeiculoPatch(cor="Azul")
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.atualizar_parcial_veiculo(db, 999, payload)

    assert exc_info.value.status_code == 404


# ── remover_veiculo ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remover_veiculo_sucesso():
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = make_veiculo(id=1)

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        await veiculo_service.remover_veiculo(db, 1)

    mock_repo.soft_delete.assert_called_once()


@pytest.mark.asyncio
async def test_remover_veiculo_nao_encontrado():
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        with pytest.raises(HTTPException) as exc_info:
            await veiculo_service.remover_veiculo(db, 999)

    assert exc_info.value.status_code == 404


# ── relatorio_por_marca ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_relatorio_por_marca():
    db = AsyncMock()
    mock_repo = AsyncMock()
    mock_repo.relatorio_por_marca.return_value = [
        ("Toyota", 5), ("Honda", 3), ("Ford", 1),
    ]

    with patch("app.services.veiculo_service.VeiculoRepository", return_value=mock_repo):
        result = await veiculo_service.relatorio_por_marca(db)

    assert result.total_marcas == 3
    assert result.total_veiculos == 9
    assert result.items[0].marca == "Toyota"
    assert result.items[0].total == 5
