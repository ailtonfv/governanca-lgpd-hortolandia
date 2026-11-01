# Fluxo de conclusão institucional do FORM 1 Integral

**Incremento:** 8T

**Data:** 01/11/2026

**Situação:** especificação documental; não libera submissão nem altera código, contrato, matriz ou banco

## 1. Resumo executivo

O FORM 1 Integral já possui os 14 blocos, rascunho incompleto, retomada, atribuição do Agente Responsável pelo Preenchimento (ARP), pré-validação consultiva e snapshot técnico imutável do contrato candidato 3. Ainda não existem, porém, atos ou estados executáveis para o ARP declarar o preenchimento concluído e para o Agente Público Autorizado (APA) confirmar sua conclusão institucional.

A decisão institucional aprovada estabelece o percurso **ARP conclui o levantamento factual → APA confere e confirma a conclusão institucional → sistema preserva a versão e a disponibiliza aos perfis autorizados**. Não haverá envio manual à T.I. nem exportação obrigatória para Excel. A T.I. administra e presta suporte; não recebe automaticamente acesso irrestrito ao conteúdo nem competência jurídica.

A menor evolução segura requer três situações próprias do FORM 1 Integral: `EM_PREENCHIMENTO`, `AGUARDANDO_CONFERENCIA_APA` e `CONCLUIDO_INSTITUCIONALMENTE`. A devolução do APA retorna o instrumento a `EM_PREENCHIMENTO`, preservando o snapshot conferido, a justificativa e o evento; não exige, inicialmente, um quarto estado persistente.

Essa solução é compatível com o event sourcing pragmático, o snapshot do Incremento 8C e a continuidade institucional do APA. Ela não deve reutilizar silenciosamente os estados do FORM 1 sintético: o contrato nuclear 2 permanece separado. A implementação continua bloqueada pelas seis exceções P0 da auditoria 8S e pela aprovação versionada da matriz.

### 1.1 Legenda de situação

- **Implementado:** comportamento comprovadamente disponível na aplicação.
- **Decisão institucional aprovada, ainda não implementada:** comportamento definido pelo 8T, sem execução atual.
- **Proposta técnica dependente de aprovação:** desenho mínimo recomendado, ainda sujeito ao incremento técnico e às decisões indicadas neste documento.

## 2. Fluxo institucional aprovado

1. **Implementado — preenchimento factual.** O ARP autorizado inicia, salva e retoma rascunhos incompletos do FORM 1 Integral. Cada gravação preserva autoria, versão lida, lacre e auditoria.
2. **Decisão aprovada — declaração do ARP.** Quando entender que terminou o levantamento, o ARP pratica ato explícito de conclusão do preenchimento. O sistema congela a versão exata disponibilizada ao APA.
3. **Decisão aprovada — conferência do APA.** O APA em exercício confere a versão e escolhe entre devolvê-la para correção ou confirmar sua conclusão institucional.
4. **Decisão aprovada — preservação e disponibilidade.** A confirmação registra versão, conteúdo, autoria, matrícula funcional proveniente da identidade institucional, papel exercido, data, evento e auditoria. A versão confirmada permanece disponível aos agentes e às unidades autorizadas para as etapas seguintes.
5. **Decisão aprovada — limites da conclusão.** Conclusão institucional significa que o levantamento factual do FORM 1 foi encerrado pela Secretaria responsável. Não significa legitimidade jurídica, ausência de riscos, adequação à LGPD, validação do FORM 2 ou conclusão dos FORMs 2, 3 e 4.

Não existe etapa de “enviar arquivo à T.I.”. A disponibilização ocorre no próprio sistema, por perfil e alcance institucional. Essa decisão esclarece a formulação anterior do Incremento 8R que tratava a T.I. como destinatária do encaminhamento: a T.I. não é destinatária obrigatória do conteúdo nem cria uma transição manual adicional.

## 3. Estados atuais e estados propostos

### 3.1 Situação atual implementada

O FORM 1 Integral não possui máquina de estados própria. Seu estado é inferido por projeções independentes:

- `AtribuicaoForm1Integral` identifica o ARP atual; o histórico permanece no livro de atos;
- `RascunhoForm1Integral` guarda o conteúdo editável, a versão, a autoria do último salvamento, a data e o lacre;
- `VersaoForm1Integral` guarda snapshot técnico imutável do contrato 3, com a natureza `preparacao_tecnica_sem_submissao` e `submissao_habilitada: false`;
- a pré-validação é consultiva e não altera estado;
- não há rota, botão ou comando de conclusão institucional.

O estado global do `Registro` e o ciclo do FORM 1 sintético pertencem ao contrato nuclear 2. Eles não representam o ciclo do FORM 1 Integral e não devem ser reinterpretados.

### 3.2 Estados mínimos propostos

| Situação | Significado | Edição do rascunho |
|---|---|---|
| `EM_PREENCHIMENTO` | ARP autorizado está preparando ou corrigindo o levantamento | Permitida ao ARP autorizado |
| `AGUARDANDO_CONFERENCIA_APA` | ARP declarou conclusão e uma versão exata aguarda decisão do APA | Bloqueada; o snapshot permanece imutável |
| `CONCLUIDO_INSTITUCIONALMENTE` | APA confirmou a conclusão da versão submetida à conferência | Bloqueada; consulta conforme permissão |

```text
EM_PREENCHIMENTO
    | ARP declara conclusão do preenchimento
    v
AGUARDANDO_CONFERENCIA_APA
    | APA devolve com justificativa          | APA confirma a versão
    v                                        v
EM_PREENCHIMENTO                  CONCLUIDO_INSTITUCIONALMENTE
    | nova correção gera nova versão
    +-------------------------------------> nova conferência
```

**Proposta técnica dependente de aprovação:** a devolução não precisa ser um quarto estado. O evento de devolução e sua justificativa distinguem o rascunho corrigido de um primeiro preenchimento. Se relatórios operacionais exigirem fila própria de devolvidos, uma projeção de leitura pode derivá-la do último evento sem ampliar a máquina de estados.

### 3.3 Transições mínimas

| Ato proposto | Origem | Destino | Executor | Efeito atômico mínimo |
|---|---|---|---|---|
| Declarar preenchimento concluído | `EM_PREENCHIMENTO` | `AGUARDANDO_CONFERENCIA_APA` | ARP atual autorizado | validar versão lida, executar regras bloqueantes aprovadas, congelar snapshot, registrar evento e auditoria |
| Devolver para correção | `AGUARDANDO_CONFERENCIA_APA` | `EM_PREENCHIMENTO` | APA em exercício | exigir justificativa, preservar snapshot examinado, liberar nova versão do rascunho e registrar evento |
| Confirmar conclusão institucional | `AGUARDANDO_CONFERENCIA_APA` | `CONCLUIDO_INSTITUCIONALMENTE` | APA em exercício | confirmar o mesmo snapshot e lacre, registrar autoria funcional, data, evento, auditoria e projeção |

Não se propõe, neste incremento, reabertura de FORM 1 já concluído. Correção posterior à conclusão requer decisão própria sobre competência, motivo, efeito nos FORMs seguintes e criação de nova versão, sem sobrescrever a versão confirmada.

## 4. Matriz de permissões por papel

| Papel | Preencher e corrigir | Declarar conclusão do preenchimento | Devolver | Confirmar conclusão institucional | Consultar após conclusão | Observação |
|---|---:|---:|---:|---:|---:|---|
| ARP atual autorizado | Sim | Sim | Não | Não | Conforme alcance | A indicação como ARP não concede acesso por si só; autorização vigente continua obrigatória |
| APA em exercício | Somente se também estiver autorizado como preenchedor/ARP | Somente quando atuar também como ARP | Sim | Sim | Sim, no alcance da Secretaria | Abertura do Registro não concede automaticamente permissão de edição |
| Chefia autorizada | Não por esse papel | Não | Não | Não | Sim, conforme alcance | Pode registrar observação sem veto, bloqueio ou aprovação implícita |
| T.I. técnica | Não | Não | Não | Não | Somente com permissão explícita | Administra infraestrutura, suporte e indicadores operacionais; não recebe acesso irrestrito nem validação jurídica automática |
| DPO e áreas competentes | Conforme perfil específico | Não por presunção | Não por presunção | Não por presunção | Conforme perfil | Atuam nas etapas e competências formalmente atribuídas, inclusive nos futuros FORMs |
| Sistema | Não decide | Não decide | Não decide | Não decide | Produz projeções autorizadas | Executa efeitos derivados, nunca substitui o ato administrativo humano |

### 4.1 Quando APA e ARP são a mesma pessoa

**Decisão aprovada:** a mesma pessoa pode abrir e preencher o Registro quando possuir ambas as autorizações. Para preservar a distinção funcional, deverá praticar dois comandos explícitos e sucessivos: primeiro, como ARP, declara a conclusão do preenchimento; depois, como APA em exercício, confirma institucionalmente a versão.

O sistema deve registrar a mesma identidade com papéis exercidos distintos, dois `comando_id`, datas e eventos próprios. A segunda ação não será automática. A regra de segregação do fluxo nuclear, que impede o autor da submissão de analisar a própria versão, não deve ser transferida silenciosamente ao contrato 3, pois a decisão institucional do FORM 1 Integral admite APA e ARP coincidentes.

## 5. Autoria, auditoria, correção e continuidade

### 5.1 Critérios do ato do ARP

**Proposta técnica dependente de aprovação:** o comando só poderá prosseguir quando:

- o executor for o ARP atual e possuir autorização vigente sobre o Registro;
- o Registro permanecer sob a mesma Secretaria responsável;
- a versão lida for a versão corrente e seu lacre conferir;
- não houver gravação concorrente posterior;
- a matriz versionada aplicável tiver aprovação institucional;
- não houver campo obrigatório ativo incompleto nem regra P0 sem decisão;
- alertas não bloqueantes permaneçam visíveis, sem serem convertidos em respostas;
- o `comando_id` ainda seja válido para aquele conteúdo e estado.

O sistema deverá criar ou selecionar o snapshot imutável da versão exata declarada. O snapshot técnico 8C pode ser reutilizado como infraestrutura, mas sua natureza atual não será retroativamente convertida em submissão.

### 5.2 Critérios do ato do APA

**Proposta técnica dependente de aprovação:** o comando deverá exigir:

- APA em exercício no momento do ato, resolvido pelo mecanismo de titularidade, suplência ou substituição vigente;
- alcance sobre a Secretaria responsável pelo Registro;
- situação `AGUARDANDO_CONFERENCIA_APA`;
- referência ao mesmo snapshot, número, versão de rascunho, contrato e lacre conferidos;
- confirmação humana explícita ou devolução com justificativa;
- versão do estado lida e `comando_id`, evitando decisão dupla ou tela desatualizada.

A substituição do APA durante a conferência não invalida o trabalho do ARP nem o snapshot. O novo APA em exercício recebe a competência futura, enquanto o histórico preserva quem ocupava cada papel em cada ato.

### 5.3 Correção e devolução

- a devolução nunca apaga nem reescreve a versão examinada;
- a justificativa é obrigatória, identificada e auditada;
- o ARP corrige um novo estado do rascunho, mantendo autoria de cada salvamento;
- nova declaração do ARP cria ou vincula nova versão imutável;
- a versão devolvida continua recuperável no histórico;
- observação da chefia não equivale a devolução e não impede o fluxo;
- eventual reabertura após confirmação institucional permanece fora do escopo e depende de decisão própria.

### 5.4 Idempotência, concorrência e rollback

Cada ato deverá seguir o padrão vigente:

- `comando_id` idempotente, com repetição devolvendo o resultado original;
- rejeição da mesma chave com parâmetros diferentes;
- controle otimista pela versão lida do rascunho e da projeção de ciclo;
- unicidade da decisão válida para o mesmo snapshot;
- evento, auditoria, snapshot e projeção gravados na mesma transação;
- falha em qualquer gravação desfaz todo o comando;
- tentativa negada gera auditoria sem produzir mudança de domínio;
- nenhuma confirmação pode apontar para conteúdo cujo lacre não confira.

### 5.5 Projeção de estado e persistência

Os dados mínimos consultáveis são: situação atual, versão da projeção, snapshot sob conferência, autoria e data da declaração do ARP, autoria e data da confirmação do APA e último evento relevante.

**Proposta técnica dependente de aprovação:** uma projeção própria do ciclo do FORM 1 Integral é arquiteturalmente mais clara do que acrescentar estado ao snapshot imutável ou reutilizar tabelas do contrato 2. A escolha física entre nova projeção e extensão aditiva de estrutura existente será tomada somente no desenho técnico do próximo incremento; este documento não autoriza tabela ou migração.

### 5.6 Disponibilidade para os próximos FORMs

Após a confirmação, o sistema deverá expor aos perfis autorizados a identificação da versão institucionalmente concluída. FORMs 2, 3 e 4 deverão referenciar essa versão, sem copiar arquivo manualmente, sem alterar seu conteúdo e sem pressupor que a T.I. seja validadora. Correções posteriores deverão indicar quais etapas são afetadas e nunca reescrever o histórico.

## 6. Análise das seis exceções P0

As referências abaixo reproduzem os identificadores da auditoria 8S. Nenhuma correção é autorizada por este documento.

### 6.1 8S-01 — Cargo ou função `0.2`

- **Comportamento atual:** matriz e interface classificam `0.2` como essencial somente leitura e exibem `*`; não há fonte institucional integrada.
- **Problema:** a decisão consolidada determina que a ausência não bloqueie. Permitir digitação livre enfraqueceria a identidade funcional.
- **Impacto sobre a submissão:** a aplicação literal da matriz bloquearia indevidamente a declaração do ARP.
- **Decisão existente:** matrícula funcional é a identificação principal; cargo/função é não bloqueante e pode ser automático quando houver fonte confiável.
- **Correção mínima:** criar nova versão da matriz que o torne não bloqueante; mantê-lo somente leitura quando houver fonte autenticada e não inventar valor ausente.
- **Testes necessários:** ausência sem bloqueio; valor autenticado exibido; tentativa de preenchimento livre recusada; snapshot preserva a origem institucional quando existente.
- **Situação:** **resolvida conceitualmente; dependente de versionamento e implementação**.

### 6.2 8S-02 — E-mail institucional `0.3`

- **Comportamento atual:** matriz e interface classificam `0.3` como essencial somente leitura; a PoC não integra fonte de e-mail.
- **Problema:** a ausência não deve bloquear e nenhum e-mail pode ser inventado.
- **Impacto sobre a submissão:** bloqueio indevido ou risco de identidade digitada sem fonte.
- **Decisão existente:** campo facultativo e não bloqueante; somente leitura quando houver fonte institucional.
- **Correção mínima:** versionar a matriz como não bloqueante e preservar a proibição de preenchimento identitário livre.
- **Testes necessários:** ausência sem bloqueio; valor autenticado; rejeição de valor forjado; autoria continua baseada na matrícula/identidade da sessão.
- **Situação:** **resolvida conceitualmente; dependente de versionamento e implementação**.

### 6.3 8S-03 — Política dos 25 essenciais e 69 condicionais

- **Comportamento atual:** a matriz cobre tecnicamente 128/128 IDs e classifica 25 como essenciais e 69 como condicionais; a pré-validação usa essas regras de forma consultiva.
- **Problema:** correspondência técnica não equivale a aprovação institucional; a REV13 não declara obrigatoriedade para todos os casos.
- **Impacto sobre a submissão:** 94 regras provisórias poderiam bloquear ou admitir conclusão sem mandato institucional.
- **Decisão existente:** a matriz deverá ser adotada por versão e aprovação expressa, após tratamento das exceções.
- **Correção mínima:** produzir versão candidata corrigida, relatório de exceções e ato de aprovação; manter o bloqueio até essa decisão.
- **Testes necessários:** cobertura exata dos 128 IDs; classificação e ativação por bloco; campos condicionais ativos/inativos; vínculo do snapshot à versão aprovada da matriz.
- **Situação:** **pendente de decisão institucional**.

### 6.4 8S-04 — WhatsApp em `8.7`, `8.8`, `8.8.1` e `8.9`

- **Comportamento atual:** os campos condicionais são ativados por `WhatsApp corporativo`; a matriz/REV13 também menciona WhatsApp pessoal, alternativa inexistente em `8.3`.
- **Problema:** o ramo pessoal é impossível e canal de comunicação não se confunde com ambiente de armazenamento ou repositório oficial.
- **Impacto sobre a submissão:** regra impossível de satisfazer ou alteração unilateral do catálogo.
- **Decisão existente:** preservar as três dimensões e não criar exigência automática sem decisão sobre o gatilho.
- **Correção mínima:** decidir formalmente se o contrato vigente trata apenas WhatsApp corporativo ou se uma nova versão incluirá a alternativa pessoal; alinhar fonte, catálogo, matriz e condição.
- **Testes necessários:** gatilho decidido presente/ausente; canal não inferindo armazenamento; respostas legadas preservadas; código forjado rejeitado.
- **Situação:** **pendente de decisão institucional**.

### 6.5 8S-05 — Exclusividade F1-D06 de `A confirmar`

- **Comportamento atual:** `5.1` e `13.1` possuem exclusividade expressa; 29 outras seleções múltiplas admitem `A confirmar` sem regra aprovada campo a campo. A pré-validação registra a pendência, mas o domínio não inventa incompatibilidades.
- **Problema:** resposta provisória pode coexistir com respostas factuais sem política uniforme.
- **Impacto sobre a submissão:** combinações semanticamente contraditórias podem ser aceitas ou bloqueadas por inferência indevida.
- **Decisão existente:** F1-D06 exige decisão por família de campo; não se deve generalizar silenciosamente.
- **Correção mínima:** aprovar combinações permitidas e proibidas por grupo, versionar a matriz e somente então alinhar domínio e interface, sem reescrever dados históricos.
- **Testes necessários:** combinações válidas/inválidas parametrizadas; rascunho permissivo quando aplicável; submissão bloqueada apenas pela regra aprovada; conteúdo legado preservado.
- **Situação:** **pendente de decisão institucional**.

### 6.6 8S-06 — `Não se aplica` em `3.4.1` e `13.4`

- **Comportamento atual:** a matriz proíbe coexistência de `Não se aplica` com alternativa factual ou `A confirmar`, mas o domínio só possui exclusividade explícita relacionada em `13.1`.
- **Problema:** política declarada e validação executável divergem.
- **Impacto sobre a submissão:** combinação contrária à política pode chegar à conclusão ou uma generalização pode atingir campos não aprovados.
- **Decisão existente:** a regra precisa ser confirmada especificamente para `3.4.1` e `13.4`.
- **Correção mínima:** confirmar a exclusividade, versionar a matriz e implementar somente nesses identificadores, salvo nova decisão expressa.
- **Testes necessários:** `Não se aplica` isolado; coexistência recusada; alternativa factual isolada; `A confirmar` conforme F1-D06; rascunhos antigos sem conversão automática.
- **Situação:** **pendente de confirmação institucional e de implementação**.

## 7. Decisões ainda necessárias

Antes de liberar a conclusão institucional, devem ser formalizados:

1. nova versão da matriz com `0.2` e `0.3` não bloqueantes;
2. aprovação institucional da política de obrigatoriedade dos 128 IDs;
3. decisão do gatilho de WhatsApp;
4. decisões F1-D06 e de `Não se aplica` para os campos afetados;
5. nomes e códigos definitivos dos três atos do FORM 1 Integral;
6. competência para reabrir uma versão já concluída e efeitos sobre etapas posteriores;
7. forma e visibilidade das observações não bloqueantes da chefia;
8. perfis autorizados a consultar a versão concluída e a iniciar cada FORM posterior;
9. vínculo do ciclo com a versão aprovada da matriz e do contrato;
10. escolha física da projeção, somente após o desenho técnico.

## 8. Plano mínimo de implementação futura

| Incremento | Entrega mínima | Dependência |
|---|---|---|
| T1 — Governança da matriz | decisões P0, matriz candidata versionada e aprovação | decisão institucional |
| T2 — Ciclo de conclusão | projeção mínima, comandos ARP/APA, permissões, eventos, auditoria, idempotência, concorrência e rollback | T1 e códigos dos atos aprovados |
| T3 — Interface controlada | declarar conclusão, conferir, devolver, confirmar e explicar limites; sem exportação manual | T2 estável |
| T4 — Disponibilidade autorizada | leitura da versão confirmada pelos perfis posteriores e referência pelos futuros FORMs | perfis e competências definidos |
| T5 — Ensaio sintético | percurso ARP distinto e APA=ARP, substituição de APA, devolução, correção e histórico | T1–T4 |

Cada incremento deverá terminar testado e commitado separadamente. A PoC nuclear e o contrato 2 permanecerão como regressão obrigatória.

## 9. Casos de teste e critérios de aceite

### 9.1 Declaração do ARP

- ARP atual e autorizado declara a versão corrente;
- agente indicado, mas sem permissão, é recusado e auditado;
- ARP substituído ou de outro Registro é recusado;
- rascunho incompleto continua salvável, mas não pode ser declarado concluído quando faltar requisito bloqueante aprovado;
- tela desatualizada não congela versão mais nova;
- comando repetido devolve o mesmo snapshot sem duplicação;
- mesma chave com conteúdo diferente é recusada;
- dois comandos simultâneos produzem uma única declaração válida;
- falha em evento, auditoria, snapshot ou projeção causa rollback integral.

### 9.2 Conferência do APA

- APA em exercício confirma o snapshot exato;
- APA antigo, suplente fora de vigência ou agente de outra Secretaria é recusado;
- substituição formal do APA mantém o item aguardando e autoriza somente o novo APA em exercício;
- APA devolve com justificativa e o ARP retoma sem perda de versão;
- confirmação e devolução concorrentes resultam em uma única decisão;
- tentativa de confirmar snapshot adulterado ou superado é recusada;
- APA=ARP exige dois atos explícitos, preservando os dois papéis;
- observação da chefia não bloqueia nem confirma;
- T.I. sem permissão de conteúdo não visualiza o levantamento.

### 9.3 Matriz e exceções P0

- `0.2` e `0.3` ausentes não bloqueiam e não admitem digitação livre;
- 128 IDs correspondem exatamente à matriz aprovada;
- todas as condições aprovadas ativam e desativam os campos corretos;
- WhatsApp segue somente o gatilho formalmente decidido;
- exclusividades F1-D06 e `Não se aplica` aceitam e recusam as combinações aprovadas;
- alertas facultativos permanecem não bloqueantes;
- versão confirmada registra a versão do contrato e da matriz utilizada.

### 9.4 Preservação arquitetural

- contrato nuclear 2 e FORM 1 sintético permanecem inalterados;
- snapshot técnico 8C continua imutável e não é retroativamente tratado como conclusão;
- nenhuma transição do Registro global é criada por conveniência de interface;
- eventos, auditoria e projeções são reconstruíveis;
- nenhum dado pessoal real entra em massa, log, evento ou evidência;
- conclusão não gera automaticamente FORM 2, validação jurídica, relatório para T.I. ou exportação Excel.

## 10. Conclusão

O fluxo institucional está definido, mas ainda não implementado. A arquitetura existente oferece os elementos necessários — rascunho versionado, atribuição do ARP, continuidade do APA, snapshot imutável, eventos e auditoria — sem exigir alteração do contrato nuclear. A menor solução segura acrescenta um ciclo próprio do FORM 1 Integral com três estados e três atos humanos, mantendo a devolução como transição auditada.

O próximo incremento técnico somente deverá começar após a decisão e o versionamento das seis exceções P0, especialmente a aprovação institucional da matriz. Até lá, a pré-validação permanece consultiva e a submissão/conclusão integral permanece bloqueada.
