import { useCallback, useEffect, useState } from 'react'
import { api, fmtDataHora, qs } from '../api.js'
import { Aviso, Status, Vazio, useAviso } from '../componentes.jsx'

// Simulador de leitor: o mesmo contrato (POST /api/catraca/passagens) que um equipamento real chamaria (ADR-012).
export default function Catraca({ onMudou }) {
  const [pontos, setPontos] = useState([])
  const [emUso, setEmUso] = useState([])
  const [visitas, setVisitas] = useState([])
  const [pontoId, setPontoId] = useState('')
  const [sentido, setSentido] = useState('ENTRADA')
  const [codigo, setCodigo] = useState('')
  const [ultima, setUltima] = useState(null)
  const [visitaId, setVisitaId] = useState('')
  const [trajeto, setTrajeto] = useState([])
  const { aviso, erro, limpar } = useAviso()

  const carregarListas = useCallback(async () => {
    try {
      const [p, c, v] = await Promise.all([
        api('/pontos-acesso'),
        api('/cartoes?status=EM_USO'),
        api(`/visitas${qs({ status: 'PRESENTE' })}`),
      ])
      setPontos(p)
      setEmUso(c)
      setVisitas(v)
      setPontoId((atual) => atual || (p[0] ? String(p[0].id) : ''))
    } catch (e) { erro(e) }
  }, [])
  useEffect(() => { carregarListas() }, [carregarListas])

  const carregarTrajeto = useCallback(async (id) => {
    if (!id) { setTrajeto([]); return }
    try { setTrajeto(await api(`/visitas/${id}/passagens`)) } catch (e) { erro(e) }
  }, [])
  useEffect(() => { carregarTrajeto(visitaId) }, [visitaId, carregarTrajeto])

  const ler = async (e) => {
    e.preventDefault()
    limpar()
    try {
      const r = await api('/catraca/passagens', {
        method: 'POST',
        body: { codigo_lido: codigo, ponto_id: Number(pontoId), sentido },
      })
      setUltima(r)
      onMudou()
      // Mostra o trajeto da visita lida, quando há uma.
      if (r.passagem.visita_id) {
        if (String(r.passagem.visita_id) === visitaId) carregarTrajeto(visitaId)
        else setVisitaId(String(r.passagem.visita_id))
      }
    } catch (e2) { erro(e2) }
  }

  const ponto = pontos.find((p) => String(p.id) === pontoId)

  return (
    <section>
      <h1>Catraca (simulador)</h1>
      <p className="nota">
        Rastreamento por pontos de passagem, nunca contínuo: sem câmera nem geolocalização. Toda leitura é gravada e não
        pode ser editada nem excluída.
      </p>
      <Aviso aviso={aviso} onFechar={limpar} />

      <div className="duas-colunas">
        <div>
          <form className="cartao-form" onSubmit={ler} aria-label="Simular leitura de cartão">
            <h2>Leitura de cartão</h2>
            <div className="grade">
              <label>Ponto de acesso
                <select value={pontoId} onChange={(e) => setPontoId(e.target.value)} required>
                  {pontos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nome} — {p.setor || 'área comum'}{p.ativo ? '' : ' (inativo)'}
                    </option>
                  ))}
                </select>
              </label>
              <label>Código lido
                <input
                  value={codigo}
                  onChange={(e) => setCodigo(e.target.value)}
                  list="cartoes-em-uso"
                  required
                  maxLength={32}
                  placeholder="RFID-TESTE-0002"
                />
                <datalist id="cartoes-em-uso">
                  {emUso.map((c) => <option key={c.id} value={c.codigo_leitura}>{c.codigo}</option>)}
                </datalist>
                <small>Digite ou escolha um cartão em uso.</small>
              </label>
            </div>
            <fieldset>
              <legend>Sentido</legend>
              <div className="checks">
                {['ENTRADA', 'SAIDA'].map((s) => (
                  <label key={s}>
                    <input type="radio" name="sentido" value={s} checked={sentido === s} onChange={() => setSentido(s)} />
                    {s === 'ENTRADA' ? 'Entrada' : 'Saída'}
                  </label>
                ))}
              </div>
            </fieldset>
            {emUso.length > 0 && (
              <div className="atalhos">
                <span className="sub">Cartões em uso:</span>
                {emUso.map((c) => (
                  <button key={c.id} type="button" className="btn btn-pq" onClick={() => setCodigo(c.codigo_leitura)}>
                    {c.codigo}
                  </button>
                ))}
              </div>
            )}
            <div className="acoes-form">
              <button type="submit" className="btn btn-primario" disabled={!pontoId || !codigo}>
                Ler cartão em {ponto?.nome || '…'}
              </button>
              <button type="button" className="btn" onClick={carregarListas}>Atualizar listas</button>
            </div>
          </form>

          {ultima && (
            <div className={`resultado resultado-${ultima.resultado.toLowerCase()}`} role="status" aria-live="assertive">
              <span className="resultado-titulo">{ultima.resultado}</span>
              <span>{ultima.passagem.ponto_nome} · {ultima.passagem.sentido === 'ENTRADA' ? 'entrada' : 'saída'} · {ultima.passagem.codigo_lido}</span>
              {ultima.motivo && <strong>Motivo: {ultima.motivo}</strong>}
            </div>
          )}
        </div>

        <div className="bloco">
          <h2>Trajeto da visita</h2>
          <label>Visita presente
            <select value={visitaId} onChange={(e) => setVisitaId(e.target.value)}>
              <option value="">Selecione…</option>
              {visitas.map((v) => (
                <option key={v.id} value={v.id}>{v.nome_exibido} — {v.setor_destino} ({v.cartao_codigo})</option>
              ))}
              {visitaId && !visitas.some((v) => String(v.id) === visitaId) && <option value={visitaId}>Visita #{visitaId}</option>}
            </select>
          </label>
          {!visitaId ? (
            <Vazio>Selecione uma visita para ver as passagens.</Vazio>
          ) : trajeto.length === 0 ? (
            <Vazio>Nenhuma passagem registrada para esta visita.</Vazio>
          ) : (
            <ol className="trajeto">
              {trajeto.map((p) => (
                <li key={p.id}>
                  <Status valor={p.resultado} /> <strong>{p.ponto_nome}</strong> · {p.sentido === 'ENTRADA' ? 'entrada' : 'saída'}
                  <div className="sub">{fmtDataHora(p.ocorrido_em)}{p.motivo ? ` · ${p.motivo}` : ''}</div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </section>
  )
}
