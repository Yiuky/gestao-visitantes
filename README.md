# Gestão de visitantes — MVP

> Desafio 06 · Formação Claude Code · SEMA/MT · Laboratório de Engenharia de Software Agêntica
> **Todos os dados deste projeto são fictícios.**

Sistema web local para a recepção de um órgão público fictício. Ele cobre o registro de visitas por tipo, a entrada e a saída com cartão de acesso, uma catraca simulada, o rastreamento por pontos de passagem e um painel de indicadores.

> ⚠️ Este README é um esqueleto. As seções marcadas com `TODO` são preenchidas na Sprint 5 com resultados **reais**.

## Funcionalidades
- Tipos de visita configuráveis (documento obrigatório, veículo permitido, setores permitidos)
- Registro, pesquisa, edição, cancelamento e exclusão de visitas (exclusão só antes da entrada)
- Entrada com cartão de acesso e saída com controle de devolução
- Cadastro de cartões de acesso (disponível, em uso, extraviado, inativo)
- Catraca simulada com liberação ou negação e registro de toda tentativa
- Lista "quem está no prédio agora", com último local (evacuação)
- Painel: visitas do dia, presentes, encerradas do dia, veículos no pátio, cartões pendentes, acessos negados

## Instalação e execução (Windows / PowerShell)
```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py                 # opcional: carrega dados fictícios
uvicorn app.main:app --reload  # API em http://127.0.0.1:8000 (docs em /docs)

# frontend (outro terminal)
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## Testes
```powershell
pytest -q
```
TODO: tabela com o que passou, falhou e foi corrigido (copiar de `docs/EXECUCAO.md`).

## Exemplos de uso
TODO: passo a passo curto (registrar → entrada com cartão → passagem na catraca → saída) com capturas em `docs/img/`.

## Privacidade e legislação
Resumo de `docs/LGPD.md`:
- O sistema coleta o mínimo e mascara o documento.
- Usa nome social, não registra o motivo da prioridade e não coleta foto nem biometria.
- Não retém documentos (Lei 5.553/1968).
- Mantém os registros de presença e as passagens sem possibilidade de exclusão, como prova em incidentes.

> Os campos, a base legal e os prazos de retenção são **propostos para validação** do encarregado de dados e da assessoria jurídica do órgão. Não constituem parecer jurídico.

## Limitações
- Sem login nem perfis de acesso (ADR-001); sem trilha de auditoria de edições.
- Catraca simulada; não há integração com equipamento físico.
- Sem anonimização automática ao fim do prazo de retenção.
- SQLite local; sem HTTPS, criptografia de banco ou rotina de backup.
- Biometria prevista no backlog como épico **bloqueado** por pré-requisitos legais (ADR-011).

## Documentação
`docs/PLANO.md` · `docs/REQUISITOS.md` · `docs/ARQUITETURA.md` · `docs/BACKLOG.md` · `docs/TESTES.md` · `docs/LGPD.md` · `docs/EXECUCAO.md`
