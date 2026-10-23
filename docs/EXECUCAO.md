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
backendpp\database.py:29: in <module> engine = criar_engine(DATABASE_URL)
C:\Program Files\QGIS 3.44.10pps\Python312\Lib\sqlite3\dbapi2.py:27: from _sqlite3 import *
E   ImportError: DLL load failed while importing _sqlite3: Não foi possível encontrar o módulo especificado.
```
Resultado: FALHOU → corrigido (falha F1)
Correção: o `python` do PATH é o Python embutido do QGIS, sem a DLL do SQLite. O venv foi recriado com Python gerenciado pelo uv:
`uv venv --native-tls --managed-python --python 3.12 .venv` + `uv pip install --native-tls -r requirements.txt`
→ `3.12.14 ... sqlite 3.53.1`

### S1 — Suíte automatizada — 2026-10-23
Comando: `.ackend\.venv\Scripts\python.exe -m pytest -p no:warnings -o addopts=""`
Saída: `============================= 54 passed in 5.60s ==============================`
Resultado: PASSOU (T01–T29 + casos extras de 404, filtros, normalização de placa, ADR-013)
Versões: fastapi 0.161.1 · starlette 1.9.0 · sqlalchemy 2.1.6 · pydantic 2.14.1 · uvicorn 0.54.0 · pytest 9.1.1 · httpx 0.28.1 · tzdata 2026.5 (fixadas em `backend/requirements.txt`)

### S1 — Persistência após reinício (API real, uvicorn :8000) — 2026-10-23
Comando: subir uvicorn → `POST /api/tipos-visita` + `POST /api/visitas` → `Stop-Process` → subir de novo → `GET /api/visitas`
Saída:
```
criada antes do reinicio: id=1 status=AGENDADA
apos reinicio: 1 visita(s): Pessoa Persistida / AGENDADA
arquivo: ...\gestao-visitantesackend\dataisitantes.db
```
Resultado: PASSOU (confirma também o caminho absoluto do banco, correção #1 da S0)

### S1 — Seed fictício — 2026-10-23
Comando: `python seed.py` (duas vezes)
Saída: `Seed carregado: 5 tipos, 10 cartões, 5 visitas (dados fictícios).` · `Banco já possui dados; seed ignorado.`
Resultado: PASSOU (idempotente)

## S2 — Frontend núcleo
_(pendente)_

## S3 — Painel
_(pendente)_

## S4 — Catraca e rastreamento (extensão)
_(pendente)_

## S5 — Homologação e GitHub
_(pendente)_

## Falhas identificadas e corrigidas
> Exigido na ficha de entrega: pelo menos uma falha real.

| # | Sprint | Falha | Causa | Correção | Teste que comprova |
|---|---|---|---|---|---|
| F1 | S1 | `ImportError: DLL load failed while importing _sqlite3` ao rodar pytest | `python` do PATH é o do QGIS, sem DLL do SQLite | venv recriado com Python gerenciado pelo `uv` | suíte 54 passed após a troca |

## Resumo final dos testes
| Suíte | Passou | Falhou | Corrigido | Não testado |
|---|---|---|---|---|
| Automatizados (pytest) | | | | |
| Roteiro manual (M01–M12) | | | | |
