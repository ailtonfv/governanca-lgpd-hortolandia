# FORM02_03 — Primeiro incremento demonstrativo do FORM 2

**Especificação técnica mínima candidata · 06/11/2026 · versão 0.1**  
**Somente planejamento. A implementação depende de nova autorização.**

## 1. Resultado proposto e decisões recebidas

Entregar uma área denominada **FORM 2 — Preparação demonstrativa**, na qual um preparador explicitamente designado e autorizado consulta um snapshot técnico identificado do FORM 1 e salva/retoma um rascunho próprio. A área deverá distinguir fatos de origem, anotações preparatórias e funcionalidades ainda indisponíveis.

A instrução FORM02_03 adota o APA como ponto focal administrativo dos quatro FORMs e aceita, para o recorte demonstrativo candidato, snapshot técnico identificado e lacrado, preparação autorizada, separação de manifestação/decisão e preservação das análises anteriores. Isso resolve a direção do marco **demonstrativo**, sem aprovar submissão institucional, competências especializadas ou a implementação deste documento.

Os documentos [GOV — matriz](GOV_FORMS_01_MATRIZ_RESPONSABILIDADES_CANDIDATA.md), [fluxo](GOV_FORMS_01_FLUXO_ENCAMINHAMENTOS_CANDIDATO.md) e [configuração](GOV_FORMS_01_CONFIGURACAO_VERSIONAMENTO_CANDIDATO.md) permanecem referências candidatas. Esta especificação registra as decisões posteriores sem reescrever os produtos anteriores.

**Dentro do primeiro incremento proposto:** consulta à origem; habilitação e atribuição delimitadas; início, salvamento e retomada de preparação; autoria, histórico técnico, idempotência, concorrência e testes de isolamento.

**Fora:** implementação das 245 perguntas; análise jurídica estruturada; manifestações especializadas; submissão, validação ou decisão institucional; tramitação intersecretarial; motor geral de políticas; troca da origem de uma preparação existente; implementação de FORMs 3/4; atualização da Cartilha, apresentação ou README nesta tarefa de planejamento.

## 2. Reaproveitamento: evidência e limites

| Componente examinado | Reaproveitar | Limite comprovado |
|---|---|---|
| `app/modelos.py`, `VersaoForm1Integral`, linha 306 | Snapshot com Registro, número, versão do rascunho, contrato, revisão, JSON, texto canônico, lacre, autor/data e evento. | É preparação técnica sem submissão. Não transformar em `VersaoInstrumento` submetida. |
| `app/submissao_form1_integral.py`, `_envelope_snapshot` e `preparar_snapshot_na_transacao` | Formato de leitura da origem: `form1_integral`, `contrato`, `origem` e `retrato_canais`. | O FORM 2 somente lê snapshots já existentes; não chama a preparação do FORM 1 para fabricar uma origem no acesso. |
| `app/extensao_medidas_form1.py`, `catalogo_efetivo`/`versao_estrutura`, e extensão GUARDA | Leitura conforme a definição efetiva original, MEDIDAS, GUARDA ou combinação. | Não usar o catálogo atual para reinterpretar respostas históricas nem acionar adoção de extensão. |
| `app/comandos.py`, `abrir_comando`/`fechar_comando`; `app/eventos.py`, registro e verificação | Chave idempotente, lacres, eventos encadeados, auditoria e transação pelos padrões existentes. | Tipo de evento e versão de regra próprios para o recorte; não usar códigos de submissão/validação nuclear. |
| `app/atribuicao_form1_integral.py`, `atribuir_arp_form1_integral` | Padrão de atribuição explícita, versão lida e indicação separada da habilitação. | Não chamar esse serviço para designar preparador do FORM 2 nem alterar o ARP. |
| `app/permissoes.py`, `tem_papel`, linha 41 | Referência de consulta a vínculos existentes. | Verifica papel/unidade e `ativa`, sem filtrar intervalo temporal. Não basta para a nova autorização por ato e Registro. Não corrigir globalmente o núcleo neste incremento. |
| `app/consultas_interface.py`, `_ids_visiveis` | Referência das regras atuais de visibilidade do Registro. | Ser consultável não concede preparação do FORM 2. Adicionar papel genérico em `Designacao` pode ampliar visibilidade de Registros da unidade; evitar esse atalho. |
| `Instrumento`/`RascunhoInstrumento`; `app/instrumentos.py` | Padrões conceituais de instrumento e rascunho. | Comandos ainda usam papel `preenchedor` e validador sintético. `workflow.py`, `concluir_registro_sem_medidas`, consulta os instrumentos do Registro e exige validação. Inserir ali FORM 2 preparatório afetaria o núcleo. |

**Recomendação:** reutilizar serviços transversais e estruturas de origem, com domínio e projeção próprios para a preparação demonstrativa. Não refatorar os comandos nucleares para transformá-los em motor genérico. A opção por projeção adicional decorre dos acoplamentos acima, não da simples preferência por tabelas novas.

## 3. Consulta à origem

O preparador seleciona explicitamente um **snapshot existente do mesmo Registro**. Não escolher silenciosamente o mais recente. Mostrar número/ID, data, autor funcional disponível, versão do rascunho de origem, contrato/revisão/estrutura e lacre; mostrar a conferência interna correspondente, se houver, como informação separada.

Para o ensaio candidato, recomenda-se aceitar snapshot técnico íntegro mesmo incompleto, sem exigir que tenha conferência confirmada. Isso deve ser ratificado no recorte de implementação; não representa aprovação da suficiência dos fatos. Registro sem snapshot recebe orientação compreensível, sem criação automática nem botão que prometa preparação possível.

Antes de vincular a origem, verificar:

1. Conta/pessoa ativas, escopo de consulta e habilitação específica de preparação.
2. Existência do Registro e snapshot; correspondência entre ambos; contrato 3/REV13 e estrutura reconhecida.
3. Concordância entre JSON, representação canônica e lacre, conforme algoritmo existente, incluindo coerência do evento de preparação. Falha recusa o vínculo, sem tentar reparar o snapshot.
4. Origem histórica lida exclusivamente do envelope: canais, respostas e ocorrências de participantes/destinatários. IDs das ocorrências devem permanecer identificáveis.

A consulta apresenta enunciados e alternativas compatíveis com a origem: REV13 original (128 IDs), MEDIDAS (129), GUARDA (139), combinação (140). Snapshot antigo sem metadado posterior só pode ser interpretado pela compatibilidade histórica já documentada; perfil desconhecido deve gerar indisponibilidade explicada, não suposição. Separar dados atuais do Registro de fatos congelados; metadado inexistente no snapshot não pode ser apresentado como histórico certificado.

A origem é somente leitura. Alterar o rascunho do FORM 1 ou produzir outro snapshot não modifica a preparação existente. Pode-se informar que há outra versão disponível, sem copiar dados, migrar análises ou determinar automaticamente qual está correta.

## 4. Autorização e designação

São duas condições cumulativas: **habilitação para o ato** e **atribuição expressa da preparação**. Nenhuma decorre automaticamente de APA, ARP, SAA, TI, DPO ou cargo. O APA acompanha administrativamente; seu poder de designar o preparador não é inferido dessa condição.

Proposta para o primeiro ensaio: habilitações de demonstração por pessoa fictícia e Registro, com ações permitidas, vigência, fundamento de ensaio, autor da autorização e versão da política; atribuição identificando preparador, designante e data. Os atores autorizadores/designantes precisam ser definidos antes da implementação. Podem coincidir somente se isso for explicitamente aprovado; a indicação nunca cria uma habilitação ausente.

Evitar uma nova tela de administração de perfis. No primeiro recorte, provisionamento por executor controlado de demonstração/testes, invocando os comandos de domínio, é suficiente se aprovado. Não usar gravações SQL sem auditoria nem identidade enviada pelo formulário como fonte de competência. A autenticação permanece a simulada da PoC, sem promessa de integração institucional real.

Cada consulta e escrita verifica conta, pessoa, escopo, vigência e revogação. A escrita verifica também a atribuição da preparação. Revogação impede novos atos, preservando o histórico. Consulta pelo APA ou outro perfil é separada da edição e depende do escopo aprovado; por padrão não ampliar leitores do novo rascunho apenas porque consultam o Registro.

Repetição de comando não concede acesso após revogação: proteger a entrega do resultado idempotente pela autorização atual, sem duplicar nem desfazer o ato anterior. O papel exercido deve constar do evento como preparação demonstrativa, nunca validação jurídica.

## 5. Rascunho próprio: conteúdo e persistência mínima

### 5.1. Recorte de conteúdo proposto

Os tipos/opções/condicionais das 245 perguntas continuam candidatos. Não criar uma matriz de obrigatoriedade por imitação do FORM 1 nem declarar a Área A integralmente implementada por mostrar dados herdados.

Para testar salvamento útil sem antecipar decisões jurídicas, propõe-se **uma anotação preparatória facultativa**, intitulada “Anotações de preparação”, texto simples de até **2.000 caracteres**, aceitando vazio, sem HTML executável ou anexos. Deve orientar a registrar dúvidas sobre o levantamento, sem informações pessoais concretas. É um metadado do espaço de trabalho, **não nova pergunta canônica**, resposta a F2 1.3/1.3.1, parecer ou encaminhamento automático. O conteúdo e limite dependem de aprovação desta proposta. Se for preferível começar com perguntas canônicas, selecionar e aprovar primeiro os IDs, tipos e regras; não improvisá-los durante a implementação.

Identificação e autoria vêm da origem/cadastro existente, sem exigir digitação de nome, cargo ou e-mail. Mostrar aviso permanente: “Preparação demonstrativa. Salvar não emite parecer, não submete e não aprova o tratamento.”

### 5.2. Projeções candidatas

Propor duas projeções adicionais, sem inserir FORM 2 nas tabelas operacionais nucleares neste recorte:

| Projeção | Estrutura mínima candidata |
|---|---|
| Habilitação de preparação FORM 2 | ID, pessoa, Registro, ações delimitadas (consulta/preparação/atribuição conforme aprovação), vigência, situação/revogação, fundamento, autorizador e evento. Não usar `Designacao` genérica para conceder acesso a toda a Secretaria. |
| Preparação/rascunho FORM 2 | UUID, FK Registro/ciclo, FK snapshot técnico, perfil/lacre da origem verificados, versão do envelope próprio, preparador designado, designante/data/evento, referência da habilitação e política, JSON da anotação, contador otimista, autor/data do último salvamento e lacre próprio. |

Nomes físicos, constraints e número da migração serão definidos no início autorizado, após nova conferência do esquema. Proposta de envelope: `F2-DEMO-PREP-v1`, sem reutilizar o número do contrato nuclear ou afirmar que é o contrato completo do FORM 2 REV17.

Recomenda-se uma preparação por Registro/snapshot para o primeiro recorte, com unicidade no banco e no domínio. Inicialização repetida não cria outro rascunho nem redefine preparador. O snapshot vinculado não é editável. Não implementar substituição de preparador ou troca da origem neste primeiro incremento; apresentar a limitação. Revogação preserva a preparação, mas pode exigir regularização em incremento posterior.

Cada salvamento registra evento imutável com versão de trabalho, conteúdo preparatório completo, origem, autor/papel e versão da regra, suficiente para reconstruir as revisões; a projeção guarda o último conteúdo. Não usar `VersaoInstrumento` nem metadados “submetida_por/em” para uma anotação técnica. A retenção de todas as revisões deve ser testada, não apenas a existência do último lacre.

Nova origem exige **nova preparação explícita e independente**, se autorizada, sem copiar anotações automaticamente. A anterior permanece consultável aos autorizados. No primeiro incremento não há manifestação especializada: a preservação cobre as preparações existentes, e não pode ser divulgada como implementação do histórico completo de pareceres do FORM 2.

Migração aditiva provavelmente necessária para essas projeções. Testar aplicação em base com dados sintéticos existentes e reversão apenas em base isolada; reversão deve recusar eliminar preparações/habilitações com histórico. Não reaproveitar campo do FORM 1 nem introduzir dependência que altere sua conclusão. Nenhuma migração é criada ou aplicada nesta tarefa documental.

## 6. Comandos, interface e isolamento

Serviço específico para consultar origem, autorizar/atribuir conforme recorte aprovado, iniciar preparação e salvar rascunho. Leituras não criam preparação, snapshot ou tarefa; podem registrar auditoria de consulta. Escritas usam `comando_id`, versão lida e transação única para comando, evento, auditoria e projeção.

Para evitar alterar a corrente e a reconstrução nuclear, propõe-se cadeia própria de preparação, UUID globalmente único e vínculo explícito ao Registro/ciclo nos eventos. A integridade deve ser verificada pelos serviços existentes e a reconstrução específica da nova projeção deve ser testada. Não atualizar estado do Registro, `versao_vigente_id` nuclear, conferência ou rascunho do FORM 1. A estratégia de travas deve serializar inicialização/salvamento e a atribuição/revogação concorrente; conflito deve recusar a escrita sem perda de dados.

Página própria e mínima, com seleção explícita da origem, resumo da identificação, consulta expansível aos blocos do snapshot e área editável visualmente distinta. Não redesenhar o painel nem embutir o formulário sintético. Destinos candidatos:

- `GET /registros/{registro_id}/form2/preparacao`: consulta e retomada autorizadas.
- `POST /registros/{registro_id}/form2/preparacao/iniciar`: origem e atribuição verificadas no servidor.
- `POST /registros/{registro_id}/form2/preparacao/{preparacao_id}/salvar`: gravação otimista da anotação.

As URLs são propostas, não rotas existentes. Habilitação/atribuição podem permanecer no executor controlado; nenhum endpoint de submissão, manifestação, aprovação ou decisão. Usar POST–redirecionamento–GET, feedback acessível, foco no trabalho e proteção contra saída com alteração não salva, reutilizando apenas componentes cuja independência do FORM 1 seja comprovada. Usuário sem acesso não recebe conteúdo ou metadados do snapshot por manipular a URL.

## 7. Arquivos previstos, não modificados agora

| Arquivo ou grupo candidato | Finalidade futura |
|---|---|
| `app/form2_preparacao.py` — novo | Envelope mínimo, validação estrutural e serviços de início/salvamento, sem validador sintético. |
| `app/autorizacao_form2_preparacao.py` — novo | Habilitação, atribuição, vigência, revogação e escopo da demonstração; nenhuma mudança global em `permissoes.py`. |
| `app/consultas_form2_preparacao.py` — novo | Leitura da origem histórica e rascunho; projeção sem escrita e sem dependência de catálogo corrente. |
| `app/modelos.py` e `migracoes/<nome_a_definir>.py` | Projeções adicionais isoladas, integridade referencial, unicidade e migração aditiva. Registro da migração no mecanismo existente, no ponto que vier a ser confirmado. |
| `app/main.py` ou roteador específico registrado nele | Apenas rotas demonstrativas delimitadas e obtenção da identidade pelo padrão atual. |
| `app/paginas/form2_preparacao.html` — novo | Consulta da origem, anotação e limites explícitos; componentes existentes quando seguros. |
| `app/estaticos/form2_preparacao.js` — somente se necessário | Saída segura/foco sem copiar lógica de blocos do FORM 1. Sem biblioteca externa. |
| `demonstracoes/form2_preparacao.py` — novo | Preparação controlada da massa sintética e atos de habilitação/atribuição aprovados; sem provisionamento em banco real. |
| `testes/test_form2_preparacao.py`, `testes/test_interface_form2_preparacao.py`, `testes/test_migracao_form2_preparacao.py` — novos | Aceites abaixo; fixtures específicas sem alterar papéis das massas nucleares. |
| Documento técnico próprio do incremento | Registrar contrato técnico mínimo efetivamente autorizado e evidências, sem substituir o candidato completo REV17. |

`app/comandos.py`, `app/eventos.py`, serviços do FORM 1 e catálogos/extensões devem ser consumidos sem alterações, salvo incompatibilidade comprovada que exija nova avaliação. Não modificar contratos 2/3, REV13, matriz, Cartilha ou apresentação. O README permanece intocado nesta especificação.

## 8. Testes e critérios de aceite do futuro incremento

| ID | Cenário obrigatório | Resultado esperado |
|---|---|---|
| T01 | Consultar snapshot S1 dos quatro perfis históricos reconhecidos | Enunciados/respostas/canais/ocorrências exatos; origem identificada e somente leitura. |
| T02 | Snapshot inexistente, de outro Registro, perfil desconhecido ou lacre incoerente | Recusa compreensível; sem criação/reparo automático e sem exposição indevida. |
| T03 | Registro sem snapshot; snapshot incompleto/devolvido/confirmado | Sem snapshot não inicia; demais elegibilidades seguem a decisão explícita do recorte, sem classificar conferência como aprovação. |
| T04 | APA/ARP/SAA sem habilitação própria; pessoa indicada sem autorização; autorização sem atribuição | Não editam por herança ou indicação. Consulta também verifica seu escopo. |
| T05 | Conta/pessoa inativa, prazo expirado, revogação, outra pessoa/Registro e requisição forjada | Recusa no servidor, auditoria e nenhum dado alterado. |
| T06 | Iniciar e salvar anotação vazia/parcial; recarregar/retomar | Rascunho próprio persistido, mesma origem, autoria e versão corretas; limite e chaves extras validados. |
| T07 | Repetir comando; repetir com conteúdo diferente; iniciar simultaneamente | Repetição exata idempotente, reuso indevido recusado e única preparação por origem. |
| T08 | Dois salvamentos com a mesma versão; revogação/atribuição concorrente | Nenhuma sobrescrita; decisão consistente segundo travas e autorização vigente. |
| T09 | Falha induzida entre evento, auditoria e projeção | Rollback integral; nenhuma gravação parcial. |
| T10 | S1 + preparação P1; FORM 1 alterado e novo snapshot S2 | P1 e suas revisões continuam ligadas a S1; S1/S2 íntegros; nenhuma troca/cópia automática. |
| T11 | Nova preparação P2 explicitamente autorizada sobre S2 | P1 preservada; P2 começa vazia; histórico, autores e origens distinguíveis. |
| T12 | Reconstruir versões de anotação e verificar cadeias | Conteúdo e lacres coincidem; anotação não é snapshot submetido ou parecer. |
| T13 | Executar jornadas nucleares e do FORM 1 antes/depois | Estados, contratos, respostas, permissões e critérios de conclusão existentes preservados; novo rascunho não entra na lista nuclear de instrumentos obrigatórios. |
| T14 | Tentar submissão/validação/decisão pelas novas rotas ou rotas legadas | Nenhuma capacidade nova desse tipo; preparação não pode ser operada como instrumento nuclear. |
| T15 | Migração em base existente e reversão em base isolada | Dados anteriores íntegros; reversão recusa destruição de histórico novo. |
| T16 | Teclado, tela estreita/larga, erro, saída com alteração não salva e retorno da consulta | Conteúdo legível, foco previsível, origem distinta da edição, sem perda de anotação. Aceitação visual registrada separadamente. |

Executar testes focais no banco terminado em `_teste`, depois regressão completa antes de considerar o incremento tecnicamente estável, incluindo núcleo, conferência interna, snapshots e extensões. Aceitação manual demonstra início, consulta a S1, salvamento/retomada e preservação após S2. Não afirmar aceitação visual com base apenas em HTTP. **Nenhum desses testes foi executado nesta tarefa de especificação.**

## 9. Decisões restantes para autorizar o primeiro incremento

| Decisão | Recomendação mínima | Efeito |
|---|---|---|
| Quem autoriza e quem designa o preparador demonstrativo? Quem pode consultar sua preparação? | Aprovar matriz restrita ao ensaio, pessoas fictícias e Registro; atos separados, ainda que exercidos pela mesma pessoa se expressamente permitido. Sem poder automático ao APA. | Impede implementação segura da atribuição enquanto indefinido. Não exige decidir validadores institucionais. |
| Qual conteúdo editável inicial? | Aprovar anotação preparatória facultativa de até 2.000 caracteres, sem ID canônico; ou selecionar perguntas e aprovar tipos antes da implementação. | Evita inventar regras das 245 perguntas. |
| Elegibilidade e multiplicidade | Ratificar snapshot técnico íntegro, inclusive incompleto, sem exigência de conferência confirmada; uma preparação por Registro/snapshot, origem fixa, nova preparação explícita para nova origem. | Concretiza a direção demonstrativa já adotada, sem liberar marco institucional. |
| Persistência isolada e limite operacional | Aprovar duas projeções aditivas, histórico pelos eventos e provisionamento controlado; sem substituição/troca de origem no primeiro incremento. | Evita interferência comprovável no núcleo e limita o tamanho da entrega. |

Competências jurídicas, manifestações, decisão institucional, matriz completa do FORM 2, DPO/Comitê e aceitação de riscos continuam reservadas aos atos futuros pertinentes. Não bloqueiam este recorte preparatório depois de aprovadas as decisões técnicas/operacionais acima, nem são resolvidas por ele.

**Estado desta entrega:** apenas esta especificação documental foi acrescentada. Arquivos preexistentes preservados; nenhuma implementação, migração, alteração de README/Cartilha/apresentação, commit ou push. A aprovação desta especificação e a autorização de implementação devem delimitar expressamente o primeiro incremento.
