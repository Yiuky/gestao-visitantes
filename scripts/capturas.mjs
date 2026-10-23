// Roteiro E2E com capturas: clica nos botões reais da interface (Chrome headless via CDP),
// confere o resultado na tela e salva as evidências em docs/img/.
//
// Pré-requisito: stack no ar com o seed recém-carregado, por exemplo:
//   docker compose down -v; docker compose up -d; docker compose run --rm api python seed.py
//   node scripts/capturas.mjs                         (BASE_URL padrão: http://localhost:8080)
// Variáveis: BASE_URL, CHROME (caminho do executável).
// Sem dependências: usa o WebSocket nativo do Node 22+.
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const BASE = process.env.BASE_URL || 'http://localhost:8080'
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const SAIDA = resolve(dirname(fileURLToPath(import.meta.url)), '../docs/img')
const PORTA = 9333
const espera = (ms) => new Promise((r) => setTimeout(r, ms))

const resultados = []
function confere(id, descricao, ok, detalhe = '') {
  resultados.push({ id, descricao, ok, detalhe })
  console.log(`${ok ? 'PASSOU' : 'FALHOU'}  ${id}  ${descricao}${detalhe ? `  → ${detalhe}` : ''}`)
}

// ---------- CDP mínimo ----------
async function abrirChrome() {
  const perfil = mkdtempSync(join(tmpdir(), 'gv-chrome-'))
  const proc = spawn(CHROME, [
    '--headless=new', `--remote-debugging-port=${PORTA}`, `--user-data-dir=${perfil}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', '--lang=pt-BR', 'about:blank',
  ], { stdio: 'ignore' })
  for (let i = 0; i < 50; i++) {
    try {
      const alvo = await (await fetch(`http://127.0.0.1:${PORTA}/json/new?about:blank`, { method: 'PUT' })).json()
      return { proc, perfil, wsUrl: alvo.webSocketDebuggerUrl }
    } catch { await espera(200) }
  }
  throw new Error('Chrome headless não respondeu')
}

class Pagina {
  constructor(ws) {
    this.ws = ws
    this.id = 0
    this.pendentes = new Map()
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data)
      if (msg.id && this.pendentes.has(msg.id)) {
        const { ok, falha } = this.pendentes.get(msg.id)
        this.pendentes.delete(msg.id)
        msg.error ? falha(new Error(msg.error.message)) : ok(msg.result)
      }
    })
  }
  static async conectar(url) {
    const ws = new WebSocket(url)
    await new Promise((ok, falha) => { ws.addEventListener('open', ok); ws.addEventListener('error', falha) })
    return new Pagina(ws)
  }
  enviar(method, params = {}) {
    const id = ++this.id
    this.ws.send(JSON.stringify({ id, method, params }))
    return new Promise((ok, falha) => this.pendentes.set(id, { ok, falha }))
  }
  async avaliar(fn, ...args) {
    const r = await this.enviar('Runtime.evaluate', {
      expression: `(${fn})(...${JSON.stringify(args)})`, awaitPromise: true, returnByValue: true,
    })
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text)
    return r.result.value
  }
  async tela(largura, altura, movel = false) {
    await this.enviar('Emulation.setDeviceMetricsOverride', {
      width: largura, height: altura, deviceScaleFactor: movel ? 2 : 1, mobile: movel,
    })
  }
  async ir(url) {
    await this.enviar('Page.navigate', { url })
    await this.esperar(() => document.readyState === 'complete' && !!document.querySelector('h1'))
  }
  async esperar(cond, ...args) {
    for (let i = 0; i < 50; i++) {
      if (await this.avaliar(cond, ...args)) return true
      await espera(100)
    }
    throw new Error(`condição não atendida: ${cond}`)
  }
  async capturar(nome, paginaInteira = false) {
    const params = { format: 'png' }
    if (paginaInteira) {
      const { cssContentSize } = await this.enviar('Page.getLayoutMetrics')
      params.captureBeyondViewport = true
      params.clip = { x: 0, y: 0, width: cssContentSize.width, height: cssContentSize.height, scale: 1 }
    }
    const { data } = await this.enviar('Page.captureScreenshot', params)
    writeFileSync(join(SAIDA, nome), Buffer.from(data, 'base64'))
    console.log(`        captura: docs/img/${nome}`)
  }
}

// ---------- ações na página (rodam no navegador) ----------
const H = {
  clicarAba: (rotulo) => { [...document.querySelectorAll('[role=tab]')].find((b) => b.textContent === rotulo).click(); return true },
  clicar: (texto, escopo = 'body', linha = null) => {
    const raiz = linha
      ? [...document.querySelectorAll('tbody tr')].find((r) => r.textContent.includes(linha))
      : document.querySelector(escopo)
    const b = [...raiz.querySelectorAll('button')].find((x) => x.textContent.trim().startsWith(texto))
    if (!b) throw new Error(`botão "${texto}" não encontrado`)
    b.click()
    return true
  },
  definir: (rotulo, valor, escopo = 'body') => {
    const label = [...document.querySelector(escopo).querySelectorAll('label')].find((l) => l.textContent.trim().startsWith(rotulo))
    const campo = label.querySelector('input, select')
    if (campo.tagName === 'SELECT') {
      const opcao = [...campo.options].find((o) => o.textContent.startsWith(valor) || o.value === valor)
      if (!opcao) throw new Error(`opção "${valor}" não encontrada em "${rotulo}"`)
      valor = opcao.value
    }
    const proto = campo.tagName === 'SELECT' ? HTMLSelectElement.prototype : HTMLInputElement.prototype
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(campo, valor)
    campo.dispatchEvent(new Event(campo.tagName === 'SELECT' ? 'change' : 'input', { bubbles: true }))
    return true
  },
  aviso: () => document.querySelector('.aviso')?.textContent.replace('×', '').trim() || '',
  indicadores: () => Object.fromEntries([...document.querySelectorAll('[data-indicador]')].map((e) => [e.dataset.indicador, e.querySelector('.valor').textContent])),
}

async function main() {
  mkdirSync(SAIDA, { recursive: true })
  const { proc, perfil, wsUrl } = await abrirChrome()
  const p = await Pagina.conectar(wsUrl)
  await p.enviar('Page.enable')
  await p.enviar('Runtime.enable')
  try {
    // 1. Painel com o seed
    await p.tela(1280, 860)
    await p.ir(BASE)
    await p.esperar(() => document.querySelector('[data-indicador=visitas_do_dia] .valor')?.textContent !== '–')
    let ind = await p.avaliar(H.indicadores)
    confere('E01', 'Painel com seed: 4 do dia, 1 presente, 1 encerrada', ind.visitas_do_dia === '4' && ind.presentes === '1' && ind.encerradas_do_dia === '1', JSON.stringify(ind))
    await p.capturar('01-painel.png')

    // 2. Formulário com erro 422 da API (placa inválida) e depois registro válido
    await p.avaliar(H.clicarAba, 'Visitas')
    // espera as listas de tipos e setores chegarem da API antes de preencher
    await p.esperar(() => document.querySelectorAll('form[aria-label="Formulário de visita"] select option').length > 7)
    await p.avaliar(H.definir, 'Tipo de visita', 'Reunião técnica')
    await p.avaliar(H.definir, 'Nome civil', 'Helena Exemplo')
    await p.avaliar(H.definir, 'Documento', 'DOC-0200')
    await p.avaliar(H.definir, 'Setor de destino', 'Jurídico')
    await p.avaliar(H.definir, 'Horário previsto', '16:00')
    await p.esperar(() => !!document.querySelector('legend') && [...document.querySelectorAll('legend')].some((l) => l.textContent === 'Veículo'))
    await p.avaliar(H.definir, 'Placa', 'AB12345')
    await p.avaliar(H.clicar, 'Registrar visita', 'form')
    await p.esperar(() => !!document.querySelector('.aviso-erro'))
    let aviso = await p.avaliar(H.aviso)
    confere('E02', 'Placa inválida mostra o 422 da API na tela', aviso.includes('placa inválida'), aviso)
    await p.avaliar(() => window.scrollTo(0, 0))
    await p.capturar('02-formulario-erro-422.png')
    await p.avaliar(H.definir, 'Placa', '')
    await p.avaliar(H.clicar, 'Registrar visita', 'form')
    await p.esperar(() => document.querySelector('.aviso-ok')?.textContent.includes('AGENDADA'))
    confere('E03', 'Visita válida registrada como AGENDADA', true, await p.avaliar(H.aviso))

    // 3. Entrada negada por cartão em uso (409): outra recepção usa o cartão enquanto o modal está aberto
    await p.esperar(() => [...document.querySelectorAll('tbody tr')].some((r) => r.textContent.includes('Caio Fictício')))
    await p.avaliar(H.clicar, 'Entrada', 'body', 'Caio Fictício')
    await p.esperar(() => !!document.querySelector('[role=dialog] select'))
    const cartaoId = await p.avaliar(() => document.querySelector('[role=dialog] select').value)
    const usoParalelo = await p.avaliar(async (id) => {
      const [helena] = await (await fetch('/api/visitas?q=Helena')).json()
      const r = await fetch(`/api/visitas/${helena.id}/entrada`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ cartao_id: Number(id) }),
      })
      return r.status
    }, cartaoId)
    await p.avaliar(H.clicar, 'Confirmar entrada', '[role=dialog]')
    await p.esperar(() => !!document.querySelector('.aviso-erro'))
    aviso = await p.avaliar(H.aviso)
    confere('E04', 'Entrada com cartão já em uso → 409 visível', usoParalelo === 200 && aviso.includes('não está disponível'), aviso)
    await espera(400)
    await p.capturar('03-entrada-409-cartao-em-uso.png')

    // 4. Catraca: leitor de outro setor (NEGADO) e do setor de destino (LIBERADO)
    await p.avaliar(() => window.scrollTo(0, 0))
    await p.avaliar(H.clicarAba, 'Catraca')
    await p.esperar(() => [...document.querySelectorAll('.atalhos button')].some((b) => b.textContent === 'V-002'))
    await p.avaliar(H.clicar, 'V-002', '.atalhos')
    await p.avaliar(H.definir, 'Ponto de acesso', 'Leitor Diretoria')
    await p.avaliar(H.clicar, 'Ler cartão', 'form')
    await p.esperar(() => !!document.querySelector('.resultado-negado'))
    const negado = await p.avaliar(() => document.querySelector('.resultado').innerText)
    confere('E05', 'Leitor de outro setor → NEGADO com motivo', negado.includes('área não autorizada'), negado.replace(/\n/g, ' · '))
    await p.esperar(() => document.querySelectorAll('.trajeto li').length >= 1)
    await p.capturar('04-catraca-negado.png')
    await p.avaliar(H.definir, 'Ponto de acesso', 'Leitor Jurídico')
    await p.avaliar(H.clicar, 'Ler cartão', 'form')
    await p.esperar(() => !!document.querySelector('.resultado-liberado'))
    await p.esperar(() => document.querySelectorAll('.trajeto li').length >= 2)
    confere('E06', 'Leitor do setor de destino → LIBERADO; trajeto com 2 passagens', true)
    await p.capturar('05-catraca-liberado-trajeto.png')

    // 5. Painel reflete as operações e o último local
    await p.avaliar(H.clicarAba, 'Painel')
    await p.esperar(() => document.querySelector('[data-indicador=acessos_negados_hoje] .valor')?.textContent === '1')
    ind = await p.avaliar(H.indicadores)
    const local = await p.avaliar(() => [...document.querySelectorAll('tbody tr')].find((r) => r.textContent.includes('Bruno'))?.children[3].textContent)
    confere('E07', 'Painel: 5 do dia, 2 presentes, 1 negado; último local do Bruno = Leitor Jurídico',
      ind.visitas_do_dia === '5' && ind.presentes === '2' && ind.acessos_negados_hoje === '1' && local === 'Leitor Jurídico', `${JSON.stringify(ind)} · ${local}`)
    await p.capturar('06-painel-presentes.png')

    // 6. Impressão da lista de evacuação (M11)
    await p.enviar('Emulation.setEmulatedMedia', { media: 'print' })
    const impressao = await p.avaliar(() => ({
      topo: getComputedStyle(document.querySelector('.topo')).display,
      indicadores: getComputedStyle(document.querySelector('.indicadores')).display,
      cabecalho: getComputedStyle(document.querySelector('.so-imprimir')).display,
      linhas: document.querySelectorAll('.lista-evacuacao tbody tr').length,
    }))
    confere('E08', 'Impressão mostra só a lista de evacuação', impressao.topo === 'none' && impressao.indicadores === 'none' && impressao.cabecalho === 'block' && impressao.linhas === 2, JSON.stringify(impressao))
    await p.capturar('07-impressao-lista-evacuacao.png')
    const pdf = await p.enviar('Page.printToPDF', { printBackground: false, preferCSSPageSize: false })
    writeFileSync(join(SAIDA, 'lista-evacuacao.pdf'), Buffer.from(pdf.data, 'base64'))
    console.log('        captura: docs/img/lista-evacuacao.pdf')
    await p.enviar('Emulation.setEmulatedMedia', { media: '' })

    // 7. Celular 360 px (M12)
    await p.tela(360, 780, true)
    await p.avaliar(H.clicarAba, 'Visitas')
    await p.esperar(() => document.querySelectorAll('tbody tr').length > 0)
    await p.avaliar(() => document.querySelector('.tabela').scrollIntoView())
    const movel = await p.avaliar(() => ({
      largura: window.innerWidth, rolagem: document.documentElement.scrollWidth,
      cabecalho: getComputedStyle(document.querySelector('thead')).display,
      // F5: selos e sublinhas não podem cair na coluna do rótulo
      invadeRotulo: [...document.querySelectorAll('.tabela td *')].filter((el) =>
        el.getBoundingClientRect().left < el.closest('td').getBoundingClientRect().left + 120).length,
    }))
    confere('E09', '360 px sem rolagem horizontal; tabela vira cartões; nada na coluna do rótulo',
      movel.rolagem <= movel.largura && movel.cabecalho === 'none' && movel.invadeRotulo === 0, JSON.stringify(movel))
    await p.capturar('08-celular-360.png')
  } finally {
    p.ws.close()
    proc.kill()
    await espera(300)
    try { rmSync(perfil, { recursive: true, force: true }) } catch { /* Chrome pode segurar arquivos por alguns ms */ }
  }

  const falhas = resultados.filter((r) => !r.ok).length
  console.log(`\n${resultados.length - falhas} passaram, ${falhas} falharam`)
  process.exitCode = falhas ? 1 : 0
}

main().catch((e) => { console.error(e); process.exitCode = 1 })
