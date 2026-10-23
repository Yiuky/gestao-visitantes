"""Aplicação FastAPI: Gestão de visitantes (dados fictícios)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import models  # noqa: F401  (registra as tabelas no metadata)
from .config import CORS_ORIGINS, SETORES
from .database import SessionLocal, criar_tabelas, engine
from .routers import cartoes, catraca, dashboard, tipos, visitas
from .services.regras import RegraViolada, garantir_pontos


@asynccontextmanager
async def lifespan(_app: FastAPI):
    criar_tabelas(engine)  # ADR-005: create_all, sem Alembic no MVP; RLS no PostgreSQL (ADR-020)
    with SessionLocal() as db:
        garantir_pontos(db)
    yield


app = FastAPI(
    title="Gestão de visitantes",
    description="MVP local de recepção de um órgão público fictício. Todos os dados são fictícios.",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(RegraViolada)
async def _regra_violada(_req: Request, exc: RegraViolada):
    return JSONResponse(status_code=exc.status, content={"detail": exc.mensagem})


@app.get("/api/health", tags=["sistema"])
def health():
    return {"status": "ok"}


@app.get("/api/setores", tags=["sistema"])
def setores():
    return SETORES


app.include_router(tipos.router)
app.include_router(cartoes.router)
app.include_router(visitas.router)
app.include_router(dashboard.router)
app.include_router(catraca.router)
