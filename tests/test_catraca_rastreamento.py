"""Catraca simulada e rastreamento por pontos de passagem (RN21–RN26, T40–T49)."""
from datetime import datetime, timedelta

import pytest

from app import models as m

# Ids do seed fixo (garantir_pontos)
PORTARIA, ATENDIMENTO, PROTOCOLO, JURIDICO, TECNOLOGIA, DIRETORIA = 1, 2, 3, 4, 5, 6


def _ler(client, codigo, ponto_id, sentido="ENTRADA"):
    r = client.post("/api/catraca/passagens", json={"codigo_lido": codigo, "ponto_id": ponto_id, "sentido": sentido})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def presente(client, criar_cartao, criar_visita, dar_entrada):
    """Visita PRESENTE com destino Protocolo; devolve (visita, cartao)."""
    cartao = criar_cartao()
    visita = criar_visita(setor_destino="Protocolo")
    assert dar_entrada(visita["id"], cartao["id"]).status_code == 200
    return visita, cartao


def test_pontos_de_acesso_seed(client):
    pontos = client.get("/api/pontos-acesso").json()
    assert [p["nome"] for p in pontos][:2] == ["Catraca Portaria", "Leitor Atendimento"]
    assert pontos[0]["setor"] is None and len(pontos) == 6
    assert {p["metodos_aceitos"] for p in pontos} == {"CARTAO"}


def test_t40_codigo_desconhecido(client):
    r = _ler(client, "RFID-NAO-EXISTE", PORTARIA)
    assert r["resultado"] == "NEGADO" and "desconhecido" in r["motivo"]
    assert r["passagem"]["cartao_id"] is None and r["passagem"]["codigo_lido"] == "RFID-NAO-EXISTE"
    assert client.get(f"/api/catraca/passagens/{r['passagem']['id']}").status_code == 200  # foi gravada


def test_t41_cartao_disponivel_sem_visita(client, criar_cartao):
    c = criar_cartao()
    r = _ler(client, c["codigo_leitura"], PORTARIA)
    assert r["resultado"] == "NEGADO" and "não está em uso" in r["motivo"]
    assert r["passagem"]["cartao_id"] == c["id"]


def test_t42_cartao_de_visita_encerrada(client, presente):
    visita, cartao = presente
    client.post(f"/api/visitas/{visita['id']}/saida", json={"cartao_devolvido": True})
    assert _ler(client, cartao["codigo_leitura"], PORTARIA)["resultado"] == "NEGADO"


def test_t43_ponto_inativo(client, sessao, presente):
    _, cartao = presente
    with sessao() as db:
        db.get(m.PontoAcesso, PORTARIA).ativo = False
        db.commit()
    r = _ler(client, cartao["codigo_leitura"], PORTARIA)
    assert r["resultado"] == "NEGADO" and "inativo" in r["motivo"]


def test_t44_setor_diferente_do_destino(client, presente):
    _, cartao = presente
    r = _ler(client, cartao["codigo_leitura"], DIRETORIA)
    assert r["resultado"] == "NEGADO" and "área não autorizada" in r["motivo"]
    assert r["passagem"]["visita_id"] == presente[0]["id"]


def test_t45_area_comum_liberada(client, presente):
    _, cartao = presente
    r = _ler(client, cartao["codigo_leitura"], PORTARIA)
    assert r["resultado"] == "LIBERADO" and r["motivo"] is None


def test_t46_setor_de_destino_atualiza_ultimo_local(client, presente):
    visita, cartao = presente
    assert client.get("/api/presentes").json()[0]["ultimo_local"] == "Recepção"
    _ler(client, cartao["codigo_leitura"], PORTARIA)
    r = _ler(client, cartao["codigo_leitura"], PROTOCOLO)
    assert r["resultado"] == "LIBERADO"
    assert client.get("/api/presentes").json()[0]["ultimo_local"] == "Leitor Protocolo"
    # negada e SAIDA não mudam o último local (RN24)
    _ler(client, cartao["codigo_leitura"], DIRETORIA)
    _ler(client, cartao["codigo_leitura"], PORTARIA, "SAIDA")
    assert client.get("/api/presentes").json()[0]["ultimo_local"] == "Leitor Protocolo"


def test_t47_trajeto_em_ordem_cronologica(client, presente):
    visita, cartao = presente
    for ponto in (PORTARIA, DIRETORIA, PROTOCOLO):
        _ler(client, cartao["codigo_leitura"], ponto)
    trajeto = client.get(f"/api/visitas/{visita['id']}/passagens").json()
    assert [p["ponto_nome"] for p in trajeto] == ["Catraca Portaria", "Leitor Diretoria", "Leitor Protocolo"]
    assert [p["resultado"] for p in trajeto] == ["LIBERADO", "NEGADO", "LIBERADO"]
    horarios = [p["ocorrido_em"] for p in trajeto]
    assert horarios == sorted(horarios)


def test_trajeto_de_visita_inexistente_404(client):
    assert client.get("/api/visitas/999/passagens").status_code == 404


def test_t48_passagem_sem_put_nem_delete_405(client):
    pid = _ler(client, "QUALQUER", PORTARIA)["passagem"]["id"]
    assert client.put(f"/api/catraca/passagens/{pid}", json={"resultado": "LIBERADO"}).status_code == 405
    assert client.delete(f"/api/catraca/passagens/{pid}").status_code == 405
    assert client.delete("/api/catraca/passagens").status_code == 405
    assert client.get(f"/api/catraca/passagens/{pid}").json()["resultado"] == "NEGADO"


def test_t49_negados_hoje_no_painel(client, presente):
    _, cartao = presente
    assert client.get("/api/dashboard").json()["acessos_negados_hoje"] == 0
    _ler(client, cartao["codigo_leitura"], DIRETORIA)
    _ler(client, "RFID-DESCONHECIDO", PORTARIA)
    _ler(client, cartao["codigo_leitura"], PORTARIA)  # liberada não conta
    assert client.get("/api/dashboard").json()["acessos_negados_hoje"] == 2


def test_negados_de_ontem_nao_contam(client, sessao, hoje):
    """ADR-016: contagem por intervalo do dia local."""
    with sessao() as db:
        db.add(m.Passagem(ponto_id=PORTARIA, codigo_lido="X", sentido="ENTRADA", resultado="NEGADO",
                          motivo="teste", ocorrido_em=datetime.combine(hoje, datetime.min.time()) - timedelta(minutes=1)))
        db.add(m.Passagem(ponto_id=PORTARIA, codigo_lido="Y", sentido="ENTRADA", resultado="NEGADO",
                          motivo="teste", ocorrido_em=datetime.combine(hoje, datetime.max.time()).replace(microsecond=0)))
        db.commit()
    assert client.get("/api/dashboard").json()["acessos_negados_hoje"] == 1


def test_leitura_ponto_inexistente_404_e_sentido_invalido_422(client):
    assert client.post("/api/catraca/passagens", json={"codigo_lido": "X", "ponto_id": 99}).status_code == 404
    r = client.post("/api/catraca/passagens", json={"codigo_lido": "X", "ponto_id": 1, "sentido": "LADO"})
    assert r.status_code == 422
