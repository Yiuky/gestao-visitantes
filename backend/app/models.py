"""Modelos SQLAlchemy (seção 7 do handoff)."""
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .relogio import get_agora

# Status
AGENDADA, PRESENTE, ENCERRADA, CANCELADA = "AGENDADA", "PRESENTE", "ENCERRADA", "CANCELADA"
DISPONIVEL, EM_USO, EXTRAVIADO, INATIVO = "DISPONIVEL", "EM_USO", "EXTRAVIADO", "INATIVO"


class TipoVisita(Base):
    __tablename__ = "tipos_visita"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    descricao: Mapped[str | None] = mapped_column(String(200))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    exige_documento: Mapped[bool] = mapped_column(Boolean, default=False)
    permite_veiculo: Mapped[bool] = mapped_column(Boolean, default=False)
    setores_permitidos: Mapped[str] = mapped_column(String(255), default="")  # CSV; vazio = todos
    prazo_retencao_dias: Mapped[int] = mapped_column(Integer, default=180)  # proposto para validação

    @property
    def setores_lista(self) -> list[str]:
        return [s for s in (self.setores_permitidos or "").split(",") if s]


class CartaoAcesso(Base):
    __tablename__ = "cartoes_acesso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True)
    codigo_leitura: Mapped[str] = mapped_column(String(32), unique=True)
    cor: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(10), default=DISPONIVEL)


class Visita(Base):
    __tablename__ = "visitas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_visita_id: Mapped[int] = mapped_column(ForeignKey("tipos_visita.id"))
    nome_civil: Mapped[str] = mapped_column(String(120))
    nome_social: Mapped[str | None] = mapped_column(String(120))
    documento: Mapped[str | None] = mapped_column(String(30))
    setor_destino: Mapped[str] = mapped_column(String(50))
    data_visita: Mapped[date] = mapped_column(Date, index=True)
    horario_previsto: Mapped[time] = mapped_column(Time)
    atendimento_prioritario: Mapped[bool] = mapped_column(Boolean, default=False)
    placa: Mapped[str | None] = mapped_column(String(7))
    descricao_veiculo: Mapped[str | None] = mapped_column(String(60))
    vaga_reservada: Mapped[bool] = mapped_column(Boolean, default=False)
    observacao: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(10), default=AGENDADA, index=True)
    cartao_id: Mapped[int | None] = mapped_column(ForeignKey("cartoes_acesso.id"))
    cartao_devolvido: Mapped[bool | None] = mapped_column(Boolean)
    entrada_em: Mapped[datetime | None] = mapped_column(DateTime)
    saida_em: Mapped[datetime | None] = mapped_column(DateTime)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=get_agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=get_agora, onupdate=get_agora)

    tipo: Mapped[TipoVisita] = relationship()
    cartao: Mapped[CartaoAcesso | None] = relationship()

    @property
    def nome_exibido(self) -> str:
        return self.nome_social or self.nome_civil


LIBERADO, NEGADO = "LIBERADO", "NEGADO"
ENTRADA, SAIDA = "ENTRADA", "SAIDA"
CARTAO = "CARTAO"


class PontoAcesso(Base):
    __tablename__ = "pontos_acesso"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str] = mapped_column(String(60), unique=True)
    setor: Mapped[str | None] = mapped_column(String(50))  # NULL = área comum (RN23)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    # ADR-011: ponto de extensão para biometria futura; no MVP só CARTAO.
    metodos_aceitos: Mapped[str] = mapped_column(String(30), default=CARTAO)


class Passagem(Base):
    """Somente inserção (RNF07, ADR-008): a API não expõe edição nem exclusão."""

    __tablename__ = "passagens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ponto_id: Mapped[int] = mapped_column(ForeignKey("pontos_acesso.id"))
    codigo_lido: Mapped[str] = mapped_column(String(32))
    cartao_id: Mapped[int | None] = mapped_column(ForeignKey("cartoes_acesso.id"))
    visita_id: Mapped[int | None] = mapped_column(ForeignKey("visitas.id"), index=True)
    credencial_tipo: Mapped[str] = mapped_column(String(10), default=CARTAO)
    sentido: Mapped[str] = mapped_column(String(7))
    resultado: Mapped[str] = mapped_column(String(8))
    motivo: Mapped[str | None] = mapped_column(String(80))
    ocorrido_em: Mapped[datetime] = mapped_column(DateTime, default=get_agora, index=True)

    ponto: Mapped[PontoAcesso] = relationship()
