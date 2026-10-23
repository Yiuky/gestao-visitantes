# PLANO — Gestão de visitantes (Desafio 06)

> Evidência de planejamento exigida na entrega. Fonte completa: `HANDOFF_CLAUDE_CODE.md`.

## Problema
A portaria de um órgão fictício controla visitantes em papel. Não sabe quem está no prédio nem onde, perde crachás e tende a coletar dados demais e a reter documentos.

## MVP
Registro de visitas por **tipo configurável**, entrada e saída com **cartão de acesso**, **catraca simulada** com rastreamento por pontos de passagem e **painel** de indicadores. Coleta mínima de dados (LGPD); biometria apenas prevista no backlog, como épico bloqueado.

## Critérios de aceite (resumo)
- **CA1:** visita válida é registrada e persiste; regras do tipo de visita bloqueiam registros inválidos (422).
- **CA2:** entrada exige cartão disponível e a data de hoje; saída controla a devolução do cartão; registros de presença não são excluídos.
- **CA3:** os indicadores mudam com cada operação; a pesquisa filtra corretamente; a catraca nega áreas não autorizadas e atualiza o último local.

## Marcos e sprints
| Sprint | Entrega | Prioridade |
|---|---|---|
| M0 | Documentação de requisitos, arquitetura e plano | ✅ concluído |
| S0 | Estrutura, ambiente, Git | MVP |
| S1 | API núcleo: tipos de visita, cartões, visitas, entrada/saída | MVP |
| S2 | Frontend núcleo integrado | MVP |
| S3 | Painel com indicadores reais e lista de presentes | MVP |
| S4 | Catraca simulada e rastreamento interno | Extensão |
| S5 | Homologação, README e GitHub | MVP |

**Regra de tempo:** se o encontro estiver acabando ao fim da S3, pular para a S5 e registrar a S4 como pendente.

## Indicadores
- Obrigatórios: visitas do dia · presentes · encerradas do dia.
- Complementares: veículos no pátio · cartões pendentes · acessos negados hoje.

## Decisões principais
Ver ADRs em `docs/ARQUITETURA.md`. As mais relevantes:
- ADR-008: registros de presença não se excluem.
- ADR-009: cartão sem dados pessoais e sem troca por documento.
- ADR-011: biometria condicionada a pré-requisitos legais.

## Riscos
| Risco | Mitigação |
|---|---|
| Escopo grande para um encontro | S4 é extensão; gates por sprint |
| Fuso horário no Windows | `tzdata` no requirements; "hoje" injetável nos testes |
| Coleta excessiva de dados | Lista de proibições em `CLAUDE.md` e `docs/LGPD.md` |
| Afirmar testes sem executar | `docs/EXECUCAO.md` com saídas reais; marcador NÃO TESTADO |
