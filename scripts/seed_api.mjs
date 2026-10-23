// Carrega o seed FICTÍCIO pela API pública (sem acesso direto ao banco).
// Útil no deploy: a DATABASE_URL tem senha e não precisa sair do Render.
//   node scripts/seed_api.mjs                 (BASE_URL padrão: http://localhost:8080)
//   $env:BASE_URL="https://gestao-visitantes.vercel.app"; node scripts/seed_api.mjs
// Só roda com o banco vazio (nenhum tipo de visita cadastrado).
//
// Diferença para backend/seed.py: a API só dá entrada em visitas do dia (RN13), então a
// "Elisa Simulada" (cartão não devolvido) é registrada hoje, e não ontem.
const BASE = (process.env.BASE_URL || 'http://localhost:8080').replace(/\/$/, '')

async function api(caminho, method = 'GET', body) {
  const r = await fetch(`${BASE}/api${caminho}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  const texto = await r.text()
  if (!r.ok) throw new Error(`${method} ${caminho} → ${r.status} ${texto}`)
  return texto ? JSON.parse(texto) : null
}

async function main() {
  const { data_referencia: hoje } = await api('/dashboard')
  if ((await api('/tipos-visita')).length) {
    console.log('Banco já possui dados; seed ignorado.')
    return
  }

  const tipos = {}
  for (const [nome, exige_documento, permite_veiculo, setores_permitidos] of [
    ['Atendimento ao público', false, false, ['Atendimento', 'Protocolo']],
    ['Reunião técnica', true, true, []],
    ['Entrega de material', true, true, ['Protocolo']],
    ['Prestador de serviço', true, true, ['Tecnologia']],
    ['Audiência com autoridade', true, true, ['Diretoria']],
  ]) {
    tipos[nome] = (await api('/tipos-visita', 'POST', { nome, exige_documento, permite_veiculo, setores_permitidos })).id
  }

  const cartoes = {}
  for (let i = 1; i <= 10; i++) {
    const codigo = `V-${String(i).padStart(3, '0')}`
    const c = await api('/cartoes', 'POST', {
      codigo, codigo_leitura: `RFID-TESTE-${String(i).padStart(4, '0')}`, cor: i % 2 ? 'verde' : 'amarelo',
    })
    cartoes[codigo] = c.id
  }

  const visita = (tipo, dados) =>
    api('/visitas', 'POST', { tipo_visita_id: tipos[tipo], data_visita: hoje, ...dados })
  const entrada = (v, cartao) => api(`/visitas/${v.id}/entrada`, 'POST', { cartao_id: cartoes[cartao] })
  const saida = (v, devolvido) => api(`/visitas/${v.id}/saida`, 'POST', { cartao_devolvido: devolvido })

  const ana = await visita('Atendimento ao público', { nome_civil: 'Ana Exemplo', setor_destino: 'Protocolo', horario_previsto: '08:30' })
  await entrada(ana, 'V-001')
  await saida(ana, true)

  const bruno = await visita('Reunião técnica', {
    nome_civil: 'Bruno Teste', documento: 'DOC-0002', setor_destino: 'Jurídico', horario_previsto: '09:00',
    placa: 'TST1A01', descricao_veiculo: 'Carro prata (fictício)',
  })
  await entrada(bruno, 'V-002')

  await visita('Prestador de serviço', {
    nome_civil: 'Carla Fictícia', nome_social: 'Caio Fictício', documento: 'DOC-0003', setor_destino: 'Tecnologia',
    horario_previsto: '10:15', atendimento_prioritario: true,
  })
  await visita('Audiência com autoridade', {
    nome_civil: 'Diego Modelo', documento: 'DOC-0004', setor_destino: 'Diretoria', horario_previsto: '14:00',
  })

  const elisa = await visita('Entrega de material', {
    nome_civil: 'Elisa Simulada', documento: 'DOC-0005', setor_destino: 'Protocolo', horario_previsto: '07:45',
  })
  await entrada(elisa, 'V-009')
  await saida(elisa, false)

  console.log('Seed carregado pela API: 5 tipos, 10 cartões, 5 visitas (dados fictícios).')
  console.log('Painel:', JSON.stringify(await api('/dashboard')))
}

main().catch((e) => { console.error(e.message); process.exitCode = 1 })
