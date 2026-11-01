# Auditoria da matriz de obrigatoriedade — FORM 1 Integral REV13

**Incremento:** 8S

**Data:** 01/11/2026

**Catálogo:** `REV13-2026-09-20`

**Matriz auditada:** `MATRIZ-F1-REV13-OBR-v1`

**Situação:** auditoria técnica e funcional; não aprova nem altera a matriz e não libera submissão

## 1. Resultado executivo

Foram confrontados o Documento-Mestre REV13, o inventário canônico, o contrato candidato 3, a matriz vigente, as condições de domínio, a pré-validação consultiva e as decisões consolidadas no Incremento 8R.

O inventário externo e o catálogo executável possuem o mesmo SHA-256 (`37b0c10b...8cc002`). A matriz contém exatamente os mesmos **128 identificadores**, sem faltas, duplicidades ou excedentes. Os 125 campos dos Blocos 1 a 14 estão disponíveis no rascunho e os três campos `0.1`–`0.3` são tratados como metadados institucionais.

A cobertura estrutural está completa, mas a matriz **ainda não está pronta para governar uma submissão**. As exceções prioritárias são:

1. `0.2` e `0.3` continuam marcados como essenciais, embora a decisão institucional consolidada determine que não bloqueiem;
2. o ramo de WhatsApp contém uma condição documental que menciona alternativa inexistente em `8.3`;
3. exclusividades de seleções múltiplas permanecem sem decisão campo a campo;
4. `A confirmar` em campo facultativo não é hoje apresentado pela pré-validação como pendência não bloqueante;
5. falta a aprovação institucional da política que classificou 25 campos como essenciais e 69 como condicionais.

Não foi encontrada outra condição impossível de satisfazer. As condições codificadas cobrem os 69 campos condicionais, incluindo participantes repetíveis do Bloco 3 e destinatários estruturados de `10.2.1`. Essa correspondência técnica não transforma a política em decisão institucional aprovada.

## 2. Fontes e método

### 2.1 Fontes confrontadas

- Documento-Mestre `FORM1_INTEGRAL_REV13_PARA_CODEX.md`, SHA-256 `26f502eb...0719d`;
- inventário `INVENTARIO_CAMPOS_FORM1_REV13.csv`, SHA-256 `37b0c10b...8cc002`;
- [`app/catalogos/form1_rev13.csv`](../../app/catalogos/form1_rev13.csv), cópia íntegra do inventário;
- [contrato candidato 3](../arquitetura/CONTRATO_FORM1_INTEGRAL_REV13_CANDIDATO.md);
- [matriz vigente](MATRIZ_CAMPOS_FORM1_REV13.md);
- `app/form1_integral.py`, com IDs, catálogos e condições;
- `app/pre_validacao_form1_integral.py`, com classificação, ativação e pendências consultivas;
- [auditoria do Incremento 7](AUDITORIA_MATRIZ_F1_REV13_INCREMENTO_7.md);
- [consolidação do Incremento 8R](CONSOLIDACAO_FORM1_DECISOES_PENDENCIAS_2026-10-31.md).

### 2.2 Critério

Cada identificador foi verificado quanto a existência, classificação, condição, representação visual e comportamento da pré-validação. A auditoria tratou como exceção somente divergência comprovada, condição não decidida ou regra que possa bloquear ou descaracterizar uma futura submissão.

Não se presumiu aprovação porque uma regra está implementada. Também não se transformou silêncio da REV13 em obrigatoriedade.

## 3. Cobertura e classificações

### 3.1 Quantidade por classificação

| Classificação vigente | Quantidade | Situação da auditoria |
|---|---:|---|
| Essencial, somente leitura | 3 | `0.1` permanece essencial; `0.2` e `0.3` divergem da decisão institucional do 8R |
| Obrigatória essencial | 25 | Cobertura técnica completa; política ainda depende de aprovação institucional |
| Obrigatória condicional | 69 | Condições tecnicamente cobertas; exceções específicas nas seções 5 e 6 |
| Facultativa (REV13) | 4 | Coerente com indicação explícita da fonte |
| Facultativa nesta proposta | 27 | Não bloqueia; classificação provisória precisa integrar a aprovação da matriz |
| **Total** | **128** | **Cobertura integral** |

### 3.2 Cobertura por cabeçalho e bloco

As colunas seguem esta ordem: somente leitura, essencial, condicional, facultativa REV13 e facultativa proposta.

| Grupo | Total | Somente leitura | Essencial | Condicional | Facultativa REV13 | Facultativa proposta |
|---|---:|---:|---:|---:|---:|---:|
| Cabeçalho `0.1`–`0.3` | 3 | 3 | 0 | 0 | 0 | 0 |
| Bloco 1 | 5 | 0 | 3 | 1 | 0 | 1 |
| Bloco 2, incluindo OUV/e-SIC | 27 | 0 | 7 | 11 | 3 | 6 |
| Bloco 3 | 7 | 0 | 1 | 6 | 0 | 0 |
| Bloco 4 | 9 | 0 | 1 | 7 | 0 | 1 |
| Bloco 5 | 1 | 0 | 1 | 0 | 0 | 0 |
| Bloco 6 | 5 | 0 | 1 | 2 | 0 | 2 |
| Bloco 7 | 1 | 0 | 1 | 0 | 0 | 0 |
| Bloco 8 | 23 | 0 | 2 | 14 | 1 | 6 |
| Bloco 9 | 5 | 0 | 1 | 2 | 0 | 2 |
| Bloco 10 | 12 | 0 | 1 | 10 | 0 | 1 |
| Bloco 11 | 8 | 0 | 1 | 5 | 0 | 2 |
| Bloco 12 | 10 | 0 | 2 | 5 | 0 | 3 |
| Bloco 13 | 4 | 0 | 1 | 0 | 0 | 3 |
| Bloco 14 | 8 | 0 | 2 | 6 | 0 | 0 |
| **Total** | **128** | **3** | **25** | **69** | **4** | **27** |

## 4. Marcadores visuais

| Marcador | Regra implementada | Resultado da auditoria |
|---|---|---|
| `*` | Obrigatória essencial ou essencial somente leitura; também substitui `**` quando a condição está ativa | Tecnicamente coerente, exceto em `0.2` e `0.3`, que não deverão bloquear |
| `**` | Obrigatória condicional ainda dependente da condição | Coerente; quando ativa, a interface mostra `*` e “Obrigatório neste caso” |
| `***` | Categoria visual reservada para “Recomendado” | Nenhum dos 128 campos possui essa classificação; portanto, o marcador não é usado |
| `****` | Facultativa, tanto explícita na REV13 quanto provisória na proposta | Coerente; a interface distingue os dois rótulos textuais |

Os marcadores são apresentação da matriz, não fonte autônoma de regra. Assim, a correção de `0.2` e `0.3` deve começar em nova versão da matriz e somente depois alcançar a interface e a pré-validação.

## 5. Relatório de exceções

Prioridades: **P0** impede liberação segura da submissão; **P1** deve ser resolvida antes da liberação ou formalmente aceita; **P2** é manutenção documental ou evolução não bloqueante.

| Ref. | Campo(s) | Problema comprovado | Impacto | Recomendação | Prioridade |
|---|---|---|---|---|---|
| 8S-01 | `0.2` | Matriz e interface tratam cargo/função como essencial `*`; o 8R determinou que sua ausência não bloqueie e que seja facultativo ou automático quando confiável | Uma futura submissão fiel à matriz bloquearia indevidamente; preenchimento livre violaria os guardrails de identidade | Versionar a matriz para torná-lo não bloqueante; manter somente leitura quando houver fonte autenticada, sem exigir valor ausente | P0 |
| 8S-02 | `0.3` | Matriz e interface tratam e-mail institucional como essencial `*`; o 8R determinou que seja facultativo e não bloqueante | Mesmo conflito de bloqueio; não há fonte institucional integrada na PoC | Versionar a matriz como facultativo/não bloqueante e preservar a proibição de inventar e-mail | P0 |
| 8S-03 | 25 essenciais e 69 condicionais | A classificação é tecnicamente consistente, mas a REV13 não declara obrigatoriedade em todos os campos; a própria fonte manda não converter silêncio em obrigação | Implementação atual pode ser tomada indevidamente como aprovação funcional de 94 regras | Aprovar institucionalmente a matriz por relatório de exceções, após aplicar as decisões deste documento | P0 |
| 8S-04 | `8.7`, `8.8`, `8.8.1`, `8.9` | A matriz/REV13 diz “WhatsApp corporativo ou pessoal”, mas `8.3` contém somente `WhatsApp corporativo`; o ramo pessoal é impossível de acionar | Regra documental e catálogo divergem; uma alteração unilateral mudaria o contrato | Formalizar, na fonte funcional, se o gatilho vigente é apenas `WhatsApp corporativo` ou criar versão contratual que acrescente a alternativa pessoal | P0 |
| 8S-05 | Seleções múltiplas com `A confirmar` | Fora de `5.1` e `13.1`, a exclusividade de `A confirmar` não foi aprovada campo a campo; a pré-validação registra F1-D06, mas o domínio não inventa bloqueios | Respostas provisórias podem coexistir com respostas factuais sem regra institucional uniforme | Decidir F1-D06 por família de campo e registrar explicitamente as combinações proibidas antes de validar submissão | P0 |
| 8S-06 | `3.4.1`, `13.4` | São seleções múltiplas com `Não se aplica`; a política da matriz proíbe coexistência com alternativa factual ou `A confirmar`, mas somente `13.1` aplica exclusividade explícita no domínio | A futura submissão poderia aceitar combinação contrária à política declarada | Confirmar a regra e implementá-la após versionar a matriz; não generalizar para outros campos sem alternativa equivalente | P0 |
| 8S-07 | 28 facultativos que admitem `A confirmar` | A matriz determina que `A confirmar` facultativo seja apresentado como pendência de confirmação, sem bloquear; a pré-validação ignora facultativos e não gera esse alerta | Informação provisória pode passar sem destaque, embora não deva bloquear | Criar, no próximo incremento funcional, categoria não bloqueante de aviso separada de `incompletos` e de dependências institucionais | P1 |
| 8S-08 | `2.8.1`, `2.9.1`, `2.10.1` | A REV13 não explicita se o período só aparece quando o volume correspondente foi informado; a matriz os mantém sempre visíveis e facultativos | Permite período sem volume ou volume sem período; não impede submissão, mas reduz consistência analítica | Decidir se continuarão independentes ou se haverá condição; preservar `2.9` como evolução futura do 8Q | P1 |
| 8S-09 | `6.1.1` | Condição exata não é explicitada; permanece facultativo e sempre visível. A interface usa redação mais clara, mas o catálogo e o contrato conservam o texto REV13 | Não há bloqueio, porém existe diferença entre apresentação e fonte e uma proposta futura de seleção múltipla | Submeter a redação à aprovação e decidir a evolução catalogada em versão futura, sem converter rascunhos existentes | P1 |
| 8S-10 | `0.1` | É essencial somente leitura e funciona com identidade fictícia na PoC; integração institucional real ainda não existe | Não bloqueia a demonstração fictícia, mas é dependência de implantação | Preservar como essencial e exigir fonte autenticada antes de uso institucional real | P1 |
| 8S-11 | Contrato candidato 3 | O cabeçalho do documento ainda descreve “rascunho parcial dos Blocos 1 a 5”, embora os 14 blocos estejam implementados | Pode induzir leitura equivocada do estágio, sem alterar comportamento | Atualizar futuramente apenas o estado documental, sem mexer nas regras auditadas | P2 |

### 5.1 Identificadores agrupados em 8S-05

Há 31 seleções múltiplas com `A confirmar`. `5.1` e `13.1` já possuem exclusividade expressa; permanecem **29** sob F1-D06:

`2.5`, `2.13.1`, `OUV.1`, `OUV.2`, `3.2`, `3.4`, `3.4.1`, `3.5.1`, `4.1`, `4.2.1`, `4.2.2`, `4.2.3`, `4.2.4.1`, `6.1`, `7.1`, `8.2`, `8.2.2.1`, `8.3`, `8.4.1`, `8.4.3`, `8.6.1`, `8.6.4`, `9.1`, `10.2`, `10.3`, `10.8.1`, `11.1`, `12.1.3` e `13.4`.

Essa relação não propõe que todas recebam a mesma regra; apenas delimita onde a decisão ainda precisa ser tomada.

### 5.2 Identificadores agrupados em 8S-07

Os 28 facultativos que admitem `A confirmar` são:

`1.1`, `2.5`, `2.8`, `2.8.1`, `2.9`, `2.9.1`, `2.10`, `2.10.1`, `2.12`, `2.13`, `4.2`, `6.2`, `8.2`, `8.2.1`, `8.2.2`, `8.4`, `8.5`, `8.6`, `9.2`, `10.9`, `11.2`, `11.3`, `12.3`, `12.4`, `12.5`, `13.2`, `13.3` e `13.4`.

Em todos eles, `A confirmar` deve continuar não bloqueante conforme a política vigente, mas não deve desaparecer do resumo consultivo.

## 6. Condições que exigem esclarecimento

| Campo(s) | Situação atual | Esclarecimento necessário |
|---|---|---|
| `8.7`–`8.9` | Implementação ativa somente com `WhatsApp corporativo`; matriz menciona também pessoal | Resolver a inconsistência da fonte sem inventar alternativa em `8.3` |
| `2.8.1`, `2.9.1`, `2.10.1` | Facultativos e sempre visíveis | Decidir dependência em relação ao volume correspondente |
| `6.1.1` | Facultativo e sempre visível | Aprovar redação e decidir se permanece texto livre ou evolui para catálogo múltiplo |
| Seleções de 8S-05 | F1-D06 pendente | Definir quando `A confirmar` é exclusivo e se outras alternativas são incompatíveis |
| `3.4.1`, `13.4` | Política geral de `Não se aplica` não refletida no domínio | Confirmar exclusividade e alinhar matriz, domínio e testes |

`10.2.1` **não permanece como lacuna estrutural**: a matriz e a pré-validação já o tratam por categoria concreta de `10.2`, com ocorrências repetíveis, compatibilidade legada e avaliação humana quando necessária. Ainda será preciso aprovar a competência da avaliação humana, mas não inventar nova condição.

## 7. Respostas especiais e vazias

### 7.1 `A confirmar`

- é aceito no rascunho quando consta no catálogo;
- em essencial ou condicional ativo, `_respondido` o trata como não conclusivo e a pré-validação aponta o campo como incompleto;
- em facultativo, não bloqueia, mas falta o alerta não bloqueante descrito em 8S-07;
- em `5.1`, é exclusivo por decisão expressa;
- em `13.1`, integra o conjunto de alternativas expressamente excludentes;
- nas demais seleções múltiplas, a decisão F1-D06 continua aberta.

### 7.2 `Não se aplica`

- é conclusivo quando a alternativa existe e satisfaz a obrigatoriedade do próprio campo;
- desativa dependentes quando a condição registrada não inclui esse valor;
- não deve ser convertido em vazio, `Não` ou zero;
- a exclusividade está implementada em `13.1`, mas precisa ser alinhada em `3.4.1` e `13.4` conforme 8S-06.

### 7.3 Resposta vazia

- é permitida no rascunho;
- aparece como incompleta quando o campo é essencial ou condicional ativo;
- não bloqueia quando o campo é facultativo;
- é diferente de ausência de canais expressamente confirmada em `2.1`: nesse caso, o retrato histórico vazio do APA é uma decisão registrada e satisfaz o campo somente leitura, sem significar falta de resposta.

## 8. Diferenças entre REV13 e implementação

| Tema | REV13/matriz | Implementação atual | Conclusão |
|---|---|---|---|
| Cobertura | 128 IDs | 128 IDs cobertos | Conforme |
| Rascunho incompleto | Permitido | Permitido | Conforme |
| Condicionais inequívocas | Campos dependentes | 69 condicionais cobertos por regras gerais e rotinas específicas | Conforme tecnicamente |
| `0.2` e `0.3` | Essenciais na matriz v1 | Mostrados como dependências institucionais, sem fonte; 8R determina não bloqueio | Divergência P0 da matriz e da sinalização |
| `A confirmar` obrigatório | Não conclusivo | Incompleto na pré-validação | Conforme |
| `A confirmar` facultativo | Não bloqueia, mas deve ser sinalizado | Não gera alerta | Divergência P1 |
| `Não se aplica` | Conclusivo e exclusivo em seleção múltipla segundo a política | Conclusivo; exclusividade parcial | Divergência P0 em `3.4.1` e `13.4` |
| Complementos de “Outro” | Política F1-D05 para 38 contextos | Pré-validação exige complemento ativo, sem impedir rascunho | Conforme |
| WhatsApp | Texto menciona corporativo ou pessoal; `8.3` só oferece corporativo | Ramo ativa somente com corporativo | Divergência documental P0 |
| `10.2.1` | Identificação por destinatário concreto | Estrutura repetível, por categoria, com legado preservado | Conforme tecnicamente |
| `2.9` histórico | Evolução futura aprovada conceitualmente | Faixa REV13 preservada | Conforme ao limite do 8Q; não implementar no 8S |
| `6.1.1` catalogado | Evolução futura proposta | Texto existente preservado, com redação visual mais clara | Conforme ao limite do 8R; não implementar no 8S |
| Submissão | Depende de aprovação e regras fechadas | Bloqueada; pré-validação é consultiva | Conforme |

## 9. Correções mínimas antes da futura submissão

1. Produzir uma nova versão candidata da matriz, sem editar silenciosamente `MATRIZ-F1-REV13-OBR-v1`.
2. Reclassificar `0.2` e `0.3` como não bloqueantes, preservando somente leitura quando houver fonte confiável.
3. Manter `0.1` essencial e registrar a dependência de identidade institucional para uso real.
4. Resolver formalmente o gatilho de WhatsApp entre a fonte, o catálogo e a regra condicional.
5. Decidir F1-D06, pelo menos para todas as seleções múltiplas com `A confirmar` e para `Não se aplica` em `3.4.1` e `13.4`.
6. Acrescentar à futura pré-validação uma categoria de alerta não bloqueante para `A confirmar` em facultativos.
7. Deliberar sobre as condições de `2.8.1`, `2.9.1`, `2.10.1` e `6.1.1`, sem antecipar as evoluções de `2.9` e `6.1.1`.
8. Aprovar institucionalmente as classificações restantes e o marco de liberação.
9. Somente depois alinhar interface, pré-validação e validação de submissão à nova matriz versionada.

Essas correções não autorizam a submissão. O fluxo ARP → APA → T.I. e as competências posteriores também precisam de especificação própria.

## 10. Testes recomendados para o próximo incremento

Após as decisões institucionais e a criação de nova versão da matriz:

1. cobertura exata dos 128 IDs, sem duplicidade e com contagens aprovadas;
2. `0.1` obrigatório e somente leitura;
3. ausência de `0.2` e `0.3` sem bloqueio, sem permitir identidade digitada livremente;
4. teste parametrizado das 69 condições, incluindo ramo ativo, inativo e resposta forjada;
5. representação de `*`, `**`, `***` e `****` conforme a matriz aprovada;
6. `A confirmar` bloqueando essencial/condicional ativo e gerando apenas alerta em facultativo;
7. `Não se aplica` conclusivo e exclusivo nos campos aprovados;
8. todas as exclusividades F1-D06 aprovadas, com combinações válidas e inválidas;
9. ramo WhatsApp com o gatilho formalmente decidido;
10. complementos dos 38 contextos de “Outro”, ativos, ausentes e historicamente inativos;
11. participantes do Bloco 3 validados por ocorrência;
12. destinatários de `10.2.1` validados por categoria e modalidade;
13. ausência de canais expressamente confirmada distinta de resposta vazia em `2.1`;
14. preservação de rascunho e conteúdo diante de rejeição da validação;
15. pré-validação sem mutação, sem versão submetida e sem mudança de estado;
16. regressão integral do contrato nuclear 2 e do contrato candidato 3.

## 11. Conclusão

A matriz v1 possui excelente cobertura técnica e corresponde integralmente ao catálogo REV13, mas ainda mistura decisões provisórias, regras implementadas e deliberações institucionais posteriores. O principal trabalho restante não é revisar 128 perguntas uma a uma com o usuário: é decidir e corrigir as exceções listadas neste relatório.

Até que os itens P0 sejam resolvidos, a pré-validação deve permanecer consultiva e a submissão integral bloqueada. Nenhum campo, regra, contrato, código ou dado foi alterado por esta auditoria.
