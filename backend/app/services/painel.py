"""Indicadores do painel e lista de presentes. Toda contagem é COUNT no banco, nunca em Python."""
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m


def _contar(db: Session, modelo, *condicoes) -> int:
    return db.scalar(select(func.count()).select_from(modelo).where(*condicoes))


def indicadores(db: Session, hoje: date) -> dict:
    V, P = m.Visita, m.Passagem
    # ADR-016: intervalo [hoje 00:00, amanhã 00:00) no horário local gravado no banco
    inicio = datetime.combine(hoje, time.min)
    fim = inicio + timedelta(days=1)
    return {
        "data_referencia": hoje,
        # obrigatórios
        "visitas_do_dia": _contar(db, V, V.data_visita == hoje, V.status != m.CANCELADA),
        "presentes": _contar(db, V, V.status == m.PRESENTE),
        "encerradas_do_dia": _contar(db, V, V.status == m.ENCERRADA, V.data_visita == hoje),
        # complementares
        "veiculos_no_patio": _contar(db, V, V.status == m.PRESENTE, V.placa.is_not(None)),
        "cartoes_pendentes": _contar(db, m.CartaoAcesso, m.CartaoAcesso.status == m.EXTRAVIADO),
        "acessos_negados_hoje": _contar(db, P, P.resultado == m.NEGADO, P.ocorrido_em >= inicio, P.ocorrido_em < fim),
    }


def ultimo_local(db: Session, visita: m.Visita) -> tuple[str, datetime | None]:
    """RN24: ponto da última passagem LIBERADA de ENTRADA; sem passagens, "Recepção"."""
    p = db.scalar(
        select(m.Passagem)
        .where(m.Passagem.visita_id == visita.id, m.Passagem.resultado == m.LIBERADO, m.Passagem.sentido == m.ENTRADA)
        .order_by(m.Passagem.ocorrido_em.desc(), m.Passagem.id.desc())
        .limit(1)
    )
    return (p.ponto.nome, p.ocorrido_em) if p else ("Recepção", visita.entrada_em)


def presentes(db: Session) -> list[dict]:
    visitas = db.scalars(select(m.Visita).where(m.Visita.status == m.PRESENTE).order_by(m.Visita.entrada_em)).all()
    lista = []
    for v in visitas:
        local, em = ultimo_local(db, v)
        lista.append({
            "visita_id": v.id,
            "nome_exibido": v.nome_exibido,
            "setor_destino": v.setor_destino,
            "cartao_codigo": v.cartao.codigo if v.cartao else None,
            "placa": v.placa,
            "ultimo_local": local,
            "ultimo_local_em": em,
            "desde": v.entrada_em,
        })
    return lista
