# GOV_FORMS_01 — Matriz candidata de responsabilidades dos FORMs 1–4

**Produto A · versão documental 0.1 · 06/11/2026**  
**Situação: proposta para avaliação; não concede competência nem autoriza implementação.**

## 1. Alcance e leitura da matriz

Os quatro instrumentos pertencem ao mesmo Registro LGPD. Propõe-se manter o APA como **ponto focal administrativo durante todo o ciclo**, sem transferir para ele a análise especializada, a execução de todas as providências ou a decisão reservada à autoridade competente. Essa continuidade ampliada é candidata; a abertura e a conferência interna do FORM 1 já possuem regras próprias implementadas.

Este documento complementa o [fluxo candidato](GOV_FORMS_01_FLUXO_ENCAMINHAMENTOS_CANDIDATO.md) e a [estratégia de configuração](GOV_FORMS_01_CONFIGURACAO_VERSIONAMENTO_CANDIDATO.md). Não substitui SADs, contratos, matriz de obrigatoriedade ou atos municipais.

Legenda de evidência:

- **I — Implementado/documentado:** regra atual do FORM 1, confrontada com README, AGENTS e estruturas existentes; não significa nova aceitação visual ou institucional nesta tarefa.
- **D — Diretriz documental:** previsão de SAD ou Documento-Mestre; não equivale a competência legal confirmada nem a funcionalidade implementada.
- **C — Candidato:** proposta desta instrução, sujeita a aprovação.
- **V — Verificação/decisão pendente:** não habilitar o ato correspondente por inferência.

“Autoridade competente” é uma posição a identificar por objeto, matéria, unidade, alçada e ato vigente, **não um perfil universal que esta proposta cria**. A referência a uma unidade como destinatária também não autoriza todos os seus integrantes a consultar o conteúdo.

## 2. Fontes examinadas e localização

Raiz dos SADs e da Cartilha: `D:\Ailton\PMH\Cidades_Inteligentes\LGPD\Solution_Architecture_Document_(SAD)_Documento_de_Arquitetura_da_Solução`.

| Referência | Arquivo/versão efetivamente examinada | Seções relevantes e limite da evidência |
|---|---|---|
| Orientações atuais | [AGENTS.md](../../AGENTS.md) e [README.md](../../README.md), estado local de 06/11/2026 | Escopo autorizado; APA/ARP/SAA; conferência interna; continuidade do APA; integração futura dos instrumentos. Alterações locais preexistentes preservadas. |
| SAD 02 | `02_Requisitos_Funcionais/SAD_02_REQUISITOS_FUNCIONAIS_REV17.docx` | §5.4, RF-WFL: separação de estados, encaminhamentos, devoluções, responsabilidade e rastreabilidade. |
| SAD 03 | `03_Atores_Papeis_e_Permissoes/SAD_03_ATORES_PAPEIS_E_PERMISSOES_REV11.docx` | §§11.2–11.3, 12/12A/12B e 13: validação provisória na PoC, RACI versus permissão, escopo efetivo e segregação. |
| SAD 04 | `04_Workflow_e_Estados/SAD_04_WORKFLOW_E_ESTADOS_REV12.docx` | §12.2: dependências entre instrumentos, alternativas ainda sujeitas a validação; §12.3: próxima ação. |
| SAD 05 | `05_Modelo_de_Dados_e_Identificadores/SAD_05_MODELO_DE_DADOS_E_IDENTIFICADORES_REV11.docx` | Instrumento, versões, ações/providências, vínculos e histórico; §§7–8. |
| SAD 10 | `10_Decisoes_de_Arquitetura/SAD_10_DECISOES_DE_ARQUITETURA_REV16.docx` | DA-05/06, DA-22, DA-26/27; AB-05 sobre transições críticas do Comitê. DA-13 está substituída, não é a decisão vigente sobre o Comitê. |
| Documento-Mestre | `D:\Ailton\PMH\Cidades_Inteligentes\LGPD\curso_senac_lgpd\FORMS\DOCUMENTO_MESTRE_FORMS_LGPD_HORTOLANDIA_REV17.0_2026-09-23.docx` | FORM 2 completo; FORM 3, especialmente orientação de responsabilidade, 3.52, 3.57 e 3.61; FORM 4, especialmente 4.6–4.8 e 4.18–4.26. Não substitui a REV13 implementada do FORM 1. |
| Cartilha | `11_Cartilha_Apresentacoes/CARTILHA_LGPD_REV30_14_CONSOLIDADA_SAA_05-11-2026.docx` | §§3.1 e 11.4, orientações APA/ARP/SAA, DPO e referências municipais; capa indica versão para validação editorial. Referência conceitual, não ato de atribuição de competência. |
| Candidatos FORM 2 | [Matriz](FORM2_REV17_MATRIZ_CORRESPONDENCIA_CANDIDATA.md), [organização/contrato](FORM2_REV17_ORGANIZACAO_CONTRATO_CANDIDATO.md), [decisões](FORM2_REV17_DECISOES_PENDENTES.md), [incrementos](FORM2_REV17_INCREMENTOS_COMPLEXIDADE.md) | Quatro propostas preservadas. A matriz inventaria 245 identificadores; não autoriza implementar esses itens nem designar validadores. |
| Decisões FORM 1 | [Fluxo 8T](FLUXO_CONCLUSAO_FORM1_INTEGRAL_8T.md) e decisões consolidadas no README/AGENTS | Diferenciar conclusão institucional proposta do ciclo preparatório efetivamente implementado. Submissão institucional continua bloqueada. |

O índice local `INDICE_REVISOES_VIGENTES_2026-10-14_v2.docx` foi utilizado para localizar os SADs; sua data não certifica a inexistência de revisões ou atos posteriores. A verificação foi documental, sem consulta ou alteração de registros reais.

### 2.1. Atos municipais: o que foi e o que não foi confirmado

| Fonte | Evidência disponível | Consequência segura para esta proposta |
|---|---|---|
| Decreto 4.822/2021 | Referenciado na [página oficial LGPD](https://www.hortolandia.sp.gov.br/lgpd/) e na [notícia institucional sobre o Programa](https://acervo.hortolandia.sp.gov.br/noticias/item/23907-prefeitura-de-hortolandia-reforca-diretrizes-da-lei-geral-de-protecao-de-dados/23907-prefeitura-de-hortolandia-reforca-diretrizes-da-lei-geral-de-protecao-de-dados). | Há referência oficial à instituição do Comitê/Programa. Isso não prova alçada para cada ato dos FORMs. Texto consolidado e alterações devem compor o processo de aprovação da política. |
| Decreto 4.914/2021 | Cópia local em `documentos de apoio/decreto LGPD.pdf`: Diário Oficial, edição 1362, 19/11/2021, pp. 3–4. O arquivo não é a íntegra do Decreto 4.822. | Ato de designação não deve ser convertido em lista atual de permissões. Nenhum nome ou matrícula foi incorporado a estes produtos. |
| Decretos 5.200/2023 e 5.357/2024 | Referidos na Cartilha e/ou SAD 10. A DA-22 registra que o 5.357 acrescentou caráter permanente e atuação orientativa, consultiva e deliberativa ao Comitê; substitui a DA-13. Íntegra oficial consolidada dessas alterações **não verificada independentemente nesta tarefa**. | Preservar a DA-22 como decisão arquitetural vigente, sem reduzir o Comitê a simples elaborador de programa. A extensão dessa competência a transições concretas continua pendente (AB-05); não afirmar que seja aprovador universal. |
| Lei 4.383/2024 — Ouvidoria | [Texto oficial](https://www.hortolandia.sp.gov.br/arquivos/ADMINISTRACAO/LEI%204383-2024.pdf), especialmente arts. 2º, 9º, 17–18 e 22: rede setorial, encaminhamento e proteção de identificação. | A responsabilidade setorial pela Ouvidoria não equivale automaticamente à designação de APA ou de validador do FORM 2. |
| Decreto 5.729/2025 — e-SIC | [Página oficial do e-SIC](https://www.hortolandia.sp.gov.br/esic/) e cópia local `curso_senac_lgpd/ouvidoria/LEI 5.729 DE 17.10.25 - E-SIC.pdf`. Apesar do nome do arquivo, é decreto. Capa e pp. 1–3 conferidas; art. 6º trata de transparência e proteção da informação. Acesso ao texto externo vinculado pelo portal retornou 403. | Verificação parcial, sem inferência de competências não lidas. Canal de atendimento/acesso à informação não determina a alçada de conferência ou decisão nos FORMs. |
| Estrutura administrativa e delegações | SAD 10 referencia Lei 4.148/2023; Cartilha também aponta atos a conferir. [Página de Assuntos Jurídicos](https://www.hortolandia.sp.gov.br/secretaria-de-assuntos-juridicos/) descreve assessoramento/consultoria; [página de Tecnologia e Inovação](https://www.hortolandia.sp.gov.br/secretaria-de-tecnologia-e-inovacao/) descreve funções técnicas. Não foi validada a consolidação integral da lei de estrutura, suas alterações e delegações. | Descrição institucional apoia a indicação de interlocutores, mas não certifica signatário, alçada ou competência final por FORM. Essa verificação normativa é condição de habilitação dos atos institucionais. |

Ausência de confirmação nesta investigação **não significa ausência de competência legal**. Também não autoriza preencher a lacuna por configuração. As conclusões normativas devem ser confirmadas pela instância institucional responsável, com a íntegra vigente dos atos e eventuais delegações.

## 3. Matrizes por instrumento

### FORM 1 — Levantamento factual

| Função | Responsável e atribuição | Limite/segregação | Evidência |
|---|---|---|---|
| Ponto focal administrativo | APA responsável pela Secretaria do Registro; abertura e acompanhamento atual. Continuidade ao longo dos quatro FORMs proposta. | Participação de outra unidade não transfere a responsabilidade. Substituição formal segue mecanismos vigentes. | I/C; README, AGENTS |
| Preenchimento/preparação | ARP vigente autorizado; APA pode assumir esse papel mediante ato explícito. | Indicação não concede acesso. Somente o agente habilitado altera o rascunho. | I |
| Colaboradores/fontes | SAA e áreas que conhecem o tratamento, inclusive unidades participantes. | Apoio factual não cria perfil de edição; dados de cidadãos não são cadastrados no inventário. | D/C; Cartilha §3.1 |
| Manifestação especializada | Especialista solicitado quando houver dúvida; proposta de encaminhamento delimitado. | Não substituir fatos por análise jurídica nem decidir automaticamente nos demais instrumentos. | C |
| Conferência | APA confere o snapshot apresentado, devolve com justificativa ou confirma internamente. | Não confirma rascunho diferente; APA=ARP exige atos separados, sem afirmar dupla revisão independente. | I |
| Validação/decisão institucional | Não habilitada no Integral. Autoridade e marco de conclusão deverão ser formalizados. | Conferência interna não equivale a homologação, conformidade ou submissão institucional. | V; SAD 03 §11.2, 8T, AGENTS |
| Destinatário | Atualmente APA na solicitação interna; futuramente unidade habilitada à preparação do FORM 2, mediante marco aprovado. | Sem remessa obrigatória à TI; encaminhar não amplia acesso. | I/C/V |
| Acompanhamento | APA acompanha administrativamente; ARP responde por correções factuais que lhe forem atribuídas. | Rascunho e apresentações anteriores têm funções distintas; histórico imutável. | I/C |

### FORM 2 — Análise de legitimidade e manifestação

Atualização de 07/11/2026. A [decisão funcional AAL_01](../arquitetura/DECISAO_AAL_01_FORM2.md) fixa a denominação da função de preparação na PoC. A atribuição administrativa municipal e as alçadas especializadas continuam sujeitas à validação e aos atos competentes.

| Função | Proposta | Limite/segregação | Evidência |
|---|---|---|---|
| Ponto focal administrativo | APA acompanha encaminhamentos, prazos e obtenção de esclarecimentos. | Não ganha competência jurídica por ser ponto focal. | C |
| Preenchimento/preparação | AAL previamente habilitado para o Registro e designado pelo APA em exercício para a preparação. Consulta a origem factual atribuída e revisa o rascunho. | O papel de ARP não concede acesso ao FORM 2. A atuação como AAL não confere competência de parecer ou decisão. | AAL_01 (desenho funcional) e FORM2_07 (acesso demonstrativo) |
| Colaboradores/fontes | ARP/SAA para fatos; unidades participantes, TI/segurança e outras áreas para questões delimitadas. | Colaboração por escopo; consulta ou resposta a uma pendência não permite alterar todo o instrumento. | D/C; SAD 03 §12A |
| Manifestação especializada | Área jurídica para questão jurídica; outras áreas sobre sua especialidade, conforme competência formal. | Autoria individualizada da opinião; fundamentos podem diferir por operação de tratamento. DPO orienta/articula sem aprovação universal. | D/C/V; SAD 03 §11.2; REV17 FORM 2 |
| Conferência | Conferência de completude e consistência pela função a designar; APA acompanha a obtenção dos insumos. | Não atribuir ao APA uma revisão jurídica por mera configuração de fila. | C/V |
| Validação/decisão | Autoridade competente por matéria/objeto, com manifestações exigíveis. O SAD propõe essa distribuição provisoriamente. | Parecer, validação e decisão são atos distintos. Identificar autoridade e base formal antes de habilitar. | D/V; SAD 03 §11.2; DA-05 |
| Destinatário | Área responsável pelo risco no FORM 3, executores de medidas no FORM 4 ou ARP para esclarecimento/revisão factual. | Exceções de sequência dependem de regra aprovada; não alterar FORM 1 por cópia de conclusões. | C/V |
| Acompanhamento | O APA acompanha o Registro administrativamente. O AAL responde pela preparação, e cada especialista responde pela manifestação de sua autoria. | Ponto focal não assume responsabilidade técnica dos pareceres. | AAL_01 para a preparação; C/V para os atos especializados |

### FORM 3 — Riscos e controles

| Função | Proposta | Limite/segregação | Evidência |
|---|---|---|---|
| Ponto focal administrativo | APA acompanha o mesmo Registro e solicita os insumos faltantes. | Não calcula nem aceita risco automaticamente. | C |
| Preenchimento/preparação | Unidade operacional descreve contexto, ocorrências e controles; responsável habilitado organiza a avaliação. | Preparação factual não equivale à determinação especializada de probabilidade, impacto ou risco residual. | D/C; REV17 FORM 3 |
| Colaboradores/fontes | ARP/SAA, unidades executoras, TI/segurança, áreas técnicas e jurídica conforme questão. | Cada contribuição identifica origem, escopo e evidência. | D/C |
| Manifestação especializada | REV17 prevê DPO/Comitê na definição/validação dos parâmetros de risco, com apoio técnico. | Divergência com distribuição provisória do SAD 03 exige delimitação formal; não aplicar como atribuição automática. | D/V; GOV-04 |
| Conferência | Revisão da completude e fundamentação pela função especializada que vier a ser aprovada. | Não confundir conferência administrativa do APA com avaliação de controles. | C/V |
| Validação/decisão | SAD 03 aponta autoridade competente, TI/segurança consultada e DPO orientador. Aceitação de risco residual exige autoridade competente. | Distinguir validar parâmetros técnicos de decidir sobre continuidade, mitigação ou aceitação do risco. | D/V; REV17 3.52, 3.57; SAD 03 §11.2 |
| Destinatário | Responsáveis por medidas no FORM 4; revisão de fatos/legitimidade; eventual avaliação de necessidade de RIPD. | RIPD e competências correspondentes não são automaticamente criados por este planejamento. | D/C; REV17 3.61 |
| Acompanhamento | APA administrativamente; responsável pela avaliação acompanha revisão técnica e efeitos das medidas. | Mudança de fatos ou controles exige exame de impacto, não recálculo histórico silencioso. | C |

### FORM 4 — Providências e acompanhamento

| Função | Proposta | Limite/segregação | Evidência |
|---|---|---|---|
| Ponto focal administrativo | APA acompanha o plano associado ao Registro. | Não se torna executor de todas as ações. | C |
| Preenchimento/preparação | Responsável habilitado organiza as providências; unidade executora fornece planejamento, prazos e evidências. | Cada providência identifica origem e responsável, sem lista genérica sem atribuição. | D/C; SAD 05 §8 |
| Colaboradores/fontes | Áreas executoras e técnicas, responsáveis por orçamento/contratação quando pertinentes e autorizados. | Participação não concede poderes de contratação ou aprovação. | C |
| Manifestação especializada | Área competente atesta aspectos técnicos/jurídicos quando a ação exigir. | Evidência de execução não prova automaticamente eficácia ou conformidade. | D/C; REV17 4.18–4.22 |
| Conferência | Agente competente verifica entrega e evidência segundo a regra aprovada para a ação. | Separação entre executor e verificador deve ser definida; exceções explícitas e auditadas, não presumidas. | C/V |
| Validação/decisão | Autoridade responsável pelas ações/medidas, conforme matéria e alçada, inclusive risco residual ou encerramento com ressalva. | Não autorizar encerramento pelo simples preenchimento de prazo ou anexação de arquivo. | D/V; SAD 03 §11.2; REV17 4.24–4.25 |
| Destinatário | Unidade executora; avaliadores de eficácia; instância competente; revisão dos FORMs anteriores quando necessária. | Não impor passagem sequencial por todos os instrumentos a toda atualização de ação. | D/C |
| Acompanhamento | Dono de cada ação acompanha execução; APA acompanha o conjunto; autoridade competente decide situações reservadas. | Atraso é alerta, não decisão automática; medida pode continuar após marco do Registro quando formalmente permitido. | D/C/V; SAD 02 RF-WFL; SAD 05 §8 |

## 4. Operações que não podem ser confundidas

| Operação | Significado e condição mínima | O que não concede |
|---|---|---|
| Consultar | Ler conteúdo/versão dentro do escopo autorizado. | Editar, compartilhar irrestritamente ou decidir. |
| Preparar | Organizar fatos, evidências ou minuta, mediante atribuição e autorização. | Emitir manifestação reservada a outra competência. |
| Editar | Alterar rascunho habilitado, com autoria e controle de versão. | Alterar snapshot ou parecer já emitido. |
| Encaminhar | Solicitar atuação delimitada de unidade/papel habilitado. | Transferir responsabilidade do Registro ou conceder acesso por indicação. |
| Manifestar-se | Emitir opinião identificada sobre matéria e versão específicas. | Validar todo o instrumento ou decidir pelo órgão, salvo competência expressa adicional. |
| Validar | Registrar juízo de verificação no escopo formalmente definido. | Aprovar juridicamente tudo que consta do Registro. |
| Decidir | Praticar ato com alçada e fundamento definidos, preservando consequências e motivação. | Exceder competência por configuração administrativa. |
| Revisar | Reexaminar fatos, manifestação ou decisão segundo atribuição; gerar nova versão/ato quando necessário. | Reescrever autoria, conteúdo ou regra histórica. |

SAA é condição de acesso/tratamento no exercício das atribuições, **não um novo perfil sistêmico**. APA, ARP, integrante do Comitê, DPO e servidor de TI também não são papéis intercambiáveis. Um agente pode acumular vínculos válidos, mas a decisão efetiva considera ato, escopo, vigência e impedimentos.

O impedimento de autor validar a própria versão institucional previsto no SAD 03 §13 não deve ser desativado para reproduzir o caso APA=ARP da conferência interna preparatória. Esse caso atual conserva atos distintos; sua existência não autoriza autovalidação futura do FORM 2.

## 5. Divergências e decisões humanas indispensáveis

| ID | Questão comprovada | Proposta para decisão; condição antes da implementação |
|---|---|---|
| GOV-01 | APA ponto focal em todo o ciclo é diretriz candidata; hoje sua atuação implementada concentra-se no FORM 1. | Aprovar alcance administrativo, substituição e acompanhamento, sem atribuição automática de competência especializada. |
| GOV-02 | README menciona submissão válida de FORM 1; SAD 04 §12.2 usa FORM 1 Validado para a passagem; 8T descreve conclusão institucional; o fluxo atual é conferência interna bloqueada para submissão. | Escolher marco de entrada do FORM 2 e distinguir ensaio preparatório de ato institucional. Uma conferência confirmada não satisfaz automaticamente o marco. |
| GOV-03 | O AAL está definido para a preparação no desenho funcional da PoC. Sua instituição municipal e a identificação formal de conferente, signatário especializado e decisor por matéria e alçada permanecem pendentes. | Verificar unidade, competência e ato de suporte, inclusive para segregação e substituição. Não delegar ao DPO/APA/TI por padrão. |
| GOV-04 | REV17 FORM 3 concentra definição/validação de risco em DPO/Comitê; SAD 03 §11.2 atribui validação à autoridade competente, com consultas. DA-22 reconhece atuação deliberativa geral do Comitê, mas AB-05 mantém transições críticas abertas. | Delimitar avaliação técnica, orientação, manifestação colegiada e decisão/aceitação de risco. Obter atos vigentes e regra de competência antes de implementar decisões do FORM 3 ou dependências equivalentes do FORM 2. |
| GOV-05 | REV17 FORM 2 menciona unidades validando sua participação; SAD distingue resposta a pendência, parecer e validação de versão. | Aprovar o significado de cada ato por unidade. Uma resposta factual não deve fechar a análise global. |
| GOV-06 | SAD admite bloqueios e sequência conservadora; README admite ações FORM 4 antes de conclusão completa do FORM 3 mediante autorização. | Definir dependências por ato e exceções justificadas, responsável pela autorização e efeito de revisão do FORM 1 sobre trabalhos em curso. |
| GOV-07 | REV17 4.15 e SAD 05 §8 usam conjuntos diferentes de situações de ação. | Aprovar correspondência versionada antes da implementação do FORM 4; não tratar “parcialmente concluída” ou “bloqueada” como aliases automáticos de execução/conclusão. Não impede planejamento do FORM 2. |
| GOV-08 | Fontes arquiteturais e editoriais não comprovam a íntegra vigente de alçadas, delegações e alterações dos atos municipais. | A instância institucional competente deve validar base normativa, vigência, aprovador da política e liberação. Configuração técnica só poderá expressar competências confirmadas. |

Antes de implementar o FORM 2, são indispensáveis a definição do **recorte autorizado**, do marco de entrada (GOV-02), dos atos/papéis habilitados (GOV-03/05/08), do papel administrativo do APA (GOV-01) e do tratamento de revisões/dependências que fizerem parte desse recorte (GOV-06). GOV-04 deve ser resolvida antes de atribuir ao DPO/Comitê poderes de validação ou aceitação de risco; GOV-07 pode aguardar o contrato do FORM 4. Partes documentais e protótipos sem efeitos institucionais podem ser autorizados separadamente, sem presumir essas decisões.

## 6. Situação de entrega

Planejamento documental, sem criação de permissões, contratos, rotas, estados persistidos ou atos institucionais. As matrizes propostas não estão executadas nem testadas como funcionalidades. Não foram executados testes de aplicação ou migrações. Mantidos o bloqueio da submissão institucional, os contratos e as extensões GUARDA/MEDIDAS. Sem commit ou push nesta tarefa.
