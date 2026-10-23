# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/). Uma entrada por sprint.

## [Não publicado]

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
