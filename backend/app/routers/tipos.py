from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..database import get_db
from ..schemas import TipoVisitaIn, TipoVisitaOut
from ..services import regras

router = APIRouter(prefix="/api/tipos-visita", tags=["tipos de visita"])


@router.get("", response_model=list[TipoVisitaOut])
def listar(db: Session = Depends(get_db)):
    return db.scalars(select(m.TipoVisita).order_by(m.TipoVisita.nome)).all()


@router.post("", response_model=TipoVisitaOut, status_code=201)
def criar(dados: TipoVisitaIn, db: Session = Depends(get_db)):
    tipo = regras.salvar_tipo(db, dados)
    db.commit()
    return tipo


@router.get("/{tipo_id}", response_model=TipoVisitaOut)
def detalhar(tipo_id: int, db: Session = Depends(get_db)):
    return regras.obter(db, m.TipoVisita, tipo_id, "tipo de visita")


@router.put("/{tipo_id}", response_model=TipoVisitaOut)
def editar(tipo_id: int, dados: TipoVisitaIn, db: Session = Depends(get_db)):
    tipo = regras.salvar_tipo(db, dados, regras.obter(db, m.TipoVisita, tipo_id, "tipo de visita"))
    db.commit()
    return tipo


@router.delete("/{tipo_id}", status_code=204)
def excluir(tipo_id: int, db: Session = Depends(get_db)):
    regras.excluir_tipo(db, regras.obter(db, m.TipoVisita, tipo_id, "tipo de visita"))
    db.commit()
