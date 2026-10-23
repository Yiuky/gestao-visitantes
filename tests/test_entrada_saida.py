"""Entrada, saída, cancelamento e exclusão de registros de presença (RN05–RN07, RN13–RN17)."""
from datetime import timedelta


def _cartao(client, cartao_id):
    return client.get(f"/api/cartoes/{cartao_id}").json()


def test_t13_entrada_ok(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    v = criar_visita()
    r = dar_entrada(v["id"], cartao["id"])
    assert r.status_code == 200
    assert r.json()["status"] == "PRESENTE" and r.json()["cartao_codigo"] == cartao["codigo"]
    assert r.json()["entrada_em"] is not None
    assert _cartao(client, cartao["id"])["status"] == "EM_USO"


def test_t14_entrada_com_cartao_em_uso_409(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    dar_entrada(criar_visita()["id"], cartao["id"])
    r = dar_entrada(criar_visita()["id"], cartao["id"])
    assert r.status_code == 409
    assert "não está disponível" in r.json()["detail"]


def test_entrada_com_cartao_inativo_ou_inexistente(client, criar_cartao, criar_visita, dar_entrada):
    inativo = criar_cartao(status="INATIVO")
    assert dar_entrada(criar_visita()["id"], inativo["id"]).status_code == 409
    assert dar_entrada(criar_visita()["id"], 999).status_code == 404


def test_t15_entrada_fora_da_data_409(client, criar_visita, dar_entrada, hoje):
    v = criar_visita(data_visita=(hoje + timedelta(days=1)).isoformat())
    r = dar_entrada(v["id"])
    assert r.status_code == 409
    assert "dia da visita" in r.json()["detail"]


def test_t16_placa_ja_no_patio_409(client, criar_visita, dar_entrada):
    assert dar_entrada(criar_visita(placa="TST1A01")["id"]).status_code == 200
    r = dar_entrada(criar_visita(placa="TST1A01")["id"])
    assert r.status_code == 409
    assert "pátio" in r.json()["detail"]


def test_entrada_duas_vezes_409(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    assert dar_entrada(v["id"]).status_code == 409


def test_t17_saida_com_devolucao(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    v = criar_visita()
    dar_entrada(v["id"], cartao["id"])
    r = client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": True})
    assert r.status_code == 200
    assert r.json()["status"] == "ENCERRADA" and r.json()["cartao_devolvido"] is True and r.json()["saida_em"]
    assert _cartao(client, cartao["id"])["status"] == "DISPONIVEL"


def test_t18_saida_sem_devolucao(client, criar_cartao, criar_visita, dar_entrada):
    cartao = criar_cartao()
    v = criar_visita()
    dar_entrada(v["id"], cartao["id"])
    r = client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": False})
    assert r.status_code == 200
    assert r.json()["status"] == "ENCERRADA" and r.json()["cartao_devolvido"] is False
    assert _cartao(client, cartao["id"])["status"] == "EXTRAVIADO"


def test_saida_exige_cartao_devolvido_422(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    assert client.post(f"/api/visitas/{v['id']}/saida", json={}).status_code == 422


def test_t19_saida_de_agendada_409(client, criar_visita):
    v = criar_visita()
    assert client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": True}).status_code == 409


def test_t20_excluir_presente_409(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    assert client.delete(f"/api/visitas/{v['id']}").status_code == 409
    assert client.get(f"/api/visitas/{v['id']}").status_code == 200


def test_t21_excluir_encerrada_409(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": True})
    assert client.delete(f"/api/visitas/{v['id']}").status_code == 409


def test_cancelar_agendada(client, criar_visita):
    v = criar_visita()
    r = client.post(f"/api/visitas/{v['id']}/cancelar")
    assert r.status_code == 200 and r.json()["status"] == "CANCELADA"
    # cancelada não volta: nova entrada ou novo cancelamento → 409
    assert client.post(f"/api/visitas/{v['id']}/cancelar").status_code == 409


def test_t23_cancelar_presente_409(client, criar_visita, dar_entrada):
    v = criar_visita()
    dar_entrada(v["id"])
    assert client.post(f"/api/visitas/{v['id']}/cancelar").status_code == 409


def test_t24_editar_encerrada_409(client, criar_visita, dar_entrada, dados_visita):
    v = criar_visita()
    dar_entrada(v["id"])
    client.post(f"/api/visitas/{v['id']}/saida", json={"cartao_devolvido": True})
    assert client.put(f"/api/visitas/{v['id']}", json=dados_visita(v["tipo_visita_id"])).status_code == 409


def test_editar_presente_nao_fura_regras(client, criar_visita, dar_entrada, dados_visita, hoje):
    """ADR-013: presente não muda de data nem assume placa de veículo já no pátio."""
    dar_entrada(criar_visita(placa="TST1A01")["id"])
    v = criar_visita()
    dar_entrada(v["id"])
    tipo = v["tipo_visita_id"]
    amanha = (hoje + timedelta(days=1)).isoformat()
    assert client.put(f"/api/visitas/{v['id']}", json=dados_visita(tipo, data_visita=amanha)).status_code == 409
    assert client.put(f"/api/visitas/{v['id']}", json=dados_visita(tipo, placa="TST1A01")).status_code == 409
    r = client.put(f"/api/visitas/{v['id']}", json=dados_visita(tipo, nome_civil="Corrigido"))
    assert r.status_code == 200 and r.json()["status"] == "PRESENTE"
