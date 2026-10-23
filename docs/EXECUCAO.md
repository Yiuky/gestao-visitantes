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
_(pendente)_

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
| | | | | | |

## Resumo final dos testes
| Suíte | Passou | Falhou | Corrigido | Não testado |
|---|---|---|---|---|
| Automatizados (pytest) | | | | |
| Roteiro manual (M01–M12) | | | | |
