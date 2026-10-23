import { useEffect, useRef, useState } from 'react'

// Mensagens de sucesso/erro exibidas no topo de cada página.
export function useAviso() {
  const [aviso, setAviso] = useState(null)
  const ok = (texto) => setAviso({ tipo: 'ok', texto })
  const erro = (e) => setAviso({ tipo: 'erro', texto: e?.message || String(e) })
  const limpar = () => setAviso(null)
  return { aviso, ok, erro, limpar }
}

export function Aviso({ aviso, onFechar }) {
  const ref = useRef(null)
  // A mensagem fica no topo da página; sem isso, um erro de ação na tabela ficaria fora da tela.
  useEffect(() => {
    if (aviso) ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [aviso])
  if (!aviso) return null
  return (
    <div ref={ref} className={`aviso aviso-${aviso.tipo}`} role={aviso.tipo === 'erro' ? 'alert' : 'status'}>
      <span>{aviso.texto}</span>
      <button type="button" className="btn-link" onClick={onFechar} aria-label="Fechar mensagem">×</button>
    </div>
  )
}

// Modal da própria página (sem alert/confirm do navegador).
export function Modal({ titulo, children, onFechar, acoes }) {
  const ref = useRef(null)
  useEffect(() => {
    ref.current?.focus()
    const esc = (e) => e.key === 'Escape' && onFechar()
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [onFechar])
  return (
    <div className="modal-fundo" onMouseDown={(e) => e.target === e.currentTarget && onFechar()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={titulo} tabIndex={-1} ref={ref}>
        <h3>{titulo}</h3>
        <div className="modal-corpo">{children}</div>
        <div className="modal-acoes">{acoes}</div>
      </div>
    </div>
  )
}

export function Confirmar({ titulo, texto, rotulo = 'Confirmar', perigo, onConfirmar, onFechar }) {
  return (
    <Modal
      titulo={titulo}
      onFechar={onFechar}
      acoes={
        <>
          <button type="button" className="btn" onClick={onFechar}>Voltar</button>
          <button type="button" className={`btn ${perigo ? 'btn-perigo' : 'btn-primario'}`} onClick={onConfirmar}>
            {rotulo}
          </button>
        </>
      }
    >
      <p>{texto}</p>
    </Modal>
  )
}

export function Vazio({ children }) {
  return <p className="vazio">{children}</p>
}

const CORES_STATUS = {
  AGENDADA: 'azul', PRESENTE: 'verde', ENCERRADA: 'cinza', CANCELADA: 'vermelho',
  DISPONIVEL: 'verde', EM_USO: 'azul', EXTRAVIADO: 'laranja', INATIVO: 'cinza',
  LIBERADO: 'verde', NEGADO: 'vermelho',
}
const ROTULOS_STATUS = { DISPONIVEL: 'DISPONÍVEL', EM_USO: 'EM USO' }

export function Status({ valor }) {
  return <span className={`badge badge-${CORES_STATUS[valor] || 'cinza'}`}>{ROTULOS_STATUS[valor] || valor}</span>
}
