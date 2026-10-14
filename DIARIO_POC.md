# Diário da PoC — Sistema de Governança Municipal LGPD (Prefeitura Municipal de Hortolândia)

Registro técnico da construção da PoC nuclear (SAD 09 REV10; IMPLEMENTAR_POC_2026-10-08, minuta).
Regras deste diário: sem senhas, tokens ou dados pessoais; cada entrada com data; acessos diretos ao banco anotados aqui.

## 2026-10-09 — Preparação do ambiente

- Python: ambiente conda `lgpd-poc`, Python 3.14.8 (D:\Vendramini\anaconda3\envs\lgpd-poc).
- Banco: PostgreSQL 18.6 (64 bits), serviço `postgresql-x64-18` em execução; pasta de dados em C:\Program Files\PostgreSQL\18\data. Acesso de teste com o usuário `postgres` (SELECT version; SHOW data_directory) — nenhuma base da PoC criada ainda.
- Git 2.45.2; repositório privado https://github.com/ailtonfv/governanca-lgpd-hortolandia clonado em D:\Ailton\PMH\Cidades_Inteligentes\LGPD\poc (repositório ainda vazio).
- Documentação da série SAD movida para D:\Ailton\PMH\Cidades_Inteligentes\LGPD\Solution_Architecture_Document_(SAD)_Documento_de_Arquitetura_da_Solução (fora da pasta do curso).
- Operador da PoC: Encarregado de Dados (operador único; dados exclusivamente fictícios).

## 2026-10-10 — Base de dados e primeiros commits

- Git: pasta registrada como safe.directory (clone feito em terminal de administrador); primeiro commit (182d239) e segundo commit (abd8c0c) enviados ao GitHub.
- PostgreSQL: criado o usuário `lgpd_poc_app` (sem privilégios de administrador) e a base `lgpd_poc` (UTF8), de propriedade desse usuário — princípio do menor privilégio. Operação feita pelo Encarregado com o usuário `postgres`. Senhas fora do código e do repositório.

## 2026-10-11 — Conexão Python → PostgreSQL

- Bibliotecas instaladas no ambiente `lgpd-poc`: SQLAlchemy 2.1.4, psycopg 3.3.6, python-dotenv 1.2.4.
- Criados `.gitignore` (bloqueia `.env`, `.vscode/`, temporários e evidências) e `.env.exemplo` (modelo sem senha). O `.env` real fica só no computador.
- Teste de conexão (`teste_conexao.py`): falhou por autenticação. Causa: senha do `.env` diferente da do banco (mesmo tamanho, conteúdo diferente). Diagnóstico feito com `diagnostico_senha.py`, comparando impressões digitais (hash) sem exibir senhas. Corrigido o `.env`; conexão validada (usuário `lgpd_poc_app`, base `lgpd_poc`).
- Código de conexão usa `URL.create`, seguro para senhas com caracteres especiais.
- Primeira tabela criada (`evento`, livro de atos) via `criar_tabelas.py` e `app/modelos.py`.
- `app/eventos.py`: registro de eventos com cadeia de hash por objeto (SHA-256 sobre JSON canônico) e verificação relendo do banco. `demo_eventos.py` gravou 4 eventos fictícios (REG-0001 com 3, REG-0002 com 1); as duas correntes verificadas íntegras.
- Simulação de fraude (UPDATE direto no banco, desfeito por rollback): adulteração detectada no evento 2 do REG-0001. Nenhum dado real; livro de atos não modificado.
- Acesso direto ao banco: consulta somente leitura pelo pgAdmin (usuário `postgres`) para conferir a tabela `evento`.
- Observação: os 4 eventos têm o mesmo `registrado_em` porque foram gravados na mesma transação (o PostgreSQL usa o horário de início da transação).
- Tabelas `pessoa` e `conta` criadas (base da segregação de funções, O-66). Cada conta pertence a uma pessoa (chave estrangeira). Semeadas 3 pessoas fictícias e 4 contas (PESSOA-A com CONTA-A1 e CONTA-A2), sem CPF, matrícula ou dado real (`semear_pessoas.py`).
- Pendência registrada: alinhar a tabela `evento` ao SAD 05 REV11 e à DA-26 — trocar `pessoa_id` por `ator_tipo` + `ator_id` (eventos de pessoa, sistema ou integração), junto com os demais campos da DA-26.
- Tabelas `unidade` e `designacao` criadas; semeadas 2 unidades fictícias e 5 designações (`semear_designacoes.py`). PESSOA-A acumula elaborador e validador na Unidade Norte (cenário do O-66); o papel é dado à pessoa, não à conta.

## 2026-10-12 — README e dependências

- Criado `README.md` (versão 1): o que é o projeto, camadas de validação, situação, como montar o ambiente e rodar a PoC, autoria.
- Criado `requirements.txt` com as versões travadas das bibliotecas (reprodutibilidade).
- `COLA_COMANDOS.md`: seção sobre `git init` × `git clone`.
- README: incluídos o diagrama "De onde vem este sistema" e a seção "Quem faz o quê" (Encarregado × equipe designada).
- Segregação de funções (O-66): criados `app/permissoes.py` (papéis exigidos por ação; regra que compara a PESSOA, nunca a conta) e `teste_segregacao.py`. Cenários no REG-0003 (Unidade Norte, dados fictícios): (a) A valida pela A2 → negado; (b) A valida pela A1 → negado; (e) A devolve pela A2 → negado; B analisa → permitido; (c) B valida → permitido; (f) com A1 desativada (simulação desfeita por rollback), o autor continua sendo A e a tentativa pela A2 continua negada. Cenário (d), substituição com em_nome_de, pendente.
- Cada tentativa negada virou evento `acesso_negado` na corrente de auditoria mensal AUDITORIA-2026-10 (3 eventos), com ação tentada, objeto, conta e motivo.
- Commit d70c508 enviado ao GitHub.
- Limitação declarada: as contas foram criadas por script de carga (`semear_pessoas.py`), fora do livro de atos. O procedimento de criação de conta não está definido nos SADs (ver O-78).
- Etapa 1 — livro de atos alinhado à DA-26 e à DA-27:
  - Tabela antiga renomeada para `evento_v0` (10 eventos), travada como somente leitura (`arquivar_evento_v0.py`). Nada apagado.
  - Criadas `comando` (pedido idempotente), `evento` (domínio: cadeia_tipo, tipo_evento × codigo_evento, comando_id + ordem_no_comando, ator_tipo + ator_id, em_nome_de, ocorrido_em, versao_regra, versões de esquema e de algoritmo, payload_canonico) e `evento_auditoria` (segmentos mensais, ex.: AUDITORIA-2026-10).
  - `app/eventos.py` reescrito: lista fechada de campos lacrados, texto canônico guardado, data em UTC com microssegundos; conferência em quatro perguntas (numeração, elo, campos × texto lacrado, lacre × texto).
  - `demo_eventos.py`: REG-DEMO-01 (2 atos de um mesmo pedido) e 1 consulta na auditoria; três fraudes simuladas e desfeitas por rollback, todas detectadas (campos alterados; lacre violado; elo quebrado).
  - `app/permissoes.py` e `teste_segregacao.py` ajustados: REG-0003 refeito no livro novo; 8 cenários ✔, incluindo o clique duplo (pedido repetido, nada gravado). Tentativas negadas como `tentativa_negada` (catálogo do SAD 08). Ações gravadas com nome e código do catálogo: submeter (I3), iniciar_analise (I13), validar (I5), devolver (I6).
  - Limitação declarada: quem controla o banco pode reescrever uma corrente inteira; a proteção é o checkpoint externo (SAD 08, DA-27), ainda a fazer. Fechamento de segmento e ligação entre meses também pendentes.
  - Provisórios da PoC: versao_regra fixa "POC-1" (tabela versao_regra na etapa 2); segmento de auditoria por mês em UTC.
  - Custódia do checkpoint externo (quem guarda, quem confere, a quem se comunica divergência) registrada como O-79 na LISTA_OBSERVACOES_POS_POC: decisão institucional, independente da administração do banco.

## 2026-10-13 — README em PDF e início da etapa 2

- Gerado o PDF do README (README_PoC_LGPD_Hortolandia_2026-10-13.pdf, guardado na pasta LGPD, fora do repositório). Acrescentado ao README o comando `python teste_segregacao.py`.
- Pendência para revisão futura do README: incluir na autoria a identificação "a.vendramini", como nos demais documentos.
- Envio do README à TI previsto para sexta-feira, 16/10/2026.
- Etapa 2a — ato G1 (Criar Registro): tabelas `registro`, `ciclo` e `instrumento`; `app/workflow.py` com `criar_registro` (portões: conta ativa, tipo de objeto válido, papel de elaborador na unidade; pedido idempotente; Registro, ciclo 1, FORM 1 e evento G1 na mesma transação). `demo_registro.py`: LGPD-2026-00001 criado por PESSOA-A; PESSOA-B negada (sem papel) e registrada na auditoria; clique duplo não criou segundo Registro. 3 cenários ✔.
- Pré-condição do G1 ainda não implementada: "inexistência de Registro equivalente ativo" (SAD 04, seção 7; SAD 05, 5.3). Formato do codigo_lgpd (LGPD-AAAA-NNNNN) segue A VALIDAR.
- README: nova seção "Como os Registros são organizados" (serviço, processo e atividade; Registros e relações; regras do SAD 02 RF-PRC-06, 13, 14 e 15).
- Etapa 2b — trava contra duplicidade (O-80): tabelas `objeto_catalogo` (catálogo fictício) e `registro_objeto` (vínculo Registro × objeto, com índice único parcial: um objeto só em um Registro não cancelado); contador do banco `seq_codigo_lgpd` para os códigos (sem colisão entre pedidos simultâneos; pode haver pulos na numeração). `criar_registro` passou a receber objetos do catálogo (um ou mais, RF-PRC-13); pesquisa prévia + ponto de salvamento (savepoint): se a trava do banco recusar, só a criação é desfeita, e a tentativa vai para a auditoria com as informações do Registro existente e as ações possíveis. `teste_duplicidade.py`: cenários 1 (dois pedidos simultâneos, um só criado, barrado pela trava do banco), 2, 2b, 3 e 7 ✔. Cenários 4, 5, 6 e 8 aguardam os atos de suspender (G7), concluir (G5/G6) e cancelar (G11).
- Limitação conhecida: dois eventos de auditoria simultâneos no mesmo segmento podem colidir na numeração; tratar quando houver concorrência real (passo futuro).
- README revisado várias vezes ao longo do dia (versões em PDF v2 a v6 na pasta LGPD): seção "Como os Registros são organizados" com serviço, processo e atividade; canais como dimensão transversal (catálogo de canais, relação "atendido por", Registro próprio só com tratamento autônomo); definição dos catálogos (operacional, de canais e de finalidades) e curadoria; papéis do objeto no Registro (PRINCIPAL, ABRANGIDO, APOIO, RELACIONADO), com exemplo; situação bloqueadora; fluxograma contra duplicidade com exemplos fictícios. Revisão do Encarregado incorporada (regra por objeto e finalidade; G1 cria FORM 1 Não iniciado; canal como extensão).
- Decisões do Encarregado registradas na série SAD: O-80 (itens a a o) → DA-36 no SAD 10 REV13 (Etapa N do Cowork, com conferência cruzada de toda a série: 29 trechos a ajustar, Conferencia_DA36_2026-10-13.md); achado sobre o G11 (cancelamento só a partir de estados ativos) → O-82 e DA-37 no SAD 10 REV14 (Etapa O): cancelar a partir de qualquer estado diferente de Cancelado, catálogo de motivos, competência reforçada para Registro Concluído. Demais SADs intactos até a revisão consolidada pós-PoC (O-81 e O-82).
- Pendência de código decorrente: o catálogo fictício ainda traz o balcão como tipo "canal" no catálogo de objetos; separar no passo 2c, junto com os papéis e o alerta.
- Etapa 2c, parte 1 — catálogo de canais (DA-36, item 6): tabelas `canal` e `servico_canal` (relação "atendido por", muitos para muitos, com vigência; índice único parcial para o par vigente). `semear_canais.py`: 3 canais fictícios e 3 ligações (balcão atende 2ª via do IPTU e Certidão; portal atende 2ª via; telefone sem serviço). O balcão saiu do catálogo operacional (`semear_catalogo.py`); se existir como objeto antigo, é desativado, nunca apagado. Barreira observada: na primeira execução, sem catálogo operacional no banco, as ligações foram recusadas com aviso (só se liga canal a serviço existente).

## 2026-10-14 — Contexto de atuação, bases de dados e README

- Decisões do Encarregado (O-83): "finalidade" reservada ao sentido da LGPD (art. 6º, I, declarada no FORM 1); a classificação usada contra duplicidade passa a ser o CONTEXTO DE ATUAÇÃO (catálogo com códigos CTX-, famílias pelo prefixo); terceiro eixo transversal: catálogo de BASES E CONJUNTOS DE DADOS (ex.: Cadastro imobiliário), ligado às atividades por "utiliza"; advertência (não erro) para o mesmo objeto em dois contextos da mesma família (regra A); relação serviço → processo passa a "é realizado por" ("depende de" reservado a dependência efetiva).
- README: seções novas "PoC nuclear × PoC ampliada", "Contexto de atuação e finalidade: duas coisas diferentes" (definição, pergunta-teste, 20 exemplos, famílias, contraexemplos), "Bases e conjuntos de dados: o terceiro eixo"; fluxograma com contexto de atuação e advertência de família; exemplos 1 a 5 revistos; legenda com 📝 (decisão do Encarregado ainda não registrada no SAD 10). PDF: README_PoC_LGPD_Hortolandia_2026-10-14.pdf (17 páginas).
- README, revisão 2 (11 pontos do Encarregado): título "Prova de Conceito" (nuclear e ampliada); PoC ampliada no diagrama "De onde vem"; redação da base de dados como ativo informacional; regra das várias Secretarias condicionada a mesmo objeto, mesmo contexto e ausência de tratamentos autônomos; "contexto distinto não prova autonomia"; ordem de verificação (equivalência bloqueadora → família → relacionados → resultado); fluxograma dividido em duas partes; tabela de regras dividida (organização × duplicidade); seções novas "Marcos e critérios de saída" (M1a, M1b, M2, M3A), "Próximos passos" e "Pendências normativas consolidadas". PDF: README_PoC_LGPD_Hortolandia_2026-10-14_v2.pdf (21 páginas).
