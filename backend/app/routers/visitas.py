from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import models as m
from ..database import get_db
from ..relogio import get_agora, get_hoje
from ..schemas import EntradaIn, SaidaIn, StatusVisita, VisitaDetalhe, VisitaIn, VisitaResumo
from ..services import regras

router = APIRouter(prefix="/api/visitas", tags=["visitas"])


def _obter(db: Session, visita_id: int) -> m.Visita:
    return regras.obter(db, m.Visita, visita_id, "visita")


@router.get("", response_model=list[VisitaResumo])
def listar(
    q: str | None = None,
    setor: str | None = None,
    tipo_id: int | None = None,
    data: date | None = None,
    status: StatusVisita | None = None,
    db: Session = Depends(get_db),
):
    consulta = select(m.Visita)
    if q and q.strip():
        termo = f"%{q.strip()}%"
        consulta = consulta.where(or_(m.Visita.nome_civil.ilike(termo), m.Visita.nome_social.ilike(termo)))
    if setor:
        consulta = consulta.where(m.Visita.setor_destino == setor)
    if tipo_id:
        consulta = consulta.where(m.Visita.tipo_visita_id == tipo_id)
    if data:
        consulta = consulta.where(m.Visita.data_visita == data)
    if status:
        consulta = consulta.where(m.Visita.status == status)
    # RF03: prioritários primeiro dentro do mesmo horário
    consulta = consulta.order_by(
        m.Visita.data_visita, m.Visita.horario_previsto, m.Visita.atendimento_prioritario.desc(), m.Visita.id
    )
    return [VisitaResumo.de(v) for v in db.scalars(consulta).all()]


@router.post("", response_model=VisitaDetalhe, status_code=201)
def criar(dados: VisitaIn, db: Session = Depends(get_db)):
    visita = regras.criar_visita(db, dados)
    db.commit()
    db.refresh(visita)
    return VisitaDetalhe.de(visita)


@router.get("/{visita_id}", response_model=VisitaDetalhe)
def detalhar(visita_id: int, db: Session = Depends(get_db)):
    return VisitaDetalhe.de(_obter(db, visita_id))


@router.put("/{visita_id}", response_model=VisitaDetalhe)
def editar(visita_id: int, dados: VisitaIn, db: Session = Depends(get_db)):
    visita = regras.editar_visita(db, _obter(db, visita_id), dados)
    db.commit()
    db.refresh(visita)
    return VisitaDetalhe.de(visita)


@router.delete("/{visita_id}", status_code=204)
def excluir(visita_id: int, db: Session = Depends(get_db)):
    regras.excluir_visita(db, _obter(db, visita_id))
    db.commit()


@router.post("/{visita_id}/entrada", response_model=VisitaDetalhe)
def entrada(
    visita_id: int,
    dados: EntradaIn,
    db: Session = Depends(get_db),
    hoje: date = Depends(get_hoje),
    agora: datetime = Depends(get_agora),
):
    visita = regras.registrar_entrada(db, _obter(db, visita_id), dados.cartao_id, hoje, agora)
    db.commit()
    return VisitaDetalhe.de(visita)


@router.post("/{visita_id}/saida", response_model=VisitaDetalhe)
def saida(visita_id: int, dados: SaidaIn, db: Session = Depends(get_db), agora: datetime = Depends(get_agora)):
    visita = regras.registrar_saida(_obter(db, visita_id), dados.cartao_devolvido, agora)
    db.commit()
    return VisitaDetalhe.de(visita)


@router.post("/{visita_id}/cancelar", response_model=VisitaDetalhe)
def cancelar(visita_id: int, db: Session = Depends(get_db)):
    visita = regras.cancelar_visita(_obter(db, visita_id))
    db.commit()
    return VisitaDetalhe.de(visita)
