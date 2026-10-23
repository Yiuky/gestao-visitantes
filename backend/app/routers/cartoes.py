from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models as m
from ..database import get_db
from ..schemas import CartaoIn, CartaoOut, StatusCartao
from ..services import regras

router = APIRouter(prefix="/api/cartoes", tags=["cartões"])


@router.get("", response_model=list[CartaoOut])
def listar(status: StatusCartao | None = None, db: Session = Depends(get_db)):
    q = select(m.CartaoAcesso).order_by(m.CartaoAcesso.codigo)
    if status:
        q = q.where(m.CartaoAcesso.status == status)
    return db.scalars(q).all()


@router.post("", response_model=CartaoOut, status_code=201)
def criar(dados: CartaoIn, db: Session = Depends(get_db)):
    cartao = regras.salvar_cartao(db, dados)
    db.commit()
    return cartao


@router.get("/{cartao_id}", response_model=CartaoOut)
def detalhar(cartao_id: int, db: Session = Depends(get_db)):
    return regras.obter(db, m.CartaoAcesso, cartao_id, "cartão")


@router.put("/{cartao_id}", response_model=CartaoOut)
def editar(cartao_id: int, dados: CartaoIn, db: Session = Depends(get_db)):
    cartao = regras.salvar_cartao(db, dados, regras.obter(db, m.CartaoAcesso, cartao_id, "cartão"))
    db.commit()
    return cartao


@router.delete("/{cartao_id}", status_code=204)
def excluir(cartao_id: int, db: Session = Depends(get_db)):
    regras.excluir_cartao(db, regras.obter(db, m.CartaoAcesso, cartao_id, "cartão"))
    db.commit()
