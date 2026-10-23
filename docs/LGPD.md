# LGPD, legislação e segurança — Gestão de visitantes

> **Ressalva.** Este documento é um mapeamento de requisitos feito pelo desenvolvedor para um laboratório com dados fictícios. **Não é parecer jurídico.** Num sistema real do órgão, a base legal, os campos, os prazos de retenção e a necessidade de Relatório de Impacto (RIPD) seriam definidos pelo encarregado de dados e pela assessoria jurídica.

## 1. Finalidade declarada
Segurança das pessoas e do patrimônio, controle de acesso às dependências e registro de atendimento. Todo campo coletado deve servir a essa finalidade.

## 2. Base legal proposta (a validar)
Para o poder público, as bases mais usadas são as do art. 7º, II e III, da LGPD (obrigação legal ou regulatória e execução de políticas públicas), observado o art. 23. O consentimento não é a base adequada quando o cadastro é condição de entrada.

## 3. Normas consideradas

| Norma | Exigência | Como o sistema atende |
|---|---|---|
| Lei 5.553/1968, art. 2º §2º | Documento anotado e devolvido imediatamente | Sem campo "documento retido"; cartão nunca trocado pelo documento |
| LGPD, arts. 6º, 7º e 23 | Finalidade, necessidade, transparência | Coleta mínima; aviso de privacidade na interface |
| LGPD, art. 11 | Dado sensível exige base específica | Prioridade sem motivo; vaga reservada genérica; sem biometria |
| LGPD, art. 14 | Crianças e adolescentes | Evolução: responsável legal por tipo de visita |
| LGPD, arts. 46 e 48 | Segurança e incidentes | Mascaramento, registros que não se apagam; produção: login, HTTPS, criptografia, backup, plano de incidentes |
| Decreto MT 1.427/2025 | LGPD no Executivo estadual: encarregado, comitê, RIPD | Processo a ser mapeado pelo encarregado |
| Decreto MT 1.428/2025 (PSI-MT) | Segurança da informação, backup | Requisito de produção |
| Decreto MT 854/2021 | Campo nome social nos sistemas | `nome_social` exibido quando preenchido |
| Lei 10.048/2000 (red. Lei 14.626/2023) | Atendimento prioritário | Marcador sim/não, sem motivo |
| Lei 10.741/2003, art. 41; Lei 13.146/2015, art. 47; Res. Contran 965/2022 | Vagas reservadas com credencial | `vaga_reservada` genérico |
| Lei 12.527/2011 (LAI) | Registros podem ser pedidos | Nomes neutros; sem assunto em texto livre |

## 4. Inventário de dados

| Dado | Finalidade | Sensível? | Exibição | Observação |
|---|---|---|---|---|
| Nome civil | Identificar quem está no prédio | Não | Interna | Substituído pelo nome social na exibição |
| Nome social | Tratamento digno (Decreto 854/2021) | Não | Sim | Opcional |
| Documento (fictício) | Conferência e apuração de incidentes | Não | Mascarado | Completo só no detalhe |
| Tipo, setor, data, horários | Controle de acesso e evacuação | Não | Sim | |
| Atendimento prioritário | Ordenar a fila | Não (sem motivo) | Sim | Motivo **não** registrado |
| Placa, descrição do veículo | Controle do pátio | Não | Sim | Mesma retenção da visita |
| Vaga reservada | Controle de vagas | Não (genérica) | Sim | Não distingue PcD de idoso |
| Observação (≤100) | Nota operacional | Risco | Sim | Aviso: sem motivo, saúde ou opinião |
| Cartão vinculado | Credencial de acesso | Não | Sim | Cartão sem dados pessoais |
| Passagens | Rastreamento por pontos e evacuação | Não | Consulta específica | Imutáveis |

**Não coletar:** foto, biometria, cópia do documento, CPF real, endereço, telefone, motivo da prioridade, assunto da visita.

## 5. Medidas de segurança

**No MVP**
- Dados 100% fictícios; `.db` e `.env` fora do Git.
- Documento mascarado nas listagens.
- Registros de presença (PRESENTE e ENCERRADA) não podem ser excluídos.
- Passagens somente inserção.
- Aviso de privacidade fixo na interface.

**Requisitos de produção (fora do MVP)**
- Login com perfis (recepção, gestor, segurança) e trilha de auditoria.
- HTTPS, banco criptografado, backup e recuperação.
- Anonimização ao fim de `prazo_retencao_dias`.
- Canal de direitos do titular (art. 18) via encarregado.
- Plano de resposta a incidentes (art. 48).

## 6. Biometria
Avaliada e **não adotada** no MVP (ADR-011): dado sensível, sem base legal específica para visitantes, e existe meio menos invasivo (cartão). Prevista no backlog como **Épico B, bloqueado** até cumprir os pré-requisitos listados em `docs/BACKLOG.md`.

## 7. Pendências com o encarregado (num cenário real)
- [ ] Confirmar a base legal formal.
- [ ] Definir prazos de retenção por tipo de visita.
- [ ] Avaliar a necessidade de RIPD (obrigatória antes de qualquer biometria).
- [ ] Aprovar o texto do aviso de privacidade.
- [ ] Definir perfis de acesso aos trajetos.

## 8. Referências
- Lei 5.553/1968 — https://planalto.gov.br/ccivil_03/leis/L5553.htm
- LGPD — https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
- Guia ANPD para o Poder Público — https://lgpd.prefeitura.rio/wp-content/uploads/sites/102/2023/03/guia-poder-publico-anpd-versao-final.pdf
- Decretos MT 1.427/2025 e 1.428/2025 (citados no Decreto 1.691/2025) — https://www.legisweb.com.br/legislacao/?id=484322
- Decreto MT 854/2021 — https://www.saude.mt.gov.br/storage/old/files/854-[18680-050721-SES-MT].pdf
- Lei 10.048/2000 — https://legis.senado.leg.br/norma/551924/publicacao/34619784
- Estatuto da Pessoa Idosa, art. 41 — https://www.admdireito.com.br/legislacao/art/lei_00107412003-41
- Vagas reservadas (Contran 965/2022) — https://www.portaldotransito.com.br/?p=36577
