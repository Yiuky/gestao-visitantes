"""Tipos de visita (RN01, RN04b) e endpoints de sistema."""


def test_health_e_setores(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/setores").json() == ["Atendimento", "Protocolo", "Jurídico", "Tecnologia", "Diretoria"]


def test_t01_criar_tipo_valido(client):
    r = client.post(
        "/api/tipos-visita",
        json={"nome": "Reunião técnica", "exige_documento": True, "setores_permitidos": ["Tecnologia", "Jurídico"]},
    )
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["setores_permitidos"] == ["Tecnologia", "Jurídico"]
    assert corpo["ativo"] is True and corpo["prazo_retencao_dias"] == 180
    assert client.get("/api/tipos-visita").json()[0]["nome"] == "Reunião técnica"


def test_t02_nome_duplicado_409(client, criar_tipo):
    criar_tipo(nome="Visita oficial")
    r = client.post("/api/tipos-visita", json={"nome": "visita OFICIAL"})
    assert r.status_code == 409
    assert "já existe" in r.json()["detail"]


def test_nome_curto_e_setor_invalido_422(client):
    assert client.post("/api/tipos-visita", json={"nome": "ab"}).status_code == 422
    assert client.post("/api/tipos-visita", json={"nome": "Tipo x", "setores_permitidos": ["Cozinha"]}).status_code == 422


def test_editar_e_desativar_tipo(client, criar_tipo):
    tipo = criar_tipo(nome="Entrega")
    r = client.put(f"/api/tipos-visita/{tipo['id']}", json={"nome": "Entrega de material", "ativo": False})
    assert r.status_code == 200
    assert r.json()["nome"] == "Entrega de material" and r.json()["ativo"] is False


def test_editar_para_nome_de_outro_409(client, criar_tipo):
    criar_tipo(nome="Tipo A")
    b = criar_tipo(nome="Tipo B")
    assert client.put(f"/api/tipos-visita/{b['id']}", json={"nome": "Tipo A"}).status_code == 409


def test_excluir_tipo_sem_visitas_204(client, criar_tipo):
    tipo = criar_tipo()
    assert client.delete(f"/api/tipos-visita/{tipo['id']}").status_code == 204
    assert client.get(f"/api/tipos-visita/{tipo['id']}").status_code == 404


def test_t03_excluir_tipo_com_visitas_409(client, criar_tipo, criar_visita):
    tipo = criar_tipo()
    criar_visita(tipo["id"])
    r = client.delete(f"/api/tipos-visita/{tipo['id']}")
    assert r.status_code == 409
    assert "desative" in r.json()["detail"]
