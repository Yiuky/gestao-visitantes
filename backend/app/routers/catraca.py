"""Catraca simulada e trajetos (RN21–RN26, ADR-010, ADR-012).

Passagens só têm rotas de leitura e de inserção: PUT/DELETE respondem 405 (RNF07).
"""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..database import get_db
from ..relogio import get_agora
from ..schemas import LeituraIn, LeituraOut, PassagemOut, PontoAcessoOut
from ..services import regras

router = APIRouter(prefix="/api", tags=["catraca"])


@router.get("/pontos-acesso", response_model=list[PontoAcessoOut])
def pontos(db: Session = Depends(get_db)):
    return db.scalars(select(m.PontoAcesso).order_by(m.PontoAcesso.id)).all()


@router.post("/catraca/passagens", response_model=LeituraOut, status_code=201)
def ler(dados: LeituraIn, db: Session = Depends(get_db), agora: datetime = Depends(get_agora)):
    ponto = regras.obter(db, m.PontoAcesso, dados.ponto_id, "ponto de acesso")
    passagem = regras.registrar_passagem(db, ponto, dados.codigo_lido, dados.sentido, agora)
    db.commit()
    return {"resultado": passagem.resultado, "motivo": passagem.motivo, "passagem": PassagemOut.de(passagem)}


@router.get("/catraca/passagens", response_model=list[PassagemOut])
def ultimas(limite: int = 20, db: Session = Depends(get_db)):
    q = select(m.Passagem).order_by(m.Passagem.ocorrido_em.desc(), m.Passagem.id.desc()).limit(min(limite, 100))
    return [PassagemOut.de(p) for p in db.scalars(q).all()]


@router.get("/catraca/passagens/{passagem_id}", response_model=PassagemOut)
def detalhar(passagem_id: int, db: Session = Depends(get_db)):
    return PassagemOut.de(regras.obter(db, m.Passagem, passagem_id, "passagem"))


@router.get("/visitas/{visita_id}/passagens", response_model=list[PassagemOut])
def trajeto(visita_id: int, db: Session = Depends(get_db)):
    """RN25: trajeto só em consulta específica, em ordem cronológica."""
    regras.obter(db, m.Visita, visita_id, "visita")
    q = select(m.Passagem).where(m.Passagem.visita_id == visita_id).order_by(m.Passagem.ocorrido_em, m.Passagem.id)
    return [PassagemOut.de(p) for p in db.scalars(q).all()]
