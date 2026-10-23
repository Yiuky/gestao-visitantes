"""Indicadores do painel e lista de presentes. Toda contagem é COUNT no banco, nunca em Python."""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m


def _contar(db: Session, modelo, *condicoes) -> int:
    return db.scalar(select(func.count()).select_from(modelo).where(*condicoes))


def indicadores(db: Session, hoje: date) -> dict:
    V = m.Visita
    return {
        "data_referencia": hoje,
        # obrigatórios
        "visitas_do_dia": _contar(db, V, V.data_visita == hoje, V.status != m.CANCELADA),
        "presentes": _contar(db, V, V.status == m.PRESENTE),
        "encerradas_do_dia": _contar(db, V, V.status == m.ENCERRADA, V.data_visita == hoje),
        # complementares
        "veiculos_no_patio": _contar(db, V, V.status == m.PRESENTE, V.placa.is_not(None)),
        "cartoes_pendentes": _contar(db, m.CartaoAcesso, m.CartaoAcesso.status == m.EXTRAVIADO),
        "acessos_negados_hoje": 0,  # ADR-017: COUNT real na S4, quando a tabela passagens existir
    }


def presentes(db: Session) -> list[dict]:
    visitas = db.scalars(select(m.Visita).where(m.Visita.status == m.PRESENTE).order_by(m.Visita.entrada_em)).all()
    return [
        {
            "visita_id": v.id,
            "nome_exibido": v.nome_exibido,
            "setor_destino": v.setor_destino,
            "cartao_codigo": v.cartao.codigo if v.cartao else None,
            "placa": v.placa,
            "ultimo_local": "Recepção",  # RN24 sem passagens; a S4 passa a usar a última passagem liberada
            "ultimo_local_em": v.entrada_em,
            "desde": v.entrada_em,
        }
        for v in visitas
    ]
