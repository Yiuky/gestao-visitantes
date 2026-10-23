"""Engine, sessão e Base do SQLAlchemy (ADR-005)."""
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL, normalizar_url


class Base(DeclarativeBase):
    pass


def criar_engine(url: str):
    url = normalizar_url(url)
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        caminho = url.removeprefix("sqlite:///")
        if caminho and caminho != ":memory:":
            Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    else:
        # PostgreSQL gerenciado (Supabase): conexões ociosas caem; testa antes de usar e recicla.
        # prepare_threshold=None: compatível com o pooler do Supabase em modo transação (porta 6543).
        kwargs.update(pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=5,
                      connect_args={"prepare_threshold": None})
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
    return engine


def criar_tabelas(eng) -> None:
    """create_all (ADR-005) e, no PostgreSQL, RLS ligado em todas as tabelas (ADR-020).

    No Supabase o schema public é exposto pela API REST com a chave anon; com RLS e nenhuma política,
    esse acesso não vê nem altera nada. A API conecta como dona das tabelas e não é afetada.
    """
    Base.metadata.create_all(eng)
    if eng.dialect.name == "postgresql":
        with eng.begin() as conn:
            for tabela in Base.metadata.sorted_tables:
                conn.exec_driver_sql(f'ALTER TABLE "{tabela.name}" ENABLE ROW LEVEL SECURITY')


engine = criar_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
