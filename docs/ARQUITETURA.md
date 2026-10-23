# ARQUITETURA — Gestão de visitantes

> Extraído de `HANDOFF_CLAUDE_CODE.md` (seções 7 e 10). Novas decisões entram como ADR no fim deste arquivo.

## Visão geral
```
[React + Vite :5173] --fetch /api/* (proxy)--> [FastAPI :8000] --SQLAlchemy--> [SQLite backend/data/visitantes.db]
                                                     ^
                    [Simulador de catraca na UI] ----┘  (POST /api/catraca/passagens)
```

| Camada | Escolha |
|---|---|
| API | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Persistência | SQLAlchemy 2.x + SQLite (`DATABASE_URL`; padrão = caminho **absoluto** de `backend/data/visitantes.db`, calculado em `config.py`) |
| Interface | React 18 + Vite, `fetch`, CSS próprio |
| Testes | pytest + TestClient, banco temporário, "hoje" injetável |

## Pastas
```
backend/app/
  main.py  database.py  models.py  schemas.py  config.py
  services/regras.py         # transições, validações por tipo, decisão da catraca
  routers/ tipos.py  cartoes.py  visitas.py  catraca.py  dashboard.py
backend/seed.py              # dados fictícios (nunca nos testes)
backend/Dockerfile           # imagem da API (ADR-015)
frontend/Dockerfile          # build Vite + nginx com proxy /api (ADR-015)
docker-compose.yml           # api + web; perfil "test" roda pytest
tests/                       # conftest + um arquivo por área
frontend/src/
  api.js  App.jsx  styles.css
  pages/ Painel.jsx  Visitas.jsx  Tipos.jsx  Cartoes.jsx  Catraca.jsx
```

## Modelo de dados

**tipos_visita** — id · nome (único) · descricao · ativo · exige_documento · permite_veiculo · setores_permitidos (CSV, vazio = todos) · prazo_retencao_dias (180, a validar).

**cartoes_acesso** — id · codigo (único, ex. `V-001`) · codigo_leitura (único, ex. `RFID-TESTE-0001`) · cor · status (DISPONIVEL, EM_USO, EXTRAVIADO, INATIVO).

**visitas** — id · tipo_visita_id (FK) · nome_civil · nome_social · documento · setor_destino · data_visita · horario_previsto · atendimento_prioritario · placa · descricao_veiculo · vaga_reservada · observacao (≤100) · status · cartao_id (FK) · cartao_devolvido · entrada_em · saida_em · criado_em · atualizado_em.

**pontos_acesso** (seed) — id · nome · setor (NULL = área comum) · ativo · metodos_aceitos (`CARTAO`; extensão para biometria futura).

**passagens** (somente inserção) — id · ponto_id · codigo_lido · cartao_id · visita_id · credencial_tipo (`CARTAO`) · sentido (ENTRADA/SAIDA) · resultado (LIBERADO/NEGADO) · motivo · ocorrido_em.

**SETORES (config):** Atendimento, Protocolo, Jurídico, Tecnologia, Diretoria.

**Relacionamentos:** TipoVisita 1—N Visita · CartaoAcesso 1—N Visita (no máximo 1 PRESENTE) · Visita 1—N Passagem · PontoAcesso 1—N Passagem.

## Endpoints
| Método | Rota | Sucesso | Erros |
|---|---|---|---|
| GET | `/api/health` · `/api/setores` | 200 | — |
| GET/POST | `/api/tipos-visita` | 200/201 | 409 (nome duplicado), 422 |
| GET/PUT/DELETE | `/api/tipos-visita/{id}` | 200/200/204 | 404, 409, 422 |
| GET/POST | `/api/cartoes` (`?status=`) | 200/201 | 409, 422 |
| GET/PUT/DELETE | `/api/cartoes/{id}` | 200/200/204 | 404, 409 |
| GET | `/api/visitas?q=&setor=&tipo_id=&data=&status=` | 200 `[VisitaResumo]` | 422 |
| POST | `/api/visitas` | 201 | 422 |
| GET/PUT/DELETE | `/api/visitas/{id}` | 200/200/204 | 404, 409, 422 |
| POST | `/api/visitas/{id}/entrada` `{cartao_id}` | 200 | 404, 409 |
| POST | `/api/visitas/{id}/saida` `{cartao_devolvido}` | 200 | 404, 409, 422 |
| POST | `/api/visitas/{id}/cancelar` | 200 | 404, 409 |
| GET | `/api/visitas/{id}/passagens` | 200 | 404 |
| GET | `/api/pontos-acesso` | 200 | — |
| POST | `/api/catraca/passagens` `{codigo_lido, ponto_id, sentido}` | 201 `{resultado, motivo, passagem}` | 404, 422 |
| GET | `/api/presentes` | 200 | — |
| GET | `/api/dashboard` | 200 | — |

- `VisitaResumo` traz `nome_exibido` e `documento_mascarado`, nunca o documento completo.
- Erros: `{"detail": "mensagem em português"}`.

## Indicadores (COUNT no banco)
```sql
SELECT COUNT(*) FROM visitas WHERE data_visita = :hoje AND status <> 'CANCELADA';      -- visitas do dia
SELECT COUNT(*) FROM visitas WHERE status = 'PRESENTE';                                -- presentes
SELECT COUNT(*) FROM visitas WHERE status = 'ENCERRADA' AND data_visita = :hoje;       -- encerradas do dia
SELECT COUNT(*) FROM visitas WHERE status = 'PRESENTE' AND placa IS NOT NULL;          -- veículos no pátio
SELECT COUNT(*) FROM cartoes_acesso WHERE status = 'EXTRAVIADO';                       -- cartões pendentes
SELECT COUNT(*) FROM passagens WHERE resultado = 'NEGADO' AND date(ocorrido_em) = :hoje; -- negados hoje
```

## Telas
1. **Painel** — 6 indicadores e "Quem está no prédio agora", com impressão da lista de evacuação.
2. **Visitas** — formulário adaptado ao tipo, filtros, tabela e ações conforme o status.
3. **Tipos de visita** — CRUD com ativar/desativar.
4. **Cartões** — CRUD, filtro por status, "marcar como recuperado".
5. **Catraca** — simulador de leitura e trajeto da visita.
6. **Rodapé** — aviso de privacidade.

## ADRs
| ADR | Decisão | Status |
|---|---|---|
| 001 | Sem login no MVP; perfis são requisito de produção | Aceito |
| 002 | Setores como lista fixa em `config.py` | Aceito |
| 003 | Status armazenado; transições só por `/entrada`, `/saida`, `/cancelar` | Aceito |
| 004 | "Hoje" em America/Cuiaba, injetável nos testes; `tzdata` no Windows | Aceito |
| 005 | SQLite via `DATABASE_URL`; PostgreSQL = trocar URL + `psycopg`; `create_all` sem Alembic | Aceito |
| 006 | Tipos de visita configuráveis carregam as regras | Aceito |
| 007 | Minimização LGPD: nome social, documento mascarado, prioridade sem motivo, vaga reservada genérica, observação ≤100, sem foto ou assunto | Aceito |
| 008 | Registros de presença não são excluídos; passagens imutáveis | Aceito |
| 009 | Cartão sem dados pessoais e sem troca por documento (Lei 5.553/1968) | Aceito |
| 010 | Rastreamento por pontos de passagem, não contínuo | Aceito |
| 011 | Biometria condicionada a pré-requisitos legais; campos de extensão já no modelo; nada coletado | Aceito (épico B bloqueado) |
| 012 | Catraca simulada por API e tela; contrato pronto para equipamento real | Aceito |

<!-- Novos ADRs abaixo: número, contexto, decisão, consequências -->

### ADR-013 — Regras do tipo na edição (S0)
- **Contexto:** `CLAUDE.md` dizia que "tipo ativo" vale na criação e na edição; RN02 dizia só na criação. Aplicar na edição impediria editar visitas AGENDADA de um tipo desativado depois.
- **Decisão:** "tipo ativo" é verificado na criação e quando o PUT **troca** `tipo_visita_id`. Documento, setores, veículo, placa e vaga reservada são verificados em toda criação e edição. Se a placa mudar numa visita PRESENTE, RN15 (placa já no pátio) é reverificada.
- **Consequências:** desativar um tipo não trava visitas já agendadas; nenhum caminho de edição fura RN15.

### ADR-014 — Status do cartão pelo PUT (S0)
- **Contexto:** a tela precisa de "marcar como recuperado" (EXTRAVIADO → DISPONIVEL) e de inativar, mas o PUT não pode colocar um cartão em `EM_USO` à mão.
- **Decisão:** o PUT de cartão aceita `status` apenas `DISPONIVEL` ou `INATIVO`. `EM_USO` só pela entrada; `EXTRAVIADO` só pela saída sem devolução. Cartão `EM_USO` não é editado (409). Código duplicado → 409; nome de tipo duplicado → 409.
- **Consequências:** o ciclo do cartão continua amarrado ao da visita.

### ADR-015 — Docker para execução e testes (S0, mudança de escopo pedida pelo usuário)
- **Contexto:** o usuário pediu ambiente e testes reproduzíveis em Docker, visando publicação futura.
- **Decisão:** `backend/Dockerfile` (python:3.12-slim, uvicorn), `frontend/Dockerfile` (build Node + nginx servindo `dist` e repassando `/api` à API), `docker-compose.yml` com volume nomeado para o SQLite e serviço `tests` (perfil `test`) que roda `pytest`. A execução local sem Docker continua suportada.
- **Consequências:** nenhum segredo nas imagens; `DATABASE_URL` por variável de ambiente; publicação online continua exigindo os itens do Épico A (login, HTTPS, backup).

### ADR-016 — Horário local e contagem por intervalo (S0)
- **Contexto:** `date(ocorrido_em) = :hoje` erra entre 20h e 24h se o horário for gravado em UTC (Cuiabá = UTC−4).
- **Decisão:** datas/horas são gravadas como horário local America/Cuiaba (naive), vindas do relógio injetável (`get_agora`). O indicador de negados usa intervalo `[hoje 00:00, amanhã 00:00)` com COUNT no banco.
- **Consequências:** consultas por dia corretas; em produção multi-fuso, migrar para UTC + conversão.

### ADR-017 — Indicador de negados antes da S4 (S0)
- **Decisão:** na S3 `acessos_negados_hoje` retorna 0 (tabela `passagens` ainda não existe); a S4 troca pelo COUNT real (T49).
- **Situação:** encerrado na S4 (COUNT por intervalo, ADR-016).

### ADR-018 — Repositório público no GitHub (S5, decisão do usuário)
- **Contexto:** o handoff e o `CLAUDE.md` previam repositório **privado**; na S5 o usuário pediu explicitamente publicação **pública**.
- **Decisão:** publicar como público. Antes do push: dados 100% fictícios, nenhum `.db`/`.env` versionado e varredura de segredos sem ocorrências (registrado em `docs/EXECUCAO.md`). O token vem de variável de ambiente e não é gravado no repositório nem no remoto.
- **Consequências:** o código, a documentação e o histórico (inclusive nome e e-mail de autor dos commits) ficam públicos. O sistema continua sem login (ADR-001), portanto **não** deve ser publicado online com dados reais sem os itens do Épico A.

### ADR-019 — Roteiro E2E com capturas (S5)
- **Contexto:** as capturas pelo MCP Claude in Chrome falhavam por timeout do CDP, mas as evidências precisam ser reproduzíveis.
- **Decisão:** `scripts/capturas.mjs` (Node 22+, sem dependências) dirige o Chrome headless via CDP, clica nos botões reais, confere os resultados (E01–E09) e grava `docs/img/`.
- **Consequências:** qualquer pessoa reproduz as evidências com a stack Docker e o seed.


## Validação por camada
| Camada | Como validar |
|---|---|
| Banco | Criar registros, reiniciar a API, confirmar persistência; `.db` fora do Git |
| API | `pytest -q` e Swagger em `/docs` |
| Interface | `npm run build` e roteiro CA1–CA3 em desktop e 360 px |
| Integração | Ação na tela → conferir em `/api/...` e nos indicadores |
