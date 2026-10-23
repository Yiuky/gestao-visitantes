# REQUISITOS — Gestão de visitantes

> Extraído de `HANDOFF_CLAUDE_CODE.md` (seções 1, 2, 4, 5, 6 e 9). Em caso de divergência, o handoff prevalece até um ADR dizer o contrário.

## Perfis
| Perfil | No MVP |
|---|---|
| Recepcionista | Registra, edita, cancela, confirma entrada/saída, gerencia cartões |
| Gestor(a) / segurança | Configura tipos de visita, consulta painel, presentes e trajetos |
| Catraca/leitor (sistema) | Envia passagens à API (simulado pela interface) |

Sem login no MVP (ADR-001).

## Requisitos funcionais
| ID | Requisito |
|---|---|
| RF01 | Tipos de visita: cadastrar, listar, editar, ativar/desativar e excluir (só sem visitas vinculadas). |
| RF02 | Visitas: registrar com nome civil, nome social, documento fictício, tipo, setor, data, horário, prioridade, veículo e observação curta. Status inicial AGENDADA. |
| RF03 | Pesquisa por nome (parcial, inclusive nome social), setor, tipo, data e status; prioritários primeiro no mesmo horário. |
| RF04 | Edição, cancelamento e exclusão respeitando o ciclo de vida. |
| RF05 | Entrada com entrega de cartão disponível; saída com confirmação de devolução. |
| RF06 | Cartões de acesso: cadastrar, listar, editar, inativar; status DISPONIVEL, EM_USO, EXTRAVIADO, INATIVO. |
| RF07 | Catraca simulada: registrar passagem por cartão num ponto de acesso, liberando ou negando; toda tentativa é gravada. |
| RF08 | Rastreamento: trajeto de uma visita e lista de presentes com último local (evacuação). |
| RF09 | Painel: visitas do dia, presentes, encerradas do dia (obrigatórios); veículos no pátio, cartões pendentes, acessos negados hoje (complementares). |
| RF10 | Aviso de privacidade fixo na interface. |

## Requisitos não funcionais
- RNF01: responsivo de 360 px a desktop; tabelas viram cartões abaixo de 640 px.
- RNF02: SQLite persistente.
- RNF03: Windows/PowerShell, Python 3.11+, Node 18+.
- RNF04: nenhum dado real, credencial ou segredo no repositório.
- RNF05: "hoje" no fuso America/Cuiaba.
- RNF06: documento completo nunca em listagens (mascarado `DOC-••01`).
- RNF07: passagens imutáveis.

## Regras de negócio

### Tipos de visita
- **RN01** — nome obrigatório e único (3–60).
- **RN02** — visita só é criada com tipo ativo (422).
- **RN03** — `exige_documento` → documento obrigatório (422).
- **RN04** — `setores_permitidos` não vazio → setor deve pertencer à lista (422).
- **RN04a** — `permite_veiculo = false` → placa não aceita (422).
- **RN04b** — excluir tipo com visitas → 409 (desativar).

### Visitas
- **RN05** — ciclo `AGENDADA → PRESENTE → ENCERRADA` e `AGENDADA → CANCELADA`; outras transições → 409.
- **RN06** — PUT proibido em ENCERRADA/CANCELADA (409); o PUT nunca altera status, horários nem cartão.
- **RN07** — exclusão só em AGENDADA ou CANCELADA; PRESENTE/ENCERRADA → 409.
- **RN08** — `nome_civil` obrigatório (3–120); `nome_social`, quando preenchido, é o nome exibido.
- **RN09** — `documento_mascarado` nas listagens; completo só no detalhe.
- **RN10** — `observacao` com no máximo 100 caracteres, com aviso de uso na tela.
- **RN11** — placa normalizada e validada por `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`.
- **RN12** — `vaga_reservada` só com placa.

### Entrada, saída e cartões
- **RN13** — entrada só em AGENDADA e com `data_visita = hoje` (409).
- **RN14** — entrada exige cartão DISPONIVEL (409); ele passa a EM_USO.
- **RN15** — placa já em visita PRESENTE → 409.
- **RN16** — saída só em PRESENTE (409); exige `cartao_devolvido`.
- **RN17** — devolvido → cartão DISPONIVEL; não devolvido → EXTRAVIADO e `cartao_devolvido = false`.
- **RN18** — cartão sem dados pessoais; proibido trocá-lo pelo documento.
- **RN19** — cartão EM_USO não é editado nem inativado (409); com histórico, não é excluído (409).
- **RN20** — `codigo` e `codigo_leitura` únicos.

### Catraca e rastreamento
- **RN21** — toda leitura gera Passagem LIBERADO/NEGADO, com motivo quando negada.
- **RN22** — negar se: código desconhecido; cartão não EM_USO; sem visita PRESENTE; ponto inativo; setor do ponto ≠ setor da visita.
- **RN23** — ponto com `setor = NULL` é área comum.
- **RN24** — último local = última passagem LIBERADA de ENTRADA; sem passagens, "Recepção".
- **RN25** — rastreamento por pontos, nunca contínuo; trajetos só em consulta específica.
- **RN26** — passagens imutáveis; retenção segue o tipo de visita.

## Critérios de aceite
- **CA1 — Registro e persistência.**
  - Visita válida aparece AGENDADA e continua lá após reiniciar a API.
  - Tipo inativo, setor não permitido, documento ausente quando exigido ou placa em tipo sem veículo → 422 com mensagem na tela.
- **CA2 — Entrada, saída e cartão.**
  - Entrada com cartão disponível → PRESENTE e cartão EM_USO.
  - Cartão em uso, data diferente de hoje ou placa já no pátio → 409.
  - Saída com devolução libera o cartão; sem devolução → EXTRAVIADO e "cartões pendentes" +1.
  - PRESENTE/ENCERRADA não podem ser excluídas (409).
- **CA3 — Painel, pesquisa e rastreamento.**
  - Indicadores obrigatórios mudam após criar, cancelar, entrada, saída e exclusão.
  - A pesquisa por nome (civil ou social), setor, tipo e data retorna só os correspondentes.
  - Leitor de outro setor → NEGADO gravado com motivo; passagem permitida atualiza o último local.
