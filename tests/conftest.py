"""Fixtures: banco SQLite temporário por teste, "hoje" fixo e fábricas (docs/TESTES.md)."""
import itertools
import os
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

# Garante que nenhum teste toque no banco real, mesmo que algo crie tabelas no engine padrão.
os.environ["DATABASE_URL"] = f"sqlite:///{(Path(tempfile.gettempdir()) / 'gv_pytest_padrao.db').as_posix()}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app import models  # noqa: E402,F401
from app.database import Base, criar_engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.relogio import get_agora, get_hoje  # noqa: E402

HOJE = date(2026, 10, 23)


@pytest.fixture
def hoje() -> date:
    return HOJE


@pytest.fixture
def engine(tmp_path):
    eng = criar_engine(f"sqlite:///{(tmp_path / 'teste.db').as_posix()}")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def sessao(engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def client(sessao, hoje):
    def _get_db():
        db = sessao()
        try:
            yield db
        finally:
            db.close()

    # Relógio que avança 1 minuto a cada leitura: trajetos ficam em ordem determinística.
    passos = itertools.count()
    base = datetime.combine(hoje, datetime.min.time()).replace(hour=8)

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_hoje] = lambda: hoje
    app.dependency_overrides[get_agora] = lambda: base + timedelta(minutes=next(passos))
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def criar_tipo(client):
    contador = itertools.count(1)

    def _criar(**kw):
        dados = {"nome": f"Tipo teste {next(contador)}", **kw}
        r = client.post("/api/tipos-visita", json=dados)
        assert r.status_code == 201, r.text
        return r.json()

    return _criar


@pytest.fixture
def criar_cartao(client):
    contador = itertools.count(1)

    def _criar(**kw):
        n = next(contador)
        dados = {"codigo": f"T-{n:03d}", "codigo_leitura": f"RFID-TESTE-{n:04d}", "cor": "verde", **kw}
        r = client.post("/api/cartoes", json=dados)
        assert r.status_code == 201, r.text
        return r.json()

    return _criar


@pytest.fixture
def dados_visita(hoje):
    def _dados(tipo_id: int, **kw):
        return {
            "tipo_visita_id": tipo_id,
            "nome_civil": "Pessoa Fictícia",
            "setor_destino": "Atendimento",
            "data_visita": hoje.isoformat(),
            "horario_previsto": "09:00",
            **kw,
        }

    return _dados


@pytest.fixture
def criar_visita(client, criar_tipo, dados_visita):
    """Cria visita; sem tipo_id, cria um tipo que aceita veículo e todos os setores."""

    def _criar(tipo_id: int | None = None, **kw):
        if tipo_id is None:
            tipo_id = criar_tipo(permite_veiculo=True)["id"]
        r = client.post("/api/visitas", json=dados_visita(tipo_id, **kw))
        assert r.status_code == 201, r.text
        return r.json()

    return _criar


@pytest.fixture
def dar_entrada(client, criar_cartao):
    def _entrada(visita_id: int, cartao_id: int | None = None):
        cartao_id = cartao_id or criar_cartao()["id"]
        return client.post(f"/api/visitas/{visita_id}/entrada", json={"cartao_id": cartao_id})

    return _entrada
