# Proposta técnica — canais declarados pelo APA na abertura

**Situação:** proposta autorizada e implementada no Incremento 8AA; este documento preserva a análise que antecedeu a implementação.
**Escopo:** permitir que o APA escolha canais do catálogo geral quando ainda não existir vínculo vigente `ObjetoCanal`, sem modificar o catálogo mestre.

## Estado anterior ao Incremento 8AA

O catálogo `Canal` contém os meios autorizados. `ObjetoCanal` registra quais deles são habituais para cada Serviço, Processo ou Atividade. Na abertura, o G1 aceita somente um subconjunto desses vínculos e `RegistroCanal.objeto_canal_id` é obrigatório. Portanto, um canal existente no catálogo geral, mas ainda não vinculado ao objeto, não possui hoje uma referência válida para a projeção histórica.

Usar texto livre, criar silenciosamente `ObjetoCanal` ou gravar o código em outro campo violaria, respectivamente, o catálogo fechado, a separação entre declaração do Registro e curadoria do catálogo ou o contrato de persistência. Por isso o 8Z não implementa essa seleção.

## Estrutura implementada

Preservar `ConfirmacaoCanaisRegistro` como cabeçalho da declaração e evoluir `RegistroCanal` de modo não destrutivo:

| Elemento | Evolução proposta |
|---|---|
| `canal_id_catalogo` | Nova chave estrangeira obrigatória para `Canal`; preenchida nos vínculos antigos a partir de `ObjetoCanal.canal_id` |
| `objeto_canal_id` | Passa a aceitar nulo somente quando a origem for declaração direta do APA |
| `origem_confirmacao` | Catálogo fechado: `VINCULO_OBJETO` ou `DECLARACAO_APA` |
| snapshots atuais | Preservar objeto, código, nome e classificação exatamente como confirmados |
| autoria e data | Manter `confirmado_por_id` e `confirmado_em` em cada item e no cabeçalho |

Uma restrição deverá exigir:

- `VINCULO_OBJETO` com `objeto_canal_id` preenchido e coerente;
- `DECLARACAO_APA` com `objeto_canal_id` vazio e `canal_id_catalogo` ativo;
- unicidade de canal por Registro, independentemente da origem.

Nenhuma declaração direta deverá criar ou alterar `ObjetoCanal`. A curadoria poderá analisar essa evidência depois, em fluxo próprio e auditável.

## Contrato e evento

O comando G1 recebe uma única seleção de códigos do catálogo geral ativo. O domínio resolve e registra a origem de cada item: vínculo vigente do objeto ou declaração direta do APA. O evento usa o esquema 4 e registra essa origem. Eventos de esquema 2 e 3, Registros antigos e snapshots existentes não são reinterpretados.

As situações permanecem exclusivas:

1. canais identificados — ao menos um canal, vinculado ou declarado;
2. nenhum canal aplicável — lista vazia por confirmação expressa;
3. a confirmar — cria o Registro com pendência explícita, sem ser interpretado como “nenhum”.

## Interface implementada

Quando o objeto não possuir todos os canais conhecidos pelo APA, a tela apresenta:

1. canais já vinculados ao objeto;
2. lista fechada dos canais ativos do catálogo geral;
3. vínculos do objeto como sugestões pré-selecionadas, sempre sujeitos à confirmação do APA;
4. aviso explícito: “Esta declaração vale somente para este Registro e não altera o catálogo mestre”.

Não haverá texto livre, dados de cidadãos, protocolos ou atendimentos individuais. A decisão pendente sobre WhatsApp permanece preservada.

## Migração e compatibilidade implementadas

A migração 18 executa de modo não destrutivo:

1. adicionar colunas inicialmente anuláveis;
2. preencher `canal_id_catalogo` e `origem_confirmacao='VINCULO_OBJETO'` nas linhas existentes;
3. verificar órfãos, duplicidades e lacres;
4. aplicar chaves e restrições depois da conferência;
5. não regravar eventos nem snapshots antigos;
6. reversão estrutural protegida, recusada quando houver declarações diretas ou confirmações pendentes que o esquema anterior não represente.

## Testes necessários

- canal vinculado, declarado e combinação dos dois;
- zero, um e vários canais;
- canal inexistente, inativo, repetido ou forjado;
- exclusividade entre “nenhum”, “a confirmar” e canais substantivos;
- declaração não altera `ObjetoCanal`;
- autoria, data, evento, auditoria, idempotência e concorrência;
- preservação de Registros e eventos dos esquemas 2 e 3;
- leitura da pergunta 2.1 e condicionais independentes de Ouvidoria/e-SIC;
- rollback integral e migração não destrutiva.

## Limitações e decisões posteriores

- definição de eventual fila de curadoria para declarações recorrentes;
- a presença de WhatsApp corporativo no catálogo registra somente a modalidade factual; regularidade jurídica, dispositivo utilizado, repositório oficial, permanência de arquivos e backups continuam sujeitos à governança própria.
