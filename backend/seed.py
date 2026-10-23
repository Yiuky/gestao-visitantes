"""Carrega dados FICTÍCIOS (seção 8 do handoff). Nunca usado nos testes.

Uso (na pasta backend, com o venv ativo):  python seed.py
Só insere se o banco estiver vazio; para recomeçar, apague backend/data/visitantes.db.
"""
from datetime import datetime, time, timedelta

from sqlalchemy import func, select

from app import models as m
from app.database import SessionLocal, criar_tabelas, engine
from app.relogio import get_agora, get_hoje
from app.services.regras import garantir_pontos


def main() -> None:
    criar_tabelas(engine)
    with SessionLocal() as db:
        garantir_pontos(db)  # pontos de acesso fixos (seção 8)
        if db.scalar(select(func.count()).select_from(m.TipoVisita)):
            print("Banco já possui dados; seed ignorado.")
            return

        hoje, agora = get_hoje(), get_agora()
        ontem = hoje - timedelta(days=1)

        tipos = {
            nome: m.TipoVisita(nome=nome, exige_documento=doc, permite_veiculo=veic, setores_permitidos=setores)
            for nome, doc, veic, setores in [
                ("Atendimento ao público", False, False, "Atendimento,Protocolo"),
                ("Reunião técnica", True, True, ""),
                ("Entrega de material", True, True, "Protocolo"),
                ("Prestador de serviço", True, True, "Tecnologia"),
                ("Audiência com autoridade", True, True, "Diretoria"),
            ]
        }
        db.add_all(tipos.values())

        cartoes = [
            m.CartaoAcesso(codigo=f"V-{i:03d}", codigo_leitura=f"RFID-TESTE-{i:04d}", cor="verde" if i % 2 else "amarelo")
            for i in range(1, 11)
        ]
        db.add_all(cartoes)
        c = {cartao.codigo: cartao for cartao in cartoes}

        def em(dia, hh, mm):
            return datetime.combine(dia, time(hh, mm))

        visitas = [
            m.Visita(tipo=tipos["Atendimento ao público"], nome_civil="Ana Exemplo", setor_destino="Protocolo",
                     data_visita=hoje, horario_previsto=time(8, 30), status=m.ENCERRADA, cartao=c["V-001"],
                     cartao_devolvido=True, entrada_em=em(hoje, 8, 32), saida_em=em(hoje, 8, 55)),
            m.Visita(tipo=tipos["Reunião técnica"], nome_civil="Bruno Teste", documento="DOC-0002",
                     setor_destino="Jurídico", data_visita=hoje, horario_previsto=time(9, 0), placa="TST1A01",
                     descricao_veiculo="Carro prata (fictício)", status=m.PRESENTE, cartao=c["V-002"],
                     entrada_em=min(em(hoje, 9, 2), agora)),
            m.Visita(tipo=tipos["Prestador de serviço"], nome_civil="Carla Fictícia", nome_social="Caio Fictício",
                     documento="DOC-0003", setor_destino="Tecnologia", data_visita=hoje, horario_previsto=time(10, 15),
                     atendimento_prioritario=True),
            m.Visita(tipo=tipos["Audiência com autoridade"], nome_civil="Diego Modelo", documento="DOC-0004",
                     setor_destino="Diretoria", data_visita=hoje, horario_previsto=time(14, 0)),
            m.Visita(tipo=tipos["Entrega de material"], nome_civil="Elisa Simulada", documento="DOC-0005",
                     setor_destino="Protocolo", data_visita=ontem, horario_previsto=time(15, 30), status=m.ENCERRADA,
                     cartao=c["V-009"], cartao_devolvido=False, entrada_em=em(ontem, 15, 31), saida_em=em(ontem, 16, 10)),
        ]
        db.add_all(visitas)
        c["V-002"].status = m.EM_USO
        c["V-009"].status = m.EXTRAVIADO
        db.commit()
        print(f"Seed carregado: {len(tipos)} tipos, {len(cartoes)} cartões, {len(visitas)} visitas (dados fictícios).")


if __name__ == "__main__":
    main()
