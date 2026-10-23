# CLAUDE.md — Gestão de visitantes (Desafio 06 · SEMA/MT)

Contexto permanente para o Claude Code. Leia este arquivo e `HANDOFF_CLAUDE_CODE.md` antes de qualquer tarefa.

## O que é
MVP web local para a recepção de um órgão público **fictício**. O sistema:
- registra visitas conforme **tipos de visita** configuráveis;
- entrega **cartões de acesso** usados numa **catraca simulada**;
- rastreia por **pontos de passagem** para montar a lista de evacuação;
- mostra um **painel** com indicadores do dia.

## Stack
- Backend: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite (`backend/data/visitantes.db`)
- Frontend: React 18 + Vite (proxy `/api` → `http://127.0.0.1:8000`), CSS próprio responsivo
- Testes: pytest + `fastapi.testclient`, banco temporário, "hoje" injetável
- Fuso: America/Cuiaba (`zoneinfo` + pacote `tzdata` no Windows)

## Comandos (Windows / PowerShell)
```powershell
# backend
cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload            # http://127.0.0.1:8000/docs
python seed.py                           # dados fictícios (opcional)

# testes (na raiz, com o venv ativo)
pytest -q

# frontend
cd frontend; npm install; npm run dev    # http://localhost:5173
npm run build

# docker (ADR-015)
docker compose build
docker compose --profile test run --rm tests
docker compose up -d                     # http://localhost:8080
```

## Fluxo de trabalho obrigatório
1. **Uma sprint por vez**, na ordem de `docs/BACKLOG.md`. Antes de editar, informe objetivo, arquivos afetados e testes.
2. Ciclo de cada sprint: PLANEJAR → IMPLEMENTAR → EXECUTAR → TESTAR → CORRIGIR → REVALIDAR → DOCUMENTAR → COMMIT.
3. Registre **comandos e saídas reais** em `docs/EXECUCAO.md`. Nunca afirme que um teste passou sem executá-lo; use **NÃO TESTADO** quando for o caso.
4. Não avance se o gate da sprint falhar.
5. Mudança de escopo só com novo ADR em `docs/ARQUITETURA.md`.
6. Commits pequenos e descritivos (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
7. Push para o GitHub **somente com autorização explícita** do usuário, via `gh`. O repositório é **público** por decisão do usuário (ADR-018): nunca versionar dado real, `.db`, `.env` ou token.

## Regras de negócio que não podem ser quebradas
- Ciclo da visita: `AGENDADA → PRESENTE → ENCERRADA` e `AGENDADA → CANCELADA`. Transições só pelos endpoints `/entrada`, `/saida` e `/cancelar`; o PUT nunca muda status.
- **Visitas PRESENTE ou ENCERRADA não podem ser excluídas** (409). Exclusão só em AGENDADA ou CANCELADA.
- **Passagens da catraca são somente inserção**: sem PUT ou DELETE.
- A entrada exige um cartão DISPONIVEL e `data_visita = hoje`. A saída exige `cartao_devolvido`; se não houver devolução, o cartão fica EXTRAVIADO.
- As regras do tipo de visita valem na criação e na edição: documento quando exigido, setores permitidos, veículo permitido; "tipo ativo" na criação e quando o tipo é trocado (ADR-013).
- Indicadores do painel são calculados com COUNT no banco, nunca contando em Python.
- Regras ficam em `backend/app/services/regras.py`; os routers só orquestram.

## Proibições (LGPD e segurança)
- **Somente dados fictícios.** Nada de CPF/RG reais, nomes reais ou dados institucionais.
- **Não coletar:** foto, **biometria**, cópia de documento, endereço, telefone, motivo da prioridade, assunto da visita em texto livre.
- O documento completo nunca aparece em listagens; use `documento_mascarado`.
- A vaga reservada é genérica (`vaga_reservada`); não distinguir PcD de idoso.
- O cartão não tem dados pessoais e nunca é trocado pelo documento (Lei 5.553/1968).
- O épico de biometria está **bloqueado**: não implementar nada dele.
- Nenhum segredo, `.env` ou `.db` no Git.

## Mapa de documentos
| Arquivo | Conteúdo |
|---|---|
| `HANDOFF_CLAUDE_CODE.md` | Fonte completa: requisitos, regras, modelo, endpoints, sprints e prompts |
| `docs/REQUISITOS.md` | RF, RNF, regras de negócio, critérios de aceite |
| `docs/ARQUITETURA.md` | Stack, pastas, modelo de dados, endpoints, ADRs |
| `docs/BACKLOG.md` | Sprints S0–S5 com status, e épicos futuros |
| `docs/TESTES.md` | Estratégia e casos de teste por sprint |
| `docs/LGPD.md` | Base legal, minimização, segurança e pendências com o encarregado |
| `docs/PLANO.md` | Plano resumido (evidência de planejamento) |
| `docs/EXECUCAO.md` | Log real de comandos, resultados e falhas corrigidas |
| `docs/EVIDENCIAS.md` | Mapa de evidências: critério → teste → resultado → arquivo |
| `CHANGELOG.md` | Mudanças por versão/sprint |
