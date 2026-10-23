"""Cartões de acesso (RN19, RN20, ADR-014)."""


def test_criar_listar_e_filtrar(client, criar_cartao):
    criar_cartao()
    criar_cartao(status="INATIVO")
    assert len(client.get("/api/cartoes").json()) == 2
    disponiveis = client.get("/api/cartoes", params={"status": "DISPONIVEL"}).json()
    assert [c["status"] for c in disponiveis] == ["DISPONIVEL"]


def test_codigo_duplicado_409(client, criar_cartao):
    criar_cartao(codigo="V-001", codigo_leitura="RFID-A")
    assert client.post("/api/cartoes", json={"codigo": "V-001", "codigo_leitura": "RFID-B", "cor": "verde"}).status_code == 409
    assert client.post("/api/cartoes", json={"codigo": "V-002", "codigo_leitura": "RFID-A", "cor": "verde"}).status_code == 409


def test_t26_inativar_cartao_em_uso_409(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    visita = criar_visita()
    assert dar_entrada(visita["id"], cartao["id"]).status_code == 200
    r = client.put(f"/api/cartoes/{cartao['id']}", json={**cartao, "status": "INATIVO"})
    assert r.status_code == 409


def test_t27_excluir_cartao_com_historico_409(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    visita = criar_visita()
    dar_entrada(visita["id"], cartao["id"])
    client.post(f"/api/visitas/{visita['id']}/saida", json={"cartao_devolvido": True})
    r = client.delete(f"/api/cartoes/{cartao['id']}")
    assert r.status_code == 409
    assert "inative" in r.json()["detail"]


def test_excluir_cartao_sem_historico_204(client, criar_cartao):
    cartao = criar_cartao()
    assert client.delete(f"/api/cartoes/{cartao['id']}").status_code == 204
    assert client.get(f"/api/cartoes/{cartao['id']}").status_code == 404


def test_t29_put_nao_aceita_em_uso_422(client, criar_cartao):
    cartao = criar_cartao()
    assert client.put(f"/api/cartoes/{cartao['id']}", json={**cartao, "status": "EM_USO"}).status_code == 422


def test_marcar_extraviado_como_recuperado(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    visita = criar_visita()
    dar_entrada(visita["id"], cartao["id"])
    client.post(f"/api/visitas/{visita['id']}/saida", json={"cartao_devolvido": False})
    assert client.get(f"/api/cartoes/{cartao['id']}").json()["status"] == "EXTRAVIADO"
    r = client.put(f"/api/cartoes/{cartao['id']}", json={**cartao, "status": "DISPONIVEL"})
    assert r.status_code == 200 and r.json()["status"] == "DISPONIVEL"
