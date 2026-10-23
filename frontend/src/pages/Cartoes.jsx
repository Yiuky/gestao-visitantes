import { useCallback, useEffect, useState } from 'react'
import { api, qs } from '../api.js'
import { Aviso, Confirmar, Status, Vazio, useAviso } from '../componentes.jsx'

const VAZIO = { codigo: '', codigo_leitura: '', cor: 'verde', status: 'DISPONIVEL' }
const STATUS = ['DISPONIVEL', 'EM_USO', 'EXTRAVIADO', 'INATIVO']

export default function Cartoes({ onMudou }) {
  const [cartoes, setCartoes] = useState([])
  const [filtro, setFiltro] = useState('')
  const [form, setForm] = useState(VAZIO)
  const [editando, setEditando] = useState(null)
  const [excluir, setExcluir] = useState(null)
  const { aviso, ok, erro, limpar } = useAviso()

  const carregar = useCallback(() => api(`/cartoes${qs({ status: filtro })}`).then(setCartoes).catch(erro), [filtro])
  useEffect(() => { carregar() }, [carregar])

  const campo = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const novo = () => { setForm(VAZIO); setEditando(null) }

  const salvar = async (e) => {
    e.preventDefault()
    try {
      if (editando) await api(`/cartoes/${editando}`, { method: 'PUT', body: form })
      else await api('/cartoes', { method: 'POST', body: form })
      ok(editando ? 'Cartão atualizado.' : 'Cartão cadastrado.')
      novo(); carregar(); onMudou()
    } catch (e2) { erro(e2) }
  }

  // ADR-014: pelo PUT só DISPONIVEL ou INATIVO.
  const mudarStatus = async (c, status, texto) => {
    try {
      await api(`/cartoes/${c.id}`, { method: 'PUT', body: { codigo: c.codigo, codigo_leitura: c.codigo_leitura, cor: c.cor, status } })
      ok(`Cartão ${c.codigo} ${texto}.`)
      carregar(); onMudou()
    } catch (e) { erro(e) }
  }

  const editar = (c) => {
    setEditando(c.id)
    setForm({ codigo: c.codigo, codigo_leitura: c.codigo_leitura, cor: c.cor, status: c.status === 'INATIVO' ? 'INATIVO' : 'DISPONIVEL' })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const confirmarExclusao = async () => {
    const c = excluir
    setExcluir(null)
    try {
      await api(`/cartoes/${c.id}`, { method: 'DELETE' })
      ok(`Cartão ${c.codigo} excluído.`)
      carregar(); onMudou()
    } catch (e) { erro(e) }
  }

  return (
    <section>
      <h1>Cartões de acesso</h1>
      <p className="nota">O cartão não tem dados pessoais e nunca é entregue em troca do documento (Lei 5.553/1968).</p>
      <Aviso aviso={aviso} onFechar={limpar} />

      <form className="cartao-form" onSubmit={salvar} aria-label="Formulário de cartão">
        <h2>{editando ? 'Editar cartão' : 'Novo cartão'}</h2>
        <div className="grade">
          <label>Código impresso*<input value={form.codigo} onChange={campo('codigo')} required maxLength={10} placeholder="V-011" /></label>
          <label>Código de leitura*<input value={form.codigo_leitura} onChange={campo('codigo_leitura')} required maxLength={32} placeholder="RFID-TESTE-0011" /></label>
          <label>Cor*<input value={form.cor} onChange={campo('cor')} required maxLength={20} /></label>
        </div>
        <div className="acoes-form">
          <button type="submit" className="btn btn-primario">{editando ? 'Salvar alterações' : 'Cadastrar cartão'}</button>
          {editando && <button type="button" className="btn" onClick={novo}>Cancelar edição</button>}
        </div>
      </form>

      <div className="filtros">
        <label>Filtrar por status
          <select value={filtro} onChange={(e) => setFiltro(e.target.value)}>
            <option value="">Todos</option>
            {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
      </div>

      {cartoes.length === 0 ? (
        <Vazio>Nenhum cartão encontrado.</Vazio>
      ) : (
        <table className="tabela">
          <thead><tr><th>Código</th><th>Código de leitura</th><th>Cor</th><th>Status</th><th>Ações</th></tr></thead>
          <tbody>
            {cartoes.map((c) => (
              <tr key={c.id}>
                <td data-label="Código"><strong>{c.codigo}</strong></td>
                <td data-label="Código de leitura"><code>{c.codigo_leitura}</code></td>
                <td data-label="Cor">{c.cor}</td>
                <td data-label="Status"><Status valor={c.status} /></td>
                <td data-label="Ações"><div className="acoes">
                  {c.status === 'EM_USO' ? (
                    <span className="sub">Em uso por uma visita</span>
                  ) : (
                    <>
                      <button type="button" className="btn btn-pq" onClick={() => editar(c)}>Editar</button>
                      {c.status === 'EXTRAVIADO' && (
                        <button type="button" className="btn btn-pq btn-primario" onClick={() => mudarStatus(c, 'DISPONIVEL', 'marcado como recuperado')}>
                          Marcar como recuperado
                        </button>
                      )}
                      {c.status === 'INATIVO' ? (
                        <button type="button" className="btn btn-pq" onClick={() => mudarStatus(c, 'DISPONIVEL', 'reativado')}>Reativar</button>
                      ) : (
                        <button type="button" className="btn btn-pq" onClick={() => mudarStatus(c, 'INATIVO', 'inativado')}>Inativar</button>
                      )}
                      <button type="button" className="btn btn-pq btn-perigo" onClick={() => setExcluir(c)}>Excluir</button>
                    </>
                  )}
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {excluir && (
        <Confirmar
          titulo="Excluir cartão"
          texto={`Excluir o cartão ${excluir.codigo}? Cartões com histórico de visitas não podem ser excluídos; inative-os.`}
          rotulo="Excluir"
          perigo
          onConfirmar={confirmarExclusao}
          onFechar={() => setExcluir(null)}
        />
      )}
    </section>
  )
}
