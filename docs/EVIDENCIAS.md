# Mapa de evidências — Gestão de visitantes

> Liga cada critério do Desafio 06 (PDFs em `03_laboratorio_aluno/EXERCICIO`) ao teste que o comprova, ao resultado real e ao arquivo de evidência.
> Status: ✅ comprovado com saída real · ❌ falhou · ⬜ NÃO TESTADO. Saídas completas em [`EXECUCAO.md`](EXECUCAO.md).

## 1. Rubrica de avaliação (10 pontos)

| Critério (peso) | O que comprova | Evidência | Status |
|---|---|---|---|
| Concepção e plano do MVP (1,5) | problema, perfis, RF/RNF, regras, 3 critérios de aceite, sprints | `docs/PLANO.md`, `docs/REQUISITOS.md`, `HANDOFF_CLAUDE_CODE.md` | ✅ |
| Estrutura, documentação e clareza (1,5) | `CLAUDE.md`, README, arquitetura com ADR-001…019, backlog, changelog | `README.md`, `docs/ARQUITETURA.md`, `docs/BACKLOG.md`, `CHANGELOG.md` | ✅ |
| API, frontend e banco integrados (3,0) | ação na tela → API → SQLite → painel; persistência após reinício | B01–B29, P01–P06, C01–C05 (MCP); E01–E09 (E2E); M04, D04 | ✅ |
| CRUD e indicadores reais (2,0) | CRUD de visitas, tipos e cartões; 6 indicadores por `COUNT` que mudam a cada operação | `tests/test_*`, T30–T39, P02–P04, E07 | ✅ |
| Testes e correções demonstráveis (1,0) | 79 testes pytest; 5 falhas reais encontradas e corrigidas (F1–F5) | `docs/EXECUCAO.md` → "Falhas identificadas e corrigidas" | ✅ |
| GitHub e histórico de commits (1,0) | um commit por sprint com mensagem descritiva; push autorizado | https://github.com/Yiuky/gestao-visitantes (público, 8+ commits) | ✅ |
| Reflexão obrigatória (README) | decisão técnica + sugestão do Claude Code revisada | removida do repositório público a pedido do autor (ADR-021); a ser entregue à parte | ⬜ fora do repositório |

## 2. Requisitos mínimos compartilhados

| Requisito | Evidência | Status |
|---|---|---|
| Frontend responsivo + backend integrados e executáveis | `npm run build` ok; B29 e E09 (360 px, `invadeRotulo: 0`); D03 (stack em :8080) | ✅ |
| Banco persistente (SQLite) | S1 "Persistência após reinício"; M04/P06; D04 (volume Docker) | ✅ |
| ≥ 1 entidade com CRUD e 3 indicadores calculados dos dados | CRUD de visitas, tipos e cartões; `services/painel.py` com `COUNT` | ✅ |
| README com instalação, execução, funcionalidades e limitações | `README.md` | ✅ |

## 3. Critérios de aceite do MVP

| Critério | Testes automatizados | Na tela | Status |
|---|---|---|---|
| **CA1** visita válida persiste; regras do tipo dão 422 com mensagem | T04–T09, `test_criar_visita_valida_agendada`, `test_editar_aplica_regras_do_tipo` | B02, B03, B04, E02, E03; persistência M04/P06 | ✅ |
| **CA2** entrada exige cartão disponível e data de hoje; saída controla a devolução; presença não se exclui | T13–T24, T26, T27 | B05–B09, B15, E04; cartão extraviado → pendentes +1 (P02) | ✅ |
| **CA3** indicadores mudam a cada operação; pesquisa filtra; catraca nega área não autorizada e atualiza o último local | T30–T49, T11, T28 | P02–P04, B11–B13, C01–C03, E05–E07 | ✅ |

## 4. Checklist de homologação e entrega (roteiro do desafio)

| Item | Evidência | Status |
|---|---|---|
| Sistema inicia localmente; API e interface respondem | uvicorn + Vite (S2–S4); Docker D03 | ✅ |
| CRUD principal funciona com banco persistente | B04, B10, B09; M04 | ✅ |
| Três indicadores mudam conforme os registros | P02–P04, E07, T31–T39 | ✅ |
| Testes executados e resultado registrado (passou/falhou/não testado) | `docs/EXECUCAO.md` → "Resumo final dos testes" | ✅ |
| README e `docs/EXECUCAO.md` atualizados | ambos no commit da S5 | ✅ |
| Repositório publicado com aprovação e sem credenciais | https://github.com/Yiuky/gestao-visitantes; varredura de segredos sem ocorrências; autorização do usuário (ADR-018) | ✅ |
| Falha identificada e corrigida | F1–F5 | ✅ |

## 5. Pedidos adicionais do usuário

| Pedido | Evidência | Status |
|---|---|---|
| Testes pelo MCP, principalmente de botões | 40 interações registradas (B01–B29, P01–P07, C01–C05) em `docs/EXECUCAO.md` | ✅ |
| Ambiente e testes com Docker | ADR-015; `docker-compose.yml`; D01–D04; 79 testes no contêiner | ✅ |
| Backlog, changelog e log atualizados | `docs/BACKLOG.md`, `CHANGELOG.md`, `docs/EXECUCAO.md` (um registro por sprint) | ✅ |
| Mapa de evidências | este arquivo | ✅ |
| Execução por sprints | commits S0, S1, S2, S3, S4, S4b, S5 e S6 em `git log` | ✅ |
| Publicação online (Vercel/Render/Supabase) | https://gestao-visitantes.vercel.app; `/api/health` 200; E2E online 9/9; capturas em `docs/img/online/` (ADR-020) | ✅ |

## 6. Capturas (`docs/img/`, geradas por `scripts/capturas.mjs`)

| Arquivo | Mostra | Teste |
|---|---|---|
| `01-painel.png` | painel com seed (4 · 1 · 1 · 1 · 1 · 0) | E01 |
| `02-formulario-erro-422.png` | formulário com erro 422 da API | E02 |
| `03-entrada-409-cartao-em-uso.png` | entrada negada por cartão em uso (409) | E04 |
| `04-catraca-negado.png` | simulador negando acesso a outro setor | E05 |
| `05-catraca-liberado-trajeto.png` | acesso liberado e trajeto | E06 |
| `06-painel-presentes.png` | painel com presentes e último local | E07 |
| `07-impressao-lista-evacuacao.png` + `lista-evacuacao.pdf` | impressão só com a lista | E08 |
| `08-celular-360.png` | tela em 360 px | E09 |

## 7. Pendências conhecidas
- Diálogo real de impressão não automatizado (coberto por `printToPDF`, E08).
- Itens de produção (login, HTTPS, backup, anonimização) seguem no Épico A; biometria segue bloqueada (Épico B).
