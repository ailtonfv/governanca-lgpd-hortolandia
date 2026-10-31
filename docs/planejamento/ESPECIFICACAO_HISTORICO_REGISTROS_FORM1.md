# Especificação técnica — histórico de quantidades de registros no FORM 1

**Incremento:** 8Q

**Situação:** proposta pendente de aprovação; não autoriza implementação, migração ou alteração da REV13

**Escopo:** evolução futura dos itens `2.9` e `2.9.1` do FORM 1 Integral
**Dados permitidos na PoC:** exclusivamente fictícios

## 1. Objetivo e limite

Esta especificação propõe substituir futuramente a informação genérica de volume de registros por medições estruturadas, separadas por tipo de registro administrativo e preservadas ao longo do tempo.

A proposta não altera os 128 identificadores, a matriz de obrigatoriedade, o contrato candidato 3, o contrato nuclear 2 ou a infraestrutura atual. A submissão integral continua bloqueada. A implementação depende das decisões institucionais da seção 9.

O histórico de medições não é:

- cadastro de pessoas titulares;
- contagem obrigatória de pessoas;
- versionamento do FORM 1;
- regra de temporalidade ou descarte documental;
- declaração de adequação à LGPD.

## 2. Estado atual verificado

### 2.1 Catálogo e rascunho REV13

O catálogo `REV13-2026-09-20` define:

| Campo | Conteúdo atual | Controle e armazenamento |
|---|---|---|
| `2.9` | Volume aproximado de registros | Uma única faixa do catálogo compartilhado com `2.8`: `Não se aplica`, faixas de `Até 10` a `Mais de 10.000`, `Não mensurado` ou `A confirmar` |
| `2.9.1` | Período de referência dos registros | Uma única alternativa: dia, semana, mês, trimestre, semestre, ano, campanha, evento, projeto/programa, `Outro` ou `A confirmar` |

As respostas são armazenadas em `RascunhoForm1Integral.conteudo`, no dicionário `respostas` do envelope JSON. O salvamento gera nova `versao_rascunho`, autoria, data e lacre do envelope, mas não cria uma série de medições identificadas por tipo.

Os dois campos são facultativos na matriz vigente e permanecem sempre visíveis. A pré-validação os lê como respostas comuns; sua ausência não bloqueia a futura submissão.

### 2.2 Versões técnicas

`VersaoForm1Integral` congela uma cópia imutável e lacrada de todo o envelope REV13, com autoria e origem do rascunho. Essa projeção preserva o retrato do FORM 1 em determinado momento, mas não deve ser usada como tabela de histórico operacional das quantidades.

Uma nova medição não deve exigir novo snapshot ou nova submissão integral. Da mesma forma, uma correção de medição não pode reescrever um snapshot já produzido.

### 2.3 Estruturas reaproveitáveis e lacuna

Podem ser reaproveitados os mecanismos já existentes de:

- identidade funcional e autorização;
- `comando_id`, idempotência e recusa de reutilização indevida;
- controle otimista por versão lida;
- evento e auditoria atômicos;
- texto canônico, lacre e histórico imutável;
- vínculo ao Registro LGPD.

As tabelas atuais de rascunho e versão do FORM 1 não representam adequadamente várias medições independentes e sucessivas. `VersaoInstrumento`, `VersaoForm1Integral`, pendências e ações obrigatórias possuem outras finalidades e não devem receber significados adicionais por conveniência.

## 3. Modelo conceitual recomendado

### 3.1 Conceitos

**Tipo de registro administrativo:** classificação padronizada do estoque contado, por exemplo “matrícula ativa” ou “cadastro individual de paciente”. É diferente da categoria de titular e não contém nome de pessoa.

**Medição:** declaração da quantidade de um tipo de registro em uma data de referência, vinculada a um Registro LGPD.

**Revisão da medição:** nova declaração temporal ou correção auditada de uma declaração anterior. A anterior permanece recuperável.

### 3.2 Relações

- Um Registro LGPD pode possuir zero, uma ou várias séries de medição.
- Cada série corresponde a um tipo padronizado de registro administrativo.
- Cada série pode possuir várias medições ao longo do tempo.
- Uma medição possui exatamente um estado quantitativo: valor numérico, `Não mensurado`, `A confirmar` ou `Não se aplica`.
- Uma correção referencia explicitamente a medição corrigida; uma nova medição temporal não a substitui.
- A quantidade descreve registros administrativos. Não se presume equivalência com quantidade de pessoas titulares.

### 3.3 Separação de responsabilidades

Recomenda-se tratar as medições como um agregado histórico vinculado ao Registro LGPD, e não como uma lista mutável dentro do envelope do FORM 1. O FORM 1 poderá consultar e apresentar o retrato vigente, enquanto o histórico conserva sua própria autoria, concorrência e auditoria.

Essa recomendação ainda não determina a criação de tabelas. Antes da implementação deve ser produzida uma decisão arquitetural comparando:

1. projeção relacional própria para catálogo, séries e medições; e
2. agregado JSON versionado separado do rascunho do FORM 1.

A alternativa relacional tende a ser mais adequada para histórico, integridade, relatórios e concorrência por série. A alternativa JSON reduz o esquema inicial, mas dificulta consultas, unicidade, correções concorrentes e evolução independente. Não se recomenda reutilizar o JSON do rascunho atual para essa finalidade.

## 4. Estrutura mínima proposta

### 4.1 Catálogo versionado de tipos

| Atributo | Regra proposta |
|---|---|
| `tipo_registro_id` | Identificador técnico estável |
| `codigo` | Código institucional único e não reutilizável |
| `nome` | Denominação padronizada, sem dados pessoais |
| `descricao` | Critério do que é contado |
| `versao_catalogo` | Versão da classificação usada |
| `vigente_de` / `vigente_ate` | Vigência sem apagar classificações antigas |
| `fonte_catalogo` | Ato, unidade ou documento que aprovou o tipo |

Não existe catálogo oficial aprovado nesta data. Os exemplos deste documento não o constituem.

### 4.2 Série de medição

| Atributo | Regra proposta |
|---|---|
| `serie_id` | Identificador técnico |
| `registro_lgpd_id` | Registro LGPD ao qual a série pertence |
| `tipo_registro_id` | Tipo padronizado e sua versão histórica |
| `versao` | Controle otimista da série |
| `criada_por` / `criada_em` | Autoria funcional e data de criação |

Deverá existir, quando vigente, no máximo uma série do mesmo tipo para o mesmo Registro LGPD. Mudança de classificação exige procedimento explícito, sem reinterpretação silenciosa do histórico.

### 4.3 Medição histórica

| Atributo | Regra proposta |
|---|---|
| `medicao_id` | Identificador técnico imutável |
| `serie_id` | Série e tipo de registro medido |
| `estado_quantidade` | `INFORMADA`, `NAO_MENSURADO`, `A_CONFIRMAR` ou `NAO_SE_APLICA` |
| `quantidade` | Inteiro não negativo; preenchido somente em `INFORMADA` |
| `data_referencia` | Data a que o estoque se refere |
| `fonte_institucional` | Referência controlada ou descrição limitada da origem da informação |
| `natureza` | `NOVA_MEDICAO` ou `CORRECAO` |
| `medicao_corrigida_id` | Obrigatório somente em correção |
| `justificativa_correcao` | Motivo factual e limitado da correção |
| `declarada_por` / `declarada_em` | Identidade funcional autenticada e instante da declaração |
| `comando_id` | Idempotência da operação |
| `evento_id` | Vínculo com evento e auditoria |
| `versao_lida` | Controle de concorrência da série |
| `lacre` | Integridade do conteúdo canônico da medição |

Regras mínimas de integridade:

- `quantidade >= 0` quando `estado_quantidade = INFORMADA`;
- quantidade nula nos três estados não numéricos;
- `medicao_corrigida_id` pertence à mesma série;
- correção não altera nem elimina a medição corrigida;
- `data_referencia` não é substituída por período genérico;
- fonte institucional e autoria são obrigatórias em medição informada e em correção;
- repetição do mesmo comando devolve o resultado original;
- mesma chave com parâmetros diferentes é recusada;
- evento, auditoria e projeção são gravados ou desfeitos juntos.

## 5. Exemplos exclusivamente fictícios

Os exemplos abaixo demonstram a estrutura e não criam catálogo oficial nem massa de banco.

| Registro LGPD fictício | Tipo de registro administrativo | Estado e quantidade | Data de referência | Fonte institucional fictícia |
|---|---|---:|---|---|
| Serviço escolar fictício | Matrícula ativa | `INFORMADA`: 720 | 31/10/2026 | Relatório sintético do sistema escolar fictício |
| Escola de judô fictícia | Inscrição ativa | `INFORMADA`: 160 | 31/10/2026 | Controle administrativo sintético da unidade fictícia |
| UBS fictícia | Cadastro individual de paciente | `INFORMADA`: 18.300 | 31/10/2026 | Relatório sintético do sistema municipal fictício |

Essas quantidades representam registros administrativos. Não autorizam concluir que existam 720, 160 ou 18.300 pessoas distintas.

## 6. Compatibilidade com a REV13 vigente

### 6.1 Preservação do histórico atual

- Rascunhos existentes continuam mantendo `2.9` como faixa e `2.9.1` como período.
- Snapshots técnicos e futuras versões já produzidas não são migrados, reescritos ou reinterpretados.
- A leitura de conteúdo antigo deve continuar exibindo a resposta original e identificar a revisão de contrato que lhe deu significado.
- Não haverá conversão automática de faixa para quantidade exata. Uma faixa não permite deduzir um número.
- Não haverá conversão automática de período para data de referência.

### 6.2 Estratégia futura de contrato

A estrutura repetível e histórica não cabe na semântica atual de dois campos escalares. Sua adoção exige versão posterior do contrato ou extensão explicitamente versionada, aprovada antes da migração.

Estratégia recomendada:

1. manter `2.9` e `2.9.1` inalterados para conteúdos REV13 existentes;
2. introduzir, em contrato posterior aprovado, uma coleção de referências às séries ou um retrato das medições vigentes;
3. exibir respostas legadas como “volume declarado na REV13”, sem tratá-las como medição estruturada;
4. permitir que uma medição estruturada seja criada posteriormente por ato próprio, sem submeter novamente o FORM 1;
5. quando um snapshot do FORM 1 for produzido, congelar apenas o retrato ou as referências vigentes naquele instante, sem duplicar a fonte histórica das medições.

`Não mensurado`, `A confirmar` e `Não se aplica` devem continuar sendo estados explícitos, nunca convertidos em zero.

## 7. Impactos futuros

### 7.1 Pré-validação

A matriz atual classifica `2.9` e `2.9.1` como facultativos. Uma implementação não poderá tornar a medição obrigatória sem aprovação e nova versão da matriz. A pré-validação futura deverá distinguir:

- nenhuma série cadastrada;
- série com medição válida;
- estado explícito não numérico;
- medição desatualizada segundo regra institucional ainda não definida;
- inconsistência técnica ou correção pendente.

### 7.2 Relatórios e painéis

Relatórios poderão apresentar evolução por tipo e data, mas não deverão:

- somar tipos heterogêneos como matrículas, prontuários, inscrições e processos;
- estimar quantidade de pessoas pela quantidade de registros;
- comparar unidades sem definição equivalente do que é contado;
- substituir `Não mensurado` ou `A confirmar` por zero;
- mostrar dado atual sem sua data de referência e fonte.

Agregações somente serão admitidas dentro de tipos compatíveis e segundo regra institucional documentada.

### 7.3 FORMs 2 e 3

Os FORMs 2 e 3 poderão futuramente consultar medições como evidência contextual para validação e avaliação de riscos. Eles não devem copiar a série, alterar medições ou inferir risco automaticamente apenas pelo volume. A versão e a data da medição utilizada precisam permanecer rastreáveis.

### 7.4 Snapshots do FORM 1

O snapshot técnico atual congela o envelope do rascunho. Uma evolução futura poderá acrescentar um retrato explícito das medições vigentes, com seus identificadores e lacres, mas o histórico completo deve permanecer na fonte própria. Atualizações posteriores não alteram o snapshot antigo.

## 8. Riscos de implementação

| Risco | Tratamento recomendado |
|---|---|
| Reinterpretar faixas antigas como números | Proibir conversão automática e preservar o contrato de origem |
| Contar pessoas em vez de registros | Textos de ajuda, nomenclatura do tipo e testes semânticos |
| Somar tipos incompatíveis | Relatórios agrupados por tipo versionado; agregação somente por regra aprovada |
| Perder medições anteriores | Histórico append-only e correção por referência |
| Correções apagarem erro original | Ato `CORRECAO`, justificativa, autoria e vínculo com a medição anterior |
| Concorrência produzir duas medições conflitantes | Bloqueio/versão lida, unicidade lógica e teste concorrente |
| Atualização exigir nova submissão do FORM 1 | Comando de medição independente do fluxo de submissão |
| Catálogo mudar o significado histórico | Código estável, versão e vigência do tipo |
| Fonte institucional virar texto pessoal ou sensível | Catálogo/referência controlada, limite textual e orientação explícita |
| Painel sugerir precisão inexistente | Exibir estado, data, fonte e tipo; não converter pendência em zero |
| Duplicar a fonte em snapshots | Congelar referências ou retrato, mantendo uma única fonte histórica |

## 9. Decisões institucionais necessárias

Antes de implementar, devem ser aprovados:

1. autoridade responsável pela curadoria do catálogo de tipos de registros;
2. catálogo inicial, códigos, descrições e critérios do que cada tipo conta;
3. quem pode declarar e corrigir medições e em qual alcance institucional;
4. fontes institucionais aceitas e forma de identificá-las;
5. periodicidade esperada, critérios de atualidade e tratamento de datas desconhecidas;
6. se `Não mensurado`, `A confirmar` e `Não se aplica` exigem justificativa;
7. rito de correção, justificativa mínima e eventual validação por terceiro;
8. versão de contrato que substituirá ou estenderá a semântica de `2.9` e `2.9.1`;
9. reflexo da nova estrutura na matriz de obrigatoriedade;
10. agregações autorizadas em relatórios e painéis;
11. regra de uso das medições nos FORMs 2 e 3;
12. política de retenção do próprio histórico de medições, distinta da temporalidade dos documentos inventariados.

## 10. Implementação incremental proposta

### Incremento H1 — decisão e catálogo

- aprovar o modelo conceitual e a versão de contrato;
- definir e versionar o catálogo mínimo de tipos;
- criar testes de integridade do catálogo;
- não alterar ainda o rascunho ou a interface.

### Incremento H2 — persistência histórica

- implementar a menor projeção aprovada e migração não destrutiva;
- criar comando de nova medição e comando de correção;
- registrar evento, auditoria, idempotência, versão lida, lacre e rollback;
- manter a funcionalidade sem rota pública até os testes de domínio.

### Incremento H3 — interface do FORM 1

- apresentar séries e medições sem perder as respostas legadas;
- permitir valor numérico ou estado não numérico, data, tipo e fonte;
- impedir dados individuais de cidadãos;
- manter rascunhos incompletos e submissão conforme o marco institucional vigente.

### Incremento H4 — snapshot e compatibilidade

- congelar no contrato aprovado o retrato ou referências das medições vigentes;
- provar que atualizações posteriores não modificam versões anteriores;
- conservar a leitura integral de rascunhos e snapshots REV13.

### Incremento H5 — relatórios e integrações futuras

- relatórios por tipo, data e fonte, sem soma heterogênea;
- indicadores de ausência ou desatualização sem declarar conformidade;
- consulta rastreável pelos FORMs 2 e 3, sem cópia ou inferência automática de risco.

## 11. Testes futuros mínimos

- zero, uma e várias séries por Registro LGPD;
- vários tipos no mesmo Registro sem soma automática;
- valor zero válido, valor positivo e rejeição de negativo, decimal e excesso de escala;
- `Não mensurado`, `A confirmar` e `Não se aplica` sem quantidade numérica;
- data e fonte ausentes ou inválidas conforme a regra aprovada;
- catálogo vigente, expirado, desconhecido e mudança de versão;
- nova medição preservando todas as anteriores;
- correção vinculada à medição correta, sem mutação ou exclusão da original;
- autorização permitida e negada;
- repetição idempotente e reutilização indevida de `comando_id`;
- concorrência sobre a mesma série;
- rollback entre comando, evento, auditoria e projeção;
- compatibilidade de rascunhos e snapshots REV13 legados;
- snapshot imutável diante de medição posterior;
- atualização de medição sem nova submissão integral;
- pré-validação sem mudança silenciosa de obrigatoriedade;
- relatórios sem soma de tipos incompatíveis e sem equivalência entre registros e pessoas;
- regressão integral dos contratos 2 e 3.

## 12. Conclusão

A arquitetura atual preserva adequadamente o conteúdo REV13, mas `2.9` e `2.9.1` não oferecem granularidade nem histórico próprio para medições estruturadas. A evolução recomendada é um agregado histórico vinculado ao Registro LGPD, reutilizando os mecanismos maduros de comandos e auditoria sem reutilizar indevidamente as tabelas de versão do formulário.

Esta conclusão é exclusivamente uma proposta técnica pendente de aprovação. Nenhum modelo, tabela, migração, regra, interface ou contrato foi autorizado por este documento.
