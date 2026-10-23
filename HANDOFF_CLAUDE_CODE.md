# HANDOFF_CLAUDE_CODE — Desafio 06 · Gestão de visitantes

> Laboratório individual SEMA/MT · Engenharia de Software Agêntica · **dados exclusivamente fictícios**
> Consolida as etapas 01 (requisitos), 02 (arquitetura) e 03 (sprints) feitas no Claude.ai, já revisadas quanto a LGPD, legislação aplicável e segurança.
> O Claude Code deve ler este documento inteiro antes de qualquer código. O kit da pasta já traz `CLAUDE.md`, `README.md` (esqueleto), `.gitignore`, `pytest.ini`, `backend/requirements.txt` e `docs/` prontos; na Sprint 0 o Claude Code **confere e completa** esses arquivos em vez de recriá-los.
> **Uma sprint por rodada.** Não avançar se o gate da sprint falhar.

---

## 0. Resumo executivo

Sistema web local para a recepção de um órgão público fictício. O recepcionista:

1. registra a visita, conforme um **tipo de visita** configurável;
2. confirma a entrada entregando um **cartão de acesso** (usado nas catracas e leitores);
3. o cartão gera **passagens** nos pontos de acesso, que formam o **rastreamento interno** e a lista de evacuação;
4. confirma a saída com a devolução do cartão.

Um painel mostra os indicadores do dia. A **biometria** está prevista no backlog como épico **bloqueado**, condicionado a requisitos legais. O modelo de dados já tem os pontos de extensão, mas nenhum dado biométrico é coletado.

| Camada | Escolha |
|---|---|
| API | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Persistência | SQLAlchemy 2.x + SQLite em arquivo (caminho para PostgreSQL documentado) |
| Interface | React 18 + Vite, `fetch`, CSS próprio responsivo |
| Testes | pytest + TestClient (httpx) com banco temporário |
| Versão | Git + GitHub via `gh` (repositório **privado**, só com autorização) |

---

## 1. Visão do produto

**Problema.** A portaria de um órgão fictício controla visitantes em papel. Por isso, ninguém sabe dizer:
- quem está no prédio agora, nem onde (dado crítico numa evacuação);
- quais crachás não voltaram;
- se alguém entrou numa área não autorizada.

Além disso, o processo atual tende a coletar dados demais e a reter documentos, o que é vedado por lei.

**Solução (MVP).** Registro de visitas com regras por tipo, credencial por cartão sem dados pessoais e rastreamento por pontos de passagem. O sistema coleta o mínimo necessário, mascara o que é exibido e mantém trilha que não pode ser apagada.

**Fora do MVP (evolução registrada):** login e perfis, trilha de auditoria de edições, integração física com catraca/RFID, anonimização automática, **biometria (épico bloqueado)**, agendamento obrigatório, responsável legal para menores, lista de restrição de acesso, deploy.

## 2. Perfis de usuário

| Perfil | No MVP |
|---|---|
| Recepcionista | Registra, edita, cancela, confirma entrada/saída, gerencia cartões |
| Gestor(a) / segurança | Configura tipos de visita, consulta painel, presentes e trajetos |
| Catraca/leitor (sistema) | Envia passagens à API (simulado pela interface) |

> Sem login no MVP (ADR-001). A separação de perfis é requisito de produção.

---

## 3. Base legal e de segurança

> Mapeamento de requisitos feito pelo desenvolvedor. **Não é parecer jurídico.** Base legal formal, prazos de retenção e eventual RIPD devem ser validados pelo encarregado de dados e pela assessoria jurídica do órgão.

| Norma | Exigência | Como o sistema atende |
|---|---|---|
| Lei 5.553/1968, art. 2º §2º | Documento de identidade (inclusive CNH) deve ser anotado e **devolvido imediatamente** | Não existe campo "documento retido". O cartão **não** é trocado pelo documento; a garantia de devolução fica no sistema. |
| LGPD (Lei 13.709/2018), arts. 6º, 7º e 23 | Finalidade, necessidade, base legal pública, transparência | Finalidade declarada: segurança de pessoas e patrimônio, controle de acesso e registro de atendimento. Coleta mínima. Aviso de privacidade na interface. |
| LGPD, art. 11 | Dado sensível (saúde, biometria) exige base específica | Prioridade sem motivo; vaga "reservada" genérica, sem distinguir PcD; **biometria não coletada** (épico bloqueado). |
| LGPD, art. 14 | Dados de crianças e adolescentes no melhor interesse | Registrado como evolução (responsável legal por tipo de visita). |
| LGPD, arts. 46 e 48 | Medidas de segurança; resposta a incidentes | Mascaramento, registros que não se apagam, `.db` fora do Git; login, HTTPS, criptografia e backup como requisitos de produção. |
| Decreto MT 1.427/2025 | Regulamenta a LGPD no Executivo estadual (encarregado, comitê setorial, RIPD) | O processo de controle de visitantes deve ser mapeado pelo encarregado; campos e prazos são "propostos para validação". |
| Decreto MT 1.428/2025 (PSI-MT) | Segurança da informação, incluindo backup e recuperação | Backup e recuperação documentados como requisito de produção. |
| Decreto MT 854/2021 | Sistemas devem incorporar o campo **nome social** | Campo `nome_social`; quando preenchido, é o nome exibido. |
| Lei 10.048/2000 (red. Lei 14.626/2023) | Atendimento prioritário em repartições públicas | Marcador `atendimento_prioritario` (sim/não) ordena a fila; motivo não é registrado. |
| Lei 10.741/2003, art. 41; Lei 13.146/2015, art. 47; Res. Contran 965/2022 | Vagas reservadas a pessoas idosas (5%) e PcD (2%, mín. 1), com credencial | Campo `vaga_reservada` (credencial conferida); só com veículo informado. |
| Lei 12.527/2011 (LAI) | Registros de acesso podem ser objeto de pedido de informação | Tipos e setores com nomes neutros; nenhum assunto em texto livre. |

**Não coletar em hipótese alguma:** foto, biometria, cópia do documento, CPF real, endereço, telefone, motivo da prioridade, assunto da visita em texto livre.

---

## 4. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | **Tipos de visita:** cadastrar, listar, editar, ativar/desativar e excluir (exclusão só sem visitas vinculadas). |
| RF02 | **Visitas:** registrar visita (nome civil, nome social, documento fictício, tipo, setor, data, horário, prioridade, veículo, observação curta). Status inicial AGENDADA. |
| RF03 | **Pesquisa:** filtrar por nome (parcial, também no nome social), setor, tipo, data e status; ordenar com prioritários primeiro dentro do mesmo horário. |
| RF04 | **Edição, cancelamento e exclusão** respeitando o ciclo de vida (RN05–RN07). |
| RF05 | **Entrada** com entrega de cartão de acesso disponível; **saída** com confirmação de devolução do cartão. |
| RF06 | **Cartões de acesso:** cadastrar, listar, editar e inativar; status DISPONIVEL, EM_USO, EXTRAVIADO e INATIVO. |
| RF07 | **Catraca/leitor (simulado):** registrar passagem por cartão num ponto de acesso, liberando ou negando conforme as regras; toda tentativa é gravada. |
| RF08 | **Rastreamento interno:** trajeto de uma visita (passagens em ordem) e lista de presentes com **último local registrado** (evacuação). |
| RF09 | **Painel:** indicadores obrigatórios — visitas do dia, presentes, encerradas do dia; complementares — veículos no pátio, cartões pendentes, acessos negados hoje. |
| RF10 | **Aviso de privacidade** fixo na interface (finalidade, base legal proposta, contato fictício do encarregado). |

## 5. Requisitos não funcionais

- RNF01: interface responsiva (360 px a desktop); tabelas viram cartões abaixo de 640 px.
- RNF02: persistência em SQLite; dados sobrevivem ao reinício.
- RNF03: execução local em Windows/PowerShell (Python 3.11+, Node 18+).
- RNF04: nenhum dado real, credencial ou segredo no repositório.
- RNF05: "hoje" calculado no fuso **America/Cuiaba** (pacote `tzdata` no Windows).
- RNF06: o documento completo nunca aparece em listagens, só mascarado (`DOC-••01`).
- RNF07: passagens são imutáveis; a API não oferece edição nem exclusão delas.

---

## 6. Regras de negócio

### Tipos de visita
| ID | Regra |
|---|---|
| RN01 | `nome` obrigatório e único (3–60 caracteres). |
| RN02 | Visita só pode ser **criada** com tipo `ativo = true`; caso contrário, 422. |
| RN03 | Se `exige_documento = true`, `documento` é obrigatório (422). |
| RN04 | Se `setores_permitidos` não estiver vazio, `setor_destino` deve pertencer a ele (422). |
| RN04a | Se `permite_veiculo = false`, placa não é aceita (422). |
| RN04b | Excluir tipo com visitas vinculadas → 409 (orientar a desativar). |

### Visitas
| ID | Regra |
|---|---|
| RN05 | Ciclo: `AGENDADA → PRESENTE → ENCERRADA` e `AGENDADA → CANCELADA`. Nenhuma outra transição (409). |
| RN06 | Edição (PUT) proibida em ENCERRADA ou CANCELADA (409). O PUT nunca altera status, horários de entrada/saída nem cartão. |
| RN07 | **Exclusão só em AGENDADA ou CANCELADA.** PRESENTE e ENCERRADA são registros de presença e **não podem ser excluídos** (409). |
| RN08 | `nome_civil` obrigatório (3–120). `nome_social` opcional; quando preenchido, é o nome exibido em toda a interface. |
| RN09 | `documento` fictício, formato livre (ex.: `DOC-0001`); a API devolve `documento_mascarado` nas listagens e o valor completo só no detalhe. |
| RN10 | `observacao` opcional, **máx. 100 caracteres**, com aviso fixo na tela: "não registre motivo, saúde ou opinião sobre o visitante". |
| RN11 | `placa` opcional, normalizada para maiúsculas sem hífen, validada por `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$` (formatos antigo e Mercosul). |
| RN12 | `vaga_reservada = true` só é aceito com placa informada (422). Significa "credencial de vaga reservada conferida" e não indica o motivo. |

### Entrada, saída e cartões
| ID | Regra |
|---|---|
| RN13 | Entrada só em visita AGENDADA **e** com `data_visita = hoje` (409). |
| RN14 | Entrada exige `cartao_id` de um cartão `DISPONIVEL` (409). O cartão passa a `EM_USO` e fica vinculado à visita. |
| RN15 | Na entrada, a mesma placa não pode estar em outra visita PRESENTE (409: veículo já no pátio). |
| RN16 | Saída só em visita PRESENTE (409). O corpo exige `cartao_devolvido: bool`. |
| RN17 | Se o cartão foi devolvido, ele volta a `DISPONIVEL`. Se não foi, fica `EXTRAVIADO` e a visita fica com `cartao_devolvido = false`. A saída é registrada nos dois casos. |
| RN18 | Cartão impresso **sem dados pessoais**: só código, cor e categoria. É proibido condicionar a entrega à retenção do documento (Lei 5.553/1968). |
| RN19 | Cartão `EM_USO` não pode ser editado nem inativado (409). Cartão com histórico de visitas não é excluído; é inativado (409 no DELETE). |
| RN20 | `codigo` do cartão único (ex.: `V-001`); `codigo_leitura` único, simulando o identificador RFID/QR. |

### Catraca e rastreamento
| ID | Regra |
|---|---|
| RN21 | Toda leitura gera uma **Passagem** com `resultado` LIBERADO ou NEGADO e `motivo` quando negada. Nada é descartado. |
| RN22 | É negada a passagem quando: <br>• o código de leitura é desconhecido; <br>• o cartão não está `EM_USO`; <br>• não há visita PRESENTE vinculada ao cartão; <br>• o ponto de acesso está inativo; <br>• o ponto pertence a um setor diferente do `setor_destino` da visita. |
| RN23 | Pontos com `setor = NULL` são **área comum** (ex.: catraca da portaria) e liberam qualquer visita PRESENTE. |
| RN24 | "Último local" de um presente = ponto da última passagem LIBERADA com sentido ENTRADA. Sem passagens, o último local é "Recepção". |
| RN25 | Rastreamento é por **pontos de passagem**, nunca contínuo (sem geolocalização ou câmera). Trajetos não aparecem no painel geral, apenas na consulta específica. |
| RN26 | Passagens são imutáveis (RNF07); o prazo de retenção segue o `prazo_retencao_dias` do tipo de visita (anonimização automática é evolução). |

---

## 7. Modelo de dados

### `tipos_visita`
| Campo | Tipo | Regras |
|---|---|---|
| id | INTEGER PK | |
| nome | VARCHAR(60) | único, obrigatório |
| descricao | VARCHAR(200) | opcional |
| ativo | BOOLEAN | default true |
| exige_documento | BOOLEAN | default false |
| permite_veiculo | BOOLEAN | default false |
| setores_permitidos | VARCHAR(255) | lista separada por vírgula; vazio = todos |
| prazo_retencao_dias | INTEGER | default 180; **proposto para validação do encarregado** |

### `cartoes_acesso`
| Campo | Tipo | Regras |
|---|---|---|
| id | INTEGER PK | |
| codigo | VARCHAR(10) | único, impresso no cartão (ex.: `V-001`) |
| codigo_leitura | VARCHAR(32) | único, simula o identificador lido pela catraca |
| cor | VARCHAR(20) | ex.: verde, amarelo |
| status | VARCHAR(10) | DISPONIVEL, EM_USO, EXTRAVIADO ou INATIVO |

### `visitas`
| Campo | Tipo | Regras |
|---|---|---|
| id | INTEGER PK | |
| tipo_visita_id | FK → tipos_visita | obrigatório |
| nome_civil | VARCHAR(120) | obrigatório |
| nome_social | VARCHAR(120) | opcional |
| documento | VARCHAR(30) | condicional (RN03), fictício |
| setor_destino | VARCHAR(50) | ∈ SETORES e RN04 |
| data_visita | DATE | obrigatório |
| horario_previsto | TIME | obrigatório |
| atendimento_prioritario | BOOLEAN | default false |
| placa | VARCHAR(7) | opcional (RN11) |
| descricao_veiculo | VARCHAR(60) | opcional |
| vaga_reservada | BOOLEAN | default false (RN12) |
| observacao | VARCHAR(100) | opcional (RN10) |
| status | VARCHAR(10) | AGENDADA, PRESENTE, ENCERRADA ou CANCELADA |
| cartao_id | FK → cartoes_acesso | nulo até a entrada |
| cartao_devolvido | BOOLEAN | nulo até a saída |
| entrada_em / saida_em | DATETIME | nulos até a transição |
| criado_em / atualizado_em | DATETIME | automáticos |

### `pontos_acesso` (seed fixo no MVP)
| Campo | Tipo | Regras |
|---|---|---|
| id | INTEGER PK | |
| nome | VARCHAR(60) | ex.: "Catraca Portaria" |
| setor | VARCHAR(50) | NULL = área comum |
| ativo | BOOLEAN | default true |
| metodos_aceitos | VARCHAR(30) | default `CARTAO`; **ponto de extensão para biometria futura** |

### `passagens` (somente inserção)
| Campo | Tipo | Regras |
|---|---|---|
| id | INTEGER PK | |
| ponto_id | FK → pontos_acesso | obrigatório |
| codigo_lido | VARCHAR(32) | o que a catraca leu (mesmo se desconhecido) |
| cartao_id | FK → cartoes_acesso | nulo se o código for desconhecido |
| visita_id | FK → visitas | nulo se não houver visita presente |
| credencial_tipo | VARCHAR(10) | default `CARTAO`; **extensão para biometria futura** |
| sentido | VARCHAR(7) | ENTRADA ou SAIDA |
| resultado | VARCHAR(8) | LIBERADO ou NEGADO |
| motivo | VARCHAR(80) | preenchido quando NEGADO |
| ocorrido_em | DATETIME | automático |

**SETORES (config):** `Atendimento`, `Protocolo`, `Jurídico`, `Tecnologia`, `Diretoria`.

**Relacionamentos:**
- TipoVisita 1—N Visita
- CartaoAcesso 1—N Visita (no histórico; no máximo 1 PRESENTE por vez)
- Visita 1—N Passagem
- PontoAcesso 1—N Passagem

---

## 8. Dados fictícios (seed — `backend/seed.py`, nunca usado nos testes)

**Tipos de visita**
| Nome | exige_doc | permite_veiculo | setores_permitidos |
|---|---|---|---|
| Atendimento ao público | não | não | Atendimento, Protocolo |
| Reunião técnica | sim | sim | (todos) |
| Entrega de material | sim | sim | Protocolo |
| Prestador de serviço | sim | sim | Tecnologia |
| Audiência com autoridade | sim | sim | Diretoria |

**Cartões:** `V-001` a `V-010`, `codigo_leitura` `RFID-TESTE-0001` a `RFID-TESTE-0010`, cores alternadas verde/amarelo, todos DISPONIVEL.

**Pontos de acesso:** Catraca Portaria (área comum) · Leitor Atendimento · Leitor Protocolo · Leitor Jurídico · Leitor Tecnologia · Leitor Diretoria.

**Visitas (hoje, salvo indicação)**
| Nome civil | Nome social | Tipo | Setor | Hora | Situação |
|---|---|---|---|---|---|
| Ana Exemplo | — | Atendimento ao público | Protocolo | 08:30 | ENCERRADA, cartão devolvido |
| Bruno Teste | — | Reunião técnica | Jurídico | 09:00 | PRESENTE com V-002, placa `TST1A01` |
| Carla Fictícia | Caio Fictício | Prestador de serviço | Tecnologia | 10:15 | AGENDADA, prioritário |
| Diego Modelo | — | Audiência com autoridade | Diretoria | 14:00 | AGENDADA |
| Elisa Simulada | — | Entrega de material | Protocolo | ontem 15:30 | ENCERRADA, cartão não devolvido (V-009 EXTRAVIADO) |

Painel esperado com o seed:
- visitas do dia **4**, presentes **1**, encerradas do dia **1**;
- veículos no pátio **1**, cartões pendentes **1**.

> Placas no formato `TST…` e códigos `RFID-TESTE-…` são **evidentemente fictícios** e assim declarados no README.

---

## 9. Critérios de aceite

- **CA1 — Registro com regras por tipo e persistência.**
  - Uma visita válida aparece com status AGENDADA e continua lá após reiniciar a API.
  - Visita com tipo inativo, setor fora dos permitidos, sem documento quando exigido, ou com placa em tipo que não permite veículo é recusada (422), e a tela mostra a mensagem.
- **CA2 — Entrada, saída e cartão.**
  - A entrada com cartão disponível muda o status para PRESENTE e o cartão para EM_USO.
  - Entrada com cartão em uso, fora da data ou com placa já no pátio retorna 409.
  - A saída com devolução libera o cartão; sem devolução, o cartão fica EXTRAVIADO e o painel incrementa "cartões pendentes".
  - Visitas PRESENTE ou ENCERRADA não podem ser excluídas (409).
- **CA3 — Painel, pesquisa e rastreamento.**
  - Os três indicadores obrigatórios mudam imediatamente após criar, cancelar, dar entrada, dar saída e excluir.
  - A pesquisa por parte do nome (civil ou social), setor, tipo ou data retorna somente os registros correspondentes.
  - Uma passagem num leitor de outro setor é NEGADA e gravada com motivo; uma passagem permitida atualiza o "último local" na lista de presentes.

---

## 10. Arquitetura

```
[React + Vite :5173] --fetch /api/* (proxy)--> [FastAPI :8000] --SQLAlchemy--> [SQLite backend/data/visitantes.db]
                                                     ^
                    [Simulador de catraca na UI] ----┘  (POST /api/catraca/passagens)
```

### Mapa de pastas
```
gestao-visitantes/
├── CLAUDE.md
├── README.md
├── HANDOFF_CLAUDE_CODE.md
├── .gitignore
├── pytest.ini                      # pythonpath = backend ; testpaths = tests
├── docs/
│   ├── PLANO.md  REQUISITOS.md  ARQUITETURA.md  BACKLOG.md
│   ├── TESTES.md  EXECUCAO.md  LGPD.md
│   └── img/
├── backend/
│   ├── requirements.txt            # fastapi, uvicorn, sqlalchemy, pydantic, pytest, httpx, tzdata
│   ├── seed.py
│   ├── data/.gitkeep
│   └── app/
│       ├── main.py  database.py  models.py  schemas.py  config.py
│       ├── services/regras.py      # transições, validações por tipo, decisão da catraca
│       └── routers/
│           ├── tipos.py  cartoes.py  visitas.py
│           ├── catraca.py  dashboard.py
├── tests/
│   ├── conftest.py                 # banco temporário, override get_db, "hoje" fixo
│   ├── test_tipos.py  test_cartoes.py  test_visitas_crud.py
│   ├── test_entrada_saida.py  test_catraca_rastreamento.py  test_dashboard.py
└── frontend/
    ├── vite.config.js              # proxy /api -> http://127.0.0.1:8000
    └── src/
        ├── main.jsx  App.jsx  api.js  styles.css
        └── pages/
            ├── Painel.jsx          # indicadores + presentes com último local
            ├── Visitas.jsx         # formulário, filtros, tabela, entrada/saída
            ├── Tipos.jsx  Cartoes.jsx
            └── Catraca.jsx         # simulador de leitura + trajeto da visita
```

### Endpoints

| Método | Rota | Sucesso | Erros |
|---|---|---|---|
| GET | `/api/health` | 200 | — |
| GET | `/api/setores` | 200 | — |
| GET/POST | `/api/tipos-visita` | 200 / 201 | 422 |
| GET/PUT/DELETE | `/api/tipos-visita/{id}` | 200 / 200 / 204 | 404, 409, 422 |
| GET/POST | `/api/cartoes` (`?status=`) | 200 / 201 | 409 (código duplicado), 422 |
| GET/PUT/DELETE | `/api/cartoes/{id}` | 200 / 200 / 204 | 404, 409 |
| GET | `/api/visitas?q=&setor=&tipo_id=&data=&status=` | 200 `[VisitaResumo]` | 422 |
| POST | `/api/visitas` | 201 | 422 |
| GET/PUT/DELETE | `/api/visitas/{id}` | 200 `VisitaDetalhe` / 200 / 204 | 404, 409, 422 |
| POST | `/api/visitas/{id}/entrada` `{cartao_id}` | 200 | 404, 409 |
| POST | `/api/visitas/{id}/saida` `{cartao_devolvido}` | 200 | 404, 409, 422 |
| POST | `/api/visitas/{id}/cancelar` | 200 | 404, 409 |
| GET | `/api/visitas/{id}/passagens` | 200 (trajeto) | 404 |
| GET | `/api/pontos-acesso` | 200 | — |
| POST | `/api/catraca/passagens` `{codigo_lido, ponto_id, sentido}` | 201 `{resultado, motivo, passagem}` | 404 (ponto), 422 |
| GET | `/api/presentes` | 200 `[{visita, nome_exibido, setor, cartao, ultimo_local, desde}]` | — |
| GET | `/api/dashboard` | 200 | — |

- **`VisitaResumo`:** traz `nome_exibido` (nome social ou civil) e `documento_mascarado`, mas **não** o documento completo.
- **`VisitaDetalhe`:** traz todos os campos.
- **Erros:** formato FastAPI `{"detail": "mensagem clara em português"}`; o 422 de validação segue o padrão do Pydantic.

**`/api/dashboard`:**
```json
{
  "data_referencia": "2026-10-23",
  "visitas_do_dia": 4, "presentes": 1, "encerradas_do_dia": 1,
  "veiculos_no_patio": 1, "cartoes_pendentes": 1, "acessos_negados_hoje": 0
}
```

### Consultas dos indicadores (COUNT no banco, nunca em Python)
```sql
-- obrigatórios
SELECT COUNT(*) FROM visitas WHERE data_visita = :hoje AND status <> 'CANCELADA';
SELECT COUNT(*) FROM visitas WHERE status = 'PRESENTE';
SELECT COUNT(*) FROM visitas WHERE status = 'ENCERRADA' AND data_visita = :hoje;
-- complementares
SELECT COUNT(*) FROM visitas WHERE status = 'PRESENTE' AND placa IS NOT NULL;
SELECT COUNT(*) FROM cartoes_acesso WHERE status = 'EXTRAVIADO';
SELECT COUNT(*) FROM passagens WHERE resultado = 'NEGADO' AND date(ocorrido_em) = :hoje;
```

### Telas
1. **Painel:** 6 cartões de indicadores e a tabela "Quem está no prédio agora" (nome exibido, setor, cartão, último local, desde), com botão **Imprimir lista de evacuação** (`window.print` e CSS de impressão).
2. **Visitas:** formulário cujos campos se adaptam ao tipo (documento obrigatório; bloco de veículo só se `permite_veiculo`), filtros e tabela com ações Entrada (escolhe cartão disponível), Saída (pergunta se devolveu), Cancelar, Editar e Excluir (apenas quando permitido).
3. **Tipos de visita:** CRUD com ativar/desativar.
4. **Cartões:** CRUD, filtro por status e ação "marcar como recuperado" (EXTRAVIADO → DISPONIVEL).
5. **Catraca (simulador):** escolher ponto, sentido e digitar ou selecionar o código lido. O resultado (LIBERADO ou NEGADO, com motivo) aparece em destaque. Ao lado, o trajeto da visita selecionada.
6. **Rodapé fixo:** aviso de privacidade (RF10).

### ADRs

| ADR | Decisão |
|---|---|
| 001 | Sem login no MVP; perfis são requisito de produção. |
| 002 | Setores como lista fixa em `config.py`. |
| 003 | Status armazenado e transições só por endpoints dedicados (entrada, saída, cancelar). |
| 004 | "Hoje" no fuso America/Cuiaba, injetável nos testes; `tzdata` no Windows. |
| 005 | SQLite via `DATABASE_URL`; PostgreSQL = trocar a URL e instalar `psycopg`; `create_all`, sem Alembic no MVP. |
| 006 | Tipos de visita configuráveis carregam as regras (documento, veículo, setores, retenção). |
| 007 | Minimização (LGPD): nome social, documento mascarado, prioridade sem motivo, vaga reservada genérica, observação de 100 caracteres, nada de foto ou assunto. |
| 008 | Registros de presença não são excluídos; passagens são imutáveis. Isso preserva prova em incidentes. |
| 009 | Cartão sem dados pessoais e sem troca por documento (Lei 5.553/1968); a devolução é controlada no sistema. |
| 010 | Rastreamento por pontos de passagem, não contínuo; o "último local" serve à evacuação; trajeto só em consulta específica. |
| 011 | **Biometria condicionada:** prevista no backlog (épico B) e **bloqueada** até cumprir os pré-requisitos legais; o modelo já tem `metodos_aceitos` e `credencial_tipo` para extensão sem retrabalho; nenhum dado biométrico no MVP. |
| 012 | Catraca simulada por API e tela; a integração física é evolução (o contrato `POST /api/catraca/passagens` já é o que um equipamento chamaria). |

### Validação por camada
| Camada | Como validar |
|---|---|
| Banco | Criar registros, reiniciar a API e confirmar que continuam lá; conferir o arquivo `.db` fora do Git |
| API | `pytest -q` e Swagger em `http://127.0.0.1:8000/docs` |
| Interface | `npm run build` sem erros e roteiro CA1–CA3 no navegador, em desktop e em 360 px |
| Integração | Ação na tela, depois conferir em `/api/...` e nos indicadores |

---

## 11. Backlog e sprints

> Ciclo de cada sprint: PLANEJAR → IMPLEMENTAR → EXECUTAR → TESTAR → CORRIGIR → REVALIDAR → DOCUMENTAR → COMMIT.
> **Prioridade do encontro:** S0 a S3 formam o MVP obrigatório. S4 (catraca e rastreamento) é extensão: se o tempo apertar, pular para S5 e registrar S4 como pendente.

### M0 — Documentação ✅
Este arquivo.

### S0 — Estrutura, ambiente e Git
- **Objetivo:** conferir o kit de documentação e a estrutura; verificar as ferramentas; iniciar o Git.
- **Arquivos já entregues no kit:** `CLAUDE.md`, `README.md`, `.gitignore`, `pytest.ini`, `backend/requirements.txt`, `docs/` (PLANO, REQUISITOS, ARQUITETURA, BACKLOG, TESTES, LGPD, EXECUCAO) e `.gitkeep` em `backend/data/`, `tests/`, `frontend/` e `docs/img/`.
- **Prompt:**
  > Estamos na pasta do projeto Gestão de visitantes, que já contém o kit de documentação. Leia CLAUDE.md, HANDOFF_CLAUDE_CODE.md e todos os arquivos de docs/. Primeiro liste decisões, dúvidas e qualquer inconsistência entre os documentos; não mude o escopo sem registrar ADR. Não recrie os arquivos existentes: apenas corrija inconsistências que encontrar e me diga o que mudou. Verifique Python, Node e Git, preencha a tabela de ambiente em docs/EXECUCAO.md e inicialize o Git. Confirme que o .gitignore cobre *.db, .env, .venv e node_modules. Faça apenas a Sprint 0. Registre comandos e saídas reais em docs/EXECUCAO.md, marque S0 como concluída em docs/BACKLOG.md e proponha o primeiro commit.
- **Verificação:** `python --version` · `node --version` · `git --version` · `git status`
- **Aceite:** documentos conferidos; tabela de ambiente preenchida; `.gitignore` cobre `*.db` e `.env`; Git inicializado.
- **Parada:** commit `chore: estrutura inicial e documentação`.

### S1 — Banco e API núcleo (tipos, cartões, visitas)
- **Objetivo:** modelos `tipos_visita`, `cartoes_acesso` e `visitas`; CRUDs; entrada, saída e cancelar; RN01–RN20.
- **Arquivos:** `backend/app/*` (exceto catraca), `tests/conftest.py`, `test_tipos.py`, `test_cartoes.py`, `test_visitas_crud.py`, `test_entrada_saida.py`.
- **Prompt:**
  > Leia o BACKLOG e implemente SOMENTE a Sprint 1. Antes de editar, informe objetivo, arquivos e testes. Implemente os modelos, schemas e routers de tipos de visita, cartões e visitas (CRUD, pesquisa, entrada, saída, cancelar), /api/setores e /api/health, seguindo RN01–RN20 e os contratos da seção 10. Concentre as regras em services/regras.py. VisitaResumo deve trazer nome_exibido e documento_mascarado, nunca o documento completo. "Hoje" deve ser injetável nos testes. Rode a API e os testes, corrija as falhas e registre as saídas reais em docs/EXECUCAO.md. Proponha o commit.
- **Testes mínimos:**
  - Tipos: tipo duplicado (422 ou 409); excluir tipo com visitas (409).
  - Validações por tipo: criar visita com tipo inativo, setor não permitido, documento ausente quando exigido, placa em tipo sem veículo, placa inválida e vaga reservada sem placa (todos 422).
  - Listagem e pesquisa: lista vazia; busca pelo nome social; listagem sem o documento completo.
  - Entrada: com cartão em uso, fora da data e com placa já no pátio (409); entrada OK.
  - Saída: com devolução (cartão DISPONIVEL); sem devolução (cartão EXTRAVIADO).
  - Exclusão: de PRESENTE e de ENCERRADA (409); de AGENDADA (204).
  - Cancelamento: cancelar PRESENTE (409).
- **Verificação (PowerShell):**
  ```powershell
  cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1
  pip install -r requirements.txt
  uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs
  cd ..; pytest -q
  ```
- **Aceite:** todos os testes passando; persistência confirmada após reinício.
- **Parada:** commit `feat(api): tipos de visita, cartões e ciclo de visitas`.

### S2 — Frontend núcleo e integração
- **Objetivo:** páginas Visitas, Tipos e Cartões integradas à API, responsivas, com rodapé de privacidade.
- **Prompt:**
  > Implemente SOMENTE a Sprint 2: projeto React + Vite em frontend/ com proxy /api, navegação por abas (Painel provisório, Visitas, Tipos, Cartões), formulário de visita adaptado ao tipo, filtros, ações de entrada (seleção de cartão disponível), saída (pergunta de devolução), cancelar, editar e excluir apenas quando permitidas. Mostre as mensagens de erro da API, o estado de lista vazia e o aviso fixo no campo observação. Inclua o rodapé de privacidade. Abaixo de 640px, as tabelas viram cartões. Rode npm run build e teste no navegador com a API ativa. Registre as evidências e proponha o commit.
- **Verificação:** `cd frontend; npm install; npm run dev` · `npm run build`
- **Aceite:** CA1 e CA2 executáveis pela tela; build sem erros; layout ok em 360 px.
- **Parada:** commit `feat(web): telas de visitas, tipos e cartões`.

### S3 — Painel com dados reais
- **Objetivo:** `/api/dashboard` (6 indicadores por COUNT) e a página Painel com a lista de presentes (último local = "Recepção" até existir S4).
- **Prompt:**
  > Implemente SOMENTE a Sprint 3: endpoint /api/dashboard com as consultas da seção 10 (COUNT no banco, data de referência America/Cuiaba injetável) e /api/presentes. Testes verificam que cada indicador muda após criar, cancelar, entrada, saída com e sem devolução e exclusão, e que visita de outro dia não conta "do dia". Na página Painel, mostre os cartões de indicadores, a tabela de presentes e o botão de impressão com CSS de impressão; os indicadores recarregam após cada operação. Rode tudo e registre.
- **Aceite:** CA3 (parte painel e pesquisa) completo.
- **Parada:** commit `feat: painel com indicadores e lista de presentes`.

### S4 — Catraca simulada e rastreamento interno (extensão)
- **Objetivo:** `pontos_acesso` (seed), `passagens`, `POST /api/catraca/passagens`, trajeto, último local; RN21–RN26.
- **Prompt:**
  > Implemente SOMENTE a Sprint 4: modelos pontos_acesso (seed automático se vazio) e passagens (somente inserção, sem PUT/DELETE), POST /api/catraca/passagens com a decisão de RN22–RN23 em services/regras.py, GET /api/visitas/{id}/passagens e o último local em /api/presentes (RN24). Inclua o indicador acessos_negados_hoje. Na página Catraca, crie o simulador (ponto, sentido, código lido), com o resultado em destaque e o trajeto da visita. Testes: código desconhecido, cartão não EM_USO, visita já encerrada, setor não autorizado (NEGADO gravado com motivo), área comum liberada, último local atualizado, inexistência de rota para editar ou excluir passagem (405). Rode tudo e registre.
- **Aceite:** CA3 (parte rastreamento) completo.
- **Parada:** commit `feat: catraca simulada e rastreamento por pontos de passagem`.

### S5 — Homologação, README e GitHub
- **Prompt:**
  > Execute a Sprint 5 e homologue Gestão de visitantes. Teste criação, leitura, edição e exclusão de cada entidade; validações; lista vazia; atualização dos indicadores; persistência ao reiniciar; integração frontend/API; ausência de segredos e de .db no Git. Corrija as falhas, reexecute a suíte e revise o diff. Atualize o README com: instalação, execução, funcionalidades, exemplos de uso, seção "Privacidade e legislação" (resumo de docs/LGPD.md com a ressalva de validação pelo encarregado), limitações, épico de biometria bloqueado, resultados dos testes (passou/falhou/corrigido/NÃO TESTADO), capturas em docs/img/ e a reflexão. Confirme git status e git log. Só com minha autorização use o gh CLI para criar um repositório PRIVADO e dar push. Informe a URL verdadeira.
- **Verificação:**
  ```powershell
  pytest -q
  cd frontend; npm run build; cd ..
  git status; git log --oneline
  git ls-files | Select-String "\.db|\.env"     # deve vir vazio
  ```
- **Parada:** push feito e URL registrada.

---

## 12. Épicos de evolução (backlog futuro)

### Épico A — Produção segura
- A1: login com perfis (recepção, gestor, segurança) e trilha de auditoria de edições e consultas de trajeto.
- A2: HTTPS, banco criptografado, backup e recuperação conforme PSI-MT.
- A3: anonimização automática ao fim de `prazo_retencao_dias`, para visitas e passagens.
- A4: canal de direitos do titular (art. 18) e plano de resposta a incidentes (art. 48).

### Épico B — Biometria em pontos de acesso ⛔ BLOQUEADO
> Só pode sair de "bloqueado" quando **todos** os pré-requisitos abaixo estiverem atendidos e registrados em ADR.

**Pré-requisitos (gate legal):**
- [ ] Base legal específica do art. 11 da LGPD definida pelo encarregado e pela assessoria jurídica. Legítimo interesse não se aplica a dado sensível.
- [ ] **RIPD aprovado**, com demonstração concreta de necessidade e proporcionalidade frente ao cartão.
- [ ] Escopo restrito: áreas de segurança elevada e público definido; **visitantes eventuais não são público-alvo**.
- [ ] **Alternativa sempre disponível:** o cartão continua válido, e ninguém fica sem acesso por recusar a biometria.
- [ ] Nenhuma imagem armazenada; só o template, criptografado, num cofre separado do banco de visitas.
- [ ] Prazo de retenção e procedimento de exclusão do template ao fim do vínculo.
- [ ] Avaliação de vieses e de taxas de falso positivo e negativo do fornecedor.

**Itens técnicos (após o gate):**
- B1: aceitar `BIOMETRIA` em `pontos_acesso.metodos_aceitos` e em `passagens.credencial_tipo`.
- B2: tabela `credenciais_biometricas` com apenas `pessoa_ref`, `template_ref` (ponteiro para o cofre), `cadastrado_em`, `revogado_em`; **sem dado biométrico no banco da aplicação**.
- B3: fluxo de cadastro com aviso específico e destacado, e revogação a qualquer tempo.
- B4: testes que garantem que um ponto biométrico continua aceitando cartão.

### Épico C — Integração física e operação
- C1: integração real com catraca/RFID pelo contrato `POST /api/catraca/passagens`, autenticada por chave de equipamento.
- C2: urna de recolhimento do cartão na catraca de saída, com saída automática.
- C3: QR Code temporário com expiração no fim do dia, como alternativa ao cartão físico.
- C4: cadastro de vagas com capacidade e mapa do pátio; saída do veículo separada da pessoa.
- C5: alerta de presentes após o horário de funcionamento.
- C6: responsável legal para tipos que envolvem menores; agendamento obrigatório por tipo.
- C7: lista de restrição de acesso, somente com base legal (decisão judicial ou medida protetiva) e procedimento formal.

---

## 13. Pendências e pontos de atenção

- [ ] Confirmar as versões de Python e Node na máquina do laboratório (S0).
- [ ] `tzdata` no `requirements.txt`.
- [ ] Capturas de tela:
  - painel com presentes;
  - formulário com erro 422 por tipo;
  - entrada negada por cartão em uso (409);
  - simulador de catraca negando acesso;
  - tela em 360 px.
- [ ] Registrar em `docs/EXECUCAO.md` pelo menos **uma falha real encontrada e corrigida**.
- [ ] Reflexão (3–5 linhas no README). Sugestões de decisão técnica: ADR-008 (não excluir registros de presença), ADR-009 (cartão sem dados pessoais) ou ADR-011 (biometria condicionada). Registrar também uma sugestão do Claude Code que você revisou.
- [ ] Autorizar o push só depois de revisar o diff.

## 14. Referências legais

- Lei 5.553/1968 — https://planalto.gov.br/ccivil_03/leis/L5553.htm
- Lei 13.709/2018 (LGPD) — https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- Guia ANPD: Tratamento de dados pessoais pelo Poder Público — https://lgpd.prefeitura.rio/wp-content/uploads/sites/102/2023/03/guia-poder-publico-anpd-versao-final.pdf
- Decretos MT 1.427/2025 e 1.428/2025 (citados no Decreto 1.691/2025) — https://www.legisweb.com.br/legislacao/?id=484322
- Decreto MT 854/2021 (nome social) — https://www.saude.mt.gov.br/storage/old/files/854-[18680-050721-SES-MT].pdf
- Lei 10.048/2000 atualizada — https://legis.senado.leg.br/norma/551924/publicacao/34619784
- Estatuto da Pessoa Idosa, art. 41 — https://www.admdireito.com.br/legislacao/art/lei_00107412003-41
- Vagas reservadas e credenciais (Contran 965/2022) — https://www.portaldotransito.com.br/?p=36577
