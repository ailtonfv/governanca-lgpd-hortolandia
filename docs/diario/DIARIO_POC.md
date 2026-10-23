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
- Etapa P preparada: Instrucao_Cowork_Etapa_P_2026-10-14.md (SAD 10 REV15 com a DA-38, a partir do O-83; remissões nas DA-36 e DA-37; O-84 na lista; índice de 14/10). Sugestões do Encarregado para a PoC ampliada guardadas em Insumo_PoC_Ampliada_2026-10-14.md (O-84, para análise antes do M1b).
- Etapa 2c, parte 2 — objeto + contexto de atuação (DA-36 e O-83/DA-38): tabelas `familia_contexto`, `contexto_atuacao` (20 contextos fictícios), `base_dados` e `objeto_base` (relação "utiliza"); `registro_objeto` ganhou `papel` e `contexto_atuacao_id`, com duas travas no banco: mesmo objeto + mesmo contexto só pode ser ASSUNTO (PRINCIPAL ou ABRANGIDO) de um Registro não cancelado; exatamente um PRINCIPAL por Registro. G1 com a ordem de verificação (equivalência → família → alerta → resultado); advertência de família exige justificativa; família mutuamente exclusiva bloqueia; alerta à governança quando outro objeto usa a mesma base. Evento G1 passa ao esquema 2. Registros antigos migrados por ATO NOVO na própria corrente ("classificar_vinculos", ator sistema MIGRACAO-2C2), sem tocar nos eventos anteriores. Testado antes num banco de teste fora da Prefeitura (fictício): 11 cenários de contexto ✔ e duplicidade ✔ em banco vazio e em banco com dados antigos.
- Etapa P executada pelo Cowork: DA-38 no SAD 10 REV15 (remissões nas DA-36 e DA-37; O-83 encerrado como DA-38; O-84 na lista; INDICE_REVISOES_VIGENTES_2026-10-14.docx). README: referências 📝 O-83 passam a 🧪 DA-38; PDF v4.
- Etapa 2c, parte 2, executada no banco da PoC: migração de 4 Registros antigos por ato novo (LGPD-2026-00002 a 00005; correntes íntegras) e duas travas novas no banco; teste_contexto.py com 11 ✔ (LGPD-2026-00007 a 00010; o número 00006 ficou vago pelo cenário 9, desfeito — lacunas são permitidas). Observação: o LGPD-2026-00001 (demo de 13/10) nasceu antes da tabela de vínculos e não tem objeto vinculado, por isso não foi migrado; fica de fora da trava até um ato de classificação próprio (a fazer, sem urgência).

## 2026-10-14 (tarde) — Etapa 2d: revisão do Encarregado aplicada ao código

- Decisões do Encarregado: D1 (um contexto por Registro), D2 (advertência de família: três resoluções; transversalidade por objeto + família, declarada só pela governança), D4 (numeração anual LGPD-AAAA-NNNNN no fuso de São Paulo). Registro em Revisao_Etapa_2c_2026-10-14.md; ficha DA a criar.
- Código: pedido idempotente estrito (app/comandos.py: chave obrigatória, lacre dos parâmetros, resultado original + reexecutado, reutilização indevida recusada, colisão simultânea tratada); recusas do banco tratadas pelo NOME da regra (outras sobem); papéis explícitos no G1; todos os conflitos listados; ações por quem pede; alertas estruturais deduplicados; contador anual; chave composta Registro–contexto e CHECK para citados; transversalidade como ato próprio.
- Organização: instalacao/, migracoes/ (versao_esquema + aplicador), carga_ficticia/, demonstracoes/, testes/ (pytest em banco próprio lgpd_poc_teste).
- Base nova lgpd_poc_v2 (a anterior, lgpd_poc, é preservada com cópia de segurança, só para consulta).
- Testes: 40 aprovados no banco de teste fora da Prefeitura (fictício); conferido que falham quando a regra é quebrada de propósito.
- Organização do M1b (Encarregado, 14/10/2026): workflow único no SAD 04; M1b executado em quatro pacotes (M1b.1 autorizações/suspensão/retomada/cancelamento com P10 mínimo; M1b.2 reabertura e novos ciclos; M1b.3 pendências completas, participação e continuidade; M1b.4 backup, restauração, integridade e adaptadores), com dependências explícitas. Percurso com medidas e G6 no M1a, com ação obrigatória sintética mínima. Regras de prazo como decisão de entrada do M1b.1. README revisão 6 e O-84 atualizados juntos.
- Decisão do Encarregado (14/10/2026): devolução na Opção A, com congelamento por hash no P3 e P5/P6 restritos à pendência criada por I6 (cenário A2 em A2a e A2b). Etapa Q preparada (DA-39 no SAD 10 REV16; SAD 04 REV12; SAD 09 REV12). Achado na conferência: o núcleo do M1a inclui também I4 (A11, retirada da submissão) e I14 (A14, reatribuição da análise), já previstos no SAD 09 e regulados no SAD 04 — incluídos nos próximos passos do README.
- Etapa Q executada pelo Cowork: DA-39 no SAD 10 REV16; SAD 04 REV12 (G1, G4, G5, eventos derivados, I13, pendência da devolução, I3, A2a/A2b, remissão ao SAD 09); SAD 09 REV12 (4A.1, seção 14, nota A2a/A2b); O-82/O-83 retitulados; O-85; índice 14/10 v2. Divergências sem efeito na PoC registradas como O-86 (Figura 2 do SAD 04; contagem e remissão na 4A.6 do SAD 09). MAPA_M1a.md acrescentado ao repositório e ligado ao README (revisão 7); README com D1, D2, D4 como DA-39 e "O que já funciona" atualizado (Etapa 2d concluída, 40 testes).
- Combinado para os próximos dias (pedido do Encarregado, 14/10/2026): conversas guiadas sobre o MAPA_M1a.md, uma seção por vez (20 a 30 min cada), com um Registro fictício contínuo (Cadastro imobiliário) atravessando todas: (1) estados do Registro e eventos automáticos G2–G4; (2) percurso sem medidas, ato por ato; (3) percurso com devolução — pendência, hash, P5/P6 e por que a Opção A; (4) percurso com medidas (G6, ação sintética) e pendência intersecretarial; (5) as cinco regras comuns, com exemplos do sistema barrando. Explicação passo a passo, avançando só quando estiver claro. À medida que o núcleo do M1a for construído, cada passo vira demonstração executável ("Registro dourado", O-84). Para começar: "vamos ao mapa, conversa 1".
- Combinado para a próxima sessão (Encarregado, 14/10/2026): reorganizar o repositório. Regra: pasta na raiz = código; docs/ = texto. Estrutura: README.md (página inicial e menu, com "Por onde começar"); app/, instalacao/, migracoes/, carga_ficticia/, demonstracoes/, scripts/ (primeiro_hash.py), testes/; docs/arquitetura/ (ARQUITETURA_POC.md atualizado, MAPA_M1a.md), docs/operacao/ (INSTALACAO.md novo), docs/diario/ (DIARIO_POC.md), docs/revisoes/ (Revisao_Etapa_2c_2026-10-14.md). Nomes em português. COLA_COMANDOS.md passa a ser só do Encarregado (git rm --cached + .gitignore) e é atualizada com os comandos novos. Execução: Claude move e ajusta os arquivos na pasta; o Encarregado roda os comandos de git (não o Cowork, que não opera bem o git).

## 2026-10-15 — Repositório reorganizado

- Regra: pasta na raiz = código; docs/ = texto. Documentos movidos para docs/arquitetura (ARQUITETURA_POC.md, MAPA_M1a.md), docs/operacao (INSTALACAO.md novo, com o passo a passo que saiu do README), docs/diario (este diário) e docs/revisoes; primeiro_hash.py para scripts/. README com "Por onde começar" e links atualizados. ARQUITETURA_POC.md atualizado (mapa das pastas, comandos atuais, app/comandos.py). COLA_COMANDOS.md agora é pessoal (docs/operacao, no .gitignore) e foi atualizada com os comandos python -m.

## 2026-10-16 — M1a: rascunho e salvamento (I1 e I2)

- Implementados os atos reais do Instrumento: I1 cria o rascunho vazio, muda o FORM 1 de `nao_iniciado` para `em_preenchimento` e grava evento na cadeia própria do Instrumento; I2 salva o conteúdo sintético, incrementa a versão do rascunho e atualiza o lacre.
- Ambos exigem pedido idempotente, conta ativa e papel de elaborador na unidade principal; recusas são auditadas e cada ato é transacional.
- O Instrumento é travado durante I1 e I2. O I2 compara a versão lida com a vigente: uma gravação desatualizada é recusada sem sobrescrever conteúdo, cobrindo o POC-TS-004.
- Migração 2 acrescentada para as tabelas `rascunho_instrumento` e `versao_instrumento`; a estrutura de versão já fica persistida, mas o ato I3 continua fora deste incremento.
- Suíte completa: 54 testes aprovados no banco próprio `lgpd_poc_teste`, incluindo idempotência, autorização, dois I1 simultâneos, dois I2 simultâneos, rollback de I1 e I2, cadeia íntegra e recriação das tabelas pela migração.

## 2026-10-16 — M1a: submissão e versão imutável (I3 e G2)

- I3 implementado sobre o FORM 1 sintético: valida os campos mínimos, confere a versão e o lacre do rascunho e cria a Versão N como snapshot canônico lacrado.
- A mesma transação grava I3 na cadeia do Instrumento e o G2 derivado na cadeia do Registro; o Instrumento passa a `pronto_para_validacao` e o Registro a `em_validacao`. A versão vigente continua vazia, pois só uma validação futura poderá defini-la.
- A comparação material verifica finalidade, titulares, categorias de dados e compartilhamentos contra a versão mais recente dos demais Instrumentos. Coincidências geram alerta para análise, sem bloqueio automático.
- A migração 3 acrescenta uma proteção no PostgreSQL contra `UPDATE` e `DELETE` de versões submetidas.
- Acrescentados 10 testes de I3/G2: snapshot e cadeias, idempotência, validação obrigatória, autorização, rascunho desatualizado, submissão concorrente, rollback conjunto, alerta material, bloqueio de I2 após submissão e imutabilidade no banco.
- Suíte completa: 64 testes aprovados no banco próprio `lgpd_poc_teste`.

## 2026-10-16 — M1a: retirada antes da análise (I4 e G3)

- I4 implementado para o elaborador retirar um FORM 1 que esteja `pronto_para_validacao`, antes do início da análise. A versão submetida permanece imutável no histórico e o rascunho volta a poder ser editado.
- A mesma transação grava I4 na cadeia do Instrumento e o G3 derivado na cadeia do Registro; o Instrumento retorna a `em_preenchimento` e o Registro a `em_andamento`.
- O cenário A11 foi comprovado: após retirar a submissão, salvar a correção e submeter novamente, o sistema preserva a Versão 1 e cria a Versão 2.
- Acrescentados 7 testes de I4/G3, cobrindo estados e cadeias, idempotência, autorização, bloqueio após I13, concorrência, rollback conjunto e o cenário A11.
- Suíte completa: 71 testes aprovados no banco próprio `lgpd_poc_teste`.

## 2026-10-16 — M1a: início da análise (I13)

- I13 implementado para atribuir a análise da versão submetida a um único responsável vigente, sem mudar os estados `pronto_para_validacao` do Instrumento e `em_validacao` do Registro.
- O ato exige conta ativa e papel de analista na unidade responsável, sempre considerando a pessoa por trás da conta. Quem submeteu a versão não pode iniciar a própria análise, mesmo usando outra conta.
- O pedido identifica explicitamente a versão e só aceita a versão submetida mais recente. A trava do Instrumento e a unicidade no banco impedem duas análises concorrentes da mesma versão.
- A projeção `analise_instrumento` preserva quem iniciou, quando iniciou e quem é o responsável atual; a futura reatribuição I14 poderá trocar apenas o responsável vigente, mantendo a trilha nos eventos.
- Migração 4 aplicada à base local da PoC. Acrescentados 8 testes de I13, elevando a suíte completa para 79 testes aprovados no banco próprio `lgpd_poc_teste`.

## 2026-10-16 — M1a: contrato fechado do FORM 1 sintético

- O campo livre `titulares` foi substituído por `categorias_titulares`. Categorias de titulares, categorias de dados e destinatários de compartilhamento agora aceitam somente códigos de catálogos fechados e fictícios.
- O contrato rejeita campos adicionais, códigos desconhecidos e códigos repetidos. A finalidade permanece textual, limitada a 500 caracteres e orientada a não conter nomes, CPF, matrícula ou outros dados pessoais.
- O contrato vigente recebeu a versão 2. Versões anteriores permanecem identificadas como contrato 1 e não têm seus snapshots reescritos.
- Criado `docs/arquitetura/CONTRATO_FORM1_SINTETICO.md`, com campos, catálogos, regras e diagrama de preenchimento. README e mapa foram alinhados em linguagem coloquial.
- Migração 5 aplicada à base local da PoC. Acrescentados 2 testes de recusa de texto livre e códigos desconhecidos, elevando a suíte completa para 81 testes aprovados.

## 2026-10-16 — M1a: reatribuição da análise (I14)

- I14 implementado para a pessoa com competência de validador transferir uma análise ativa a outro analista autorizado da unidade responsável.
- A projeção troca somente `responsavel_atual_id`; `iniciada_por`, o evento I13 e todos os atos anteriores permanecem intactos. O evento I14 registra responsável anterior e novo responsável.
- O novo responsável deve estar ativo, possuir papel de analista e não pode ser o autor da submissão. Os estados do Instrumento e do Registro não mudam.
- A reatribuição usa controle otimista pelo responsável visto na tela: duas tentativas simultâneas com a mesma leitura não se sobrescrevem; somente uma vence.
- Acrescentados 6 testes de I14, elevando a suíte completa para 87 testes aprovados no banco próprio `lgpd_poc_teste`.

## 2026-10-16 — M1a: validação e recálculo (I5 e G4)

- I5 implementado para o responsável vigente da análise validar exatamente a versão examinada. A análise é encerrada, o Instrumento passa a `validado` e `versao_vigente_id` aponta para a versão aprovada.
- G4 é gravado na mesma transação do I5 e decide o estado sem escolha manual: ação obrigatória aberta leva o Registro a `em_execucao`; sem ação aberta, leva a `em_andamento`. A regra geral que prioriza outro Instrumento pronto também foi mantida no código, embora o M1a tenha somente o FORM 1.
- Criada a ação obrigatória sintética mínima, com estado, responsável, evidência e vínculos com Registro, ciclo e Instrumento. Ela permite provar o percurso com medidas sem antecipar o FORM 4 completo.
- Migração 6 aplicada à base local da PoC. Acrescentados 8 testes de I5/G4: caminhos com e sem ação aberta, ação concluída ignorada, responsável vigente após I14, idempotência, concorrência, rollback conjunto e recriação da tabela.
- Suíte completa naquele checkpoint: 95 testes aprovados no banco próprio `lgpd_poc_teste`. A conclusão da ação, G5, G6 e o percurso de devolução ainda estavam pendentes.

## 2026-10-16 — M1a: devolução com pendência automática (I6, P1 e G3)

- I6 implementado para o agente responsável vigente pela análise devolver exatamente a versão examinada, sempre com motivo. O autor da submissão continua impedido, mesmo diante de uma projeção inconsistente.
- A mesma transação preserva a Versão N, encerra a análise, deixa o Instrumento `devolvido_para_ajuste`, cria P1 na cadeia própria da pendência e grava G3 na cadeia do Registro, que volta a `em_andamento`.
- A pendência nasce `aberta`, bloqueia o gate de submissão e é dirigida à unidade responsável pelo preenchimento, sem atribuição prematura a uma pessoa. P2 fará a assunção e I7 liberará formalmente o ajuste no próximo incremento.
- Migração 7 aplicada à base local da PoC. Acrescentados 9 testes para estados e cadeias, motivo obrigatório, responsável vigente após I14, segregação, versão analisada, idempotência, concorrência, rollback conjunto e recriação da tabela.
- Suíte completa: 104 testes aprovados no banco próprio `lgpd_poc_teste`.

## 2026-10-16 — M1a: assunção da pendência, início do ajuste e flags (P2 e I7)

- P2 implementado como ato separado: um agente com autorização de preenchimento na unidade de destino assume a pendência aberta, que passa a `em_atendimento` e recebe um único responsável atual. A trava da linha garante que duas confirmações simultâneas não criem duas assunções.
- I7 exige a pendência assumida e o mesmo agente responsável. O FORM 1 passa de `devolvido_para_ajuste` para `em_preenchimento`, e o rascunho é recriado a partir do conteúdo e do lacre da versão devolvida; a pendência permanece em atendimento até P3.
- Criado o contrato inicial das flags operacionais da futura tela: `CORRECAO_SOLICITADA`, `PENDENCIA_ATRIBUIDA_A_VOCE` e `SUBMISSAO_BLOQUEADA`. As flags são calculadas a partir do estado real e não persistidas como uma segunda fonte de verdade.
- Acrescentados 9 testes de P2, I7 e flags: autorização por unidade, mudança dos alertas, idempotência, concorrência, rollback, assunção obrigatória, responsável vigente, reconstrução do rascunho e retomada do I2.
- Suíte completa: 113 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-17 — contexto institucional e identidade das apresentações

- Registrado que o trabalho é desenvolvido para a Prefeitura Municipal de Hortolândia, dentro da Secretaria de Planejamento Urbano e Gestão Estratégica.
- Referências institucionais de reporte: Andreia Missio, Secretária Adjunta, e Eduardo Marchetti Francisco, Secretário Municipal.
- Definido como padrão que toda apresentação do projeto utilize o brasão da Prefeitura Municipal de Hortolândia, conforme a identidade já adotada na Cartilha LGPD.
- Materiais do Governo do Estado de Mato Grosso do Sul permanecem como referências conceituais e históricas, sem substituir a identidade visual institucional de Hortolândia.

## 2026-10-17 — M1a: resposta da correção e congelamento do rascunho (P3)

- P3 implementado para o agente que assumiu a pendência apresentar a correção. O ato exige a versão atual do rascunho, registra seu lacre na pendência e muda o estado de `em_atendimento` para `respondida`.
- Enquanto a pendência estiver `respondida`, novos I2 são bloqueados. A trava do Instrumento serializa salvamento e resposta concorrentes, impedindo que o conteúdo mude silenciosamente durante a conferência.
- Acrescentados 6 testes de P3: lacre e cadeia, congelamento do rascunho, recusa de tela desatualizada, responsável vigente, idempotência, concorrência e rollback.
- Suíte completa: 119 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-17 — M1a: decisão e complementação da correção (P4, P5 e P6)

- P4 implementado para a instância validadora aceitar exatamente o lacre apresentado no P3, encerrar a pendência e retirar o bloqueio da submissão. A segregação impede o autor da versão devolvida de aceitar a própria correção.
- O novo I3 só cria a Versão 2 quando não existe pendência de devolução ativa e o lacre do rascunho coincide com o aceito no P4. Alteração posterior ao aceite é detectada e recusada.
- P5 devolve a mesma pendência com motivo obrigatório; P6 permite que o agente responsável retome a edição. A nova resposta substitui apenas a projeção corrente, enquanto todas as respostas e motivos anteriores permanecem na cadeia de eventos.
- As flags calculadas passaram a avisar a instância validadora quando uma resposta aguarda P4/P5 e o agente responsável quando P5 solicita complementação; o bloqueio de submissão continua aparecendo somente para quem atua no preenchimento.
- O README recebeu um guia operacional único de P1 a P6, com significado coloquial, responsável por cada ato, resultado e a ressalva de que P5/P6 são restritos ao percurso de correção do I6 no M1a.
- Acrescentados 9 testes para os cenários A2a e A2b, competência, segregação, motivo, lacre aceito, histórico, idempotência, concorrência e rollback.
- Suíte completa: 128 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-17 — M1a: conclusão sem medidas (G5)

- G5 implementado como decisão humana separada da validação. Ele parte de `em_andamento` e exige todos os Instrumentos validados, ciclo ativo, nenhuma pendência aberta e nenhuma ação obrigatória no ciclo.
- Criado o papel técnico provisório `concluidor`, separado de `validador`, para representar a competência formal exigida pelo SAD. Na carga fictícia, a Pessoa B recebeu essa designação apenas para demonstrar o percurso, sem definir a futura matriz institucional da Prefeitura.
- Registro e ciclo passam juntos a `concluido`; a versão validada e toda a cadeia anterior permanecem preservadas. A lista de ações possíveis em `em_andamento` passou a indicar G5 como dependente de competência e de seus portões.
- Acrescentados 8 testes de G5: conclusão e preservação, Instrumento validado, competência formal, pendência aberta, medida no ciclo, idempotência, concorrência, rollback e conclusão depois da correção com Versão 2.
- Suíte completa: 136 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-17 — M1a: conclusão com medidas (ação obrigatória e G6)

- Implementada a finalização da ação obrigatória sintética. Somente o responsável vigente pode praticar o ato, e apenas quando o Registro está `em_execucao`. Tanto a conclusão normal quanto o encerramento formal exigem evidência estruturada; o encerramento formal também exige motivo.
- A finalização produz o evento técnico `AO1`, preserva evidência e justificativa na projeção da ação e mantém o pedido idempotente. A ordem das travas é Registro → ação, a mesma adotada pelo G6, evitando interbloqueio entre os dois atos.
- G6 implementado como decisão humana posterior à execução: exige papel técnico provisório `concluidor`, ciclo ativo, todos os Instrumentos validados, nenhuma pendência ativa, ao menos uma ação no ciclo e todas as ações finalizadas com evidência.
- Registro e ciclo passam juntos a `concluido`; versão validada, ações e evidências permanecem preservadas. A lista de ações possíveis em `em_execucao` passou a apresentar G6 e seus portões.
- O README recebeu a explicação coloquial e o diagrama completo do percurso com medidas.
- Acrescentados 10 testes: momento e responsável corretos, validações dos campos, evidência e cadeia, bloqueio por ação aberta, conclusão e preservação, encerramento formal, competência, idempotência, concorrência e rollback.
- Suíte completa: 146 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-19 — M1a: pendência intersecretarial mínima (P1 a P4)

- Implementado o P1 humano para a unidade principal encaminhar uma participação à fila institucional de outra unidade. O destino, os itens atribuídos e a solicitação ficam explícitos; a pendência nasce bloqueante para o gate de conclusão.
- Criado o papel técnico provisório `agente_pendencia`, separado de preenchimento, análise e validação. Na carga fictícia, Pessoa A representa a Unidade Norte e Pessoa C representa a Unidade Sul nesse percurso.
- O P2 compartilhado passou a exigir `agente_pendencia` nas participações e manteve `elaborador` nas devoluções do I6. A trava da pendência continua garantindo um único responsável diante de assunções simultâneas.
- P3 intersecretarial registra um contrato fechado com etapa executada, entrada recebida, operações, saída, interfaces e evidências. A resposta é lacrada e preservada no evento; o agente destinatário não edita o FORM 1.
- P4 intersecretarial exige agente designado na unidade de origem, aceita o lacre e encerra a pendência. O Registro permanece na unidade principal durante todo o percurso.
- As flags operacionais passaram a distinguir providência intersecretarial recebida, atribuída, resposta aguardando decisão e conclusão bloqueada.
- Acrescentados 15 testes: criação e cadeia, contexto mínimo, autorização, idempotência de P1/P3/P4, fila e flags, resposta estruturada, evidência, proteção do FORM 1, aceite, propriedade do Registro, concorrência, rollback independente de P1/P3/P4 e integração com o portão do G5.
- Suíte completa: 161 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-19 — M1a: primeiro corte da interface web

- Criada a aplicação FastAPI mínima com páginas Jinja2 e estilo responsivo. O painel identifica explicitamente o agente fictício simulado, lista os Registros do seu alcance institucional e apresenta as flags calculadas a partir do estado real.
- O alcance reúne os Registros da unidade em que a pessoa possui designação ativa e os Registros que chegaram à sua atuação por pendência institucional vigente. A camada `consultas_interface.py` prepara os dados; os templates não consultam o banco nem repetem regras de negócio.
- Criada a página de detalhe em modo somente consulta. Uma tentativa de abrir diretamente um Registro fora do alcance retorna HTTP 403 e grava `tentativa_negada` na auditoria, preparando o cenário POC-TS-007.
- O seletor de contas A1, B1 e C1 é apenas um simulador transparente com dados fictícios; não é tratado como autenticação definitiva.
- Acrescentados 4 testes HTTP: identidade e recorte por unidade, pendência intersecretarial visível no destino com flags, acesso direto negado e auditado e conta inexistente.
- README e guias operacionais atualizados com explicação coloquial, diagrama da decisão de alcance e comando para ligar a tela.
- Suíte completa: 165 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.

## 2026-10-19 — diretriz para temporalidade, retenção e descarte

- Identificada uma lacuna didática: o README mencionava retenção, mas não explicava o ciclo até a destinação dos dados.
- Registrado que há um grupo municipal trabalhando a temporalidade documental e que ele é a referência institucional para prazos e destinações. A Jornada LGPD não criará tabela paralela nem inventará prazo ausente.
- O README passou a distinguir regra oficial, marco inicial da contagem, prazo, destinação, impedimento temporário e evidência da execução, com diagrama do percurso.
- Limite da etapa explicitado: a PoC nuclear usa somente dados fictícios, preserva versões e eventos para provar integridade e não executa eliminação automática. A automação dependerá do contrato de temporalidade aprovado para a PoC ampliada.

## 2026-10-19 — M1a: I1 e I2 ligados à interface

- A página de detalhe do Registro passou a mostrar o estado do FORM 1. O elaborador pode executar I1 para criar o rascunho; agentes com outros papéis continuam em consulta.
- O formulário de I2 oferece finalidade limitada a 500 caracteres e seleções fechadas para categorias de titulares, categorias de dados e compartilhamentos. Códigos inventados ou repetidos são recusados também na fronteira HTTP.
- Cada formulário carrega um `comando_id`, preservando a idempotência em reenvios, e envia a `versao_lida` do rascunho. Uma tela desatualizada é recusada pelo domínio e não sobrescreve o conteúdo mais novo.
- Aplicado o padrão POST → redirecionamento → GET: depois do ato, a página recarrega o estado confirmado pelo PostgreSQL e apresenta mensagem de sucesso ou de recusa.
- Acrescentados 5 testes HTTP específicos: visibilidade por papel, I1 pela tela, I2 com catálogos fechados, POC-TS-004 pela tela e recusa de código forjado. Com os quatro testes anteriores, a interface possui 9 testes.
- Suíte completa: 170 testes aprovados no banco próprio `lgpd_poc_teste`. Não houve mudança de esquema neste incremento.
- Teste operacional executado com o Registro fictício `LGPD-2026-00001`: o I1 criou o primeiro rascunho e o I2 preservou no PostgreSQL a finalidade, `TIT-CONTRIBUINTE` e as categorias de identificação, endereço e dados financeiros. A cadeia confirmou I1 na sequência 1 e I2 na sequência 2; o rascunho chegou à versão 2.
- A dúvida surgida no preenchimento mostrou que seleção múltipla não pode ser confundida com todos os papéis sociais de uma pessoa. A tela e o README passaram a orientar que somente os papéis pertinentes ao serviço, processo ou atividade documentado devem ser marcados.
- Acrescentado 1 teste HTTP para essa orientação contextual, elevando a interface a 10 testes. Os 10 testes da interface e a suíte completa de 171 testes foram executados com aprovação integral.

## 2026-10-19 — identidade do agente e contexto antes do FORM 1

- Registrada a decisão institucional informada por servidor da Prefeitura: em Hortolândia, cada servidor, concursado ou não, possui uma única matrícula. Na solução futura, a matrícula será o nome de usuário e a senha será individual, validada pelo mecanismo institucional a confirmar com Ana e Rafael.
- A PoC recebeu matrículas exclusivamente fictícias e únicas. O seletor inicial passou a apresentar a simulação por matrícula e continua sem senha real.
- Criada a etapa anterior ao FORM 1: o elaborador seleciona primeiro a Secretaria responsável pelo Registro dentro de seu alcance institucional; depois escolhe serviço, processo ou atividade do catálogo e o contexto de atuação. A tela não expõe a classificação técnica “unidade principal”. Na implantação municipal, a Secretaria virá de lista fechada das 18 Secretarias; departamentos e setores são executores, e outras Secretarias poderão participar. O nome oficial do objeto vem do catálogo; o G1 existente cria o Registro, o ciclo 1 e o FORM 1 Não iniciado.
- Delimitado o catálogo institucional da PoC às 18 Secretarias da Administração Direta. O Hortoprev, autarquia da Administração Indireta, fica fora do recorte e não será apresentado como Secretaria.
- O cadastro permanente de unidades participantes não foi antecipado: permanece na PoC ampliada. A colaboração mínima do M1a continua pelo percurso intersecretarial, sem troca da unidade principal.
- Criado contrato arquitetural específico para identidade e contexto inicial. Incluída migração 8 para acrescentar matrícula única sem perder as pessoas fictícias existentes.
- Acrescentados 6 testes: duas garantias da identidade e quatro percursos HTTP. O novo percurso integrado cria um Registro isolado e atravessa contexto inicial, G1, I1 e I2, sem apagar nem recomeçar o Registro 0001. Os 16 testes de identidade/interface e a suíte completa de 177 testes foram aprovados.
- Migração 8 aplicada à base local. O Registro fictício `LGPD-2026-00001` permaneceu `em_andamento`; o FORM 1 permaneceu `em_preenchimento`, com rascunho 2 e `TIT-CONTRIBUINTE` preservados.
- Servidor local reiniciado sem `--reload`. Painel e nova etapa contextual responderam HTTP 200 com matrícula fictícia, os três tipos de objeto e a unidade principal.

## 2026-10-20 — catálogo institucional das Secretarias

- Autorizado o uso dos nomes reais e públicos das 18 Secretarias da Administração Direta no catálogo institucional; o Hortoprev permanece fora do recorte. Pessoas, matrículas, designações, serviços e Registros continuam fictícios.
- Os ids legados `UNID-NORTE` e `UNID-SUL` foram preservados para manter vínculos e eventos, passando a exibir, respectivamente, Planejamento Urbano e Gestão Estratégica e Finanças. As outras 16 Secretarias foram acrescentadas sem receber designações automáticas.
- O catálogo não amplia permissões: a tela de criação apresenta somente Secretarias em que o agente possui designação vigente de elaborador. Alfa vê Planejamento e não vê Finanças.
- Acrescentado teste que garante exatamente 18 Secretarias, nomes e identificadores únicos e ausência do Hortoprev. Os 17 testes de identidade/interface e a suíte completa de 178 testes foram aprovados.
- A carga foi sincronizada na base local. O Registro `LGPD-2026-00001` permaneceu preservado.
- README ganhou diretriz operacional com diagrama: o Registro permanece com a Secretaria responsável; agentes, versões e pendências circulam sem transferência informal. Foram diferenciadas atuação interna, submissão para análise, participação de outra Secretaria e eventual mudança da Secretaria responsável. Os rótulos recomendados são “Solicitar participação de outra Secretaria” e “Atribuir próxima ação a outro agente”.
- Fechado o método operacional de formação do catálogo: Carta de Serviços e portal fornecem candidatos a serviços; os FORMs recebidos das Secretarias fornecem candidatos também a processos e atividades. Nenhum item se torna oficial automaticamente: a curadoria verifica o tratamento de dados pessoais, tipo, Secretaria, duplicidades, fonte e data e atribui o identificador canônico.
- Definido o percurso futuro em cascata: Secretaria responsável → tipo → objeto vinculado à Secretaria → contextos permitidos. A filtragem e as relações de catálogo não foram implementadas nesta rodada, conforme decisão de não antecipá-las sem carga e curadoria; ficaram como incremento próprio testado.
- Consolidada a explicação de contexto para a interface: é a frente administrativa e funcional em que o objeto utiliza dados pessoais; não é Secretaria, canal, hipótese legal nem finalidade do FORM 1.
- Canais como o 156 não formarão um quarto tipo de objeto. Serão relações informativas do catálogo; quando apenas encaminharem, serão apoio, e somente receberão Registro próprio se realizarem tratamento autônomo de dados pessoais.
- A tela de criação passou a diferenciar contexto e finalidade por um exemplo da Saúde: fornecimento de medicamento de alto custo, contexto Assistência farmacêutica e finalidade restrita aos dados necessários para verificar requisitos, fornecer o medicamento e acompanhar o tratamento. A orientação está associada ao campo para leitores de tela; o catálogo, o banco e as regras de contexto não foram alterados neste incremento. O novo teste HTTP e a suíte completa de 179 testes foram aprovados.

## 2026-10-21 — catálogo por Secretaria e leitura dos inventários

- Conferidos os materiais locais de inventário sem importar respostas ou dados pessoais. Os dois PDFs e a planilha são três representações do mesmo levantamento de 81 perguntas; a Cartilha organiza o percurso em quatro momentos: realidade, legitimidade, risco e ação/acompanhamento.
- Definido o aproveitamento seguro: nome candidato do objeto, tipo, Secretaria principal e proveniência podem alimentar a curadoria do catálogo. Frequência, executor, canais, finalidade, dados, titulares, retenção, segurança, contratos e riscos permanecem nos instrumentos e na análise posterior.
- Implementada a migração 9, com vínculo vigente entre Secretaria e objeto, papel `RESPONSAVEL` ou `PARTICIPANTE` e fonte. Os vínculos da carga continuam explicitamente fictícios e não afirmam competências reais das Secretarias.
- A tela passou a mostrar somente objetos responsáveis vinculados às Secretarias ao alcance do elaborador. O G1 repete a conferência no servidor e recusa pedidos forjados com item de outra Secretaria.
- Acrescentados três testes: vínculo fictício com proveniência, filtragem da tela por Secretaria e recusa no domínio. A suíte completa chegou a 182 testes aprovados.
- Implementada a migração 10 para a relação vigente entre item do catálogo e contexto de atuação, também com fonte. A tela agora completa a cascata Secretaria → tipo → item → contextos permitidos; o G1 recusa contexto incompatível mesmo em pedido forjado.
- Acrescentados dois testes HTTP para a filtragem e a proteção do contexto. A cobertura passou a 19 testes de interface e 184 testes no total.

### 21/10/2026 — hierarquia dos FORMs e apoio dos inventários

- Confirmado que a Cartilha e seus quatro FORMs são a referência funcional principal.
- A PoC nuclear permanece com o FORM 1 sintético; a PoC ampliada deverá cobrir o FORM 1 integral de ponta a ponta.
- Os FORMs 2, 3 e 4 ficam como referência arquitetural para etapa posterior.
- Inventários e relatórios são apoio: não criam campos nem são importados automaticamente, mas agrupamentos recorrentes podem sugerir candidatos ao catálogo de contextos, sempre sujeitos à curadoria.

### 21/10/2026 — matriz de aceite da PoC nuclear

- Criada a matriz detalhada dos testes formais `POC-TS-001` a `POC-TS-009`, preservando as descrições e os resultados esperados do SAD 09 REV12.
- A matriz separa cobertura automatizada, evidência formal e aceite institucional: sete testes possuem cobertura relevante, mas nenhum foi marcado como formalmente aceito antes da rodada identificada e da conferência das evidências.
- Permanecem como ensaios completos pendentes o bloqueio de dado pessoal real na carga sintética (`POC-TS-008`) e o volume de 1.000 Registros com cerca de 50.000 eventos (`POC-TS-009`).
- O README recebeu um resumo coloquial, um diagrama do caminho Regra → POC-TS → teste automatizado → evidência → aceite e um link para a matriz detalhada.
- O `POC-TS-003` foi reforçado no ensaio concorrente com duas pessoas: além de uma única assunção e um único evento P2, o teste exige exatamente uma tentativa negada na auditoria, ligada ao comando perdedor e à pendência disputada. O teste específico e a suíte completa de 184 testes foram aprovados.
- Implementada a barreira do `POC-TS-008` antes das gravações da carga fictícia. Pessoas, matrículas, nomes e contas exigem marcadores sintéticos; toda a massa é examinada contra CPF, e-mail e telefone em formato pessoal. A recusa aponta somente o tipo e a posição do problema, sem reproduzir o conteúdo suspeito.
- Quatro variações controladas comprovam que uma identidade sem marcadores e valores simulados nos formatos de CPF, e-mail e telefone são recusados antes de qualquer gravação. Nenhum dado pessoal real foi incluído nos testes ou nas evidências. A suíte completa passou a 188 testes aprovados.

### 22/10/2026 — ensaio de volume POC-TS-009

- Criado executor separado e protegido para o ensaio pesado: ele só aceita banco terminado em `_teste`, exige confirmação explícita e usa os mesmos texto canônico e SHA-256 do livro de atos.
- A prova reduzida passou com 10 Registros, 50 eventos e três reconstruções coincidentes.
- O ensaio completo foi aprovado com 1.000 Registros sintéticos, 50.000 eventos, cinquenta eventos por cadeia, verificação integral das 1.000 cadeias e reconstrução coincidente de 25 Registros.
- A carga levou 20,204 segundos; a verificação e a reconstrução, 5,503 segundos; o total foi de 27,298 segundos. Nenhum dado pessoal real foi utilizado.
- Acrescentado teste cotidiano pequeno para proteger o gerador sem impor o custo do ensaio pesado a cada execução. A suíte completa passou a 189 testes aprovados.
- Criada evidência técnica preliminar. O ensaio está tecnicamente coberto, mas continua aguardando associação ao commit e incorporação ao pacote formal `POC-EV` antes do aceite institucional do M1a.

### 22/10/2026 — preparação da passagem técnica para a T.I.

- Criada a pasta `11_Cartilha_Apresentacoes` no conjunto dos SADs para reunir a Cartilha e as apresentações institucionais do sistema dirigidas à Tecnologia da Informação.
- Preparada a primeira lâmina esquemática da evolução do trabalho: base metodológica, PoC nuclear M1a, apresentação e entrega técnica, eventual PoC ampliada, caso piloto e operação.
- O ciclo de aprendizado liga a coleta realizada pelas Secretarias ao cruzamento com os quatro FORMs e ao aprimoramento futuro do catálogo e dos campos.
- Confirmado que a PoC ampliada não começa automaticamente depois da apresentação. O Encarregado primeiro fará a leitura do README e decidirá expressamente sobre a etapa seguinte.
- Mantida a ata formal de aceite. A minuta passou a integrar o README e será preenchida e entregue no dia da apresentação à T.I., junto com as evidências e a referência do commit aceito.
- A primeira lâmina passou a identificar a responsabilidade por etapa: SENAC no treinamento; Secretaria de Planejamento Urbano e Gestão Estratégica da Cartilha até a PoC ampliada; Secretaria de T.I. na experiência prática, no levantamento de dados, no caso piloto e na operação.

### 22/10/2026 — rodada formal de encerramento técnico do M1a

- Criado o checkpoint técnico `df2db0f5b49579844eacd6107a633da14176f427` para associar código, matriz e ensaio de volume.
- Executada a rodada identificada `M1A-20261022-001` no banco exclusivo `lgpd_poc_teste`: 189 de 189 testes aprovados, sem falhas, erros ou testes ignorados.
- Reexecutado o `POC-TS-009`: 1.000 Registros, 50.000 eventos, 1.000 cadeias íntegras e 25 reconstruções coincidentes; tempo total de 21,092 segundos.
- Consolidados os resultados dos nove `POC-TS` e dos pacotes `POC-EV-001` a `006`, `009`, `011`, `014` e `015` no relatório formal.
- Os artefatos operacionais permanecem fora do Git e foram identificados por SHA-256. Nenhum dado pessoal real foi usado.
- A PoC nuclear ficou tecnicamente pronta para aceite. Permanecem como atos humanos a apresentação à T.I., a conferência das limitações e o preenchimento da ata de aceite e transferência técnica.

### 22/10/2026 — pacote de contexto para agentes de IA

- Criado `AGENTS.md` na raiz com ordem de leitura, invariantes do domínio, segurança, disciplina de testes e critérios de conclusão de tarefas.
- Criado `docs/contexto/` com resumos curtos de produto, domínio, glossário, arquitetura, testes e sistema visual. Os arquivos apontam para README, contratos e SADs e não criam fonte de verdade paralela.
- Formalizado o frame mínimo de cada incremento: objetivo, escopo, regra e fonte, atores, estados, dados, aceite, testes, evidências e limitações.
- Registrado o padrão Arrange–Act–Assert para testes e sua distinção do nível AAA de acessibilidade.
- Documentada a base visual existente e a proposta de evolução por tokens, componentes e movimento reduzido, sem alterar a interface nesta rodada.

### 22/10/2026 — aceite da PoC nuclear M1a

- O Encarregado de Dados aceitou expressamente o M1a após a rodada formal `M1A-20261022-001`, com 189 de 189 testes e 9 de 9 cenários `POC-TS` aprovados.
- O aceite preserva as limitações conhecidas: checkpoint externo e custódia institucional no backlog; temporalidade dependente da regra oficial; autenticação, integrações, Piloto e produção fora do M1a.
- Permanecem pendentes a apresentação, o registro dos participantes e a transferência técnica à T.I.
- O aceite do M1a não inicia automaticamente a PoC ampliada, que depende de decisão expressa própria.

### 23/10/2026 — orientação visual para a futura PoC ampliada

- O README passou a explicar à T.I. a separação proposta entre tokens, componentes, movimento e composição das páginas.
- A PoC nuclear aceita permanece como referência estável; nenhuma reorganização do CSS, biblioteca ou animação foi introduzida nesta rodada.
- Bibliotecas externas dependerão de benefício demonstrável, acessibilidade, manutenção, segurança e compatibilidade com a identidade municipal.
- O primeiro incremento visual futuro exigirá referências aprovadas, comparação antes/depois, testes de teclado, foco, contraste, responsividade e regressão HTTP.
- Criada `docs/design-system/` para guardar no Git a especificação visual completa, a paleta e o histórico de decisões, mantendo em `docs/contexto/` apenas o resumo inicial para agentes.
- A linguagem do painel foi esclarecida: “flags calculadas” permanece termo técnico, enquanto o servidor vê “Pendências e próximas ações” e “O que precisa da sua atenção”.
- “Registros ao seu alcance” foi substituído na interface por “Mapeamentos disponíveis para você”, e a criação passou a distinguir a abertura da etapa inicial da confirmação que efetivamente grava o Registro.
- O painel passou a mostrar a criação somente ao papel de elaborador; analistas e validadores recebem explicação de que podem consultar, analisar ou validar, mas não iniciar Registro.
- O cabeçalho do FORM 1 passou a declarar seu objetivo ao lado do nome e do estado, esclarecendo que o instrumento registra finalidade, categorias de titulares e dados e compartilhamentos sem identificar pessoas.
- Registrada como hipótese, ainda sem requisito aprovado, uma futura visão agregada de coordenação distinta da administração técnica da T.I.
