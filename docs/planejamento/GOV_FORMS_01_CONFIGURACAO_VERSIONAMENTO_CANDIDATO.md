# GOV_FORMS_01 — Estratégia candidata de configuração e versionamento

**Produto C · versão documental 0.1 · 06/11/2026**  
**Proposta arquitetural; não é um contrato executável, uma matriz de permissões vigente ou uma implementação autorizada.**

## 1. Recomendação e base examinada

Recomenda-se centralizar a futura política declarativa de responsabilidades e encaminhamentos, mantendo separados: **competência formal, permissão efetiva, atribuição de trabalho, regra de encaminhamento e autoria histórica**. O cadastro de um participante ou a alteração de uma fila não pode conceder competência.

A [matriz candidata](GOV_FORMS_01_MATRIZ_RESPONSABILIDADES_CANDIDATA.md) contém fontes e decisões GOV-01 a GOV-08. O [fluxo candidato](GOV_FORMS_01_FLUXO_ENCAMINHAMENTOS_CANDIDATO.md) define os atos propostos. Bases: SAD 02 RF-WFL; SAD 03 §§11–13; SAD 04 §12; SAD 05, instrumentos/versões/ações; SAD 10 DA-05/06, DA-22, DA-26/27 e AB-05.

Há estruturas aproveitáveis no repositório, mas não um motor dos quatro FORMs pronto para configurar:

| Estrutura atual examinada | Reutilização possível, sujeita a projeto e testes | Limite |
|---|---|---|
| Registro LGPD, vínculos institucionais e continuidade do APA | Identidade do mesmo Registro, responsabilidade por Secretaria e substituição formal. | Não ampliar escopo de acesso ou transferir competência por encaminhamento. |
| `VersaoForm1Integral`, `ConferenciaInternaForm1Integral` e `HistoricoConferenciaForm1Integral`, em `app/modelos.py` | Referência imutável à versão apresentada, autoria, histórico e separação de conferência. | Não converter confirmação interna em submissão ou validação jurídica. |
| `Instrumento`, `RascunhoInstrumento`, `VersaoInstrumento`, `AnaliseInstrumento` | Padrões de identidade, versionamento e análise a avaliar. | A existência de tabelas genéricas não significa suporte funcional pronto ao FORM 2. `app/instrumentos.py` mantém acoplamento à validação do instrumento nuclear. |
| Serviços existentes de autorização, comandos, eventos e auditoria | Reutilizar os padrões de autorização, `comando_id`, concorrência e transação. | Não reutilizar por cópia estados ou validadores do contrato nuclear para uma nova semântica. |
| Contrato REV13, matrizes e extensões MEDIDAS/GUARDA | Demonstram versionamento explícito e preservação de interpretações históricas. | Permanecem intactos. Política de responsabilidade é um eixo diferente da versão do questionário. |

Não há necessidade demonstrada, nesta análise, de substituir o modelo existente ou criar um sistema independente por FORM. Também não se demonstrou que apenas editar um arquivo declarativo seria suficiente: executar a política, registrar sua versão em atos e aplicar novas operações exigirá desenvolvimento autorizado.

## 2. Camadas propostas

| Camada | Conteúdo | Regra de proteção |
|---|---|---|
| Base de competência | Ato formal, órgão/unidade, função, matéria, alçada, vigência, delegação e limites. | Sem evidência válida, não habilitar operação reservada. Não armazenar credenciais ou dados pessoais nos arquivos de política. |
| Política versionada | Instrumento, operação, escopo, condições, impedimentos, destino e pré-requisitos. | Só referencia capacidades já implementadas e competências aprovadas. Negar por padrão. |
| Vínculo/atribuição | Agente autenticado, vínculo vigente, papel exercido, unidade e solicitação/Registro. | Indicação ou atribuição não concede acesso; deve haver autorização efetiva independente. |
| Execução | Comando, versão lida, validação do estado e da competência, decisão e efeitos. | Verificação no servidor em cada ato; transação única para registros relacionados. |
| Evidência histórica | Versão de política, competência utilizada, snapshot analisado, autor/papel, data, resultado, motivo e evento. | Imutável. Mudança de política não reescreve decisão anterior. |

A RACI pode ser derivada para documentação e revisão, mas não substitui a política de autorização. O mesmo vale para o painel de próximas providências: ele projeta atos permitidos, sem constituir fonte autônoma de permissão.

## 3. Estrutura mínima proposta para a política

O quadro abaixo descreve metadados candidatos; **não adiciona campos aos contratos atuais**. Nomes definitivos e representação JSON/YAML dependerão da implementação autorizada.

| Grupo | Metadados mínimos propostos | Verificação necessária |
|---|---|---|
| Identificação | Identificador estável, versão, situação candidata/aprovada/retirada, data de vigência, versão anterior, resumo e integridade. | Versão publicada imutável; nenhuma política candidata executada em produção institucional. |
| Aprovação | Responsável pela aprovação funcional, fundamento/ato de competência, âmbito da aprovação e evidência. | Aprovação técnica de uma configuração não substitui aprovação institucional ou jurídica exigível. |
| Operação | FORM, ação do vocabulário aprovado, escopo do objeto/unidade, capacidade técnica requerida. | Ação desconhecida ou não implementada deve ser rejeitada, não interpretada por texto livre. |
| Habilitação | Função/papel elegível, vínculo vigente, base de competência, alçada, limites de delegação e impedimentos. | Interseção com autorização atual e segregação, não soma permissiva de papéis. |
| Encaminhamento | Unidade/papel destinatário, matéria, dados mínimos acessíveis, condição de entrada e responsabilidade de retorno. | Destinatário existente e habilitado; ausência exige regularização explícita. |
| Dependência | Snapshot/base exigida, condições bloqueantes, manifestações requeridas e exceções autorizáveis. | Não equivaler conferência interna a aprovação institucional; não impor sequência rígida sem fonte. |
| Revisão | Tratamento de tarefas em curso, regra de seleção da política e exame de impacto sobre instrumentos dependentes. | Sem troca silenciosa de snapshot, executor ou competência. |

Preferir condições estruturadas com operadores conhecidos, sem código arbitrário, scripts ou expressões livres executáveis no arquivo. Definir esquema e validação estática. Uma política não poderá redefinir o significado de “validar” ou “decidir” apenas trocando o nome do botão.

A fonte declarativa será única e versionada; matrizes de consulta e documentação poderão ser derivadas dela ou referenciá-la. Evitar cópias independentes de regras na interface, no serviço e em planilhas. **Os três documentos deste planejamento ainda não são essa fonte executável.**

## 4. Seleção de versão e preservação histórica

Recomendação candidata, a aprovar em GOV-06/08:

1. Cada análise identifica a versão do instrumento e os snapshots de origem, incluindo contrato/revisão/extensões efetivamente utilizados. FORM 2 não lê o “FORM 1 mais recente” implicitamente.
2. Cada ato registra a política e a base de competência usadas no momento de sua prática, além de autor, papel, unidade e vínculo pertinente. A referência histórica deve permitir reconstruir a regra aplicada, inclusive após sua retirada de vigência.
3. A autorização **atual** é reavaliada a cada operação. Fixar uma política no início do ciclo não perpetua vínculo revogado, delegação expirada ou competência legal extinta.
4. Se uma política mudar durante tarefa aberta, executar avaliação explícita: manter procedimento ainda válido ou migrar prospectivamente a tarefa, indicando motivo, responsável e efeitos. Nenhuma migração administrativa altera atos já praticados.
5. Normas/revogações supervenientes prevalecem sobre uma configuração antiga. Se houver dúvida de competência, suspender a execução daquele ato, preservar o trabalho e encaminhar à autoridade responsável por regularizar a atribuição.
6. Revisar uma manifestação ou decisão cria novo ato relacionado ao anterior. Retificação, substituição ou anulação exige competência e semântica próprias; não é edição comum de rascunho.
7. Política usada em um ato histórico é consultável para auditoria, mas não concede acesso atual ao conteúdo a quem perdeu autorização. Preservação histórica e controle de leitura continuam separados.

As versões de política, formulário, rascunho, snapshot e apresentação não devem compartilhar um contador nem ser confundidas. A adoção explícita de GUARDA/MEDIDAS continua sendo assunto do FORM 1 e não será acionada por troca de política de responsabilidades.

## 5. O que poderá mudar por configuração

**Esta tabela descreve possibilidades após existir e ser aprovado o mecanismo correspondente. Hoje não autoriza edição de configuração para habilitar FORMs futuros.**

| Mudança | Por configuração? | Exigências e limites |
|---|---|---|
| Unidade destinatária ou função responsável por operação já suportada | Sim, em princípio. | Competência formal, escopo compatível, política nova, vigência e tratamento das tarefas abertas. Não atribuir acesso automaticamente aos integrantes. |
| Alçada, prazo ou ordem de manifestações já modeladas | Sim, se os tipos de condição e suas consequências já existirem. | Aprovação competente, testes de conflito/ciclos, preservação de atos e exceções autorizadas. |
| Exceção aprovada de preparação paralela/medida antecipada | Somente se houver capacidade existente para esse tipo de exceção. | Fonte formal, justificativa, autoridade e efeitos definidos; não inventar transição via configuração. |
| Designar/substituir pessoa que exerce função | Ato administrativo e vínculo existentes, não simples edição da política genérica. | Autorização, vigência e auditoria pelos mecanismos pertinentes; revogação não apaga autoria histórica. |
| Alterar texto explicativo sem mudar o ato | Pode ser metadado de apresentação, se suportado. | Não mudar competência ou significado do comando; manter coerência e acessibilidade. |
| Introduzir operação, condição, impedimento ou transição não suportados | Não apenas configuração. | Código de domínio, autorização, projeções/interface e testes; eventual contrato. |
| Alterar semântica de pergunta, tipo de resposta ou envelope de instrumento | Não. | Contrato/catalogação versionados, compatibilidade e testes. Não é política de responsabilidade. |
| Registrar nova evidência de competência/decisão não comportada pela persistência atual | Não presumir. | Examinar JSON/eventos/entidades existentes; alterar contrato/persistência e migrar somente se necessário. Sem tabela nova por conveniência. |
| Alterar modelo de estados do FORM 4 ou sentido de validação por unidade | Não antes da decisão semântica. | Resolver GOV-05/07; mapear explicitamente conceitos e versões antes de implementar. |
| Conceder poder sem ato, ignorar impedimento ou liberar submissão bloqueada | Nunca como atalho de configuração. | Exige autorização institucional e implementação específica; configuração não supera restrição legal. |

## 6. Integridade, idempotência e concorrência

Reutilizar os padrões existentes: `comando_id` para repetição; controle otimista da versão lida; autorização verificada no servidor; evento, auditoria, snapshot e projeção correlatos na mesma transação. Um clique repetido não pode duplicar manifestação, decisão ou encaminhamento. Uma decisão concorrente deve ser rejeitada quando sua base já tiver sido encerrada ou modificada de modo incompatível.

No ato futuro, identificar expressamente o papel exercido. A assinatura como ARP não pode ser tratada como assinatura jurídica do mesmo agente por ele também possuir outro vínculo. Sobreposição de papéis não vence impedimentos. O DPO não é aprovador padrão; o SAA não recebe poderes de APA/ARP; o APA não se torna decisor dos outros instrumentos; o Comitê não recebe transições críticas apenas porque sua competência geral inclui deliberar.

Proteger também a administração da política: revisão e aprovação identificadas, comparação de alterações, validação de referências, ativação controlada e trilha auditável. Reverter configuração significa publicar nova versão prospectiva; não eliminar a anterior. Aprovação funcional da PoC, aprovação técnica de implantação e ato institucional formal devem aparecer com seus âmbitos distintos.

## 7. Incrementos técnicos possíveis após nova autorização

| Etapa candidata | Entrega delimitada | Aceite antes de avançar |
|---|---|---|
| C0 — Decisões e contrato de política | Resolver GOV-01/02/03/05/06/08 no recorte do FORM 2; identificar capacidades e metadados mínimos. | Aprovação documentada, sem competências inferidas; FORM 3/4 podem permanecer apenas planejados. |
| C1 — Validador declarativo isolado | Validar esquema, referências, vigência, impedimentos e destinos, sem ativar decisões. | Rejeição de regra inválida, destinatário inexistente, concessão indevida e condição desconhecida. |
| C2 — Leitura de base e atribuição | FORM 2 candidato consulta snapshot específico e funções autorizadas conforme contrato aprovado. | Sem copiar fatos desnecessariamente, sem alterar FORM 1, sem acesso pela simples indicação. |
| C3 — Atos delimitados | Preparação/esclarecimento ou manifestação explicitamente autorizados no incremento. | Transação, autoria, versão da regra, idempotência, concorrência e rollback. Não habilitar decisão final por consequência. |
| C4 — Evolução de política | Nova versão e tratamento explícito das tarefas abertas em ambiente isolado. | Histórico íntegro; revogação/expiração prevalece; não reinterpretação de atos anteriores. |

Testes futuros devem abranger: papéis cumulativos e impedimentos; SAA colaborador sem edição; APA focal sem competência especializada; DPO consultado sem aprovação universal; encaminhamento sem expansão de acesso; parecer separado de decisão; regras antigas preservadas e vínculos revogados sem acesso; atualização do FORM 1 sem alteração silenciosa da base do FORM 2; políticas conflitantes; substituição formal; exceção de sequência; ausência de responsável habilitado; alterações de unidade/alçada e tentativas fora do escopo.

## 8. Conclusão e pendências

É viável **propor** responsabilidades e encaminhamentos declarativos sobre a arquitetura existente, com alterações futuras localizadas quando se mantiverem as capacidades e semânticas aprovadas. Não é possível prometer que qualquer nova competência, estado ou evidência dispensará evolução de código/contrato/persistência.

Antes de implementar o FORM 2, decidir seu marco de entrada, as funções e competências por ato, o alcance do APA como ponto focal, o significado da validação por unidade, o tratamento de revisões e quem aprova/ativa a política. Resolver a participação DPO/Comitê antes de ativar avaliação/decisão de risco. Manter as demais questões do FORM 4 como planejamento, sem bloquear indevidamente trabalho independente autorizado.

Não foram alterados código, banco, contratos, matrizes, Cartilha, apresentação, candidatos FORM2 ou extensões do FORM 1. Nenhuma submissão institucional foi liberada. Não foram executados testes de aplicação, commit ou push; a verificação desta entrega é documental e de preservação dos arquivos preexistentes.
