# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Uma entrada por sprint.

## [0.1.0] — 2026-10-23

### S5 — Homologação, README e publicação
- Adicionado: `scripts/capturas.mjs`, roteiro E2E sem dependências (Chrome headless via CDP) com 9 verificações e capturas em `docs/img/` (ADR-019).
- Adicionado: README completo (instalação local e Docker, uso com capturas, resultados, LGPD, limitações, reflexão) e mapa `docs/EVIDENCIAS.md`.
- Adicionado: ADR-018 (repositório público por decisão do usuário).
- Corrigido (F5): em 360 px, selos e sublinhas caíam na coluna do rótulo do cartão.

### S4b — Docker — 2026-10-23
- Adicionado: `backend/Dockerfile` multi-stage (`api` com usuário não-root e healthcheck; `test` com pytest).
- Adicionado: `frontend/Dockerfile` (build Vite + nginx) e `frontend/nginx.conf` com proxy de `/api` e `/docs` e cabeçalhos de segurança.
- Adicionado: `docker-compose.yml` (api + web em :8080, volume `dados`, perfil `test`) e `.dockerignore`.

### S4 — Catraca simulada e rastreamento — 2026-10-23
- Adicionado: modelos `pontos_acesso` (seed fixo automático) e `passagens` (somente inserção; PUT/DELETE → 405).
- Adicionado: `POST /api/catraca/passagens` (RN21–RN23), `GET /api/pontos-acesso`, `GET /api/catraca/passagens[/{id}]`, `GET /api/visitas/{id}/passagens`.
- Alterado: `/api/presentes` com último local real (RN24); `acessos_negados_hoje` por COUNT em intervalo do dia (ADR-016), encerrando o provisório do ADR-017.
- Adicionado: aba Catraca (simulador com resultado em destaque e trajeto); 14 testes (T40–T49); suíte com 79 testes.

### S3 — Painel — 2026-10-23
- Adicionado: `GET /api/dashboard` (6 indicadores por COUNT; negados = 0 até a S4, ADR-017) e `GET /api/presentes`.
- Adicionado: página Painel com indicadores, "Quem está no prédio agora", botões Atualizar e Imprimir lista de evacuação (CSS de impressão).
- Adicionado: 11 testes (T30–T39); suíte com 65 testes.
- Corrigido (F4): API fora do ar aparecia como "Erro 500"; agora "API indisponível".

### S2 — Frontend núcleo — 2026-10-23
- Adicionado: projeto React 18 + Vite 5 em `frontend/` com proxy `/api`.
- Adicionado: abas Painel (provisório), Visitas, Tipos de visita e Cartões; formulário de visita adaptado ao tipo; filtros; ações conforme o status; modais próprios (sem `alert/confirm`).
- Adicionado: rodapé de privacidade; tabelas viram cartões abaixo de 640 px.
- Corrigido (F2): mensagem de erro de ação na tabela ficava fora da tela; agora rola até o aviso.
- Corrigido (F3): bordas da coluna Ações desalinhadas.

### S1 — API núcleo — 2026-10-23
- Adicionado: modelos `tipos_visita`, `cartoes_acesso`, `visitas`; relógio injetável (`app/relogio.py`).
- Adicionado: endpoints de tipos, cartões, visitas (CRUD, pesquisa, entrada, saída, cancelar), `/api/health`, `/api/setores`.
- Adicionado: regras RN01–RN20 em `services/regras.py`; `VisitaResumo` com `nome_exibido` e `documento_mascarado`.
- Adicionado: `backend/seed.py` (dados fictícios, idempotente) e 54 testes pytest.
- Adicionado: `.gitattributes` (LF no repositório).
- Alterado: `requirements.txt` com versões fixadas.
- Corrigido (F1): venv recriado com Python do uv; o Python do QGIS no PATH não carrega `_sqlite3`.

### S0 — Estrutura, ambiente e Git — 2026-10-23
- Adicionado: `CHANGELOG.md` e `docs/EVIDENCIAS.md` (mapa de evidências).
- Adicionado: ADR-013 (regras do tipo na edição), ADR-014 (status do cartão pelo PUT), ADR-015 (Docker), ADR-016 (horário local e contagem por intervalo), ADR-017 (negados antes da S4).
- Adicionado: sprint S4b (Docker) no backlog; casos T28, T29, T39, D01–D04 e testes de botões em `docs/TESTES.md`.
- Corrigido: caminho padrão do SQLite agora é absoluto (antes dependia da pasta de execução).
- Corrigido: T02 definido como 409; IDs RN05a/RN05b renomeados para RN04a/RN04b (colidiam com RN05).
- Corrigido: `CLAUDE.md` alinhado ao RN02/ADR-013 ("tipo ativo" na criação e na troca de tipo).
