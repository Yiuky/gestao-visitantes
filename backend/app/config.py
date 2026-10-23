"""Configuração: banco, fuso e setores (ADR-002, ADR-004, ADR-005)."""
import os
from pathlib import Path
from zoneinfo import ZoneInfo

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"

# Caminho absoluto: não depende da pasta onde o uvicorn ou o pytest são executados.
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'visitantes.db').as_posix()}")

FUSO = ZoneInfo("America/Cuiaba")

SETORES = ["Atendimento", "Protocolo", "Jurídico", "Tecnologia", "Diretoria"]

# Origens aceitas pelo CORS (o proxy do Vite e o nginx dispensam CORS; útil para acesso direto).
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
