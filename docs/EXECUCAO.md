# EXECUÇÃO — log real de comandos e resultados

> Preenchido pelo Claude Code **durante** cada sprint, com comandos e saídas reais (resumidas quando longas).
> Nunca registrar "passou" sem a saída correspondente. Use **NÃO TESTADO** quando não houver execução.

## Ambiente
| Item | Versão (preencher na S0) |
|---|---|
| Sistema operacional | Windows 10 Pro 10.0.19045 |
| Python | 3.12.13 |
| Node | v24.16.0 |
| Git | 2.54.0.windows.1 |
| gh | 2.102.0 |
| Docker / Compose | 29.9.1 / v5.6.0 |

## Modelo de registro
```
### Sx — <título> — <data/hora>
Comando: <comando>
Saída: <trecho relevante>
Resultado: PASSOU | FALHOU | NÃO TESTADO
Observação: <o que foi corrigido, se houver>
```

## S0 — Estrutura, ambiente e Git

### S0 — Ferramentas — 2026-10-23
Comando: `python --version; node --version; git --version; gh --version; docker --version; docker compose version`
Saída: `Python 3.12.13` · `v24.16.0` · `git version 2.54.0.windows.1` · `gh version 2.102.0` · `Docker version 29.9.1` · `Docker Compose version v5.6.0`
Resultado: PASSOU
Observação: o daemon Docker estava parado (`failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`); Docker Desktop iniciado.

### S0 — Git e .gitignore — 2026-10-23
Comando: `git init -b main` e `git check-ignore -v tmp/x.db backend/data/visitantes.db .env backend/.venv/x node_modules/x` (arquivos de teste criados e apagados)
Saída:
```
Initialized empty Git repository in .../gestao-visitantes/.git/
.gitignore:9:*.db	tmp/x.db
.gitignore:9:*.db	backend/data/visitantes.db
.gitignore:14:.env	.env
.gitignore:4:.venv/	backend/.venv/x
.gitignore:18:node_modules/	node_modules/x
```
Resultado: PASSOU

### S0 — Inconsistências corrigidas nos documentos
| # | Inconsistência | Correção |
|---|---|---|
| 1 | `DATABASE_URL` padrão relativo à pasta de execução (uvicorn em `backend/` criaria `backend/backend/data`) | caminho absoluto em `config.py` (ARQUITETURA) |
| 2 | `CLAUDE.md` × RN02 sobre "tipo ativo" na edição | ADR-013 |
| 3 | T02 "409 ou 422" | 409 (ADR-014) |
| 4 | RN05a/RN05b colidiam com RN05 | renomeados RN04a/RN04b |
| 5 | PUT de cartão sem limite de status | ADR-014 |
| 6 | `date(ocorrido_em)` × fuso | ADR-016 |
| 7 | indicador de negados exigido na S3 sem tabela | ADR-017 |
| 8 | sem testes para ordenação e exclusão no painel | T28, T39 |

## S1 — API núcleo

### S1 — Ambiente Python — 2026-10-23
Comando: `pytest -q` (venv criado com `python -m venv`)
Saída:
```
backend\app\database.py:29: in <module> engine = criar_engine(DATABASE_URL)
C:\Program Files\QGIS 3.44.10\apps\Python312\Lib\sqlite3\dbapi2.py:27: from _sqlite3 import *
E   ImportError: DLL load failed while importing _sqlite3: Não foi possível encontrar o módulo especificado.
```
Resultado: FALHOU → corrigido (falha F1)
Correção: o `python` do PATH é o Python embutido do QGIS, sem a DLL do SQLite. O venv foi recriado com Python gerenciado pelo uv:
`uv venv --native-tls --managed-python --python 3.12 .venv` + `uv pip install --native-tls -r requirements.txt`
→ `3.12.14 ... sqlite 3.53.1`

### S1 — Suíte automatizada — 2026-10-23
Comando: `.\backend\.venv\Scripts\python.exe -m pytest -p no:warnings -o addopts=""`
Saída: `============================= 54 passed in 5.60s ==============================`
Resultado: PASSOU (T01–T29 + casos extras de 404, filtros, normalização de placa, ADR-013)
Versões: fastapi 0.161.1 · starlette 1.9.0 · sqlalchemy 2.1.6 · pydantic 2.14.1 · uvicorn 0.54.0 · pytest 9.1.1 · httpx 0.28.1 · tzdata 2026.5 (fixadas em `backend/requirements.txt`)

### S1 — Persistência após reinício (API real, uvicorn :8000) — 2026-10-23
Comando: subir uvicorn → `POST /api/tipos-visita` + `POST /api/visitas` → `Stop-Process` → subir de novo → `GET /api/visitas`
Saída:
```
criada antes do reinicio: id=1 status=AGENDADA
apos reinicio: 1 visita(s): Pessoa Persistida / AGENDADA
arquivo: ...\gestao-visitantes\backend\data\visitantes.db
```
Resultado: PASSOU (confirma também o caminho absoluto do banco, correção #1 da S0)

### S1 — Seed fictício — 2026-10-23
Comando: `python seed.py` (duas vezes)
Saída: `Seed carregado: 5 tipos, 10 cartões, 5 visitas (dados fictícios).` · `Banco já possui dados; seed ignorado.`
Resultado: PASSOU (idempotente)

## S2 — Frontend núcleo

### S2 — Instalação e build — 2026-10-23
Comando: `cd frontend; npm install --no-audit --no-fund; npm run build`
Saída:
```
added 62 packages in 18s
vite v5.4.11 building for production...
✓ 37 modules transformed.
dist/index.html                   0.50 kB │ gzip:  0.32 kB
dist/assets/index-G19SUIPB.css    5.56 kB │ gzip:  1.81 kB
dist/assets/index-dzSQlDK6.js   168.06 kB │ gzip: 52.72 kB
✓ built in 862ms
```
Resultado: PASSOU
Observação: o npm 11 avisa `allow-scripts` para o postinstall do esbuild; o build funciona sem ele (binário vem da dependência opcional).

### S2 — Testes de botões no navegador real (MCP Claude in Chrome) — 2026-10-23
Ambiente: uvicorn :8000 com o seed + `npm run dev` :5173; Chrome 1912 px de largura. Cada clique foi feito pelo MCP (`computer.left_click`, `form_input`) e o efeito conferido na tela (screenshot, `get_page_text` ou leitura do DOM).

| # | Tela · botão | Ação | Resultado observado | Status |
|---|---|---|---|---|
| B01 | Abas | Painel / Visitas / Tipos / Cartões | troca de aba; seed listado (5 visitas, 5 tipos, 10 cartões) | PASSOU |
| B02 | Visitas · Registrar (M02) | Reunião técnica sem documento | bloqueado pelo navegador: "Preencha este campo" no Documento* | PASSOU |
| B03 | Visitas · Registrar | placa `AB12345` | alerta vermelho: "Placa: placa inválida; use o formato AAA9999 ou AAA9A99" (422 da API) | PASSOU |
| B04 | Visitas · Registrar | placa `tst-1a01` | "Visita registrada como AGENDADA."; placa normalizada `TST1A01` | PASSOU |
| B05 | Visitas · Entrada → Confirmar | Fernanda (placa já no pátio) | 409 "veículo TST1A01 já está no pátio" — **mensagem fora da tela** | FALHOU → F2 |
| B05b | idem, após correção | mesma ação | alerta rolado para a área visível | PASSOU |
| B06 | Visitas · Saída → Não devolvido | Bruno | "Saída registrada; cartão marcado como EXTRAVIADO."; linha ENCERRADA, V-002 "NÃO DEVOLVIDO"; sem botão Excluir (M07, M10) | PASSOU |
| B07 | Visitas · Entrada → Confirmar | Fernanda após saída do Bruno | PRESENTE com V-001; modal lista só cartões DISPONÍVEIS (M05/M06) | PASSOU |
| B08 | Visitas · Cancelar → Cancelar visita | Diego | CANCELADA; só resta Excluir | PASSOU |
| B09 | Visitas · Excluir → Excluir | Diego (cancelada) | "Visita excluída." | PASSOU |
| B10 | Visitas · Editar → Salvar | Caio 10:15 → 10:30 | form preenchido com detalhe; "Visita atualizada."; lista mostra 10:30 | PASSOU |
| B11 | Visitas · filtros | nome "carla" | só "Caio Fictício" (busca no civil, exibe o social) | PASSOU |
| B12 | Visitas · filtros | "carla" + PRESENTE | estado vazio "Nenhuma visita encontrada." | PASSOU |
| B13 | Visitas · Limpar filtros | — | 5 linhas; campo nome vazio | PASSOU |
| B14 | Visitas · Saída → Voltar | Fernanda | modal fecha sem alterar | PASSOU |
| B15 | Visitas · Saída → Sim, devolvido | Fernanda | "Saída registrada; cartão devolvido."; ENCERRADA | PASSOU |
| B16 | Tipos · Cadastrar (M01) | "Visita institucional", doc obrigatório, Diretoria | "Tipo de visita cadastrado."; linha ATIVO | PASSOU |
| B17 | Tipos · Desativar / Ativar | Visita institucional | INATIVO → ATIVO, mensagens corretas | PASSOU |
| B18 | Tipos · Excluir (com visitas) | Atendimento ao público | 409 "tipo de visita possui visitas vinculadas; desative-o em vez de excluir" | PASSOU |
| B19 | Tipos · Editar → Salvar | renomear para "Visita institucional externa" | nome atualizado | PASSOU |
| B20 | Tipos · Excluir (sem visitas) | Visita institucional externa | "Tipo ... excluído." | PASSOU |
| B21 | Cartões · Marcar como recuperado | V-002 | "Cartão V-002 marcado como recuperado." | PASSOU |
| B22 | Cartões · Inativar / Reativar | V-010 | INATIVO (botão vira Reativar) → DISPONÍVEL | PASSOU |
| B23 | Cartões · Excluir (com histórico) | V-009 | 409 "cartão com histórico de visitas não pode ser excluído; inative-o" | PASSOU |
| B24 | Cartões · Cadastrar | V-011 / RFID-TESTE-0011 | "Cartão cadastrado." | PASSOU |
| B25 | Cartões · Editar → Salvar | V-011 cor azul | "Cartão atualizado." | PASSOU |
| B26 | Cartões · filtro status | EXTRAVIADO | só V-009 | PASSOU |
| B27 | Cartões · Excluir (sem histórico) | V-011 | "Cartão V-011 excluído." | PASSOU |
| B28 | Cartões · EM USO | V-001 em uso | nenhuma ação, texto "Em uso por uma visita" | PASSOU |
| B29 | 360 px (M12) | iframe de 360 px (a janela maximizada não redimensiona) | `innerWidth=358 scrollWidth=343`, `thead display=none`, `tr display=block` (cartões) | PASSOU |

Falhas visuais também corrigidas na S2: a célula de ações com `display:flex` desalinhava as bordas da tabela (botões agora num `div` interno); filtro único de Cartões ocupava a largura toda (`max-width`).
Observação: as capturas de tela pelo MCP falharam várias vezes com `CDP sendCommand "Page.captureScreenshot" timed out`; as interações e leituras do DOM funcionaram. As imagens de evidência são geradas na S5 por script reproduzível.

## S3 — Painel

### S3 — Testes automatizados — 2026-10-23
Comando: `pytest -q tests/test_dashboard.py` e suíte completa
Saída: `11 passed in 1.83s` · `============================= 65 passed in 14.58s =============================`
Resultado: PASSOU (T30–T39 + recuperação de cartão + data de referência injetável)

### S3 — Painel pela tela (MCP Claude in Chrome) — 2026-10-23
Banco recarregado com `seed.py`; API reiniciada com o router novo.

| # | Ação na tela | Indicadores lidos no DOM (`data-indicador`) | Status |
|---|---|---|---|
| P01 | Abrir Painel (seed) | 4 visitas do dia · 1 presente · 1 encerrada · 1 veículo · 1 cartão pendente · 0 negados (= seção 8 do handoff); lista: Bruno Teste, Jurídico, V-002, Recepção | PASSOU |
| P02 | Visitas › Entrada Caio + Saída Bruno sem devolução › Painel | 4 · 1 (Caio) · 2 · 0 · 2 · 0 | PASSOU (M05, M10) |
| P03 | Registrar visita de hoje (Gabriel) › Painel | visitas do dia 4 → 5 | PASSOU |
| P04 | Cancelar Gabriel + Excluir Diego › Painel | visitas do dia 5 → 3 | PASSOU |
| P05 | API parada › botão Atualizar | "Erro 500 ao falar com a API" | FALHOU → F4 |
| P05b | idem após correção | "API indisponível. Verifique se o backend está em execução." | PASSOU |
| P06 | API reiniciada › Atualizar (M04) | sem alerta; 3 · 1 · 2 · 0 · 2 · 0; presente Caio Fictício | PASSOU |
| P07 | Imprimir lista de evacuação (M11) | NÃO TESTADO pelo MCP (`window.print` abre diálogo que bloqueia a automação); verificado na S5 por `Page.printToPDF` | NÃO TESTADO |

## S4 — Catraca e rastreamento (extensão)

### S4 — Testes automatizados — 2026-10-23
Comando: `pytest -q tests/test_catraca_rastreamento.py` e suíte completa
Saída: `14 passed in 2.65s` · `============================= 79 passed in 13.83s =============================`
Resultado: PASSOU (T40–T49 + seed de pontos, 404/422 da leitura, trajeto 404, negados de ontem fora da contagem — ADR-016)

### S4 — Simulador pela tela (MCP Claude in Chrome) — 2026-10-23
Estado: Caio Fictício PRESENTE, destino Tecnologia, cartão V-001 (`RFID-TESTE-0001`). Pontos criados pelo `lifespan` ao recarregar a API.

| # | Ação | Resultado observado | Status |
|---|---|---|---|
| C01 | Atalho "V-001" + Leitor Diretoria + Ler cartão (M08) | painel vermelho **NEGADO** · "Motivo: área não autorizada: destino da visita é Tecnologia"; trajeto aberto sozinho | PASSOU |
| C02 | Leitor Tecnologia + Ler cartão (M09) | painel verde **LIBERADO**; trajeto com 2 passagens em ordem | PASSOU |
| C03 | Painel após C01–C02 | último local "Leitor Tecnologia"; `acessos_negados_hoje=1` | PASSOU |
| C04 | Código digitado `RFID-DESCONHECIDO-9`, sentido Saída, Portaria | NEGADO · "código de leitura desconhecido" | PASSOU |
| C05 | Selecionar visita no trajeto + Atualizar listas | trajeto NEGADO Diretoria 10:54 → LIBERADO Tecnologia 10:55; sem alerta | PASSOU |

## S4b — Docker (ADR-015)

### S4b — D01 build — 2026-10-23
Comando: `docker compose --profile test build`
Saída: `Image gestao-visitantes-web:local Built` · `Image gestao-visitantes-api:local Built` · `Image gestao-visitantes-tests:local Built`
Resultado: PASSOU (python:3.12-slim · node:22-alpine → nginx:1.27-alpine)

### S4b — D02 testes no contêiner — 2026-10-23
Comando: `docker compose --profile test run --rm tests`
Saída: `79 passed, 1 warning in 17.90s` (aviso de depreciação do `httpx` no TestClient)
Resultado: PASSOU

### S4b — D03 stack no ar — 2026-10-23
Comando: `docker compose up -d` + requisições a `http://localhost:8080`
Saída:
```
Container gestao-visitantes-api-1 Healthy
health via web:8080 => {"status":"ok"}
api   Up 6 seconds (healthy)   8000/tcp
web   Up ...                   0.0.0.0:8080->80/tcp
index: 200 · docs: 200 · pontos: 6
```
Resultado: PASSOU (a API não é publicada; só o nginx, que repassa `/api`, `/docs` e `/openapi.json`)

### S4b — D04 persistência por volume — 2026-10-23
Comando: `docker compose run --rm api python seed.py` → `GET /api/dashboard` → `docker compose restart api` → `GET /api/dashboard`
Saída:
```
Seed carregado: 5 tipos, 10 cartões, 5 visitas (dados fictícios).
antes:  {"data_referencia":"2026-10-23","visitas_do_dia":4,"presentes":1,"encerradas_do_dia":1,"veiculos_no_patio":1,"cartoes_pendentes":1,"acessos_negados_hoje":0}
depois: {"data_referencia":"2026-10-23","visitas_do_dia":4,"presentes":1,"encerradas_do_dia":1,"veiculos_no_patio":1,"cartoes_pendentes":1,"acessos_negados_hoje":0}
gestao-visitantes_dados
```
Resultado: PASSOU (contêiner em UTC, "hoje" continua America/Cuiaba via `tzdata`)

### S4b — botão no Docker (MCP) — 2026-10-23
Ação: `http://localhost:8080` › Catraca › atalho V-002 › Leitor Jurídico › Ler cartão
Resultado observado: **LIBERADO**; trajeto "Leitor Jurídico · entrada 23/10/2026 10:58"
Resultado: PASSOU

## S5 — Homologação e GitHub

### S5 — Roteiro E2E com capturas (`scripts/capturas.mjs`, ADR-019) — 2026-10-23
Comando: `docker compose down -v; docker compose up -d --wait; docker compose run --rm api python seed.py; node scripts/capturas.mjs`
Primeira execução: 9 passaram, 0 falharam. Ao inspecionar `08-celular-360.png`, o selo "NÃO DEVOLVIDO" e a linha "Veículo TST1A01" apareciam na coluna dos rótulos (falha **F5**, não detectada pela verificação de rolagem). O E09 ganhou a checagem `invadeRotulo`.
Execução com o CSS antigo (prova de que o teste detecta a falha):
```
FALHOU  E09  360 px sem rolagem horizontal; tabela vira cartões; nada na coluna do rótulo  → {"largura":360,"rolagem":360,"cabecalho":"none","invadeRotulo":3}
8 passaram, 1 falharam
```
Execução após a correção:
```
PASSOU  E01  Painel com seed: 4 do dia, 1 presente, 1 encerrada
PASSOU  E02  Placa inválida mostra o 422 da API na tela  → Placa: placa inválida; use o formato AAA9999 ou AAA9A99
PASSOU  E03  Visita válida registrada como AGENDADA
PASSOU  E04  Entrada com cartão já em uso → 409 visível  → cartão V-001 não está disponível (status: EM_USO)
PASSOU  E05  Leitor de outro setor → NEGADO com motivo  → ... Motivo: área não autorizada: destino da visita é Jurídico
PASSOU  E06  Leitor do setor de destino → LIBERADO; trajeto com 2 passagens
PASSOU  E07  Painel: 5 do dia, 2 presentes, 1 negado; último local do Bruno = Leitor Jurídico
PASSOU  E08  Impressão mostra só a lista de evacuação  → {"topo":"none","indicadores":"none","cabecalho":"block","linhas":2}
PASSOU  E09  360 px sem rolagem horizontal; tabela vira cartões; nada na coluna do rótulo  → {"largura":360,"rolagem":360,"cabecalho":"none","invadeRotulo":0}
9 passaram, 0 falharam
```
Também houve uma falha **do próprio script** (não do app): `TypeError: Cannot read properties of undefined (reading 'value')` ao escolher o tipo antes de a lista carregar; o script passou a esperar as opções.
Capturas: `docs/img/01-painel.png` … `08-celular-360.png` e `docs/img/lista-evacuacao.pdf`.

### S5 — Suíte final, build e segurança do repositório — 2026-10-23
Comando: `pytest`, `npm run build`, `git ls-files | grep -E '\.db$|\.env|\.sqlite'`, `git grep` por chaves/senhas/tokens (`ghp_`, `github_pat_`, `sk-ant-`, `AKIA`) e CPF formatado
Saída:
```
============================= 79 passed in 14.29s =============================
✓ built in 845ms
--- .db/.env versionados (vazio = ok):
--- segredos:
--- padroes de token:
--- CPF formatado:
```
Resultado: PASSOU (nenhuma ocorrência)

### S5 — GitHub
Ver "Publicação" abaixo.

## Falhas identificadas e corrigidas
> Exigido na ficha de entrega: pelo menos uma falha real.

| # | Sprint | Falha | Causa | Correção | Teste que comprova |
|---|---|---|---|---|---|
| F1 | S1 | `ImportError: DLL load failed while importing _sqlite3` ao rodar pytest | `python` do PATH é o do QGIS, sem DLL do SQLite | venv recriado com Python gerenciado pelo `uv` | suíte 54 passed após a troca |
| F2 | S2 | Erro 409 da Entrada não aparecia para o usuário (alerta em `top=-102px`) | aviso fica no topo da página e a ação acontece no fim da tabela | `Aviso` faz `scrollIntoView` ao surgir | B05b (MCP) |
| F3 | S2 | Bordas da tabela desalinhadas na coluna Ações | `td` com `display:flex` deixa de ser célula | botões num `div.acoes` dentro do `td` | inspeção visual B05b |
| F4 | S3 | Com a API parada, tela mostrava "Erro 500 ao falar com a API" | proxy do Vite responde 500 sem JSON (o `fetch` não falha) | 5xx sem corpo JSON → "API indisponível…" | P05b (MCP) |
| F5 | S5 | Em 360 px, selos e sublinhas caíam na coluna do rótulo | `td` em grid: cada filho virava item próprio do grid | rótulo `position:absolute` + `padding-left` na célula | E09 (`invadeRotulo` 3 → 0) |

## Resumo final dos testes
| Suíte | Passou | Falhou | Corrigido | Não testado |
|---|---|---|---|---|
| Automatizados (pytest, local e no Docker) | 79 | 0 | F1 (ambiente) | — |
| Botões via MCP (B01–B29, P01–P07, C01–C05) | 40 | 0 (após correção) | F2, F3, F4 | P07 (impressão: coberta por E08) |
| E2E com capturas (E01–E09) | 9 | 0 (após correção) | F5 | — |
| Docker (D01–D04) | 4 | 0 | — | — |
| Roteiro manual (M01–M12) | 12 | 0 | — | — |
