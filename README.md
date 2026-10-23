# Gestão de visitantes — MVP

> Desafio 06 · Formação Claude Code · SEMA/MT · Laboratório de Engenharia de Software Agêntica
> **Todos os dados deste projeto são fictícios.** Órgão, pessoas, documentos (`DOC-…`), placas (`TST…`) e cartões (`RFID-TESTE-…`) são inventados.

**Repositório:** https://github.com/Yiuky/gestao-visitantes

Sistema web local para a recepção de um órgão público fictício. O sistema cobre:
- o registro de visitas por tipo configurável;
- a entrada e a saída com cartão de acesso;
- uma catraca simulada;
- o rastreamento por pontos de passagem, que alimenta a lista de evacuação;
- um painel com indicadores do dia calculados no banco.

![Painel](docs/img/06-painel-presentes.png)

## Funcionalidades
- **Tipos de visita configuráveis:** documento obrigatório, veículo permitido, setores permitidos, ativar e desativar.
- **Visitas:** registrar, pesquisar (por nome civil ou social, setor, tipo, data e status), editar, cancelar e excluir. A exclusão só é permitida antes da entrada; registros de presença nunca são apagados.
- **Entrada:** exige um cartão de acesso disponível e a data de hoje; recusa uma placa que já está no pátio.
- **Saída:** pergunta se o cartão foi devolvido. Se não foi, o cartão fica EXTRAVIADO e entra em "cartões pendentes".
- **Cartões:** CRUD, filtro por status, inativar e reativar, "marcar como recuperado". O cartão não tem dados pessoais e nunca é trocado pelo documento.
- **Catraca simulada:** toda leitura é gravada como LIBERADO ou NEGADO, com motivo; o trajeto da visita é exibido. As passagens não podem ser editadas nem excluídas.
- **Painel:** traz 6 indicadores calculados por `COUNT`:
  - visitas do dia, presentes e encerradas do dia (obrigatórios);
  - veículos no pátio, cartões pendentes e acessos negados hoje.
- **Quem está no prédio agora:** mostra o último local de cada presente e permite imprimir a lista de evacuação.
- **Aviso de privacidade** fixo no rodapé; layout responsivo, com as tabelas virando cartões abaixo de 640 px.

## Stack
| Camada | Tecnologia |
|---|---|
| API | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Uvicorn |
| Banco | SQLite em arquivo (`DATABASE_URL`; caminho para PostgreSQL documentado no ADR-005) |
| Interface | React 18 + Vite 5, CSS próprio |
| Testes | pytest + TestClient (79 testes) e roteiro E2E com Chrome headless (`scripts/capturas.mjs`) |
| Contêineres | Docker: API (python:3.12-slim) e web (nginx), com `docker compose` |

## Instalação e execução

### Opção 1: Docker (recomendado)
```powershell
docker compose build
docker compose up -d --wait                    # http://localhost:8080  (Swagger em /docs)
docker compose run --rm api python seed.py     # opcional: dados fictícios
docker compose --profile test run --rm tests   # testes dentro do contêiner
docker compose down                            # para (use -v para apagar o volume de dados)
```

### Opção 2: local (Windows / PowerShell)
Requisitos: Python 3.11+ e Node 18+.
```powershell
# backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python seed.py                    # opcional: carrega dados fictícios
uvicorn app.main:app --reload     # API em http://127.0.0.1:8000 (docs em /docs)

# frontend (outro terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173 (proxy /api → :8000)
```
> Se `pytest` acusar `DLL load failed while importing _sqlite3`, o `python` do PATH pode ser o de outro programa; neste laboratório era o do QGIS. Crie o venv com outro interpretador, por exemplo:
> `uv venv --managed-python --python 3.12 .venv` e `uv pip install -r requirements.txt`. Veja a falha F1 em `docs/EXECUCAO.md`.

### Opção 3: online (Supabase + Render + Vercel, ADR-020)
> ⚠️ Sem login (ADR-001): a URL pública serve **apenas como demonstração com dados fictícios**.

1. **Supabase:** crie um projeto e copie a string de *Connect › Session pooler* (IPv4). Acrescente `?sslmode=require` ao final, se ela ainda não tiver. As tabelas são criadas pela própria API, com RLS ligado.
2. **Render:** *New › Blueprint* com este repositório (lê `render.yaml`) e preencha `DATABASE_URL` com a string do Supabase.
   Para os dados de exemplo, rode na sua máquina: `$env:DATABASE_URL="<string do Supabase>"; cd backend; python seed.py`.
3. **Vercel:** *Add New › Project* com este repositório e *Root Directory* = `frontend` (lê `vercel.json`). Se o nome do serviço no Render for diferente de `gestao-visitantes-api`, ajuste as URLs em `frontend/vercel.json`.
4. **Conferência:** `https://<seu-app>.vercel.app/api/health` deve responder `{"status":"ok"}`. Depois rode `$env:BASE_URL="https://<seu-app>.vercel.app"; node scripts/capturas.mjs`. Atenção: o script cria registros fictícios.

Para testar contra PostgreSQL localmente: `TEST_DATABASE_URL=postgres://... pytest` (a suíte apaga e recria as tabelas desse banco; use um banco descartável).

## Exemplos de uso
1. **Registrar a visita:** aba *Visitas*. O formulário se adapta ao tipo: o documento é obrigatório quando o tipo exige, e o bloco de veículo só aparece quando o tipo permite. Erros da API aparecem em destaque.
   ![Erro 422](docs/img/02-formulario-erro-422.png)
2. **Entrada:** botão *Entrada*, escolha de um cartão disponível. Se outra pessoa usar o mesmo cartão antes, a API responde 409 e a tela avisa.
   ![Entrada 409](docs/img/03-entrada-409-cartao-em-uso.png)
3. **Catraca:** aba *Catraca*. Escolha o ponto e o cartão e clique em *Ler cartão*. Um leitor de outro setor dá NEGADO, com motivo.
   ![Catraca negada](docs/img/04-catraca-negado.png)
   O leitor do setor de destino dá LIBERADO e atualiza o último local.
   ![Catraca liberada](docs/img/05-catraca-liberado-trajeto.png)
4. **Saída:** botão *Saída*, informando se o cartão foi devolvido.
5. **Painel e evacuação:** os indicadores mudam a cada operação. *Imprimir lista de evacuação* imprime só a lista ([PDF de exemplo](docs/img/lista-evacuacao.pdf)).
   ![Impressão](docs/img/07-impressao-lista-evacuacao.png)
6. **Celular (360 px):** ![360 px](docs/img/08-celular-360.png)

## Testes e resultados
```powershell
pytest -q                                      # na raiz, com o venv do backend ativo
docker compose --profile test run --rm tests   # mesma suíte no contêiner
node scripts/capturas.mjs                      # E2E + capturas (stack Docker no ar com o seed)
```

| Suíte | Passou | Falhou | Corrigido | Não testado |
|---|---|---|---|---|
| pytest (API, regras, indicadores, catraca), local e Docker | 79 | 0 | — | — |
| Botões no navegador real via MCP Claude in Chrome (B01–B29, P01–P07, C01–C05) | 40 | 0 após correções | F2, F3, F4 | impressão via MCP (coberta pelo E08) |
| E2E com capturas (E01–E09) | 9 | 0 após correção | F5 | — |
| Docker (D01–D04: build, testes, stack, persistência por volume) | 4 | 0 | — | — |
| Roteiro manual M01–M12 | 12 | 0 | — | — |

**Falhas reais encontradas e corrigidas** (detalhes em `docs/EXECUCAO.md`):

| # | Falha | Correção |
|---|---|---|
| F1 | `pytest` com `DLL load failed while importing _sqlite3` (o Python do PATH era o do QGIS) | venv com Python gerenciado pelo `uv` |
| F2 | Erro 409 de uma ação na tabela aparecia fora da área visível | o aviso rola até ficar visível |
| F3 | Bordas da tabela desalinhadas na coluna Ações | botões num `div` dentro da célula |
| F4 | Com a API parada, a tela dizia "Erro 500" | mensagem "API indisponível" |
| F5 | Em 360 px, selos caíam na coluna do rótulo | layout da célula em cartão refeito; o teste E09 detecta a falha |

Mapa completo critério → teste → evidência: [`docs/EVIDENCIAS.md`](docs/EVIDENCIAS.md).

## Privacidade e legislação
Resumo de [`docs/LGPD.md`](docs/LGPD.md):
- **Coleta mínima:**
  - o documento aparece mascarado nas listagens (`DOC-••01`);
  - o nome social é o nome exibido (Decreto MT 854/2021);
  - o atendimento prioritário não registra o motivo;
  - a vaga reservada é genérica e não distingue PcD de idoso;
  - a observação tem no máximo 100 caracteres, com aviso de uso.
- **O que não é coletado:** foto, biometria, cópia de documento, endereço, telefone e assunto da visita.
- **Lei 5.553/1968:** o documento não é retido, e o cartão nunca é entregue em troca dele.
- **Registros que não se apagam:** visitas PRESENTE e ENCERRADA não são excluídas, e as passagens da catraca são imutáveis. Elas servem de prova em incidentes (ADR-008).
- **Rastreamento:** é feito por pontos de passagem, nunca de forma contínua. O trajeto só aparece em consulta específica.
- **Biometria:** prevista no backlog como **Épico B, bloqueado** até haver base legal específica (LGPD, art. 11), RIPD aprovado e uma alternativa sempre disponível (ADR-011).

> Os campos, a base legal e os prazos de retenção são **propostos para validação** do encarregado de dados e da assessoria jurídica do órgão. Não constituem parecer jurídico.

## Limitações
- Sem login nem perfis de acesso (ADR-001) e sem trilha de auditoria de edições. **Não publique online com dados reais.**
- A catraca é simulada; não há integração com equipamento físico (o contrato da API já é o que um leitor chamaria, ADR-012).
- Não há anonimização automática ao fim de `prazo_retencao_dias`.
- SQLite local, sem HTTPS, sem criptografia de banco e sem rotina de backup (requisitos de produção do Épico A).
- O "hoje" usa o fuso America/Cuiaba, e os horários são gravados em hora local (ADR-016). Uma operação em vários fusos exigiria UTC.
- A impressão pelo navegador foi verificada por `printToPDF`; o diálogo real de impressão não foi automatizado.

## Documentação
| Arquivo | Conteúdo |
|---|---|
| [`docs/PLANO.md`](docs/PLANO.md) | Plano do MVP (evidência de planejamento) |
| [`docs/REQUISITOS.md`](docs/REQUISITOS.md) | RF, RNF, regras de negócio, critérios de aceite |
| [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) | Modelo, endpoints e ADR-001 a ADR-019 |
| [`docs/BACKLOG.md`](docs/BACKLOG.md) | Sprints S0–S5 (+ S4b Docker) e épicos futuros |
| [`docs/TESTES.md`](docs/TESTES.md) | Casos de teste planejados |
| [`docs/EXECUCAO.md`](docs/EXECUCAO.md) | Log real de comandos, saídas e falhas corrigidas |
| [`docs/EVIDENCIAS.md`](docs/EVIDENCIAS.md) | Mapa de evidências por critério do desafio |
| [`docs/LGPD.md`](docs/LGPD.md) | Base legal, inventário de dados, segurança |
| [`CHANGELOG.md`](CHANGELOG.md) | Mudanças por sprint |
