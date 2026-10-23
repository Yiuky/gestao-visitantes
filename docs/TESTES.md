# TESTES — Gestão de visitantes

> Estratégia e casos por sprint. Os **resultados reais** ficam em `docs/EXECUCAO.md`; aqui só o planejado.

## Estratégia
- **Automatizados (pytest):** API, regras de negócio e indicadores, com banco SQLite temporário por teste e "hoje" fixado por fixture (ex.: `2026-10-23`).
- **Manuais (navegador):** roteiro CA1–CA3, em desktop e em 360 px (DevTools).
- **Integração:** cada ação da tela conferida na API e no painel.
- **Persistência:** criar dados, reiniciar a API e confirmar que continuam lá.
- **Segurança do repositório:** `git ls-files` sem `.db` nem `.env`.
- Nunca registrar "passou" sem a saída do comando. Usar **NÃO TESTADO** quando for o caso.

## Fixtures previstas (`tests/conftest.py`)
- `client`: TestClient com `get_db` sobrescrito para banco temporário.
- `hoje`: data fixa injetada no lugar do relógio.
- Fábricas: `criar_tipo(**kw)`, `criar_cartao(**kw)`, `criar_visita(**kw)`.

## Casos — S1 (API núcleo)

| # | Caso | Esperado |
|---|---|---|
| T01 | Criar tipo válido | 201 |
| T02 | Criar tipo com nome duplicado | 409 (ADR-014) |
| T03 | Excluir tipo com visitas | 409 |
| T04 | Criar visita com tipo inativo | 422 |
| T05 | Setor fora de `setores_permitidos` | 422 |
| T06 | Sem documento em tipo que exige | 422 |
| T07 | Placa em tipo sem veículo | 422 |
| T08 | Placa inválida (`AB12345`) | 422 |
| T09 | `vaga_reservada` sem placa | 422 |
| T10 | Listar com banco vazio | 200 `[]` |
| T11 | Buscar por parte do nome social | só a visita correspondente |
| T12 | Listagem não expõe documento completo | campo ausente; `documento_mascarado` presente |
| T13 | Entrada OK | PRESENTE; cartão EM_USO |
| T14 | Entrada com cartão EM_USO | 409 |
| T15 | Entrada com `data_visita` ≠ hoje | 409 |
| T16 | Entrada com placa já no pátio | 409 |
| T17 | Saída com devolução | ENCERRADA; cartão DISPONIVEL |
| T18 | Saída sem devolução | ENCERRADA; cartão EXTRAVIADO; `cartao_devolvido = false` |
| T19 | Saída de visita AGENDADA | 409 |
| T20 | Excluir visita PRESENTE | 409 |
| T21 | Excluir visita ENCERRADA | 409 |
| T22 | Excluir visita AGENDADA | 204; depois GET → 404 |
| T23 | Cancelar visita PRESENTE | 409 |
| T24 | Editar visita ENCERRADA | 409 |
| T25 | PUT tentando mudar status | status inalterado |
| T26 | Inativar cartão EM_USO | 409 |
| T27 | Excluir cartão com histórico | 409 |
| T28 | Ordenação da lista | data, horário e prioritários primeiro no mesmo horário |
| T29 | PUT de cartão com `status = EM_USO` | 422 (ADR-014) |

## Casos — S3 (painel)

| # | Caso | Esperado |
|---|---|---|
| T30 | Painel com banco vazio | todos os indicadores = 0 |
| T31 | Criar visita de hoje | visitas_do_dia +1 |
| T32 | Criar visita de amanhã | visitas_do_dia inalterado |
| T33 | Cancelar visita de hoje | visitas_do_dia −1 |
| T34 | Entrada | presentes +1 |
| T35 | Entrada com placa | veiculos_no_patio +1 |
| T36 | Saída com devolução | presentes −1; encerradas_do_dia +1 |
| T37 | Saída sem devolução | cartoes_pendentes +1 |
| T38 | `/api/presentes` | lista só PRESENTE, com último local "Recepção" sem passagens |
| T39 | Excluir visita AGENDADA de hoje | visitas_do_dia −1 |

## Casos — S4 (catraca e rastreamento)

| # | Caso | Esperado |
|---|---|---|
| T40 | Código de leitura desconhecido | NEGADO gravado; `cartao_id` nulo |
| T41 | Cartão DISPONIVEL (sem visita) | NEGADO |
| T42 | Cartão de visita já encerrada | NEGADO |
| T43 | Ponto inativo | NEGADO |
| T44 | Leitor de setor diferente do destino | NEGADO, motivo "área não autorizada" |
| T45 | Catraca da portaria (área comum) | LIBERADO |
| T46 | Leitor do setor de destino | LIBERADO; último local atualizado |
| T47 | Trajeto da visita | passagens em ordem cronológica |
| T48 | PUT ou DELETE em passagem | 405 |
| T49 | Passagem negada hoje | acessos_negados_hoje +1 |

## Docker (ADR-015)
| # | Caso | Esperado |
|---|---|---|
| D01 | `docker compose build` | imagens api e web geradas |
| D02 | `docker compose --profile test run --rm tests` | suíte pytest verde dentro do contêiner |
| D03 | `docker compose up -d` + `GET /api/health` via web (:8080) | 200 |
| D04 | `docker compose restart api` | dados continuam (volume) |

## Testes de botões (E2E via MCP Claude in Chrome)
Cada botão da interface é acionado no navegador real e o efeito conferido na tela e na API. Resultados em `docs/EXECUCAO.md` e no mapa `docs/EVIDENCIAS.md`.

## Roteiro manual (S2, S3 e S5)

| # | Passo | Esperado | Resultado |
|---|---|---|---|
| M01 | Criar tipo "Reunião técnica" com documento obrigatório | Aparece na lista | ✅ S2 (B16) |
| M02 | Registrar visita sem documento nesse tipo | Mensagem de erro visível | ✅ S2 (B02, B03) |
| M03 | Registrar visita válida com nome social | Lista mostra o nome social | ✅ S2 (B04, B11) |
| M04 | Reiniciar a API e recarregar | Visita continua | ✅ S3 (P06) |
| M05 | Dar entrada escolhendo cartão | Status PRESENTE; painel atualiza | ✅ S2 (B07) e S3 (P02) |
| M06 | Tentar dar entrada noutra visita com o mesmo cartão | Cartão não aparece como disponível ou erro 409 visível | ✅ S2 (B07: modal só lista DISPONÍVEIS) |
| M07 | Tentar excluir visita PRESENTE | Ação indisponível ou erro 409 | ✅ S2 (B06: ação indisponível) |
| M08 | Simular catraca em leitor de outro setor | NEGADO em destaque | ⬜ |
| M09 | Simular leitor do setor de destino | LIBERADO; último local no painel | ⬜ |
| M10 | Saída sem devolução | Cartões pendentes +1 | ✅ S3 (P02) |
| M11 | Imprimir lista de evacuação | Prévia só com a lista | ⬜ |
| M12 | Repetir M03–M05 em 360 px | Layout legível, sem rolagem horizontal | ✅ S2 (B29, iframe 360 px) |
