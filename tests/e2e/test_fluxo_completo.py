"""
End-to-end tests: obter token → criar veículo → listar/filtrar → detalhar → atualizar → deletar
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fluxo_completo_admin(client: AsyncClient):
    # 1. Obter token ADMIN
    token_resp = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]
    admin_h = {"Authorization": f"Bearer {token}"}

    # 2. Criar veículo
    create_resp = await client.post("/veiculos", json={
        "marca": "Toyota", "modelo": "Corolla", "ano": 2022,
        "cor": "Prata", "placa": "E2E0T22", "preco_brl": 120000.0,
    }, headers=admin_h)
    assert create_resp.status_code == 201
    veiculo = create_resp.json()
    veiculo_id = veiculo["id"]
    assert veiculo["ativo"] is True
    assert veiculo["preco_usd"] > 0

    # 3. Listar e encontrar o veículo criado
    list_resp = await client.get("/veiculos", headers=admin_h)
    assert list_resp.status_code == 200
    ids = [v["id"] for v in list_resp.json()["items"]]
    assert veiculo_id in ids

    # 4. Filtrar por marca
    filter_resp = await client.get("/veiculos?marca=Toyota", headers=admin_h)
    assert filter_resp.status_code == 200
    assert filter_resp.json()["total"] >= 1

    # 5. Detalhar
    detail_resp = await client.get(f"/veiculos/{veiculo_id}", headers=admin_h)
    assert detail_resp.status_code == 200
    assert detail_resp.json()["placa"] == "E2E0T22"

    # 6. Atualizar (PATCH)
    patch_resp = await client.patch(
        f"/veiculos/{veiculo_id}", json={"cor": "Azul Metálico"}, headers=admin_h
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["cor"] == "Azul Metálico"

    # 7. Atualizar (PUT)
    put_resp = await client.put(f"/veiculos/{veiculo_id}", json={
        "marca": "Toyota", "modelo": "Corolla Cross", "ano": 2023,
        "cor": "Branco", "placa": "E2E0T22", "preco_brl": 150000.0,
    }, headers=admin_h)
    assert put_resp.status_code == 200
    assert put_resp.json()["modelo"] == "Corolla Cross"

    # 8. Relatório
    rel_resp = await client.get("/veiculos/relatorios/por-marca", headers=admin_h)
    assert rel_resp.status_code == 200
    marcas = [i["marca"] for i in rel_resp.json()["items"]]
    assert "Toyota" in marcas

    # 9. Soft delete
    del_resp = await client.delete(f"/veiculos/{veiculo_id}", headers=admin_h)
    assert del_resp.status_code == 204

    # 10. Veículo deletado não aparece mais
    gone_resp = await client.get(f"/veiculos/{veiculo_id}", headers=admin_h)
    assert gone_resp.status_code == 404


@pytest.mark.asyncio
async def test_fluxo_user_somente_leitura(client: AsyncClient):
    # Setup: create vehicle as admin
    admin_resp = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_h = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}
    await client.post("/veiculos", json={
        "marca": "Ford", "modelo": "Ka", "ano": 2019,
        "cor": "Vermelho", "placa": "USR0F19", "preco_brl": 50000.0,
    }, headers=admin_h)

    # Get USER token
    user_resp = await client.post(
        "/auth/token",
        data={"username": "user", "password": "user123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert user_resp.status_code == 200
    user_h = {"Authorization": f"Bearer {user_resp.json()['access_token']}"}

    # USER can list
    list_resp = await client.get("/veiculos", headers=user_h)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # USER can get detail
    veiculo_id = list_resp.json()["items"][0]["id"]
    detail_resp = await client.get(f"/veiculos/{veiculo_id}", headers=user_h)
    assert detail_resp.status_code == 200

    # USER cannot create
    assert (await client.post("/veiculos", json={
        "marca": "X", "modelo": "X", "ano": 2020,
        "cor": "X", "placa": "TST0X20", "preco_brl": 40000.0,
    }, headers=user_h)).status_code == 403

    # USER cannot patch
    assert (await client.patch(
        f"/veiculos/{veiculo_id}", json={"cor": "Verde"}, headers=user_h
    )).status_code == 403

    # USER cannot delete
    assert (await client.delete(
        f"/veiculos/{veiculo_id}", headers=user_h
    )).status_code == 403


@pytest.mark.asyncio
async def test_fluxo_placa_unica(client: AsyncClient):
    admin_resp = await client.post(
        "/auth/token",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    admin_h = {"Authorization": f"Bearer {admin_resp.json()['access_token']}"}

    payload = {
        "marca": "Fiat", "modelo": "Uno", "ano": 2015,
        "cor": "Branco", "placa": "UNI0Q15", "preco_brl": 30000.0,
    }

    r1 = await client.post("/veiculos", json=payload, headers=admin_h)
    assert r1.status_code == 201

    r2 = await client.post("/veiculos", json=payload, headers=admin_h)
    assert r2.status_code == 409

    # Same placa lowercase should also conflict (normalized)
    payload_lower = {**payload, "placa": "uni0q15"}
    r3 = await client.post("/veiculos", json=payload_lower, headers=admin_h)
    assert r3.status_code == 409
