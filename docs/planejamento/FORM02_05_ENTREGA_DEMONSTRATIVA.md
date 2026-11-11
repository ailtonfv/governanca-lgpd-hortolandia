# FORM02_05 — Preparação demonstrativa do FORM 2

06/11/2026. Recorte autorizado pela instrução FORM02_05 e pela confirmação expressa da política demonstrativa durante a execução. Não habilita uso institucional.

## Funcionamento entregue

- Origem: snapshot técnico existente do FORM 1, selecionado explicitamente no mesmo Registro. JSON, texto canônico, lacre, contrato, estrutura e evento de preparação são conferidos. A consulta não gera snapshot.
- Leitura histórica: REV13 original, MEDIDAS, GUARDA e combinação, incluindo canais e envelope completo com ocorrências e complementos. Campos ausentes permanecem não informados. O conteúdo é somente leitura; consulta técnica não equivale a suficiência jurídica.
- Habilitação: política `F2-DEMO-05-v1`, pessoa/Registro, finalidade `preparar` ou `acompanhar`, início/fim de vigência, referência da aprovação individual e fundamento. Registrada pelo executor local, não por endpoint público. Aprovação funcional é uma evidência externa conferida pelo operador; o aplicativo não autentica a assinatura do responsável funcional.
- Designação: APA em exercício e expressamente habilitado confirma o preparador já habilitado e cria preparação vazia sobre a origem selecionada. Não muda o ARP do FORM 1 nem concede outro acesso. APA que também preparará precisa da habilitação `preparar` e do ato explícito de designação.
- Edição: somente preparador designado com habilitação vigente, conta/pessoa ativas e Registro/ciclo ativos. APA autorizado consulta. Papel genérico, lotação ou indicação não liberam a edição.
- Rascunho: envelope `F2-DEMO-PREP-v1`; anotação facultativa de até 2.000 caracteres, sem ID canônico. Pode permanecer vazia. HTML recebido é exibido como texto, não executado. Nenhuma das 245 perguntas é implementada neste recorte.
- Histórico: evento com revisão integral da anotação, papel exercido, autoria, origem e versão da política; projeção editável contém a última revisão. Leituras verificam a concordância com o histórico. Versões anteriores permanecem consultáveis.
- Revisão do FORM 1: não altera a origem nem as anotações existentes. Outra preparação sobre outro snapshot exige ação explícita e começa vazia. Não há substituição automática do preparador nem troca da origem de preparação existente.
- Salvamento: idempotência estrita, versão otimista, transação única e serialização entre habilitação/revogação/designação/salvamento. Falha preserva a anotação enviada na resposta HTTP; conflito não sobrescreve o rascunho mais recente.

O recorte aceita snapshot técnico incompleto, sem conferência, devolvido ou confirmado; esses estados não são marcos institucionais do FORM 2. Os rascunhos do FORM 1 e as apresentações anteriores não são modificados. A identidade continua simulada pela conta fictícia conforme o padrão atual da PoC; isso não é autenticação institucional de produção.

## Isolamento e migração

Migração **23**, `migracoes/preparacao_form2.py`: somente `habilitacao_form2_preparacao` e `preparacao_form2`. Ambas são projeções novas. Não insere `Instrumento` adicional nem usa `VersaoInstrumento` ou o validador sintético. Assim, o rascunho demonstrativo não entra nas exigências de conclusão da PoC nuclear.

Eventos têm correntes próprias e referência ao Registro/ciclo. Não alteram a situação do Registro, o rascunho do FORM 1, a sequência da corrente nuclear ou snapshots anteriores. A reversão da migração recusa remover tabelas com dados ou com eventos históricos correlatos. Reversão destrutiva não foi executada em banco demonstrativo.

O executor não aplica migrações, cria contas, cria snapshots ou escolhe pessoas por conta própria. A instalação da migração e o provisionamento de habilitações são passos operacionais distintos dos testes.

## Arquivos deste incremento

Alterados: `app/main.py` (inclusão do roteador), `app/modelos.py` (duas projeções), `migracoes/aplicar.py` (registro da migração 23) e `testes/test_snapshot_form1_integral.py` (montagem do cenário anterior à migração 17, removendo/recriando também a dependência posterior do FORM 2 no banco isolado; verificações de imutabilidade preservadas).

Criados:

- `app/form2_preparacao.py` — domínio, autorização específica, atribuição, consultas e histórico.
- `app/origem_form2.py` — verificação e leitura histórica da origem.
- `app/rotas_form2_preparacao.py` e `app/paginas/form2_preparacao.html` — fronteira web e página isolada.
- `app/estaticos/form2_preparacao.css` e `app/estaticos/form2_preparacao.js` — estilos locais, foco e proteção de saída.
- `migracoes/preparacao_form2.py` — migração aditiva/reversão protegida.
- `demonstracoes/form2_preparacao.py` — executor de habilitações individualmente aprovadas.
- `testes/test_form2_preparacao.py` e `testes/apoio_form2_preparacao.cjs` — domínio, HTTP, concorrência, migração e DOM simulado.
- Este relatório e [diretrizes GOV-09/GOV-10](FORM2_GOV09_GOV10_DIRETRIZES_FORM02_05.md).

As alterações locais anteriores em README, CSS geral, ajuda da Cartilha, backlog e testes dos Blocos 12/13 foram preservadas, sem incorporar mudanças deste incremento nesses arquivos. Os documentos candidatos anteriores também foram preservados.

## Como acessar

Após instalar a migração 23 no ambiente de demonstração autorizado e registrar as habilitações aprovadas:

1. Obter o UUID do Registro fictício e identificar quem será autorizado, com aprovação individual por pessoa/Registro. Não substituir UUID por código LGPD na URL.
2. Preparar manifesto JSON local com `politica: "F2-DEMO-05-v1"`, `somente_dados_ficticios: true` e lista `habilitacoes`. Cada item deve conter: `comando_id`, `registro_id`, `pessoa_id`, `finalidade`, `vigente_de`, `vigente_ate`, `aprovacao_referencia`, `fundamento`, `ativa`. Datas em ISO 8601 com fuso. Para APA apenas consultor/designante, finalidade `acompanhar`; para o preparador, `preparar`.
3. Conferir o manifesto: `python -m demonstracoes.form2_preparacao --manifesto CAMINHO --banco lgpd_poc_v2`. Essa chamada não grava. O operador precisa conferir a aprovação individual; o nome do arquivo não prova aprovação.
4. Somente depois da aprovação, repetir com `--executar`. O executor exige banco local explicitamente identificado e só aceita banco `_teste` ou `lgpd_poc_v2`. Não executa migração ou designação.
5. APA autorizado abre `http://127.0.0.1:8000/registros/UUID/form2/preparacao?conta_id=CONTA_FICTICIA`, escolhe uma origem e confirma a designação.
6. Preparador autorizado abre a mesma rota com sua conta fictícia, seleciona “Retomar preparação”, salva a anotação e recarrega. APA consulta sem campo editável, salvo se também for o preparador explicitamente designado.

O endereço acima é um padrão de rota, não um link para Registro já provisionado. Nenhuma habilitação individual em banco demonstrativo pode ser presumida a partir da aprovação geral deste incremento. Sem a migração, a rota informa indisponibilidade (503); sem habilitação, recusa o acesso (403). Não foi acrescentado botão genérico ao painel nem alterada sua organização.

## Cobertura dos 16 cenários da especificação

| Critérios | Evidência automatizada |
|---|---|
| T01 | Quatro estruturas de origem, quantidade de IDs, respostas e retrato de canais preservados. |
| T02 | Origem inexistente, outro Registro, lacre, evento e perfil inválidos recusados. |
| T03 | Ausência de snapshot sem criação automática; incompletude, devolução e confirmação sem liberação institucional. |
| T04/T05 | Indicação sem habilitação, habilitação sem designação, APA sem habilitação própria, conta/pessoa inativa, revogação, expiração e outro Registro. |
| T06 | Texto vazio/parcial/limite, leitura após salvamento, campos extras e valores inválidos. |
| T07/T08 | Repetição/reuso indevido da chave, inicialização concorrente, duas gravações na mesma versão e revogação serializada com escrita. |
| T09 | Falha induzida depois do evento reverte comando, evento e projeção. |
| T10/T11/T12 | S1/P1 preservados após S2/P2; P2 vazia; revisões e lacres conferidos. |
| T13 | Estado/corrente do Registro, conteúdo/lacre do FORM 1 e instrumentos nucleares inalterados. |
| T14 | Ausência de rotas de submissão/validação/decisão/habilitação; UUID de preparação recusado pelo comando nuclear. |
| T15 | Migração idempotente/aditiva; reversão vazia; reversão com dados recusada. |
| T16 | Rótulo associado, ajuda, alerta acessível, saída com alterações e foco em DOM simulado. CSS responsivo local. **Aceitação visual de telas larga/estreita e uso real por teclado NÃO VERIFICADA.** |

Os testes incluem o caso APA=preparador, com designação explícita e atos identificados separadamente. T16 permanece parcialmente verificado até inspeção manual real; não se declara aceite funcional completo por HTTP/DOM simulado.

## Procedimento mínimo de aceitação manual

No ambiente sintético provisionado: APA consulta S1 e designa; preparador registra anotação, salva, recarrega e retoma; altera sem salvar e cancela a saída; APA consulta a mesma anotação sem editá-la; FORM 1 é revisado por seu fluxo próprio e produz S2; P1 continua consultando S1; APA cria P2 sobre S2 sem copiar anotações. Conferir telas larga/estreita, teclado, foco, legibilidade e ausência de ações institucionais. Registrar resultado efetivamente observado, sem tratar a inspeção anterior do FORM 1 como aceite desta tela.

## Pendências preservadas

Manifestação jurídica, conclusão, validação, submissão institucional, comunicação externa, competências e avaliação DPO/Comitê permanecem fora do código entregue. GOV-09/GOV-10 são diretrizes documentadas para evolução futura. Não há cadastro de titulares ou solicitações individuais.

Não foi realizado commit nem push.

## Situação operacional

A consulta somente leitura ao banco local de demonstração `lgpd_poc_v2` encontrou as migrações 1–22 e confirmou a ausência das duas tabelas do FORM 2. A migração 23 foi implementada e exercitada somente no banco isolado `lgpd_poc_teste`; sua instalação demonstrativa permanece pendente, junto do provisionamento individual aprovado. Nenhum Registro, pessoa ou habilitação demonstrativa foi criado ou alterado nesta execução.

Na primeira regressão completa, 703 testes passaram e um teste antigo falhou ao tentar remover a tabela de snapshots com a nova chave estrangeira do FORM 2 ainda presente. A falha ocorreu na montagem do cenário de migração, antes das verificações funcionais. A montagem foi ajustada para remover/recriar a dependência posterior em ordem, sem `CASCADE`, mantendo todas as asserções de imutabilidade. Nenhuma proteção de integridade foi removida.

## Verificação final — 06/11/2026

Todos os testes utilizaram exclusivamente `lgpd_poc_teste`, com `BANCO_NOME` e `LGPD_BANCO_TESTE` explicitamente fixadas nesse destino. Interpretador: ambiente `lgpd-poc`.

| Execução | Comando (após fixar as duas variáveis) | Resultado |
|---|---|---|
| Focais do incremento | `python -m pytest -o addopts='' -q testes/test_form2_preparacao.py --tb=short --junitxml=evidencias/form02_05/focais.xml` | 40 aprovados |
| Focais e snapshots após ajuste da montagem | `python -m pytest -o addopts='' -q testes/test_form2_preparacao.py testes/test_snapshot_form1_integral.py --tb=short --junitxml=evidencias/form02_05/focais_snapshot.xml` | 48 aprovados |
| Regressão final | `python -m pytest -o addopts='' -q --tb=short --junitxml=evidencias/form02_05/regressao_final.xml` | **704 aprovados, zero falhas**, 413,34 segundos |

Aviso não impeditivo existente na dependência Starlette: depreciação de `anyio.abc.BlockingPortal`. Não houve alteração de dependências. A conexão inicialmente impedida pelas restrições locais foi autorizada para o destino de testes explícito; nenhuma configuração de segurança foi desabilitada.

Comparação SHA-256 com o início da tarefa confirmou a preservação de todos os arquivos preexistentes, exceto os quatro arquivos expressamente relacionados nesta entrega. São 12 arquivos novos deste incremento. A revisão de espaços/conflitos pelo `git diff --check` passou. Não foram incluídas credenciais, bancos locais ou dados pessoais reais nos arquivos produzidos.

Git: branch `main`, HEAD preservado em `664f4b3ca97f95139fdb0f66abf15cc18aac58a4`; nove commits à frente da referência local de `origin/main`, nenhum atrás. Não houve consulta/atualização do remoto, commit ou push. Árvore contém este incremento não commitado e as alterações anteriores preservadas.

**Parecer:** recorte implementado e aprovado nos testes automatizados, com isolamento do FORM 1 demonstrado. Não se declara implantação no banco demonstrativo nem aceite funcional/visual integral. Para o ensaio manual, faltam a instalação da migração 23, as aprovações individualizadas pessoa/Registro e o respectivo provisionamento controlado. **ACEITAÇÃO VISUAL NÃO VERIFICADA.** Submissão institucional e competências especializadas permanecem bloqueadas/não implementadas neste recorte.
