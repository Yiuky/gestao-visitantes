// Cliente da API. Erros viram Error com a mensagem em português vinda de {"detail": ...}.

const NOMES_CAMPOS = {
  nome: 'Nome', nome_civil: 'Nome civil', nome_social: 'Nome social', documento: 'Documento',
  setor_destino: 'Setor', data_visita: 'Data', horario_previsto: 'Horário', placa: 'Placa',
  observacao: 'Observação', descricao_veiculo: 'Veículo', codigo: 'Código', codigo_leitura: 'Código de leitura',
  cor: 'Cor', status: 'Status', tipo_visita_id: 'Tipo de visita', cartao_id: 'Cartão', ponto_id: 'Ponto',
  codigo_lido: 'Código lido', sentido: 'Sentido', prazo_retencao_dias: 'Prazo de retenção',
}

function mensagemDeErro(corpo, status) {
  const d = corpo?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d
      .map((e) => {
        const campo = e.loc?.[e.loc.length - 1]
        const rotulo = NOMES_CAMPOS[campo] || (campo === 'body' ? '' : campo)
        const msg = String(e.msg || '').replace(/^Value error, /, '')
        return rotulo ? `${rotulo}: ${msg}` : msg
      })
      .join(' · ')
  }
  return `Erro ${status} ao falar com a API`
}

export async function api(caminho, { method = 'GET', body } = {}) {
  let resp
  try {
    resp = await fetch(`/api${caminho}`, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('API indisponível. Verifique se o backend está em execução.')
  }
  if (resp.status === 204) return null
  const corpo = await resp.json().catch(() => null)
  if (!resp.ok) {
    const erro = new Error(mensagemDeErro(corpo, resp.status))
    erro.status = resp.status
    throw erro
  }
  return corpo
}

export const qs = (params) => {
  const p = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== '' && v != null && p.append(k, v))
  const s = p.toString()
  return s ? `?${s}` : ''
}

export const fmtData = (iso) => (iso ? iso.slice(0, 10).split('-').reverse().join('/') : '')
export const fmtHora = (t) => (t ? t.slice(0, 5) : '')
export const fmtDataHora = (iso) => (iso ? `${fmtData(iso)} ${iso.slice(11, 16)}` : '')
