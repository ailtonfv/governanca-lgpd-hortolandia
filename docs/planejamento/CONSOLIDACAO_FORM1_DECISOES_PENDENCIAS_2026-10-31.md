# Consolidação do FORM 1 — decisões e pendências

**Incremento:** 8R

**Data de referência:** 31/10/2026

**Situação:** consolidação documental; não autoriza implementação, alteração de contrato, aprovação da matriz ou liberação da submissão

## 1. Objetivo e referências

Este documento reúne decisões comunicadas, propostas de evolução e pendências do FORM 1 Integral sem reproduzir as especificações completas. Quando houver detalhe técnico ou fonte declarativa própria, prevalece o documento relacionado.

Referências principais:

- [Contrato candidato do FORM 1 Integral — REV13](../arquitetura/CONTRATO_FORM1_INTEGRAL_REV13_CANDIDATO.md);
- [Matriz de obrigatoriedade dos 128 identificadores](MATRIZ_CAMPOS_FORM1_REV13.md);
- [Auditoria técnica da matriz — Incremento 7](AUDITORIA_MATRIZ_F1_REV13_INCREMENTO_7.md);
- [Especificação da futura submissão](ESPECIFICACAO_SUBMISSAO_FORM1_INTEGRAL.md);
- [Especificação do histórico de quantidades de registros — Incremento 8Q](ESPECIFICACAO_HISTORICO_REGISTROS_FORM1.md);
- [README — estado executável e histórico dos incrementos](../../README.md).

O contrato nuclear 2 permanece separado e inalterado. A infraestrutura técnica de snapshot do contrato candidato 3 existe, mas não representa submissão e permanece sem rota ou ação para o usuário.

## 2. Quadro consolidado

| Assunto | Situação | Documento ou campo relacionado | Impacto técnico conhecido | Próxima providência recomendada |
|---|---|---|---|---|
| Unidade receptora | Diretriz conceitual aprovada; não implementada | REV13 `2.3`; item 2.3 deste documento | Substituir texto livre por catálogo filtrado pela Secretaria; preservar separação entre recepção e execução; compatibilizar rascunhos | Identificar fonte, códigos, vigência e responsável pelo catálogo oficial antes de alterar interface ou contrato |
| Atendimentos, registros e ocorrências | Conceitos aprovados e ajuda contextual implementada | REV13 `2.8`, `2.9`, `2.10`; README, Incremento 8J | Manter três métricas semanticamente distintas; não somar nem converter automaticamente | Validar institucionalmente os exemplos e manter a distinção em futuras telas e relatórios |
| Histórico de quantidades de registros | Diretriz conceitual aprovada; especificada; não implementada | REV13 `2.9`, `2.9.1`; especificação 8Q | Exige tipos versionados, medições históricas, correção auditada e compatibilidade com faixas legadas | Decidir catálogo, competências, fontes, contrato futuro e matriz antes de escolher a persistência |
| Redação de origem dos dados | Implementada na apresentação, sem alterar catálogo ou armazenamento | REV13 `6.1.1`; README, Incremento 8P | A interface apresenta pergunta e orientação mais claras, mantendo o identificador e resposta textual existentes | Submeter a redação à aprovação funcional formal |
| Catálogo de origens dos dados | Proposta para avaliação; não implementada | REV13 `6.1.1`; seção 4 deste documento | Seleção múltipla, possíveis complementos catalogados, compatibilidade com rascunhos e nova versão contratual | Validar alternativas e semântica; decidir complementos e estratégia de migração sem conversão automática |
| Linguagem de compartilhamentos | Proposta para avaliação; não implementada | Campos de compartilhamento do Integral; contrato nuclear 2 | Rótulos visíveis podem evoluir, mas códigos e snapshots não podem ser reinterpretados | Mapear separadamente catálogos dos contratos 2 e 3 e aprovar glossário e ajuda contextual |
| Identidade principal pela matrícula | Decisão institucional comunicada; apresentação já usa matrícula e nome fictícios | Campos `0.1`–`0.3`; contrato de identidade; README, Incrementos 8G e 8I | Integração real depende de fonte institucional autenticada; a PoC não improvisa cadastro funcional | Formalizar fonte e atributos mínimos com a T.I. antes de autenticação real |
| Cargo/função `0.2` | Decisão institucional comunicada; matriz/contrato ainda não ajustados | `0.2`; matriz REV13 | Deve deixar de bloquear a submissão; poderá ser facultativo ou automático quando confiável | Formalizar a decisão e versionar matriz/contrato antes de alterar a pré-validação |
| E-mail institucional `0.3` | Decisão institucional comunicada; matriz/contrato ainda não ajustados | `0.3`; matriz REV13 | Deve ser facultativo e não bloqueante; não admite preenchimento identitário improvisado | Formalizar a decisão e versionar matriz/contrato antes de alterar a pré-validação |
| Trabalho factual do ARP | Implementado para rascunho e pré-validação; conclusão formal ainda não existe | Atribuição do ARP; 14 blocos; especificação de submissão | ARP autorizado preenche, salva e revisa; nenhuma ação atual declara conclusão ou encaminhamento | Definir o ato de conclusão do ARP e seus estados, autorizações, evento e efeitos |
| Conferência pelo APA | Aprovada conceitualmente; não implementada como etapa formal | Fluxo ARP → APA → T.I. | Exige ato distinto de preenchimento e encaminhamento, preservando autoria e segregação | Especificar critérios de conferência, devolução ao ARP e idempotência |
| Observações da chefia sem veto | Decisão institucional comunicada; não implementada | Futuro fluxo institucional | Exige registro de observação sem transição impeditiva ou poder implícito de aprovação | Definir quem pode observar, momento, visibilidade e forma de auditoria |
| Encaminhamento institucional à T.I. | Destinatário conceitualmente definido; não implementado | Futuro fluxo ARP → APA → T.I. | Requer destinatário institucional, evento, estado e fila; recebimento não equivale a validação jurídica | Especificar competência, recebimento, devolução e limites da atuação da T.I. |
| Validação jurídica e FORM 2 | Dependente de decisão institucional | Diretriz conceitual dos FORMs 1–4 | T.I. receber o FORM 1 não atribui automaticamente toda a validação jurídica nem define responsáveis do FORM 2 | Definir atores e competências antes da integração dos FORMs 2–4 |
| Auditoria institucional da matriz | Prioridade futura; auditoria técnica anterior concluída | 128 IDs; matriz REV13; relatório do Incremento 7 | Novas decisões sobre `0.2` e `0.3` e demais exceções exigem relatório institucional, sem alterar a fonte por inferência | Revisar os 128 campos e produzir relatório de exceções para aprovação humana |
| Navegação e painéis | Implementados e testados | README, Incrementos 8N–8P | Componentes atuais distinguem consulta, providências, posição, visita, respostas, salvamento e pendências | Manter regressão; reutilizar o padrão apenas após adaptar cada futuro FORM às suas permissões e estrutura |
| Submissão integral | Infraestrutura técnica preparada; funcionalidade bloqueada | Especificação de submissão; Incremento 8C | Snapshot técnico imutável existe sem rota, botão ou transição; bloqueios institucionais permanecem | Somente implementar o fluxo após auditoria da matriz e especificação ARP → APA → T.I. |

## 3. Questões do Bloco 2

### 3.1 Campo 2.3 — unidade receptora

**Decisão ou proposta.** A pergunta deverá ser simplificada futuramente para: “Qual unidade ou setor da Secretaria recebe inicialmente a demanda?”. A seleção deverá priorizar catálogo oficial de unidades, setores e equipamentos, limitado à Secretaria informada no item `2.2`.

**Situação.** Diretriz conceitual aprovada, ainda não implementada. Hoje a REV13 mantém uma resposta curta e não existe, no escopo confirmado desta PoC, fonte oficial cuja cobertura, códigos, vigência e curadoria tenham sido validados.

**Distinção obrigatória.** Unidade receptora identifica quem recebe inicialmente a demanda; unidade executora identifica quem realiza o trabalho. Uma não pode ser inferida da outra.

**Impacto e providência.** A futura mudança envolve catálogo, filtro institucional, compatibilidade com texto legado e versão de contrato. Primeiro deve ser identificada a fonte oficial e sua autoridade de manutenção; nenhuma unidade será inventada.

### 3.2 Campos 2.8, 2.9 e 2.10

Os conceitos permanecem independentes:

- **Atendimentos (`2.8`):** fluxo de atendimentos realizados em determinado período;
- **Registros (`2.9`):** estoque de registros cadastrais ou administrativos existente em determinada data;
- **Ocorrências (`2.10`):** eventos administrativos de determinada natureza durante um período; não são, por esse nome, incidentes de segurança.

A ajuda contextual com essa distinção já está implementada. Os exemplos seguintes são exclusivamente fictícios e não formam catálogo nem massa de demonstração:

| Objeto fictício | Atendimentos | Registros | Ocorrências |
|---|---|---|---|
| Escola fundamental fictícia | Solicitações atendidas no mês | Matrículas ativas na data de referência | Transferências processadas no período |
| Escola de judô fictícia | Atendimentos de inscrição no período | Inscrições ativas na data de referência | Trocas de turma registradas no período |
| UBS fictícia | Consultas ou acolhimentos realizados no período | Cadastros individuais existentes na data de referência | Encaminhamentos administrativos no período |

Não se deve somar essas grandezas nem presumir equivalência entre quantidade de registros e quantidade de pessoas.

### 3.3 Evolução dos itens 2.9 e 2.9.1

**Diretriz conceitual aprovada:** `tipo padronizado de registro → quantidade → data de referência → fonte`.

Um serviço poderá possuir vários tipos, sem soma automática de matrículas, prontuários, inscrições ou processos. Medições anteriores permanecem preservadas; nova medição temporal e correção auditada são atos distintos.

O modelo, a compatibilidade e os riscos estão na [especificação do Incremento 8Q](ESPECIFICACAO_HISTORICO_REGISTROS_FORM1.md). A evolução continua dependente de catálogo, competências, fontes aceitas, matriz e decisão de versão contratual. Nenhum modelo físico ou migração está autorizado.

## 4. Campo 6.1.1 — origem dos dados

A interface já apresenta a redação: **“Qual é a origem dos dados pessoais utilizados neste fluxo?”**, acompanhada de orientação para não registrar nomes, CPF ou identificadores de cidadãos. O identificador, a matriz, o catálogo REV13 e o armazenamento existentes não foram alterados. A redação ainda deve receber aprovação funcional formal.

Propõe-se avaliar a substituição futura da resposta livre por seleção múltipla padronizada:

1. Diretamente do titular;
2. Responsável legal ou representante autorizado;
3. Outra unidade da mesma Secretaria;
4. Outra Secretaria da Prefeitura;
5. Órgão ou entidade pública fora da Prefeitura;
6. Empresa contratada, OSC ou entidade parceira;
7. Sistema ou base de dados institucional;
8. Sistema ou base de dados de terceiro;
9. Outra origem;
10. A confirmar.

**Situação:** proposta pendente de aprovação funcional. Não é catálogo oficial e não altera a aplicação.

Antes de implementar, deverão ser decididos: códigos canônicos; exclusividades; complemento de “Outra origem”; identificação complementar por catálogo; compatibilidade com rascunhos e snapshots; e versão de contrato. A resposta continuará representando categorias ou fontes institucionais, nunca pessoas identificadas.

## 5. Linguagem de compartilhamentos

| Expressão atual | Expressão recomendada | Situação |
|---|---|---|
| Outro órgão ou unidade municipal | Outra unidade ou Secretaria da Prefeitura | Proposta para avaliação |
| Órgão público externo | Órgão ou entidade pública fora da Prefeitura | Proposta para avaliação |
| Operador contratado | Empresa ou entidade contratada | Proposta para avaliação |

Os rótulos, códigos persistidos e contratos não foram modificados. A contratação, por si só, não determina a condição jurídica de Operador LGPD; essa qualificação depende do papel efetivamente exercido no tratamento.

A revisão futura deverá mapear separadamente os campos do FORM 1 Integral e o catálogo do instrumento sintético do contrato nuclear 2. Mudança de texto visível não poderá reinterpretar snapshots antigos. A ajuda contextual deverá distinguir unidades da própria Prefeitura, órgãos ou entidades públicas externos e terceiros privados, com exemplos fictícios.

## 6. Governança do FORM 1

### 6.1 Decisões comunicadas

- matrícula funcional como identificação principal do agente;
- cargo/função (`0.2`) não bloqueante, preferencialmente facultativo ou automático quando houver fonte confiável;
- e-mail institucional (`0.3`) facultativo e não bloqueante;
- ARP responsável pelo levantamento factual;
- APA responsável pela conferência e pelo encaminhamento institucional;
- chefia autorizada a examinar e registrar observações, sem veto;
- T.I. como destinatária institucional do encaminhamento;
- recebimento pela T.I. sem atribuição automática de toda a validação jurídica do FORM 2.

Essas decisões foram comunicadas para consolidação, mas os efeitos que alteram matriz, estados, competências ou permissões ainda precisam ser formalizados e versionados antes de se tornarem executáveis.

### 6.2 Etapas que não devem ser confundidas

1. **Preenchimento factual:** o ARP descreve o tratamento e preserva o rascunho.
2. **Conclusão do trabalho do ARP:** futuro ato explícito; não equivale a submissão ou aprovação.
3. **Conferência do APA:** futura verificação institucional, com possibilidade de retorno conforme regra ainda a especificar.
4. **Observação da chefia:** manifestação registrada sem veto, quando autorizada.
5. **Encaminhamento à T.I.:** ato institucional rastreável e distinto do recebimento.
6. **Análises posteriores:** competências do FORM 2 e demais validações serão definidas separadamente.

Não serão criadas permissões, transições ou competências jurídicas por analogia. A especificação técnica do fluxo deverá indicar atores, autorização, estados, eventos, idempotência, concorrência, devolução e rollback.

## 7. Matriz de obrigatoriedade

A [matriz REV13](MATRIZ_CAMPOS_FORM1_REV13.md) permanece a fonte declarativa única. O [Incremento 7](AUDITORIA_MATRIZ_F1_REV13_INCREMENTO_7.md) já comprovou cobertura técnica dos 128 identificadores e registrou inconsistências conhecidas. Isso não substitui a auditoria institucional agora priorizada.

A próxima auditoria deverá:

- verificar campo a campo classificação, visibilidade e condição;
- confrontar as decisões comunicadas sobre `0.2` e `0.3`;
- manter rascunhos incompletos;
- preservar obrigatoriedade condicional;
- tratar `A confirmar` como estado próprio, sem convertê-lo em ausência ou resposta conclusiva;
- preservar IDs, versões e conteúdo histórico;
- apresentar somente exceções e decisões necessárias, sem aprovar alterações automaticamente.

O resultado deverá ser um relatório para decisão institucional. Até sua aprovação, a pré-validação continua consultiva e a submissão integral permanece bloqueada.

## 8. Interface e painéis

A verificação do estado atual encontrou os seguintes itens já documentados, implementados e testados:

- régua horizontal com acesso aos 14 blocos, foco no destino e aviso de alterações não salvas — Incremento 8P;
- painel inicial separado em **Mapeamentos disponíveis para você** e **O que precisa da sua atenção** — Incrementos 8N e 8O;
- indicadores independentes de jornada e pendências — Incrementos 8K e 8L;
- distinção entre posição atual, visita, evento de salvamento, respostas salvas e ausência consultiva de pendências — Incrementos 8K e 8P;
- ações de salvar e avançar ou permanecer, inclusive entre etapas — Incrementos 8J a 8M;
- identificação do Registro LGPD, objeto, APA de abertura, APA em exercício e ARP atual — Incrementos 8I, 8N e 8O.

Não foi identificada lacuna remanescente dentro dessa lista que justifique reabrir os incrementos concluídos. Permanecem como evoluções separadas as pendências de UX já registradas no README, entre elas catálogo da unidade receptora e linguagem dos compartilhamentos.

A régua horizontal é referência reutilizável para os FORMs 2, 3 e 4, mas não deve ser copiada sem adaptação à quantidade de blocos, estados, permissões e responsabilidades de cada instrumento.

## 9. Roteiro mínimo ordenado

1. **Auditar institucionalmente a matriz REV13** e produzir relatório de exceções para aprovação.
2. **Formalizar tecnicamente o fluxo ARP → APA → T.I.**, incluindo conclusão, conferência, observações, encaminhamento, devolução e limites de competência.
3. **Implementar controladamente a submissão do FORM 1 Integral**, reutilizando a infraestrutura técnica do Incremento 8C somente após o fechamento dos bloqueios.
4. **Preparar a integração dos FORMs 2, 3 e 4**, com atores e competências definidos e sem presumir validação jurídica pela T.I.
5. **Executar evoluções posteriores não bloqueantes**, como catálogos institucionais, histórico de medições e ajustes visuais aprovados.

## 10. Conclusão

O FORM 1 Integral possui os 14 blocos, rascunho, retomada, pré-validação consultiva, navegação e infraestrutura técnica de snapshot. A principal lacuna não é de preenchimento visual: é a formalização institucional da matriz e do percurso posterior ao trabalho factual do ARP.

Este documento não aprova a matriz, não libera submissão e não autoriza alterações na aplicação. O próximo incremento recomendado é a **auditoria institucional da matriz REV13 com relatório de exceções**, seguida da especificação do fluxo ARP → APA → T.I.
