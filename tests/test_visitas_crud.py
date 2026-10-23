"""CRUD, validações por tipo e pesquisa de visitas (RN02–RN12)."""
from datetime import timedelta

import pytest


def test_t10_lista_vazia(client):
    r = client.get("/api/visitas")
    assert r.status_code == 200 and r.json() == []


def test_criar_visita_valida_agendada(client, criar_visita):
    v = criar_visita(nome_social="Nome Social Teste", documento="DOC-0001")
    assert v["status"] == "AGENDADA"
    assert v["nome_exibido"] == "Nome Social Teste"
    assert v["documento"] == "DOC-0001"  # detalhe traz o completo
    assert v["documento_mascarado"] == "DOC-••01"


def test_t04_tipo_inativo_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo(ativo=False)
    r = client.post("/api/visitas", json=dados_visita(tipo["id"]))
    assert r.status_code == 422
    assert "inativo" in r.json()["detail"]


def test_t05_setor_nao_permitido_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo(setores_permitidos=["Protocolo"])
    r = client.post("/api/visitas", json=dados_visita(tipo["id"], setor_destino="Diretoria"))
    assert r.status_code == 422
    assert "Protocolo" in r.json()["detail"]


def test_t06_documento_obrigatorio_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo(exige_documento=True)
    r = client.post("/api/visitas", json=dados_visita(tipo["id"], documento="   "))
    assert r.status_code == 422
    assert "exige documento" in r.json()["detail"]


def test_t07_placa_em_tipo_sem_veiculo_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo(permite_veiculo=False)
    r = client.post("/api/visitas", json=dados_visita(tipo["id"], placa="TST1A01"))
    assert r.status_code == 422
    assert "não permite veículo" in r.json()["detail"]


@pytest.mark.parametrize("placa", ["AB12345", "TST12", "1234567"])
def test_t08_placa_invalida_422(client, criar_tipo, dados_visita, placa):
    tipo = criar_tipo(permite_veiculo=True)
    assert client.post("/api/visitas", json=dados_visita(tipo["id"], placa=placa)).status_code == 422


def test_placa_normalizada(client, criar_visita):
    assert criar_visita(placa="tst-1a01")["placa"] == "TST1A01"
    assert criar_visita(placa="")["placa"] is None


def test_t09_vaga_reservada_sem_placa_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo(permite_veiculo=True)
    r = client.post("/api/visitas", json=dados_visita(tipo["id"], vaga_reservada=True))
    assert r.status_code == 422


def test_observacao_maior_que_100_422(client, criar_tipo, dados_visita):
    tipo = criar_tipo()
    assert client.post("/api/visitas", json=dados_visita(tipo["id"], observacao="x" * 101)).status_code == 422


def test_t11_busca_por_parte_do_nome_social(client, criar_visita):
    criar_visita(nome_civil="Carla Fictícia", nome_social="Caio Fictício")
    criar_visita(nome_civil="Bruno Teste")
    r = client.get("/api/visitas", params={"q": "caio"}).json()
    assert [v["nome_exibido"] for v in r] == ["Caio Fictício"]
    # busca pelo nome civil também encontra, mas exibe o nome social
    assert [v["nome_exibido"] for v in client.get("/api/visitas", params={"q": "carla"}).json()] == ["Caio Fictício"]


def test_filtros_setor_tipo_data_status(client, criar_tipo, criar_visita, hoje):
    t1, t2 = criar_tipo()["id"], criar_tipo()["id"]
    criar_visita(t1, setor_destino="Protocolo")
    criar_visita(t2, setor_destino="Diretoria", data_visita=(hoje + timedelta(days=1)).isoformat())
    assert len(client.get("/api/visitas", params={"setor": "Protocolo"}).json()) == 1
    assert len(client.get("/api/visitas", params={"tipo_id": t2}).json()) == 1
    assert len(client.get("/api/visitas", params={"data": hoje.isoformat()}).json()) == 1
    assert len(client.get("/api/visitas", params={"status": "AGENDADA"}).json()) == 2
    assert client.get("/api/visitas", params={"status": "QUALQUER"}).status_code == 422


def test_t12_listagem_nao_expoe_documento(client, criar_visita):
    criar_visita(documento="DOC-1234", nome_social="Social")
    item = client.get("/api/visitas").json()[0]
    assert "documento" not in item and "nome_civil" not in item
    assert item["documento_mascarado"] == "DOC-••34"


def test_t28_ordenacao_prioritarios_primeiro(client, criar_visita):
    criar_visita(nome_civil="Comum Nove", horario_previsto="09:00")
    criar_visita(nome_civil="Prioritaria Nove", horario_previsto="09:00", atendimento_prioritario=True)
    criar_visita(nome_civil="Comum Oito", horario_previsto="08:00")
    nomes = [v["nome_exibido"] for v in client.get("/api/visitas").json()]
    assert nomes == ["Comum Oito", "Prioritaria Nove", "Comum Nove"]


def test_editar_visita_agendada(client, criar_visita, dados_visita):
    v = criar_visita()
    r = client.put(f"/api/visitas/{v['id']}", json=dados_visita(v["tipo_visita_id"], nome_civil="Nome Editado"))
    assert r.status_code == 200 and r.json()["nome_civil"] == "Nome Editado"


def test_editar_aplica_regras_do_tipo(client, criar_tipo, criar_visita, dados_visita):
    tipo = criar_tipo(exige_documento=True)
    v = criar_visita(tipo["id"], documento="DOC-0001")
    r = client.put(f"/api/visitas/{v['id']}", json=dados_visita(tipo["id"], documento=None))
    assert r.status_code == 422


def test_editar_visita_de_tipo_desativado_depois(client, criar_tipo, criar_visita, dados_visita):
    """ADR-013: desativar o tipo não trava a edição das visitas já agendadas; trocar para tipo inativo trava."""
    tipo = criar_tipo()
    v = criar_visita(tipo["id"])
    client.put(f"/api/tipos-visita/{tipo['id']}", json={"nome": tipo["nome"], "ativo": False})
    assert client.put(f"/api/visitas/{v['id']}", json=dados_visita(tipo["id"], nome_civil="Outro Nome")).status_code == 200
    inativo = criar_tipo(ativo=False)
    assert client.put(f"/api/visitas/{v['id']}", json=dados_visita(inativo["id"])).status_code == 422


def test_t25_put_nao_muda_status(client, criar_visita, dados_visita):
    v = criar_visita()
    corpo = {**dados_visita(v["tipo_visita_id"]), "status": "ENCERRADA", "cartao_id": 99, "entrada_em": "2026-10-23T08:00:00"}
    r = client.put(f"/api/visitas/{v['id']}", json=corpo)
    assert r.status_code == 200
    assert r.json()["status"] == "AGENDADA" and r.json()["cartao_id"] is None and r.json()["entrada_em"] is None


def test_t22_excluir_agendada_204(client, criar_visita):
    v = criar_visita()
    assert client.delete(f"/api/visitas/{v['id']}").status_code == 204
    assert client.get(f"/api/visitas/{v['id']}").status_code == 404


def test_excluir_cancelada_204(client, criar_visita):
    v = criar_visita()
    client.post(f"/api/visitas/{v['id']}/cancelar")
    assert client.delete(f"/api/visitas/{v['id']}").status_code == 204


def test_visita_inexistente_404(client):
    assert client.get("/api/visitas/999").status_code == 404
    assert client.delete("/api/visitas/999").status_code == 404
