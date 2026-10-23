"""Relógio injetável: "hoje" e "agora" no fuso America/Cuiaba (ADR-004, ADR-016).

Os testes sobrescrevem `get_hoje` e `get_agora` via `app.dependency_overrides`.
"""
from datetime import date, datetime

from .config import FUSO


def get_agora() -> datetime:
    # Horário local sem tzinfo: é o que vai para o banco (ADR-016).
    return datetime.now(FUSO).replace(tzinfo=None, microsecond=0)


def get_hoje() -> date:
    return datetime.now(FUSO).date()
