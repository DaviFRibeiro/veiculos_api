import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_admin_sucesso(client: AsyncClient):
    resp = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_user_sucesso(client: AsyncClient):
    resp = await client.post(
        "/auth/token",
        data={"username": "user", "password": "user123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_senha_errada(client: AsyncClient):
    resp = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "errada"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_login_usuario_inexistente(client: AsyncClient):
    resp = await client.post(
        "/auth/token",
        data={"username": "ninguem", "password": "123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_acesso_sem_token(client: AsyncClient):
    resp = await client.get("/veiculos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_acesso_token_invalido(client: AsyncClient):
    resp = await client.get(
        "/veiculos",
        headers={"Authorization": "Bearer token_completamente_invalido"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_user_nao_pode_criar(client: AsyncClient, user_headers: dict, veiculo_payload: dict):
    resp = await client.post("/veiculos", json=veiculo_payload, headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_nao_pode_deletar(client: AsyncClient, user_headers: dict):
    resp = await client.delete("/veiculos/1", headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_nao_pode_put(client: AsyncClient, user_headers: dict):
    payload = {
        "marca": "X", "modelo": "Y", "ano": 2020,
        "cor": "Z", "placa": "TST0T00", "preco_brl": 50000.0,
    }
    resp = await client.put("/veiculos/1", json=payload, headers=user_headers)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_user_nao_pode_patch(client: AsyncClient, user_headers: dict):
    resp = await client.patch("/veiculos/1", json={"cor": "Azul"}, headers=user_headers)
    assert resp.status_code == 403
