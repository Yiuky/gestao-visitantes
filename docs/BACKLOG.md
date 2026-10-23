# BACKLOG — Gestão de visitantes

> Status: ⬜ pendente · 🔄 em andamento · ✅ concluído · ⛔ bloqueado
> **Uma sprint por rodada.** O Claude Code atualiza o status ao fim de cada sprint, junto com `docs/EXECUCAO.md`.
> Prompts completos de cada sprint: `HANDOFF_CLAUDE_CODE.md`, seção 11.

## Sprints do encontro

| Sprint | Status | Objetivo | Gate (condição para avançar) |
|---|---|---|---|
| M0 | ✅ | Documentação de requisitos, arquitetura e plano | Kit de documentos na pasta |
| S0 | ✅ | Conferir estrutura e docs, verificar ferramentas, iniciar Git | Ferramentas verificadas; Git inicializado; 1º commit |
| S1 | ✅ | API núcleo: tipos, cartões, visitas, entrada/saída/cancelar (RN01–RN20) | `pytest -q` verde; persistência após reinício |
| S2 | ✅ | Frontend: Visitas, Tipos, Cartões, rodapé de privacidade | `npm run build` ok; CA1 e CA2 pela tela; 360 px ok |
| S3 | ✅ | Painel: 6 indicadores por COUNT, lista de presentes, impressão | Testes de indicadores verdes; CA3 (painel e pesquisa) |
| S4 | ✅ | Extensão: catraca simulada, passagens, trajeto, último local (RN21–RN26) | Testes de catraca verdes; CA3 (rastreamento) |
| S4b | ✅ | Docker: imagens api/web, compose, testes no contêiner (ADR-015) | `docker compose` build/test/up ok; persistência por volume |
| S5 | ✅ | Homologação, README, capturas, reflexão, GitHub (público, ADR-018) | Suíte verde; README completo; push autorizado |

**Regra de tempo:** se a S3 terminar com pouco tempo de encontro, pule para a S5 e marque a S4 como ⬜ pendente no README.

### Itens por sprint

**S1**
- [x] Modelos e schemas (tipos_visita, cartoes_acesso, visitas)
- [x] `services/regras.py` com validações por tipo e transições
- [x] Routers de tipos, cartões e visitas; `/api/setores`; `/api/health`
- [x] `nome_exibido` e `documento_mascarado` no `VisitaResumo`
- [x] Testes de `docs/TESTES.md` (S1)
- [x] `backend/seed.py`

**S2**
- [x] Projeto Vite com proxy `/api`
- [x] Abas: Painel (provisório), Visitas, Tipos, Cartões
- [x] Formulário adaptado ao tipo; ações conforme status
- [x] Mensagens de erro da API e estado de lista vazia
- [x] Rodapé de privacidade; layout em cartões abaixo de 640 px
- [x] Testes de botões B01–B29 via MCP Claude in Chrome

**S3**
- [x] `/api/dashboard` e `/api/presentes`
- [x] Página Painel com indicadores e lista de evacuação imprimível
- [x] Recarregar indicadores após cada operação (e a cada 30 s)

**S4 (extensão)**
- [x] Modelos pontos_acesso (seed se vazio) e passagens (sem PUT/DELETE)
- [x] `POST /api/catraca/passagens` com RN22–RN23
- [x] Trajeto e último local; indicador de acessos negados
- [x] Página Catraca (simulador + trajeto)

**S4b (Docker)**
- [x] `backend/Dockerfile`, `frontend/Dockerfile` (nginx), `docker-compose.yml`, `.dockerignore`
- [x] Serviço `tests` (perfil `test`) com pytest
- [x] Volume nomeado para o SQLite

**S5**
- [x] Roteiro de homologação completo (E2E E01–E09 + segurança do repositório)
- [x] README com resultados reais, capturas, LGPD, limitações e reflexão
- [x] Revisão do diff; `git status` limpo
- [x] Push autorizado pelo usuário; repositório **público** (ADR-018)

## Épicos de evolução (fora do encontro)

### Épico A — Produção segura ⬜
- A1: login com perfis e trilha de auditoria (edições e consultas de trajeto)
- A2: HTTPS, banco criptografado, backup e recuperação (PSI-MT)
- A3: anonimização automática ao fim de `prazo_retencao_dias`
- A4: canal de direitos do titular (LGPD art. 18) e plano de incidentes (art. 48)

### Épico B — Biometria em pontos de acesso ⛔ BLOQUEADO
Não implementar nada deste épico enquanto todos os pré-requisitos não estiverem atendidos e registrados em ADR.

**Pré-requisitos (gate legal):**
- [ ] Base legal específica do art. 11 da LGPD definida pelo encarregado e pela assessoria jurídica
- [ ] RIPD aprovado, com necessidade e proporcionalidade demonstradas frente ao cartão
- [ ] Escopo restrito a áreas de segurança elevada; visitantes eventuais fora do público-alvo
- [ ] Alternativa sempre disponível (cartão), sem perda de acesso para quem recusar
- [ ] Nenhuma imagem armazenada; template criptografado em cofre separado
- [ ] Prazo de retenção e exclusão do template ao fim do vínculo
- [ ] Avaliação de vieses e taxas de erro do fornecedor

**Itens técnicos (após o gate):**
- B1: aceitar `BIOMETRIA` em `metodos_aceitos` e `credencial_tipo`
- B2: tabela `credenciais_biometricas` só com referências ao cofre
- B3: cadastro com aviso específico e revogação a qualquer tempo
- B4: testes garantindo que pontos biométricos aceitam cartão

### Épico C — Integração física e operação ⬜
- C1: catraca/RFID real via `POST /api/catraca/passagens`, com chave de equipamento
- C2: urna de recolhimento do cartão na saída
- C3: QR Code temporário com expiração diária
- C4: vagas com capacidade e mapa; saída do veículo separada
- C5: alerta de presentes após o expediente
- C6: responsável legal para menores; agendamento obrigatório por tipo
- C7: lista de restrição de acesso, só com base legal e procedimento formal
