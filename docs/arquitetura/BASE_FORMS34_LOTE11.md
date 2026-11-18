# Base técnica dos FORMs 3 e 4 — Lote 11

Branch `lote-11-forms34-base`, base `c46d531`. Sem interface ou concessão de
competência. Este contrato prepara infraestrutura; não implementa ingresso,
avaliação, aceitação, aprovação, verificação, prorrogação ou cancelamento.

## Catálogos

`app/catalogos/form3_estrutura_base_v1.json` e
`app/catalogos/form4_estrutura_base_v1.json` contêm 77 e 39 identificadores,
tipos, blocos e condições estruturais. Não contêm enunciados, opções editoriais
ou ajudas do Mestre. Condições simples conservam identificador/código; condições
compostas ou dependentes de decisão permanecem declarativas, sem avaliador.
Nenhuma exibição temática, escala, triagem ou competência é executada.

O pacote local `entrega-lgpd-lote11` contém os dois arquivos privados. O envelope
mantém o padrão editorial (`blocos/itens`) e o contrato de controles
(`itens/alternativas/condicoes`) do FORM 2. `LGPD_CATALOGO_FORM3` e
`LGPD_CATALOGO_FORM4` apontam para os arquivos locais; os lacres conferidos estão
na estrutura pública. Ausência/divergência é recusada, sem catálogo substituto.
Alternativas têm códigos locais estáveis desta edição candidata; não representam
aprovação de cálculo ou adoção institucional. Não há respostas novas ou migração.

## Referências e identidades

`ReferenciaParticipacaoForms34` é o contexto técnico do futuro instrumento,
identificado por UUID, vinculado a Registro e origem exata. Não é uma participação
em fila: não contém unidade designada, responsável, papel, ingresso ou estado
institucional. Nenhuma rotina existente a cria automaticamente.

- FORM 3: referência a snapshot imutável do FORM 1 ou evento versionado do FORM 2.
- FORM 4: referência a evento versionado do FORM 2 ou da base do FORM 3.
- O vínculo conserva identificador, número da versão, lacre e representação
  canônica da fonte. Também conserva o snapshot factual do FORM 1 correspondente.
- Eventos e snapshots são conferidos quanto a integridade e Registro. Uma fonte
  posterior não substitui a examinada; a repetição com outra fonte é recusada.
- Referência a evento da base do FORM 3 não significa avaliação de risco: o
  futuro adaptador terá de distinguir versão técnica de avaliação efetiva.

`IdentidadeForms34` reserva Rnn/Ann por Registro, em sequências independentes.
O bloqueio transacional do Registro serializa alocação concorrente. O banco
reforça unicidade por número e por chave de origem. A chave de origem é técnica,
definida pelo futuro adaptador a partir da identidade do encaminhamento, nunca
por semelhança textual. Repetir a mesma origem não cria outra identidade.

Retirada técnica é um evento sem exclusão física e sem reuso de número. Não é
cancelamento institucional de ação e não altera estado do Registro. Retentativa
da origem retirada devolve a identidade preservada; não a reativa silenciosamente.

## Histórico e transações

Reutiliza `Comando`, `Evento` e `EventoAuditoria`, sem um livro paralelo. Autor é
a pessoa associada à conta ativa, não um nome informado no payload. Data/hora vêm
do servidor. Tipos permitidos nesta base: anotação, correção e retirada técnica.
Correção referencia anotação anterior da mesma identidade; não altera o original.
O limite técnico provisório da anotação é 1000 caracteres; não é limite de
produção nem implementação dos controles editoriais dos novos FORMs.

Idempotência inclui parâmetros e autoria. Controle otimista compara a versão do
histórico depois do bloqueio transacional. Savepoint garante atomicidade do
comando, identidade, evento e auditoria mesmo se o chamador tratar uma exceção.
O commit da transação continua sob responsabilidade do futuro caso de uso.

Triggers PostgreSQL recusam UPDATE/DELETE nas duas novas tabelas e nos eventos
das cadeias `forms34_contexto`/`forms34_objeto`. Os eventos de outros instrumentos
não recebem nova política neste lote. Não se pretende proteger contra um
administrador que deliberadamente remova as proteções do banco.

A proteção em `evento` é por linha, com predicado sobre `OLD.cadeia_tipo`:
alterar o discriminador não permite escapar da proteção de uma linha 3/4.
Não há trigger de INSERT nem proteção nova nas demais cadeias. Mantém-se a
tabela comum para preservar o livro de eventos e seus contratos de auditoria;
os testes comparam o comportamento SQL dos eventos F1/F2 antes e depois do
trigger, inclusive suas restrições anteriores de integridade referencial.

## Projeções e autorização futura

`fatos_existentes` exige lista explícita de Registros e não escreve. Retorna
somente identidades, referência, autoria/data observadas e retirada técnica.
Ausência de fatos e indicadores ainda não implementados permanecem `None`.
Não calcula risco, cumprimento, percentuais ou cobertura. A quantidade positiva
de identidades é contagem técnica, não número de avaliações concluídas.

Todas as funções são internas: não são chamadas por rotas, telas, filas ou
callbacks existentes. Elas não constituem autorização. O adaptador futuro
deverá verificar o ato e escopo antes da chamada. Não criar endpoint apontando
diretamente para estas funções. Uma conta ativa é autoria válida, não competência.

## Preparação para decisões 1–4

1. Condução: acrescentar autorização e papéis no caso de uso futuro, preservando
   autoria e independência; nenhuma competência foi inferida aqui.
2. Ingresso: o ato futuro escolherá unidade/participação e referência exata e
   usará a base na mesma transação, com seu próprio evento institucional.
3. Aceitação/plano: serão novos atos separados, nunca uma anotação técnica.
4. Metodologia: avaliação será um objeto/evento versionado próprio; as projeções
   atuais deixam os indicadores ausentes até existirem fatos verificáveis.

## Instalação e testes

`migracoes/base_forms34.py::aplicar` é explícita e idempotente, aceita somente banco
terminado em `_teste`, antes de abrir conexão. Cria as duas tabelas e instala
função/triggers; inclui um trigger limitado na tabela `evento` existente.
Portanto, não é uma migração exclusivamente de novas tabelas e índices.
Não altera colunas nem remove estruturas/dados existentes. A função e os
triggers próprios são substituídos idempotentemente pela migração.
Não há callback em `Base.metadata` nem instalação por `create_all()` ou pela
inicialização do servidor. Somente os testes deste lote invocam explicitamente
a migração em sua preparação. A preparação
local `abrir_8012.py` copia a base da 8009 para banco isolado `_teste` e não inicia
servidor. A suíte recria somente essa cópia. 8009 e 8011 ficam preservadas.

Testar integridade das fontes, origem de outro Registro, congelamento, reenvio,
não reuso, autoria, correção, proteção SQL, rollback e concorrência com conexões
independentes; depois repetir a seleção de regressão dos lotes anteriores.

### Verificação de 18/11/2026

Executados exclusivamente na cópia isolada terminada em `_teste`: 42 testes
novos aprovados e os mesmos 188 testes da entrega anterior, com 185 aprovados
e somente as três falhas antigas. Total: 227 aprovados em 230, sem regressão
nova. A base fixa permanece em 123/126; lotes 4–8 em 44/44, lote 9 em 13/13,
regressão adicional em 1/1 e lote 10 em 4/4.

Falhas antigas: `test_cartoes_explicam_disponibilidade_sem_oferecer_acesso_direto`,
`test_catalogo_local_indisponivel_preserva_preparacao[True]` e
`test_unidade_isola_origens_e_reutiliza_anotacao`.
Evidências no pacote local `entrega-lgpd-lote11`: `testes-novos.xml` e
`testes.xml`, com seus logs. Nenhum servidor ou banco de vistoria foi alterado.
Não há conferência visual neste lote, pois nenhuma tela foi criada.
