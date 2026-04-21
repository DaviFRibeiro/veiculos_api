import pytest
from httpx import AsyncClient


# ── GET /veiculos ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_listar_vazia(client: AsyncClient, user_headers: dict):
    resp = await client.get("/veiculos", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_listar_paginacao(client: AsyncClient, admin_headers: dict, user_headers: dict):
    # Create 3 vehicles
    for i in range(3):
        payload = {
            "marca": "Toyota", "modelo": "Corolla",
            "ano": 2020 + i, "cor": "Prata",
            "placa": f"ABC{i}D23", "preco_brl": 100000.0,
        }
        await client.post("/veiculos", json=payload, headers=admin_headers)

    resp = await client.get("/veiculos?page=1&size=2", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["pages"] == 2


@pytest.mark.asyncio
async def test_listar_filtro_marca(client: AsyncClient, admin_headers: dict, user_headers: dict):
    await client.post("/veiculos", json={
        "marca": "Honda", "modelo": "Civic", "ano": 2021,
        "cor": "Azul", "placa": "HON0A11", "preco_brl": 90000.0,
    }, headers=admin_headers)
    await client.post("/veiculos", json={
        "marca": "Toyota", "modelo": "Corolla", "ano": 2022,
        "cor": "Prata", "placa": "TOY0T22", "preco_brl": 110000.0,
    }, headers=admin_headers)

    resp = await client.get("/veiculos?marca=Honda", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["marca"] == "Honda"


@pytest.mark.asyncio
async def test_listar_filtro_preco(client: AsyncClient, admin_headers: dict, user_headers: dict):
    await client.post("/veiculos", json={
        "marca": "Barato", "modelo": "Básico", "ano": 2018,
        "cor": "Branco", "placa": "BAR0T18", "preco_brl": 30000.0,
    }, headers=admin_headers)
    await client.post("/veiculos", json={
        "marca": "Caro", "modelo": "Luxo", "ano": 2023,
        "cor": "Preto", "placa": "CAR0L23", "preco_brl": 300000.0,
    }, headers=admin_headers)

    resp = await client.get("/veiculos?minPreco=20000&maxPreco=50000", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["marca"] == "Barato"


@pytest.mark.asyncio
async def test_listar_order_by_invalido(client: AsyncClient, user_headers: dict):
    resp = await client.get("/veiculos?order_by=campo_fake", headers=user_headers)
    assert resp.status_code == 422


# ── POST /veiculos ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_criar_veiculo_sucesso(client: AsyncClient, admin_headers: dict, veiculo_payload: dict):
    resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["placa"] == "ABC1D23"
    assert data["marca"] == "Toyota"
    assert "preco_usd" in data
    assert "preco_brl" in data
    assert data["ativo"] is True


@pytest.mark.asyncio
async def test_criar_veiculo_placa_duplicada(
    client: AsyncClient, admin_headers: dict, veiculo_payload: dict
):
    await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    assert resp.status_code == 409
    assert "ABC1D23" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_criar_veiculo_payload_invalido(client: AsyncClient, admin_headers: dict):
    resp = await client.post("/veiculos", json={"marca": "X"}, headers=admin_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_criar_veiculo_preco_negativo(client: AsyncClient, admin_headers: dict):
    payload = {
        "marca": "Toyota", "modelo": "Corolla", "ano": 2022,
        "cor": "Prata", "placa": "ABC1D23", "preco_brl": -1000.0,
    }
    resp = await client.post("/veiculos", json=payload, headers=admin_headers)
    assert resp.status_code == 422


# ── GET /veiculos/{id} ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_obter_veiculo_sucesso(
    client: AsyncClient, admin_headers: dict, user_headers: dict, veiculo_payload: dict
):
    create_resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    veiculo_id = create_resp.json()["id"]

    resp = await client.get(f"/veiculos/{veiculo_id}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == veiculo_id


@pytest.mark.asyncio
async def test_obter_veiculo_nao_encontrado(client: AsyncClient, user_headers: dict):
    resp = await client.get("/veiculos/99999", headers=user_headers)
    assert resp.status_code == 404


# ── PUT /veiculos/{id} ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_put_veiculo_sucesso(
    client: AsyncClient, admin_headers: dict, veiculo_payload: dict
):
    create_resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    veiculo_id = create_resp.json()["id"]

    update = {
        "marca": "Honda", "modelo": "Civic", "ano": 2023,
        "cor": "Azul", "placa": "ABC1D23", "preco_brl": 130000.0,
    }
    resp = await client.put(f"/veiculos/{veiculo_id}", json=update, headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["marca"] == "Honda"
    assert data["modelo"] == "Civic"


@pytest.mark.asyncio
async def test_put_veiculo_nao_encontrado(client: AsyncClient, admin_headers: dict):
    update = {
        "marca": "Honda", "modelo": "Civic", "ano": 2023,
        "cor": "Azul", "placa": "ABC1D23", "preco_brl": 100000.0,
    }
    resp = await client.put("/veiculos/99999", json=update, headers=admin_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_veiculo_placa_duplicada(client: AsyncClient, admin_headers: dict):
    await client.post("/veiculos", json={
        "marca": "A", "modelo": "A", "ano": 2020,
        "cor": "A", "placa": "VEI0A20", "preco_brl": 50000.0,
    }, headers=admin_headers)
    r2 = await client.post("/veiculos", json={
        "marca": "B", "modelo": "B", "ano": 2021,
        "cor": "B", "placa": "VEI0B21", "preco_brl": 60000.0,
    }, headers=admin_headers)
    id2 = r2.json()["id"]

    update = {
        "marca": "B", "modelo": "B", "ano": 2021,
        "cor": "B", "placa": "VEI0A20", "preco_brl": 60000.0,
    }
    resp = await client.put(f"/veiculos/{id2}", json=update, headers=admin_headers)
    assert resp.status_code == 409


# ── PATCH /veiculos/{id} ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_veiculo_sucesso(
    client: AsyncClient, admin_headers: dict, veiculo_payload: dict
):
    create_resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    veiculo_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/veiculos/{veiculo_id}", json={"cor": "Azul"}, headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["cor"] == "Azul"


@pytest.mark.asyncio
async def test_patch_veiculo_sem_campos(
    client: AsyncClient, admin_headers: dict, veiculo_payload: dict
):
    create_resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    veiculo_id = create_resp.json()["id"]

    resp = await client.patch(f"/veiculos/{veiculo_id}", json={}, headers=admin_headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_veiculo_nao_encontrado(client: AsyncClient, admin_headers: dict):
    resp = await client.patch("/veiculos/99999", json={"cor": "Azul"}, headers=admin_headers)
    assert resp.status_code == 404


# ── DELETE /veiculos/{id} ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deletar_veiculo_sucesso(
    client: AsyncClient, admin_headers: dict, user_headers: dict, veiculo_payload: dict
):
    create_resp = await client.post("/veiculos", json=veiculo_payload, headers=admin_headers)
    veiculo_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/veiculos/{veiculo_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    # Soft delete: vehicle should no longer appear in listing
    get_resp = await client.get(f"/veiculos/{veiculo_id}", headers=user_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_deletar_veiculo_nao_encontrado(client: AsyncClient, admin_headers: dict):
    resp = await client.delete("/veiculos/99999", headers=admin_headers)
    assert resp.status_code == 404


# ── Relatório ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_relatorio_por_marca(client: AsyncClient, admin_headers: dict, user_headers: dict):
    for i, marca in enumerate(["Toyota", "Toyota", "Honda"]):
        await client.post("/veiculos", json={
            "marca": marca, "modelo": "M", "ano": 2020,
            "cor": "Prata", "placa": f"REL{i}M20", "preco_brl": 80000.0,
        }, headers=admin_headers)

    resp = await client.get("/veiculos/relatorios/por-marca", headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_marcas"] == 2
    assert data["total_veiculos"] == 3
    marcas = {item["marca"]: item["total"] for item in data["items"]}
    assert marcas["Toyota"] == 2
    assert marcas["Honda"] == 1
