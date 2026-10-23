import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, fmtData, fmtHora, qs } from '../api.js'
import { Aviso, Confirmar, Modal, Status, Vazio, useAviso } from '../componentes.jsx'

const hojeISO = () => new Date().toLocaleDateString('sv-SE', { timeZone: 'America/Cuiaba' })

const novoForm = () => ({
  tipo_visita_id: '', nome_civil: '', nome_social: '', documento: '', setor_destino: '',
  data_visita: hojeISO(), horario_previsto: '', atendimento_prioritario: false,
  placa: '', descricao_veiculo: '', vaga_reservada: false, observacao: '',
})
const FILTROS = { q: '', setor: '', tipo_id: '', data: '', status: '' }
const STATUS = ['AGENDADA', 'PRESENTE', 'ENCERRADA', 'CANCELADA']

export default function Visitas({ onMudou }) {
  const [visitas, setVisitas] = useState([])
  const [tipos, setTipos] = useState([])
  const [setores, setSetores] = useState([])
  const [filtros, setFiltros] = useState(FILTROS)
  const [form, setForm] = useState(novoForm)
  const [editando, setEditando] = useState(null) // {id, status, tipo_visita_id}
  const [modal, setModal] = useState(null) // {tipo: 'entrada'|'saida'|'cancelar'|'excluir', visita}
  const [cartoesLivres, setCartoesLivres] = useState([])
  const [cartaoEscolhido, setCartaoEscolhido] = useState('')
  const [devolvido, setDevolvido] = useState('')
  const { aviso, ok, erro, limpar } = useAviso()

  const carregar = useCallback(() => api(`/visitas${qs(filtros)}`).then(setVisitas).catch(erro), [filtros])
  useEffect(() => { carregar() }, [carregar])
  useEffect(() => {
    api('/tipos-visita').then(setTipos).catch(erro)
    api('/setores').then(setSetores).catch(erro)
  }, [])

  const tipo = useMemo(() => tipos.find((t) => t.id === Number(form.tipo_visita_id)), [tipos, form.tipo_visita_id])
  // Novo cadastro: só tipos ativos. Edição: mantém o tipo atual mesmo se foi desativado (ADR-013).
  const tiposDoForm = tipos.filter((t) => t.ativo || t.id === editando?.tipo_visita_id)
  const setoresDoTipo = tipo?.setores_permitidos?.length ? tipo.setores_permitidos : setores

  const campo = (k) => (e) => setForm({ ...form, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })
  const mudarTipo = (e) => {
    const t = tipos.find((x) => x.id === Number(e.target.value))
    const setorOk = !t?.setores_permitidos?.length || t.setores_permitidos.includes(form.setor_destino)
    setForm({
      ...form,
      tipo_visita_id: e.target.value,
      setor_destino: setorOk ? form.setor_destino : '',
      ...(t && !t.permite_veiculo ? { placa: '', descricao_veiculo: '', vaga_reservada: false } : {}),
    })
  }

  const limparForm = () => { setForm(novoForm()); setEditando(null) }

  const salvar = async (e) => {
    e.preventDefault()
    const corpo = { ...form, tipo_visita_id: Number(form.tipo_visita_id) }
    try {
      if (editando) await api(`/visitas/${editando.id}`, { method: 'PUT', body: corpo })
      else await api('/visitas', { method: 'POST', body: corpo })
      ok(editando ? 'Visita atualizada.' : 'Visita registrada como AGENDADA.')
      limparForm(); carregar(); onMudou()
    } catch (e2) { erro(e2) }
  }

  const editar = async (v) => {
    try {
      const d = await api(`/visitas/${v.id}`)
      setEditando({ id: d.id, status: d.status, tipo_visita_id: d.tipo_visita_id })
      setForm({
        tipo_visita_id: String(d.tipo_visita_id), nome_civil: d.nome_civil, nome_social: d.nome_social || '',
        documento: d.documento || '', setor_destino: d.setor_destino, data_visita: d.data_visita,
        horario_previsto: fmtHora(d.horario_previsto), atendimento_prioritario: d.atendimento_prioritario,
        placa: d.placa || '', descricao_veiculo: d.descricao_veiculo || '', vaga_reservada: d.vaga_reservada,
        observacao: d.observacao || '',
      })
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) { erro(e) }
  }

  const abrir = async (tipoModal, visita) => {
    limpar()
    if (tipoModal === 'entrada') {
      try {
        const livres = await api('/cartoes?status=DISPONIVEL')
        setCartoesLivres(livres)
        setCartaoEscolhido(livres[0] ? String(livres[0].id) : '')
      } catch (e) { erro(e); return }
    }
    if (tipoModal === 'saida') setDevolvido('')
    setModal({ tipo: tipoModal, visita })
  }
  const fechar = () => setModal(null)

  const executar = async (acao, msg) => {
    try {
      await acao()
      ok(msg)
      fechar(); carregar(); onMudou()
    } catch (e) { fechar(); erro(e) }
  }

  const confirmarEntrada = () =>
    executar(
      () => api(`/visitas/${modal.visita.id}/entrada`, { method: 'POST', body: { cartao_id: Number(cartaoEscolhido) } }),
      `Entrada confirmada: ${modal.visita.nome_exibido}.`,
    )
  const confirmarSaida = () =>
    executar(
      () => api(`/visitas/${modal.visita.id}/saida`, { method: 'POST', body: { cartao_devolvido: devolvido === 'sim' } }),
      devolvido === 'sim' ? 'Saída registrada; cartão devolvido.' : 'Saída registrada; cartão marcado como EXTRAVIADO.',
    )
  const confirmarCancelar = () =>
    executar(() => api(`/visitas/${modal.visita.id}/cancelar`, { method: 'POST' }), 'Visita cancelada.')
  const confirmarExcluir = () =>
    executar(() => api(`/visitas/${modal.visita.id}`, { method: 'DELETE' }), 'Visita excluída.')

  const filtro = (k) => (e) => setFiltros({ ...filtros, [k]: e.target.value })

  return (
    <section>
      <h1>Visitas</h1>
      <Aviso aviso={aviso} onFechar={limpar} />

      <form className="cartao-form" onSubmit={salvar} aria-label="Formulário de visita">
        <h2>{editando ? `Editar visita (${editando.status})` : 'Registrar visita'}</h2>
        <div className="grade">
          <label>Tipo de visita*
            <select value={form.tipo_visita_id} onChange={mudarTipo} required>
              <option value="">Selecione…</option>
              {tiposDoForm.map((t) => <option key={t.id} value={t.id}>{t.nome}{t.ativo ? '' : ' (inativo)'}</option>)}
            </select>
          </label>
          <label>Nome civil*<input value={form.nome_civil} onChange={campo('nome_civil')} required minLength={3} maxLength={120} /></label>
          <label>Nome social<input value={form.nome_social} onChange={campo('nome_social')} maxLength={120} />
            <small>Quando preenchido, é o nome exibido.</small>
          </label>
          <label>Documento (fictício){tipo?.exige_documento ? '*' : ''}
            <input value={form.documento} onChange={campo('documento')} maxLength={30} placeholder="DOC-0001" required={!!tipo?.exige_documento} />
            <small>Anotado e devolvido na hora; nunca retido.</small>
          </label>
          <label>Setor de destino*
            <select value={form.setor_destino} onChange={campo('setor_destino')} required>
              <option value="">Selecione…</option>
              {setoresDoTipo.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label>Data*<input type="date" value={form.data_visita} onChange={campo('data_visita')} required disabled={editando?.status === 'PRESENTE'} /></label>
          <label>Horário previsto*<input type="time" value={form.horario_previsto} onChange={campo('horario_previsto')} required /></label>
        </div>
        <div className="checks">
          <label><input type="checkbox" checked={form.atendimento_prioritario} onChange={campo('atendimento_prioritario')} /> Atendimento prioritário <small>(o motivo não é registrado)</small></label>
        </div>

        {tipo?.permite_veiculo && (
          <fieldset>
            <legend>Veículo</legend>
            <div className="grade">
              <label>Placa<input value={form.placa} onChange={campo('placa')} maxLength={8} placeholder="TST1A01" /></label>
              <label>Descrição do veículo<input value={form.descricao_veiculo} onChange={campo('descricao_veiculo')} maxLength={60} /></label>
            </div>
            <div className="checks">
              <label><input type="checkbox" checked={form.vaga_reservada} onChange={campo('vaga_reservada')} disabled={!form.placa} /> Vaga reservada (credencial conferida)</label>
            </div>
          </fieldset>
        )}

        <label className="largo">Observação ({form.observacao.length}/100)
          <input value={form.observacao} onChange={campo('observacao')} maxLength={100} />
          <small className="alerta-campo">Não registre motivo, saúde ou opinião sobre o visitante.</small>
        </label>

        <div className="acoes-form">
          <button type="submit" className="btn btn-primario">{editando ? 'Salvar alterações' : 'Registrar visita'}</button>
          {editando && <button type="button" className="btn" onClick={limparForm}>Cancelar edição</button>}
        </div>
      </form>

      <div className="filtros" role="search">
        <label>Nome<input value={filtros.q} onChange={filtro('q')} placeholder="Parte do nome civil ou social" /></label>
        <label>Setor
          <select value={filtros.setor} onChange={filtro('setor')}>
            <option value="">Todos</option>
            {setores.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <label>Tipo
          <select value={filtros.tipo_id} onChange={filtro('tipo_id')}>
            <option value="">Todos</option>
            {tipos.map((t) => <option key={t.id} value={t.id}>{t.nome}</option>)}
          </select>
        </label>
        <label>Data<input type="date" value={filtros.data} onChange={filtro('data')} /></label>
        <label>Status
          <select value={filtros.status} onChange={filtro('status')}>
            <option value="">Todos</option>
            {STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <button type="button" className="btn" onClick={() => setFiltros(FILTROS)}>Limpar filtros</button>
      </div>

      {visitas.length === 0 ? (
        <Vazio>Nenhuma visita encontrada.</Vazio>
      ) : (
        <table className="tabela">
          <thead>
            <tr><th>Data e hora</th><th>Visitante</th><th>Tipo</th><th>Setor</th><th>Documento</th><th>Cartão</th><th>Status</th><th>Ações</th></tr>
          </thead>
          <tbody>
            {visitas.map((v) => (
              <tr key={v.id}>
                <td data-label="Data e hora">{fmtData(v.data_visita)} {fmtHora(v.horario_previsto)}</td>
                <td data-label="Visitante">
                  <strong>{v.nome_exibido}</strong>
                  {v.atendimento_prioritario && <span className="badge badge-roxo" title="Atendimento prioritário">PRIORITÁRIO</span>}
                  {v.placa && <div className="sub">Veículo {v.placa}{v.vaga_reservada ? ' · vaga reservada' : ''}</div>}
                </td>
                <td data-label="Tipo">{v.tipo_nome}</td>
                <td data-label="Setor">{v.setor_destino}</td>
                <td data-label="Documento">{v.documento_mascarado || '—'}</td>
                <td data-label="Cartão">
                  {v.cartao_codigo || '—'}
                  {v.cartao_devolvido === false && <span className="badge badge-laranja">NÃO DEVOLVIDO</span>}
                </td>
                <td data-label="Status"><Status valor={v.status} /></td>
                <td data-label="Ações"><div className="acoes">
                  {v.status === 'AGENDADA' && <button type="button" className="btn btn-pq btn-primario" onClick={() => abrir('entrada', v)}>Entrada</button>}
                  {v.status === 'PRESENTE' && <button type="button" className="btn btn-pq btn-primario" onClick={() => abrir('saida', v)}>Saída</button>}
                  {(v.status === 'AGENDADA' || v.status === 'PRESENTE') && <button type="button" className="btn btn-pq" onClick={() => editar(v)}>Editar</button>}
                  {v.status === 'AGENDADA' && <button type="button" className="btn btn-pq" onClick={() => abrir('cancelar', v)}>Cancelar</button>}
                  {(v.status === 'AGENDADA' || v.status === 'CANCELADA') && <button type="button" className="btn btn-pq btn-perigo" onClick={() => abrir('excluir', v)}>Excluir</button>}
                  {v.status === 'ENCERRADA' && <span className="sub">Registro de presença</span>}
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {modal?.tipo === 'entrada' && (
        <Modal
          titulo={`Entrada de ${modal.visita.nome_exibido}`}
          onFechar={fechar}
          acoes={
            <>
              <button type="button" className="btn" onClick={fechar}>Voltar</button>
              <button type="button" className="btn btn-primario" onClick={confirmarEntrada} disabled={!cartaoEscolhido}>Confirmar entrada</button>
            </>
          }
        >
          {cartoesLivres.length === 0 ? (
            <p className="aviso aviso-erro" role="alert">Nenhum cartão disponível. Cadastre ou recupere um cartão.</p>
          ) : (
            <label>Cartão de acesso a entregar
              <select value={cartaoEscolhido} onChange={(e) => setCartaoEscolhido(e.target.value)}>
                {cartoesLivres.map((c) => <option key={c.id} value={c.id}>{c.codigo} ({c.cor})</option>)}
              </select>
            </label>
          )}
          <p className="nota">Entregue o cartão e devolva o documento imediatamente (Lei 5.553/1968).</p>
        </Modal>
      )}

      {modal?.tipo === 'saida' && (
        <Modal
          titulo={`Saída de ${modal.visita.nome_exibido}`}
          onFechar={fechar}
          acoes={
            <>
              <button type="button" className="btn" onClick={fechar}>Voltar</button>
              <button type="button" className="btn btn-primario" onClick={confirmarSaida} disabled={!devolvido}>Confirmar saída</button>
            </>
          }
        >
          <fieldset>
            <legend>O cartão {modal.visita.cartao_codigo} foi devolvido?</legend>
            <div className="checks">
              <label><input type="radio" name="devolvido" value="sim" checked={devolvido === 'sim'} onChange={(e) => setDevolvido(e.target.value)} /> Sim, devolvido</label>
              <label><input type="radio" name="devolvido" value="nao" checked={devolvido === 'nao'} onChange={(e) => setDevolvido(e.target.value)} /> Não devolvido (fica EXTRAVIADO)</label>
            </div>
          </fieldset>
        </Modal>
      )}

      {modal?.tipo === 'cancelar' && (
        <Confirmar
          titulo="Cancelar visita"
          texto={`Cancelar a visita de ${modal.visita.nome_exibido}?`}
          rotulo="Cancelar visita"
          onConfirmar={confirmarCancelar}
          onFechar={fechar}
        />
      )}

      {modal?.tipo === 'excluir' && (
        <Confirmar
          titulo="Excluir visita"
          texto={`Excluir definitivamente a visita de ${modal.visita.nome_exibido}?`}
          rotulo="Excluir"
          perigo
          onConfirmar={confirmarExcluir}
          onFechar={fechar}
        />
      )}
    </section>
  )
}
