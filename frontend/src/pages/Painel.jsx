import { useCallback, useEffect, useState } from 'react'
import { api, fmtData, fmtDataHora } from '../api.js'
import { Aviso, Vazio, useAviso } from '../componentes.jsx'

const INDICADORES = [
  { chave: 'visitas_do_dia', rotulo: 'Visitas do dia', principal: true },
  { chave: 'presentes', rotulo: 'Presentes agora', principal: true },
  { chave: 'encerradas_do_dia', rotulo: 'Encerradas do dia', principal: true },
  { chave: 'veiculos_no_patio', rotulo: 'Veículos no pátio' },
  { chave: 'cartoes_pendentes', rotulo: 'Cartões pendentes' },
  { chave: 'acessos_negados_hoje', rotulo: 'Acessos negados hoje' },
]

export default function Painel({ versao }) {
  const [dados, setDados] = useState(null)
  const [presentes, setPresentes] = useState([])
  const [atualizado, setAtualizado] = useState(null)
  const { aviso, erro, limpar } = useAviso()

  const carregar = useCallback(async () => {
    try {
      const [d, p] = await Promise.all([api('/dashboard'), api('/presentes')])
      setDados(d)
      setPresentes(p)
      setAtualizado(new Date())
      limpar()
    } catch (e) { erro(e) }
  }, [])

  // Recarrega ao abrir, após cada operação nas outras abas (versao) e a cada 30 s.
  useEffect(() => {
    carregar()
    const t = setInterval(carregar, 30000)
    return () => clearInterval(t)
  }, [carregar, versao])

  return (
    <section>
      <div className="cabecalho-painel">
        <h1>Painel {dados && <small>· {fmtData(dados.data_referencia)}</small>}</h1>
        <div className="acoes-form nao-imprimir">
          <button type="button" className="btn" onClick={carregar}>Atualizar</button>
          <button type="button" className="btn btn-primario" onClick={() => window.print()} disabled={!presentes.length}>
            Imprimir lista de evacuação
          </button>
        </div>
      </div>
      <Aviso aviso={aviso} onFechar={limpar} />

      <div className="indicadores nao-imprimir" aria-live="polite">
        {INDICADORES.map((i) => (
          <div key={i.chave} className={`indicador ${i.principal ? 'principal' : ''}`} data-indicador={i.chave}>
            <span className="valor">{dados ? dados[i.chave] : '–'}</span>
            <span className="rotulo">{i.rotulo}</span>
          </div>
        ))}
      </div>

      <div className="lista-evacuacao">
        <h2>Quem está no prédio agora</h2>
        <p className="so-imprimir">
          Lista de evacuação · gerada em {atualizado?.toLocaleString('pt-BR')} · {presentes.length} pessoa(s) · dados fictícios
        </p>
        {presentes.length === 0 ? (
          <Vazio>Nenhum visitante no prédio no momento.</Vazio>
        ) : (
          <table className="tabela">
            <thead><tr><th>Visitante</th><th>Setor de destino</th><th>Cartão</th><th>Último local</th><th>No prédio desde</th></tr></thead>
            <tbody>
              {presentes.map((p) => (
                <tr key={p.visita_id}>
                  <td data-label="Visitante"><strong>{p.nome_exibido}</strong>{p.placa && <div className="sub">Veículo {p.placa}</div>}</td>
                  <td data-label="Setor">{p.setor_destino}</td>
                  <td data-label="Cartão">{p.cartao_codigo}</td>
                  <td data-label="Último local">{p.ultimo_local}</td>
                  <td data-label="Desde">{fmtDataHora(p.desde)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {atualizado && <p className="nota nao-imprimir">Atualizado às {atualizado.toLocaleTimeString('pt-BR')}.</p>}
    </section>
  )
}
