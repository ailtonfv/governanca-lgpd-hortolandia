# Proposta técnica — canais declarados pelo APA na abertura

**Situação:** proposta pendente de autorização; não implementada no Incremento 8Z.
**Escopo:** permitir que o APA escolha canais do catálogo geral quando ainda não existir vínculo vigente `ObjetoCanal`, sem modificar o catálogo mestre.

## Estado atual e impedimento

O catálogo `Canal` contém os meios autorizados. `ObjetoCanal` registra quais deles são habituais para cada Serviço, Processo ou Atividade. Na abertura, o G1 aceita somente um subconjunto desses vínculos e `RegistroCanal.objeto_canal_id` é obrigatório. Portanto, um canal existente no catálogo geral, mas ainda não vinculado ao objeto, não possui hoje uma referência válida para a projeção histórica.

Usar texto livre, criar silenciosamente `ObjetoCanal` ou gravar o código em outro campo violaria, respectivamente, o catálogo fechado, a separação entre declaração do Registro e curadoria do catálogo ou o contrato de persistência. Por isso o 8Z não implementa essa seleção.

## Estrutura mínima recomendada

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

O comando G1 deverá receber, separadamente, os códigos confirmados por vínculo do objeto e os códigos declarados a partir do catálogo geral. O evento deverá usar uma nova versão de esquema e registrar a origem de cada canal. Eventos de esquema 2 e 3, Registros antigos e snapshots existentes não serão reinterpretados.

As situações permanecem exclusivas:

1. canais identificados — ao menos um canal, vinculado ou declarado;
2. nenhum canal aplicável — lista vazia por confirmação expressa;
3. a confirmar — não cria o Registro até a política autorizar outro comportamento.

## Interface proposta

Quando o objeto não possuir todos os canais conhecidos pelo APA, a tela poderá apresentar:

1. canais já vinculados ao objeto;
2. ação **Adicionar canal do catálogo geral**;
3. lista somente com canais ativos ainda não selecionados;
4. aviso explícito: “Esta declaração vale somente para este Registro e não altera o catálogo mestre”.

Não haverá texto livre, dados de cidadãos, protocolos ou atendimentos individuais. A decisão pendente sobre WhatsApp permanece preservada.

## Migração e compatibilidade

Implementar em incremento próprio:

1. adicionar colunas inicialmente anuláveis;
2. preencher `canal_id_catalogo` e `origem_confirmacao='VINCULO_OBJETO'` nas linhas existentes;
3. verificar órfãos, duplicidades e lacres;
4. aplicar chaves e restrições depois da conferência;
5. não regravar eventos nem snapshots antigos;
6. documentar reversão estrutural sem executar operação destrutiva na base de demonstração.

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

## Decisões ainda necessárias

- aprovação da nova versão do contrato G1 e do esquema de evento;
- autorização da migração e da origem `DECLARACAO_APA`;
- definição de eventual fila de curadoria para declarações recorrentes;
- confirmação de que “a confirmar” continuará bloqueando a abertura;
- tratamento institucional definitivo do WhatsApp.
