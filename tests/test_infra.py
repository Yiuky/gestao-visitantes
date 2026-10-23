"""Infraestrutura de deploy (ADR-020): URL do banco e RLS no PostgreSQL."""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.config import normalizar_url
from app.database import Base


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("postgres://u:s@h:5432/db", "postgresql+psycopg://u:s@h:5432/db"),
        ("postgresql://u:s@h:6543/db?sslmode=require", "postgresql+psycopg://u:s@h:6543/db?sslmode=require"),
        ("postgresql+psycopg://u:s@h/db", "postgresql+psycopg://u:s@h/db"),
        ("sqlite:///x.db", "sqlite:///x.db"),
    ],
)
def test_normalizar_url(entrada, esperado):
    assert normalizar_url(entrada) == esperado


def test_rls_bloqueia_papel_anon_no_postgres(engine, client, criar_visita):
    if engine.dialect.name != "postgresql":
        pytest.skip("RLS só existe no PostgreSQL (rode com TEST_DATABASE_URL)")
    criar_visita()
    with engine.begin() as conn:
        sem_rls = conn.execute(text(
            "SELECT relname FROM pg_class WHERE relname = ANY(:t) AND NOT relrowsecurity"
        ), {"t": [t.name for t in Base.metadata.sorted_tables]}).scalars().all()
        assert sem_rls == []
        # Simula o papel "anon" do Supabase com permissão de tabela, mas sem política de RLS
        conn.execute(text("DO $$ BEGIN CREATE ROLE anon_teste NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$"))
        conn.execute(text("GRANT USAGE ON SCHEMA public TO anon_teste"))
        conn.execute(text("GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO anon_teste"))
        conn.execute(text("GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon_teste"))  # como o Supabase faz
    with engine.connect() as conn:
        conn.execute(text("SET ROLE anon_teste"))
        assert conn.execute(text("SELECT count(*) FROM visitas")).scalar() == 0  # dado existe, mas não é visível
        with pytest.raises(ProgrammingError, match="row-level security"):
            conn.execute(text("INSERT INTO pontos_acesso (nome, ativo, metodos_aceitos) VALUES ('x', true, 'CARTAO')"))
        conn.rollback()
    with engine.begin() as conn:
        conn.execute(text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon_teste"))
        conn.execute(text("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon_teste"))
        conn.execute(text("REVOKE USAGE ON SCHEMA public FROM anon_teste"))
    # A API (dona das tabelas) continua vendo tudo
    assert len(client.get("/api/visitas").json()) == 1
