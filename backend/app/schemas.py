"""Schemas Pydantic v2: contratos de entrada e saída (seção 10 do handoff)."""
import re
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .config import SETORES

PLACA_RE = re.compile(r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$")

StatusVisita = Literal["AGENDADA", "PRESENTE", "ENCERRADA", "CANCELADA"]
StatusCartao = Literal["DISPONIVEL", "EM_USO", "EXTRAVIADO", "INATIVO"]


def _vazio_para_none(v):
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


def _strip(v):
    return v.strip() if isinstance(v, str) else v


def _validar_setor(v: str) -> str:
    if v not in SETORES:
        raise ValueError(f"setor inválido; use um de: {', '.join(SETORES)}")
    return v


# ---------- Tipos de visita ----------
class TipoVisitaIn(BaseModel):
    nome: str = Field(min_length=3, max_length=60)
    descricao: str | None = Field(default=None, max_length=200)
    ativo: bool = True
    exige_documento: bool = False
    permite_veiculo: bool = False
    setores_permitidos: list[str] = Field(default_factory=list)  # vazio = todos
    prazo_retencao_dias: int = Field(default=180, ge=1, le=3650)

    _nome = field_validator("nome", mode="before")(_strip)
    _desc = field_validator("descricao", mode="before")(_vazio_para_none)

    @field_validator("setores_permitidos")
    @classmethod
    def _setores(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(_validar_setor(s) for s in v))


class TipoVisitaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    descricao: str | None
    ativo: bool
    exige_documento: bool
    permite_veiculo: bool
    setores_permitidos: list[str]
    prazo_retencao_dias: int

    @field_validator("setores_permitidos", mode="before")
    @classmethod
    def _csv(cls, v):
        return [s for s in v.split(",") if s] if isinstance(v, str) else v


# ---------- Cartões ----------
class CartaoIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=10)
    codigo_leitura: str = Field(min_length=1, max_length=32)
    cor: str = Field(min_length=1, max_length=20)
    # ADR-014: pelo cadastro/PUT só DISPONIVEL ou INATIVO; EM_USO e EXTRAVIADO vêm do ciclo da visita.
    status: Literal["DISPONIVEL", "INATIVO"] = "DISPONIVEL"

    _textos = field_validator("codigo", "codigo_leitura", "cor", mode="before")(_strip)


class CartaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    codigo: str
    codigo_leitura: str
    cor: str
    status: StatusCartao


# ---------- Visitas ----------
class VisitaIn(BaseModel):
    # extra="ignore": status, cartao_id, entrada_em etc. enviados no PUT são descartados (RN06).
    model_config = ConfigDict(extra="ignore")

    tipo_visita_id: int
    nome_civil: str = Field(min_length=3, max_length=120)
    nome_social: str | None = Field(default=None, max_length=120)
    documento: str | None = Field(default=None, max_length=30)
    setor_destino: str
    data_visita: date
    horario_previsto: time
    atendimento_prioritario: bool = False
    placa: str | None = None
    descricao_veiculo: str | None = Field(default=None, max_length=60)
    vaga_reservada: bool = False
    observacao: str | None = Field(default=None, max_length=100)

    _nome = field_validator("nome_civil", mode="before")(_strip)
    _opcionais = field_validator("nome_social", "documento", "descricao_veiculo", "observacao", mode="before")(
        _vazio_para_none
    )

    @field_validator("setor_destino")
    @classmethod
    def _setor(cls, v: str) -> str:
        return _validar_setor(v)

    @field_validator("placa", mode="before")
    @classmethod
    def _placa(cls, v):
        # RN11: maiúsculas, sem hífen nem espaço; vazio vira NULL (conta certo em "veículos no pátio").
        if v is None:
            return None
        v = re.sub(r"[\s-]", "", str(v)).upper()
        if not v:
            return None
        if not PLACA_RE.match(v):
            raise ValueError("placa inválida; use o formato AAA9999 ou AAA9A99")
        return v

    @model_validator(mode="after")
    def _vaga(self):
        # RN12
        if self.vaga_reservada and not self.placa:
            raise ValueError("vaga reservada só pode ser marcada com placa informada")
        if not self.placa:
            self.descricao_veiculo = None
        return self


class Dashboard(BaseModel):
    data_referencia: date
    visitas_do_dia: int
    presentes: int
    encerradas_do_dia: int
    veiculos_no_patio: int
    cartoes_pendentes: int
    acessos_negados_hoje: int


class Presente(BaseModel):
    visita_id: int
    nome_exibido: str
    setor_destino: str
    cartao_codigo: str | None
    placa: str | None
    ultimo_local: str
    ultimo_local_em: datetime | None
    desde: datetime | None


class EntradaIn(BaseModel):
    cartao_id: int


class SaidaIn(BaseModel):
    cartao_devolvido: bool


def mascarar_documento(doc: str | None) -> str | None:
    """RNF06: mantém um prefixo alfabético curto e os 2 últimos caracteres (DOC-0001 → DOC-••01)."""
    if not doc:
        return None
    if len(doc) <= 2:
        return "••"
    m = re.match(r"^[A-Za-z]{1,4}[-./ ]?", doc)
    prefixo = m.group(0) if m and len(doc) - len(m.group(0)) > 2 else ""
    corpo = doc[len(prefixo):]
    return prefixo + "•" * (len(corpo) - 2) + corpo[-2:]


class VisitaResumo(BaseModel):
    """Listagens: nunca traz o documento completo nem o nome civil quando há nome social."""

    id: int
    tipo_visita_id: int
    tipo_nome: str
    nome_exibido: str
    documento_mascarado: str | None
    setor_destino: str
    data_visita: date
    horario_previsto: time
    atendimento_prioritario: bool
    placa: str | None
    vaga_reservada: bool
    status: StatusVisita
    cartao_id: int | None
    cartao_codigo: str | None
    cartao_devolvido: bool | None
    entrada_em: datetime | None
    saida_em: datetime | None

    @classmethod
    def de(cls, v) -> "VisitaResumo":
        return cls(
            id=v.id, tipo_visita_id=v.tipo_visita_id, tipo_nome=v.tipo.nome, nome_exibido=v.nome_exibido,
            documento_mascarado=mascarar_documento(v.documento), setor_destino=v.setor_destino,
            data_visita=v.data_visita, horario_previsto=v.horario_previsto,
            atendimento_prioritario=v.atendimento_prioritario, placa=v.placa, vaga_reservada=v.vaga_reservada,
            status=v.status, cartao_id=v.cartao_id, cartao_codigo=v.cartao.codigo if v.cartao else None,
            cartao_devolvido=v.cartao_devolvido, entrada_em=v.entrada_em, saida_em=v.saida_em,
        )


class VisitaDetalhe(VisitaResumo):
    nome_civil: str
    nome_social: str | None
    documento: str | None
    descricao_veiculo: str | None
    observacao: str | None
    criado_em: datetime
    atualizado_em: datetime

    @classmethod
    def de(cls, v) -> "VisitaDetalhe":
        return cls(
            **VisitaResumo.de(v).model_dump(), nome_civil=v.nome_civil, nome_social=v.nome_social,
            documento=v.documento, descricao_veiculo=v.descricao_veiculo, observacao=v.observacao,
            criado_em=v.criado_em, atualizado_em=v.atualizado_em,
        )
