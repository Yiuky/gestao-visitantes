"""Painel: indicadores por COUNT e lista de presentes (T30–T39)."""
from datetime import timedelta

import pytest


def _painel(client):
    return client.get("/api/dashboard").json()


def test_t30_banco_vazio_tudo_zero(client, hoje):
    p = _painel(client)
    assert p.pop("data_referencia") == hoje.isoformat()
    assert set(p.values()) == {0}


def test_t31_visita_de_hoje_conta(client, criar_visita):
    criar_visita()
    assert _painel(client)["visitas_do_dia"] == 1


def test_t32_visita_de_amanha_nao_conta(client, criar_visita, hoje):
    criar_visita(data_visita=(hoje + timedelta(days=1)).isoformat())
    criar_visita(data_visita=(hoje - timedelta(days=1)).isoformat())
    assert _painel(client)["visitas_do_dia"] == 0


def test_t33_cancelar_visita_de_hoje(client, criar_visita):
    v = criar_visita()
    criar_visita()
    assert _painel(client)["visitas_do_dia"] == 2
    client.post(f"/api/visitas/{v['id']}/cancelar")
    assert _painel(client)["visitas_do_dia"] == 1


def test_t34_t35_entrada_conta_presente_e_veiculo(client, criar_visita, dar_entrada):
    dar_entrada(criar_visita()["id"])
    p = _painel(client)
    assert (p["presentes"], p["veiculos_no_patio"]) == (1, 0)
    dar_entrada(criar_visita(placa="TST1A01")["id"])
    p = _painel(client)
    assert (p["presentes"], p["veiculos_no_patio"]) == (2, 1)


def test_t36_saida_com_devolucao(client, criar_visita, dar_entrada):
    v = criar_visita(placa="TST1A01")
    dar_entrada(v["id"])
    client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": True})
    p = _painel(client)
    assert (p["presentes"], p["encerradas_do_dia"], p["veiculos_no_patio"], p["cartoes_pendentes"]) == (0, 1, 0, 0)
    assert p["visitas_do_dia"] == 1  # encerrada continua sendo visita do dia


def test_t37_saida_sem_devolucao(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": False})
    assert _painel(client)["cartoes_pendentes"] == 1


def test_cartao_recuperado_sai_dos_pendentes(client, criar_cartao, criar_visita, dar_entrada):
    c = criar_cartao()
    v = criar_visita()
    dar_entrada(v["id"], c["id"])
    client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": False})
    client.put(f"/api/cartoes/{c['id']}", json={**c, "status": "DISPONIVEL"})
    assert _painel(client)["cartoes_pendentes"] == 0


def test_t38_presentes_lista_so_presente_com_recepcao(client, criar_visita, dar_entrada):
    presente = criar_visita(nome_civil="Nome Civil", nome_social="Presente Social", setor_destino="Protocolo")
    dar_entrada(presente["id"])
    criar_visita(nome_civil="Ainda Agendada")
    encerrada = criar_visita(nome_civil="Ja Saiu")
    dar_entrada(encerrada["id"])
    client.post(f"/api/visitas/{encerrada['id']}/saida", json={"cartao_devolvido": True})

    lista = client.get("/api/presentes").json()
    assert [p["nome_exibido"] for p in lista] == ["Presente Social"]
    item = lista[0]
    assert item["ultimo_local"] == "Recepção" and item["setor_destino"] == "Protocolo"
    assert item["cartao_codigo"] and item["desde"]
    assert "documento" not in item and "nome_civil" not in item


def test_t39_excluir_visita_de_hoje(client, criar_visita):
    v = criar_visita()
    assert _painel(client)["visitas_do_dia"] == 1
    client.delete(f"/api/visitas/{v['id']}")
    assert _painel(client)["visitas_do_dia"] == 0


@pytest.mark.parametrize("data_ref", ["2026-10-24"])
def test_data_referencia_injetavel(client, criar_visita, hoje, data_ref):
    """A data de referência vem do relógio injetável: outro "hoje" muda o que é "do dia"."""
    from datetime import date

    from app.main import app
    from app.relogio import get_hoje

    criar_visita()
    app.dependency_overrides[get_hoje] = lambda: date.fromisoformat(data_ref)
    p = _painel(client)
    assert p["data_referencia"] == data_ref and p["visitas_do_dia"] == 0
