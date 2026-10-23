import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { Aviso, Confirmar, Vazio, useAviso } from '../componentes.jsx'

const VAZIO = {
  nome: '', descricao: '', ativo: true, exige_documento: false, permite_veiculo: false,
  setores_permitidos: [], prazo_retencao_dias: 180,
}

export default function Tipos({ onMudou }) {
  const [tipos, setTipos] = useState([])
  const [setores, setSetores] = useState([])
  const [form, setForm] = useState(VAZIO)
  const [editando, setEditando] = useState(null)
  const [excluir, setExcluir] = useState(null)
  const { aviso, ok, erro, limpar } = useAviso()

  const carregar = useCallback(() => api('/tipos-visita').then(setTipos).catch(erro), [])
  useEffect(() => {
    carregar()
    api('/setores').then(setSetores).catch(erro)
  }, [carregar])

  const campo = (k) => (e) => setForm({ ...form, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const alternarSetor = (s) =>
    setForm({
      ...form,
      setores_permitidos: form.setores_permitidos.includes(s)
        ? form.setores_permitidos.filter((x) => x !== s)
        : [...form.setores_permitidos, s],
    })

  const novo = () => { setForm(VAZIO); setEditando(null) }

  const salvar = async (e) => {
    e.preventDefault()
    try {
      const corpo = { ...form, prazo_retencao_dias: Number(form.prazo_retencao_dias) }
      if (editando) await api(`/tipos-visita/${editando}`, { method: 'PUT', body: corpo })
      else await api('/tipos-visita', { method: 'POST', body: corpo })
      ok(editando ? 'Tipo de visita atualizado.' : 'Tipo de visita cadastrado.')
      novo(); carregar(); onMudou()
    } catch (e2) { erro(e2) }
  }

  const editar = (t) => {
    setEditando(t.id)
    setForm({ ...t, descricao: t.descricao || '' })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const alternarAtivo = async (t) => {
    try {
      await api(`/tipos-visita/${t.id}`, { method: 'PUT', body: { ...t, ativo: !t.ativo } })
      ok(`Tipo "${t.nome}" ${t.ativo ? 'desativado' : 'ativado'}.`)
      carregar(); onMudou()
    } catch (e) { erro(e) }
  }

  const confirmarExclusao = async () => {
    const t = excluir
    setExcluir(null)
    try {
      await api(`/tipos-visita/${t.id}`, { method: 'DELETE' })
      ok(`Tipo "${t.nome}" excluído.`)
      if (editando === t.id) novo()
      carregar(); onMudou()
    } catch (e) { erro(e) }
  }

  return (
    <section>
      <h1>Tipos de visita</h1>
      <Aviso aviso={aviso} onFechar={limpar} />

      <form className="cartao-form" onSubmit={salvar} aria-label="Formulário de tipo de visita">
        <h2>{editando ? 'Editar tipo de visita' : 'Novo tipo de visita'}</h2>
        <div className="grade">
          <label>Nome*<input value={form.nome} onChange={campo('nome')} required minLength={3} maxLength={60} /></label>
          <label>Descrição<input value={form.descricao} onChange={campo('descricao')} maxLength={200} /></label>
          <label>Prazo de retenção (dias)
            <input type="number" min={1} max={3650} value={form.prazo_retencao_dias} onChange={campo('prazo_retencao_dias')} />
            <small>Proposto para validação do encarregado.</small>
          </label>
        </div>
        <div className="checks">
          <label><input type="checkbox" checked={form.ativo} onChange={campo('ativo')} /> Ativo</label>
          <label><input type="checkbox" checked={form.exige_documento} onChange={campo('exige_documento')} /> Exige documento</label>
          <label><input type="checkbox" checked={form.permite_veiculo} onChange={campo('permite_veiculo')} /> Permite veículo</label>
        </div>
        <fieldset>
          <legend>Setores permitidos (nenhum marcado = todos)</legend>
          <div className="checks">
            {setores.map((s) => (
              <label key={s}>
                <input type="checkbox" checked={form.setores_permitidos.includes(s)} onChange={() => alternarSetor(s)} /> {s}
              </label>
            ))}
          </div>
        </fieldset>
        <div className="acoes-form">
          <button type="submit" className="btn btn-primario">{editando ? 'Salvar alterações' : 'Cadastrar tipo'}</button>
          {editando && <button type="button" className="btn" onClick={novo}>Cancelar edição</button>}
        </div>
      </form>

      {tipos.length === 0 ? (
        <Vazio>Nenhum tipo de visita cadastrado.</Vazio>
      ) : (
        <table className="tabela">
          <thead>
            <tr><th>Nome</th><th>Regras</th><th>Setores</th><th>Situação</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {tipos.map((t) => (
              <tr key={t.id}>
                <td data-label="Nome"><strong>{t.nome}</strong>{t.descricao && <div className="sub">{t.descricao}</div>}</td>
                <td data-label="Regras">
                  {t.exige_documento ? 'Documento obrigatório' : 'Documento opcional'} ·{' '}
                  {t.permite_veiculo ? 'aceita veículo' : 'sem veículo'}
                </td>
                <td data-label="Setores">{t.setores_permitidos.length ? t.setores_permitidos.join(', ') : 'Todos'}</td>
                <td data-label="Situação">
                  <span className={`badge badge-${t.ativo ? 'verde' : 'cinza'}`}>{t.ativo ? 'ATIVO' : 'INATIVO'}</span>
                </td>
                <td data-label="Ações"><div className="acoes">
                  <button type="button" className="btn btn-pq" onClick={() => editar(t)}>Editar</button>
                  <button type="button" className="btn btn-pq" onClick={() => alternarAtivo(t)}>{t.ativo ? 'Desativar' : 'Ativar'}</button>
                  <button type="button" className="btn btn-pq btn-perigo" onClick={() => setExcluir(t)}>Excluir</button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {excluir && (
        <Confirmar
          titulo="Excluir tipo de visita"
          texto={`Excluir o tipo "${excluir.nome}"? Tipos com visitas vinculadas não podem ser excluídos; desative-os.`}
          rotulo="Excluir"
          perigo
          onConfirmar={confirmarExclusao}
          onFechar={() => setExcluir(null)}
        />
      )}
    </section>
  )
}
