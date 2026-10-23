from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..relogio import get_hoje
from ..schemas import Dashboard, Presente
from ..services import painel

router = APIRouter(prefix="/api", tags=["painel"])


@router.get("/dashboard", response_model=Dashboard)
def dashboard(db: Session = Depends(get_db), hoje: date = Depends(get_hoje)):
    return painel.indicadores(db, hoje)


@router.get("/presentes", response_model=list[Presente])
def presentes(db: Session = Depends(get_db)):
    return painel.presentes(db)
