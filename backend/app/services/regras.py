"""Regras de negócio (RN01–RN20). Os routers só orquestram; nada aqui depende do FastAPI."""
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models as m
from ..schemas import CartaoIn, TipoVisitaIn, VisitaIn


class RegraViolada(Exception):
    """Erro de regra com status HTTP; convertido em {"detail": mensagem} no main."""

    def __init__(self, status: int, mensagem: str):
        super().__init__(mensagem)
        self.status = status
        self.mensagem = mensagem


def obter(db: Session, modelo, id_: int, oque: str):
    obj = db.get(modelo, id_)
    if obj is None:
        raise RegraViolada(404, f"{oque} não encontrado(a)")
    return obj


def _existe(db: Session, q) -> bool:
    return db.scalar(select(func.count()).select_from(q.subquery())) > 0


# ---------- Tipos de visita ----------
def salvar_tipo(db: Session, dados: TipoVisitaIn, tipo: m.TipoVisita | None = None) -> m.TipoVisita:
    # RN01: nome único, sem diferenciar maiúsculas
    q = select(m.TipoVisita.id).where(func.lower(m.TipoVisita.nome) == dados.nome.lower())
    if tipo is not None:
        q = q.where(m.TipoVisita.id != tipo.id)
    if _existe(db, q):
        raise RegraViolada(409, "já existe um tipo de visita com esse nome")
    tipo = tipo or m.TipoVisita()
    valores = dados.model_dump()
    valores["setores_permitidos"] = ",".join(dados.setores_permitidos)
    for k, v in valores.items():
        setattr(tipo, k, v)
    db.add(tipo)
    return tipo


def excluir_tipo(db: Session, tipo: m.TipoVisita) -> None:
    # RN04b
    if _existe(db, select(m.Visita.id).where(m.Visita.tipo_visita_id == tipo.id)):
        raise RegraViolada(409, "tipo de visita possui visitas vinculadas; desative-o em vez de excluir")
    db.delete(tipo)


# ---------- Cartões ----------
def salvar_cartao(db: Session, dados: CartaoIn, cartao: m.CartaoAcesso | None = None) -> m.CartaoAcesso:
    if cartao is not None and cartao.status == m.EM_USO:
        raise RegraViolada(409, "cartão em uso não pode ser editado nem inativado")  # RN19
    for campo, rotulo in (("codigo", "código"), ("codigo_leitura", "código de leitura")):
        q = select(m.CartaoAcesso.id).where(getattr(m.CartaoAcesso, campo) == getattr(dados, campo))
        if cartao is not None:
            q = q.where(m.CartaoAcesso.id != cartao.id)
        if _existe(db, q):
            raise RegraViolada(409, f"já existe um cartão com esse {rotulo}")  # RN20
    cartao = cartao or m.CartaoAcesso()
    for k, v in dados.model_dump().items():
        setattr(cartao, k, v)
    db.add(cartao)
    return cartao


def excluir_cartao(db: Session, cartao: m.CartaoAcesso) -> None:
    if cartao.status == m.EM_USO:
        raise RegraViolada(409, "cartão em uso não pode ser excluído")
    if _existe(db, select(m.Visita.id).where(m.Visita.cartao_id == cartao.id)):
        raise RegraViolada(409, "cartão com histórico de visitas não pode ser excluído; inative-o")  # RN19
    db.delete(cartao)


# ---------- Visitas ----------
def _placa_no_patio(db: Session, placa: str, ignorar_id: int | None) -> bool:
    q = select(m.Visita.id).where(m.Visita.status == m.PRESENTE, m.Visita.placa == placa)
    if ignorar_id is not None:
        q = q.where(m.Visita.id != ignorar_id)
    return _existe(db, q)


def validar_visita(db: Session, dados: VisitaIn, visita: m.Visita | None = None) -> m.TipoVisita:
    tipo = db.get(m.TipoVisita, dados.tipo_visita_id)
    if tipo is None:
        raise RegraViolada(422, "tipo de visita inexistente")
    troca_tipo = visita is None or visita.tipo_visita_id != tipo.id
    if troca_tipo and not tipo.ativo:  # RN02 + ADR-013
        raise RegraViolada(422, f"o tipo de visita '{tipo.nome}' está inativo")
    if tipo.exige_documento and not dados.documento:  # RN03
        raise RegraViolada(422, f"o tipo '{tipo.nome}' exige documento")
    if tipo.setores_lista and dados.setor_destino not in tipo.setores_lista:  # RN04
        raise RegraViolada(422, f"o tipo '{tipo.nome}' só permite os setores: {', '.join(tipo.setores_lista)}")
    if dados.placa and not tipo.permite_veiculo:  # RN04a
        raise RegraViolada(422, f"o tipo '{tipo.nome}' não permite veículo")
    if visita is not None and visita.status == m.PRESENTE:
        # ADR-013: visita no prédio não muda de data nem passa a usar placa de veículo já no pátio.
        if dados.data_visita != visita.data_visita:
            raise RegraViolada(409, "visita presente não pode mudar de data")
        if dados.placa and dados.placa != visita.placa and _placa_no_patio(db, dados.placa, visita.id):
            raise RegraViolada(409, f"veículo {dados.placa} já está no pátio")
    return tipo


def criar_visita(db: Session, dados: VisitaIn) -> m.Visita:
    validar_visita(db, dados)
    visita = m.Visita(**dados.model_dump(), status=m.AGENDADA)
    db.add(visita)
    return visita


def editar_visita(db: Session, visita: m.Visita, dados: VisitaIn) -> m.Visita:
    if visita.status in (m.ENCERRADA, m.CANCELADA):  # RN06
        raise RegraViolada(409, f"visita {visita.status} não pode ser editada")
    validar_visita(db, dados, visita)
    for k, v in dados.model_dump().items():  # só campos de cadastro; status, cartão e horários ficam
        setattr(visita, k, v)
    return visita


def excluir_visita(db: Session, visita: m.Visita) -> None:
    if visita.status not in (m.AGENDADA, m.CANCELADA):  # RN07
        raise RegraViolada(409, "visitas com presença registrada (PRESENTE ou ENCERRADA) não podem ser excluídas")
    db.delete(visita)


def registrar_entrada(db: Session, visita: m.Visita, cartao_id: int, hoje: date, agora: datetime) -> m.Visita:
    if visita.status != m.AGENDADA:  # RN05/RN13
        raise RegraViolada(409, f"entrada só é possível em visita AGENDADA (atual: {visita.status})")
    if visita.data_visita != hoje:  # RN13
        raise RegraViolada(409, f"entrada só é possível no dia da visita ({visita.data_visita:%d/%m/%Y})")
    cartao = obter(db, m.CartaoAcesso, cartao_id, "cartão")
    if cartao.status != m.DISPONIVEL:  # RN14
        raise RegraViolada(409, f"cartão {cartao.codigo} não está disponível (status: {cartao.status})")
    if visita.placa and _placa_no_patio(db, visita.placa, visita.id):  # RN15
        raise RegraViolada(409, f"veículo {visita.placa} já está no pátio")
    cartao.status = m.EM_USO
    visita.cartao = cartao
    visita.status = m.PRESENTE
    visita.entrada_em = agora
    return visita


def registrar_saida(visita: m.Visita, cartao_devolvido: bool, agora: datetime) -> m.Visita:
    if visita.status != m.PRESENTE:  # RN16
        raise RegraViolada(409, f"saída só é possível em visita PRESENTE (atual: {visita.status})")
    if visita.cartao is not None:  # RN17
        visita.cartao.status = m.DISPONIVEL if cartao_devolvido else m.EXTRAVIADO
    visita.cartao_devolvido = cartao_devolvido
    visita.status = m.ENCERRADA
    visita.saida_em = agora
    return visita


def cancelar_visita(visita: m.Visita) -> m.Visita:
    if visita.status != m.AGENDADA:  # RN05
        raise RegraViolada(409, f"só visitas AGENDADA podem ser canceladas (atual: {visita.status})")
    visita.status = m.CANCELADA
    return visita
