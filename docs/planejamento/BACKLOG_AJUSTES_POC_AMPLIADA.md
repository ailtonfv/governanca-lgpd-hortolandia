# Acompanhamento dos ajustes da PoC ampliada

**Data da consolidação:** 05/11/2026. **Base inspecionada:** `main`, commit `26b9e97f0d6cdca4a19b342929128591947bab13`, com alterações locais descritas abaixo.

O diagnóstico e a tabela registram a situação anterior aos commits de estabilização. A seção final atualiza o versionamento e a evidência dos testes, preservando as 13 ocorrências e suas propostas.

Este documento reúne o diagnóstico e as propostas da primeira avaliação assistida dos 14 blocos. Não autoriza implementação das propostas, mudança de contrato ou liberação da submissão institucional. Cartilha e apresentação não foram modificadas.

## Evidências e limites

O responsável funcional informou ter percorrido os 14 blocos no Registro fictício `LGPD-2026-00004`, com navegação, condicionais, salvamento e recuperação satisfatórios. Naquela avaliação, foram observados 15 obrigatórios ativos incompletos, 49 condicionais não aplicáveis, um aviso facultativo e duas dependências de governança. São valores daquele momento, relatados pelo usuário, não totais fixos nem uma nova consulta ao banco nesta tarefa. A avaliação não equivale à conclusão integral nem à submissão institucional.

A correção local da ordenação teve **71 testes aprovados**, incluindo dez cenários novos, e comparação de **102 cenários** com a versão anterior: conteúdo, contagens, ocorrências e regras preservados. Esses resultados pertencem à tarefa imediatamente anterior; não foram repetidos nesta consolidação documental.

**ACEITAÇÃO VISUAL DA ORDENAÇÃO NÃO VERIFICADA.** Nesta sessão, a ferramenta de navegador falhou na inicialização: `failed to write kernel assets`, erro do Windows 3, caminho não encontrado. Não foi possível abrir a tela por essa ferramenta. Não houve contorno, salvamento ou alteração do rascunho demonstrativo.

Situações abaixo descrevem a entrega indicada, não uma aceitação global: **identificada**, **em análise**, **autorizada**, **implementada**, **testada** ou **concluída**. Uma entrega testada automaticamente pode ainda depender de avaliação manual. P1 indica precisão factual ou usabilidade importante; P2 indica consolidação editorial. O bloqueio institucional é requisito para futura liberação, não defeito que impeça demonstrar o rascunho e a conferência interna.

## Registro das ocorrências

| ID | Identificação | Componente e descrição | Classificação | Prioridade | Situação e evidência |
|---|---|---|---|---|---|
| AJ-001 | 05/11/2026 | 12.3 e 12.4 agregam procedimentos e evidências de operações diferentes. | Revisão conceitual | P1 / A | Implementada na INSTRUÇÃO_FORMS01_04: extensão optativa, procedimentos/evidências independentes por operação e localização condicional; legado preservado. 652/652 testes aprovados; aceitação visual NÃO VERIFICADA. |
| AJ-002 | 05/11/2026 | 12.5 não diferencia transferência de sistema, arquivo, custódia e mudança de localização. | Revisão conceitual | P1 / A | Implementada na INSTRUÇÃO_FORMS01_04: modalidades múltiplas, destino factual e complemento de Outra situação na extensão versionada, sem avaliação jurídica. 652/652 testes aprovados; aceitação visual NÃO VERIFICADA. |
| AJ-003 | 05/11/2026 | 13.1 precisa explicar as três alternativas especiais no contexto da pergunta. | Melhoria | P1 / B | Implementada e testada na INSTRUÇÃO_FORMS01_01 / Etapa A: ajuda contextual diferencia as três alternativas; exclusividade preservada. 51 testes aprovados. Aceitação visual NÃO VERIFICADA. |
| AJ-004 | 05/11/2026 | 13.2 reúne guarda de documentos e bloqueio de estações em uma resposta. | Revisão conceitual | P1 / B | Extensão autorizada pela INSTRUÇÃO_FORMS01_03 e implementada: adoção explícita pelo ARP, 13.2 e 13.2.1 facultativas e independentes, snapshot e resposta agregada preservados. 32 testes focalizados e 624/624 na regressão integral aprovados; aceitação visual NÃO VERIFICADA. Diagnóstico anterior preservado abaixo. |
| AJ-005 | 05/11/2026 | Total de obrigatórios no painel não aponta diretamente à sua distribuição. | Melhoria | P1 / C | Implementada e testada na INSTRUÇÃO_FORMS01_01 / Etapa B: distribuição expansível usa a mesma projeção autorizada e contagens, sem novas consultas. 79 testes aprovados. Aceitação visual NÃO VERIFICADA. |
| AJ-006 | 05/11/2026 | Pendências complementares fora da ordem canônica. | Defeito | P1 / D | Testada localmente, sem commit; `pre_validar_form1_integral()`. 71 testes e comparação de 102 cenários. Aceitação visual pendente. |
| AJ-007 | 05/11/2026 | Formalização documental de APA e SAA. | Melhoria documental | P2 / E | Implementada no README local, sem commit. SAA não cria perfil ou permissão. Harmonização de outros documentos pendente. |
| AJ-008 | 05/11/2026 | Dependência editorial de “WhatsApp corporativo”. | Dependência institucional/documental | P2 / E | Em análise: expressão encontrada na REV30.14; dependência continua no código. Reconciliar antes de declará-la resolvida no sistema. |
| AJ-009 | 05/11/2026 | Ajuda usa REV30.13 enquanto referência editorial consolidada é REV30.14. | Melhoria documental | P1 / E | Em análise; 12 títulos preservados, dez seções com texto extraído igual e duas alteradas. Sem troca de edição. |
| AJ-010 | 05/11/2026 | Aprovação institucional da matriz e marco de liberação. | Dependência institucional | P0 para submissão | Identificada; submissão permanece bloqueada. Demonstração de rascunho/conferência não depende dessa liberação. |
| AJ-011 | 05/11/2026 | Categoria única em 10.2.1 dispensando escolha repetida. | Melhoria | P1 | Concluída tecnicamente e versionada em `26b9e97`; não constitui nova aceitação visual nesta sessão. |
| AJ-012 | 05/11/2026 | Coordenação do salvamento das respostas e destinatários do Bloco 10. | Melhoria | P1 | Concluída tecnicamente e versionada em `35f66a3`; cobertura em `test_jornada_destinatarios_form1.py`, incluída na rodada anterior de 71 testes. |
| AJ-013 | 05/11/2026 | Destinatários na posição 10.2 → 10.2.1 → 10.3 da área de preenchimento. | Defeito | P1 | Correção existente em `b75a660`; reforço de teste local em `test_usabilidade_blocos_9_10.py`. Não confundir com AJ-006, relativo à lista de pendências. |

As pendências históricas do 8Z continuam em [BACKLOG_VERIFICACOES_VISUAIS_8Z.md](BACKLOG_VERIFICACOES_VISUAIS_8Z.md). Este acompanhamento não as declara aprovadas; critérios antigos vinculados ao painel de duas listas precisam ser confrontados com o painel unificado antes de nova execução, sem reescrever o histórico.

## A — Guarda e destinação no Bloco 12

### Estado comprovado

O catálogo `app/catalogos/form1_rev13.csv`, carregado por `app/form1_integral.py`, define:

| ID | Representação atual | Obrigatoriedade vigente |
|---|---|---|
| 12.3 | Seleção única: Sim, Não, A confirmar; abrange eliminação, arquivamento, devolução e transferência. | Facultativa nesta proposta. |
| 12.4 | Seleção única: Sim, Não, Em alguns casos, A confirmar, Não se aplica; evidência de eliminação, devolução ou transferência. | Facultativa nesta proposta. |
| 12.4.1 | Texto único para localização da evidência. | Condicional a 12.4 = Sim ou Em alguns casos. |
| 12.5 | Seleção única: Sim, Não, A confirmar; transferência para outro sistema ou arquivo como destinação/guarda. | Facultativa nesta proposta. |
| 12.5.1 | Texto único para o sistema/arquivo de destino. | Condicional a 12.5 = Sim. |

Fontes: `CONDICOES_BLOCO_12`, `MATRIZ_CAMPOS_FORM1_REV13.md`, `salvar_bloco_12_form1_integral()` e contrato candidato 3. As respostas ficam no envelope JSON do rascunho. `VersaoForm1Integral` e `app/submissao_form1_integral.py` preservam snapshots; não se deve reescrever uma versão para aplicar novas interpretações.

### Proposta mínima para aprovação

Preservar os números 12.3 e 12.4 como grupos visuais. Dentro de cada grupo, identificar separadamente quatro operações: guarda/arquivamento, eliminação, devolução e transferência. Para cada operação, registrar a existência de procedimento e, em dimensão distinta, a existência de evidência de execução. Não inferir um valor a partir da outra dimensão. Aplicar a documentos físicos e digitais, sem pressupor que serão eliminados.

Propor respostas por operação que distingam existência, ausência, informação parcial, informação a confirmar e não aplicabilidade, com o catálogo exato submetido à aprovação. “Não se aplica” deve permanecer disponível para evidências; ausência de execução a evidenciar não deve ser confundida automaticamente com ausência de procedimento. Definir expressamente esse caso antes de implementar. Não presumir que toda resposta negativa exija justificativa.

Manter 12.4.1 como localização/referência da evidência, mas associada à operação pertinente. Uma mesma referência pode apoiar várias operações, sem copiar arquivos ou dados de cidadãos. A regra de exigência de 12.4.1 precisará ser reexpressa por operação e aprovada; não converter as perguntas facultativas em obrigatórias por conveniência técnica.

Em 12.5, identificar a natureza da transferência: outro sistema, arquivo/unidade documental ou custódia. Essas dimensões podem coexistir; não impor exclusividade. Simples mudança de localização não implica automaticamente transferência de custódia. 12.5.1 mantém o destino e a explicação factual pertinente. A mudança de local já descrita no Bloco 11 pode ser referenciada, sem exigir nova resposta idêntica.

Separação proposta: Bloco 8 descreve sistemas/meios utilizados na execução; Bloco 10 descreve disponibilização a destinatários; Bloco 11 descreve a guarda atual; Bloco 12 descreve temporalidade, destinação e transferências ligadas a esse ciclo. Um mesmo sistema pode aparecer em mais de um contexto com funções distintas; isso não deve gerar cópia automática de respostas. O levantamento não aprova a legalidade da destinação nem fixa prazos arquivísticos.

### Impacto e compatibilidade

Não se trata de simples troca de rótulos: os escalares atuais não representam quatro respostas independentes. Propor uma estrutura versionada no envelope JSON, com discriminação das operações, mantendo os IDs externos preferencialmente. O desenho definitivo deve ser aprovado no contrato e na matriz antes do código; não introduzir tipos novos sob a mesma versão sem discriminação. Não há evidência de necessidade de nova tabela; avaliar primeiro o envelope existente.

Preservar integralmente a resposta legada e sua versão de origem. Um “Sim” antigo não pode virar quatro respostas “Sim”. Propor leitura legada identificada e confirmação explícita pelo ARP ao adotar o novo formato, com ato auditável e novas respostas inicialmente não inferidas. Manter snapshots, lacres e eventos antigos intocados; eventual evolução do rascunho deve ter estratégia reversível, sem conversão em lote implícita.

**Arquivos potencialmente afetados:** catálogo e carregador `app/form1_integral.py`; contrato candidato e matriz versionados; `app/rascunho_form1_integral.py`; `app/pre_validacao_form1_integral.py`; projeções em `app/consultas_interface.py`; `_bloco_catalogado_form1.html` e consulta somente leitura; testes de Bloco 12, snapshots e pré-validação. Inspecionar serialização em `app/submissao_form1_integral.py` antes de decidir se precisa de alteração; não presume mudança de banco.

**Testes futuros:** procedimento existente somente para arquivamento; evidência presente somente para eliminação; aplicação parcial; não aplicabilidade e informação desconhecida; físicos/digitais; transferência simultânea de sistema/custódia; mudança de local sem troca de custódia; condicionais por operação; salvamento incompleto; reabertura de legado; snapshots anteriores íntegros; autorização, concorrência, idempotência e rollback se a escrita mudar.

**Risco:** alto de reinterpretar legado ou alterar exigências indevidamente; mitigação por esquema discriminado e testes de compatibilidade. **Esforço indicativo:** 8–14 horas de implementação e testes após decisões fechadas; incerteza maior se houver nova matriz/contrato ou migração de formato não prevista. Não inclui tempo de aprovação institucional.

## B — Clareza e granularidade do Bloco 13

### 13.1 — Orientação sem mudança de regra

As três alternativas especiais existem no catálogo. `problema_exclusividade_multisselecao()` em `app/politica_form1_integral_8v.py` exige que cada uma seja usada isoladamente. O teste parametrizado `test_bloco_13_recusa_excludente_com_outra_situacao`, em `testes/test_bloco13_form1_integral.py`, já cobre **cada uma das três** combinada com uma exposição concreta. Não criar teste duplicado; complementar a cobertura visual/da ajuda se aprovada. Esse teste foi inspecionado, não reexecutado nesta tarefa documental.

Proposta de texto no componente existente “Entenda esta pergunta”:

> **Nenhuma das situações acima:** o fluxo foi examinado e nenhuma das situações de exposição listadas foi identificada. **Não se aplica:** as situações investigadas não são pertinentes ao fluxo analisado. **A confirmar:** ainda não existem informações suficientes para concluir a avaliação. Escolha cada uma dessas alternativas isoladamente; elas não podem ser combinadas com situações concretas de exposição.

13.1 não possui entrada em `AJUDAS_CARTILHA_FORM1`. Reutilizar o componente com orientação sem criar um link editorial inexistente; se houver referência à Cartilha, verificar antes a seção real e executar os testes de vínculos exigidos no AGENTS. Não atribuir uma nova seção por analogia. A pré-validação continua tratando “A confirmar” como pendência no campo obrigatório; o texto não deve prometer conclusão ou aprovação.

Arquivos possíveis: mapa de ajudas, componente `_ajuda_cartilha_form1.html`, projeção da ajuda e testes associados, somente se necessários ao mecanismo sem referência. Risco baixo, de contradizer a regra ou inventar um destino. Testar alternativas especiais isoladas, todas as combinações proibidas pertinentes, preservação do rascunho e leitura por teclado. **Esforço: 1–2 horas**, após autorização.

### 13.2 — Duas medidas independentes

A resposta atual é única: Sempre, Às vezes, Não, A confirmar ou Não se aplica. A matriz a classifica como facultativa nesta proposta. Não é possível representar com precisão guarda realizada e estação não bloqueada.

Propor duas linhas sob 13.2: guarda dos documentos e bloqueio das estações, cada uma com resposta própria. Preservar a numeração visual não elimina a mudança de estrutura de dados. Aprovar o esquema versionado e as condições de não aplicabilidade, sem inferir “Não se aplica” para uma medida a partir da outra. Evitar criar novas perguntas independentes se o grupo puder comportar as dimensões.

Manter a resposta antiga explicitamente como agregada; não copiá-la para ambas as linhas. Preservar a natureza facultativa até decisão contrária. Aplicam-se as salvaguardas de compatibilidade do Bloco 12.

Arquivos possíveis: catálogo/contrato/matriz aprovados, `app/form1_integral.py`, `salvar_bloco_13_form1_integral()`, pré-validação, templates e consulta histórica. Testar combinações discordantes, uma dimensão vazia, não aplicabilidade, salvamento/retomada, legado e versões imutáveis. Risco médio de conversão indevida e mudança de exigência. **Esforço: 4–6 horas**, com decisões fechadas e reutilização do formato aprovado; estimativa pode cair se a infraestrutura do Bloco 12 servir ao mesmo desenho.

## C — Distribuição das pendências no painel

`carregar_painel()` em `app/consultas_interface.py` já calcula `preenchimentos_arp` somente após `_pode_editar_form1_integral()`. Usa a pré-validação vigente, inclui rascunho não iniciado por cálculo em memória e soma uma entrada por Registro. A projeção entrega `registro.preenchimento_arp.quantidade`; `app/paginas/inicio.html` já a apresenta em **Seu preenchimento** no cartão. O indicador consolidado, porém, é apenas texto e não leva diretamente a essa distribuição.

Proposta mínima: tornar consultável junto ao contador uma seção expansível “Distribuição por Registro”, utilizando exclusivamente os mesmos cartões/projeções já autorizados. Cada linha mostra código, título, quantidade e link ao cartão correspondente. Não listar cada pergunta nem duplicar formulários/botões de ação. O link ao cartão destaca o item e preserva a navegação de início/retomada já existente. Incluir Registros pertinentes com zero quando necessário para explicar a soma; identificar rascunho ainda não iniciado. A soma exibida deve coincidir com o indicador e não incluir Registros apenas consultáveis de outro ARP.

Alternativa ainda menor: ligação do contador à lista existente, destacando os cartões com preenchimento do usuário. Escolher a seção expansível se a quantidade de cartões dificultar a compreensão imediata; não reconstruir dois painéis de tarefas.

**Arquivos possíveis:** `app/paginas/inicio.html`, estilos existentes e testes do painel; projeção apenas se faltar um dado, sem nova consulta de autorização ou recálculo. **Testes futuros:** um/vários Registros, soma sem duplicação, zero, rascunho não iniciado, APA com outro ARP, sem acesso, conferência pendente e histórico confirmado; links corretos, foco por teclado e telas estreitas. **Risco:** vazamento de contagens ou duplicação caso se abandone o filtro existente; minimizar reutilizando `preenchimento_arp`. **Esforço: 2–4 horas**, incluindo testes e conferência manual.

## D — Ordenação local e aceitação visual

A alteração em `pre_validar_form1_integral()` ordena estavelmente `incompletos` pela matriz antes de agrupar por bloco. Complementos e ocorrências da mesma pergunta conservam conteúdo e identidade. O total não muda. A lista global também segue a ordem canônica, mantendo coerência da primeira pendência com a lista exibida. Os casos 10.2.1 antes de 10.3, inclusive com 10.2 já respondida, estão cobertos por teste de HTML.

Permanecem locais e sem commit: `app/pre_validacao_form1_integral.py`, `testes/test_ordenacao_pendencias_form1.py`, o reforço anterior de `testes/test_usabilidade_blocos_9_10.py` e as adições de APA/SAA e ordenação no README. A sessão atual não mudou esses arquivos de código/teste.

Roteiro de aceite sem editar o Registro 00004: abrir o Registro com autorização, expandir **Pendências antes da futura submissão → Bloco 10** e conferir a ordem dos IDs presentes. Se 10.2 estiver satisfeita, ela não deve aparecer; isso não é defeito. Se 10.2.1 e 10.3 estiverem ambas pendentes, 10.2.1 deve preceder 10.3. A sequência com os três IDs exige que 10.2 também tenha uma pendência, como complemento de “Outro”; usar somente massa isolada de teste para esse cenário, não mudar o rascunho avaliado para provocá-lo. Conferir os detalhes das ocorrências e os destinos de consulta/edição conforme permissão. Registrar data, perfil, captura e resultado. **Esforço manual estimado: 0,5–1 hora**, sem repetir a regressão se o código não mudar.

## E — Dependências documentais e institucionais

### APA, SAA e ARP

A seção **APA e SAA — autorização de governança e acesso aos dados** já existe no README local. Diferencia autorização de acesso/tratamento de competência de abertura/governança; SAA não é novo perfil. A referência à apresentação de 9.1 preserva códigos históricos. Cartilha, apresentação e demais fontes terão harmonização em marco posterior, sem ampliar permissões. Situação documental implementada não significa commit/publicação.

### Cartilha REV30.13 e REV30.14

Leitura somente textual, sem edição nem avaliação da diagramação:

- A edição efetivamente usada pela PoC é `documentos_locais/cartilha/CARTILHA_LGPD_HORTOLANDIA_REV30_13_MARCO_03-11-2026.docx`, fora do Git. Existe e seu SHA-256 corresponde ao configurado em `app/ajudas_cartilha_form1.py`.
- O carregador `app/cartilha_local.py` disponibiliza **12 seções temáticas**, utilizadas pelas **22 ajudas** do mapa. Há identidade temática estável, edição explícita e checagem do hash; não há fundamento para substituir apenas o rótulo por REV30.14.
- Foi localizada a referência editorial `CARTILHA_LGPD_REV30_14_CONSOLIDADA_SAA_05-11-2026.docx`, em `11_Cartilha_Apresentacoes` do conjunto SAD. SHA-256: `3bc5df4c2751fd2f24ec9abdded59e436d00aaf893b6b411aa6c364d801baadf`.
- Os 12 títulos de seção do mapa existem na REV30.14. Na comparação do texto extraído, dez seções são iguais; **5.1 Levantamento da realidade** e **5.2 Operações, canais e ambientes** mudaram. 5.1 acrescenta o percurso entre Secretarias e esclarecimento sobre destinatário interno; 5.2 acrescenta orientação sobre instrumento pertinente municipal e a pendência de modelagem. A comparação não certifica equivalência de imagens/diagramação.
- As referências atuais continuam coerentes com a edição REV30.13 que identificam e com seções disponíveis localmente. Isso não constitui teste visual de navegação nesta sessão nem atualização para a nova edição.

Propor incorporação controlada após autorização: conferir a correspondência das 22 ajudas; preservar IDs temáticos; manter edições anteriores consultáveis sem substituir silenciosamente seus destinos; registrar revisão/hash e alterações editoriais; disponibilizar a nova edição somente localmente e para leitura. O carregador atual fixa uma edição/hash; preservar consulta histórica ao adotar outra edição exige desenho explícito de seleção por versão, não só trocar constantes. Não publicar DOCX nem seu conteúdo no Git/portal externo.

Testes necessários: cada destino temático na edição correta, edição ausente/divergente, autorização ao Registro, acesso apenas local, abertura em outra aba, retorno sem perda, manutenção dos destinos antigos. Reutilizar `testes/test_cartilha_local_form1.py` e `testes/test_ajudas_cartilha_incremento_8w.py`. Esses testes foram consultados, não reexecutados nesta etapa; nenhum vínculo foi modificado. **Esforço: 2–4 horas**, condicionado à revisão editorial e ao suporte de edições coexistentes.

### WhatsApp e pontos a reconciliar

`REGRAS_PENDENTES_GLOBAIS` ainda contém `F1-D04-DOC`, solicitando formalização de “WhatsApp corporativo”. A expressão foi localizada no texto da REV30.14 sobre o catálogo de canais. Portanto, registrar como **formalização textual localizada, reconciliação da dependência pendente**, em vez de prometer acrescentar novamente algo já presente. A seção 6.10 manteve o texto extraído da REV30.13; conferir se a redação aprovada cobre também a distinção entre canal, dispositivo, repositório e backups que motivou F1-D04-DOC antes de retirar o aviso. Nada foi retirado nesta sessão.

Há ainda uma cautela editorial para a atualização: o trecho sobre canais afirma que processos transversais têm Registro próprio, enquanto o AGENTS condiciona Registro próprio a tratamento autônomo. Não transportar essa frase para uma nova regra automática. Solicitar esclarecimento pontual dessa correspondência na revisão editorial, sem reabrir a arquitetura nem alterar a fonte nesta tarefa.

A aprovação da matriz e do marco institucional permanece pendente. Não alterar `APROVACAO-MATRIZ`, não habilitar submissão nem atribuir competências aos FORMs posteriores.

## Ordem recomendada e critérios de encerramento

1. Concluir o aceite visual da ordenação já testada e avaliar a proposta consolidada. Não ampliar a correção se a ordem estiver correta.
2. Aprovar conjuntamente a granularidade de 12.3/12.4/12.5 e 13.2, o esquema de compatibilidade e as condicionais. Resolver essas decisões antes de codificar; não converter valores legados por inferência.
3. Executar, após autorização específica, as melhorias independentes e pequenas de 13.1 e da distribuição do contador, aproveitando componentes e testes existentes.
4. Implementar a evolução versionada dos Blocos 12/13 somente com desenho aprovado, seguida de testes de compatibilidade e avaliação manual.
5. Incorporar a nova edição da Cartilha em revisão controlada e reconciliar F1-D04-DOC; manter o bloqueio institucional enquanto não houver autorização própria.

As faixas de esforço acima representam execução e verificação do recorte, não prazo garantido ou nova estimativa do produto completo. Não incluem espera por decisões. Testes compartilhados devem ser reutilizados, evitando somar duas vezes a mesma regressão.

Na sessão de diagnóstico foram alterados somente este documento e o link no README. Não houve testes integrais, migrações, alterações no banco demonstrativo, novos testes ou correções funcionais. As evidências anteriores foram preservadas. Naquela sessão, nenhum commit ou push foi realizado. As propostas aguardam avaliação e autorização específica.

## Estabilização e versionamento local — 05/11/2026

Por autorização específica posterior ao diagnóstico, foram revisadas as cinco alterações locais esperadas, sem encontrar arquivos estranhos ao escopo ou indícios de credenciais/dados pessoais reais nas adições. Os trechos independentes do README foram separados no índice, sem reescrever seu conteúdo ou descartar alterações.

- **AJ-006 e reforço de teste AJ-013:** commit `cea01e2de7195d1f6e9a3e1d8e8e3bf6b7cb0c05`, `fix(form1): ordenar pendencias pela sequencia canonica`. Inclui pré-validação, os dois arquivos de testes de ordenação/usabilidade e o parágrafo correspondente no README. Situação: testada e commitada localmente; aceitação visual ainda pendente.
- **AJ-007:** commit `e52c4afdd60365d446a06541486801f43be31ab6`, `docs(lgpd): formalizar distincao entre APA e SAA`. Inclui somente a definição e seus limites no README. Não cria perfil ou permissão.
- **Planejamento:** este backlog e seu link no README constituem o commit documental separado `docs(poc): consolidar backlog de ajustes da ampliacao`. As propostas dos Blocos 12/13 e do painel permanecem não implementadas.

### Verificação executada

Regressão proporcional: **109 testes aprovados, zero falhas**, em 67,79 segundos. Um aviso preexistente: depreciação de `anyio.abc.BlockingPortal` em `starlette.testclient`; não impediu a execução. Não foi executada a suíte integral.

Comando PowerShell executado na raiz do repositório, com o ambiente `lgpd-poc` ativado:

```powershell
$env:LGPD_BANCO_TESTE='lgpd_poc_teste'
python -m pytest -q -o addopts= -p no:cacheprovider testes/test_ordenacao_pendencias_form1.py testes/test_pre_validacao_form1_integral.py testes/test_complementos_outro_form1_integral.py testes/test_destinatarios_10_2_1_form1_integral.py testes/test_usabilidade_blocos_9_10.py testes/test_jornada_destinatarios_form1.py testes/test_painel_progresso_incremento_8k.py testes/test_tres_contadores_painel.py testes/test_politica_p0_incremento_8v.py testes/test_leitura_preenchimento_form1.py testes/test_p1_usabilidade_form1.py testes/test_bloco10_form1_integral.py testes/test_continuidade_navegacao_incremento_8m.py testes/test_etapa1_form1_integral.py testes/test_snapshot_form1_integral.py
```

A rodada abrange ordem canônica, condicionais, participantes/destinatários repetíveis, rascunhos, navegação, pré-validação, snapshots e bloqueio da submissão institucional. As rotinas da suíte preparam somente o banco isolado `lgpd_poc_teste`; o banco demonstrativo e suas respostas não foram alterados. Não houve alteração funcional posterior aos testes. A verificação `git diff --check` passou e os 13 IDs do backlog e o link do README foram conferidos.

Nenhum push foi autorizado ou realizado nesta estabilização. A inspeção visual continua **NÃO VERIFICADA**, com o roteiro da seção D preservado. Não houve funcionalidades adicionais, mudanças de contratos, matriz, permissões, Cartilha, apresentação ou FORMs 2–4.

## INSTRUÇÃO_FORMS01_01 — Etapa A / AJ-003 — 05/11/2026

A pergunta 13.1 agora reutiliza **Entenda esta pergunta** para diferenciar “Nenhuma das situações acima”, “Não se aplica” e “A confirmar”, com explicação da exclusividade já vigente. A orientação funcional não inventa seção, edição ou link da Cartilha; as 22 referências editoriais existentes permanecem inalteradas. Os controles estão associados à ajuda por `aria-describedby`. Não houve alteração de catálogo, matriz, respostas ou regras de escrita.

Verificação: **51 testes aprovados, zero falhas**, em 28,11 segundos, no banco isolado `lgpd_poc_teste`. Inclui as três alternativas isoladas, cada especial com exposição concreta, pares de especiais recusados sem perda da resposta anterior, apresentação da ajuda, acessibilidade estrutural, vínculos da Cartilha, pré-validação e preservação do bloqueio institucional. A primeira tentativa foi impedida na preparação pela restrição de conexão local (erro Windows 10013); a repetição com acesso autorizado ao banco de teste foi aprovada. Um aviso preexistente de depreciação de `anyio.abc.BlockingPortal` permanece.

Comando: `python -m pytest -q --tb=short -o addopts= -p no:cacheprovider testes/test_bloco13_form1_integral.py testes/test_ajudas_cartilha_incremento_8w.py testes/test_cartilha_local_form1.py testes/test_politica_p0_incremento_8v.py testes/test_leitura_preenchimento_form1.py testes/test_pre_validacao_form1_integral.py testes/test_p1_usabilidade_form1.py`, com `LGPD_BANCO_TESTE=lgpd_poc_teste`.

**ACEITAÇÃO VISUAL NÃO VERIFICADA.** Conferência manual pendente: acessar 13.1 como ARP, abrir a ajuda por teclado em tela larga e estreita, conferir legibilidade e compreensão das três distinções. A aprovação automatizada não substitui essa avaliação. Etapa B ainda não iniciada neste checkpoint; sem push.

## INSTRUÇÃO_FORMS01_01 — Etapa B / AJ-005 — 05/11/2026

Iniciada após aprovação dos 51 testes e commit local `c9af327` da Etapa A. O painel oferece **Detalhar campos obrigatórios pendentes por Registro**, em seção expansível próxima ao indicador e associada a ele por `aria-describedby`. Reutiliza `registro.preenchimento_arp`, com código, denominação, quantidade e acesso ao rascunho. Inclui zero pendências e a contagem inicial de rascunhos ainda não iniciados, sempre no conjunto autorizado que já compõe o total. Para estes últimos, o destino é o cartão existente e sua ação de início, sem criar rascunho por consulta. Mantidos os cartões individuais e a separação das providências de conferência.

Não houve mudança em consultas, cálculo, autorizações ou persistência. A expansão usa `details/summary` nativos, sem JavaScript novo, com foco visível, quebra de textos e disposição flexível. O acesso ao rascunho reutiliza a âncora existente; não cria regra nova de retomada.

Verificação: **79 testes aprovados, zero falhas**, em 55,42 segundos, exclusivamente em `lgpd_poc_teste`. Inclui sete novos cenários de distribuição (perfis parametrizados), um/vários Registros, soma das contagens exibidas, ausência de acesso, APA com outro ARP, zero, não iniciado, conferência pendente e confirmada, destino HTTP e preservação do rascunho. A regressão também reexecutou os testes do Bloco 13, Cartilha, pré-validação, consulta/edição, painel e interface nuclear. Um aviso preexistente de depreciação de `anyio.abc.BlockingPortal`; sem falha funcional. Não foi executada a suíte integral.

Comando: `python -m pytest -q --tb=short -o addopts= -p no:cacheprovider testes/test_distribuicao_pendencias_painel.py testes/test_tres_contadores_painel.py testes/test_painel_arp_incremento_8n.py testes/test_painel_lado_a_lado_incremento_8o.py testes/test_interface.py testes/test_leitura_preenchimento_form1.py testes/test_pre_validacao_form1_integral.py testes/test_bloco13_form1_integral.py testes/test_cartilha_local_form1.py`, com `LGPD_BANCO_TESTE=lgpd_poc_teste`.

**ACEITAÇÃO VISUAL NÃO VERIFICADA.** Testes de HTML/CSS e semântica não certificam a renderização real. Roteiro manual: como ARP, expandir por teclado em telas larga e estreita, comparar a soma com o indicador e acessar cada rascunho; conferir o cartão de início quando ainda não houver rascunho; como APA de outro ARP, confirmar ausência dessas contagens e preservação das ações permitidas. Nenhuma migração, alteração de contratos/matriz, banco demonstrativo, Cartilha, apresentação, FORMs 2–4 ou liberação da submissão. Sem push; demais ocorrências preservadas.

## INSTRUÇÃO_FORMS01_02 — Diagnóstico de compatibilidade / AJ-004 — 05/11/2026

Base: `main`, `687dd3adbd901be644d143a8a4a1fc50e64c8d7c`, árvore inicialmente limpa e cinco commits à frente da referência local de `origin/main`. A decisão funcional agora especifica duas perguntas independentes, 13.2 (documentos físicos) e 13.2.1 (bloqueio das estações), ambas facultativas. Ela sucede a proposta inicial de duas dimensões sob um só ID, preservada acima como histórico.

**Impedimento da alteração direta:** `app/form1_integral.py` fixa catálogo REV13/hash e 128 IDs, sem 13.2.1. `carregar_matriz_obrigatoriedade()` exige os mesmos 128 IDs. `_validar_respostas_catalogadas()` recusa 13.2.1; `_conteudo_com_respostas_do_bloco()` substitui a resposta corrente de 13.2, sem arquivamento específico da resposta agregada. A consulta de conferência em `app/main.py` monta os enunciados pelo catálogo corrente, portanto substituir o enunciado de 13.2 reinterpretaria visualmente snapshots antigos. O número de salvamento não identifica, sozinho, a versão semântica da pergunta. A estrutura JSON comporta extensão, mas ainda não há discriminador dessa evolução nem leitor por versão para este campo.

**Proposta para autorização:** preservar catálogo/matriz REV13 base e introduzir extensão identificada e versionada do contrato candidato 3, com mapa efetivo de 129 IDs, sem chamar o novo campo de original da REV13. Usar marcador explícito de versão da estrutura do Bloco 13, comum ao rascunho, snapshot e consulta. Ausência do marcador significa pergunta agregada legada. Manter 13.2 e 13.2.1 facultativas, independentes e ordenadas; “A confirmar” produz aviso não bloqueante e “Não se aplica” vale apenas para a medida respondida. Não fazer migração em lote nem alterar o banco demonstrativo nesta etapa.

Para rascunho legado, exibir a pergunta/resposta agregada em consulta, com versão de origem, e oferecer revisão explícita pelo ARP autorizado. Na adoção do novo formato, preservar atomicamente o retrato anterior completo (valor, enunciado/versão, autoria e data do salvamento, versão/lacre e vínculo ao Registro), sem alterar snapshots existentes. As duas respostas novas começam vazias e somente recebem valores escolhidos pelo ARP; confirmar adoção e salvar devem compartilhar transação, idempotência e controle de concorrência. A autoria do último salvamento não deve ser apresentada como autoria específica do campo sem evidência. Histórico antigo mantém enunciado antigo. Alternativa mais ampla, não recomendada para este recorte: novo número de contrato integral, que também exigiria revisar a restrição atual `versao_contrato = 3` das versões técnicas e planejar migração própria.

**Verificações executadas:** quatro verificações diagnósticas aprovadas em memória, sem conexão ao banco: catálogo com 128 IDs; rejeição do catálogo com 129 IDs e do envio 13.2.1 pelo validador atual; classificação facultativa de 13.2; substituição simples sem arquivo do valor agregado, preservando os demais campos. Não são os testes de aceite da funcionalidade futura. Não foi executada regressão, porque nenhum código foi modificado.

Aplicada a condição expressa da instrução, seção 3: não executar mudança incompatível automaticamente. Somente esta ocorrência/documentação foi atualizada. Código, contratos, matriz, bancos, migrações, permissões, Cartilha e apresentação permanecem intactos. Nenhum commit ou push nesta etapa; aceitação visual não se aplica à proposta ainda não implementada. Submissão institucional permanece bloqueada. Aguardar autorização da extensão versionada antes de implementar; não iniciar INSTRUÇÃO_FORMS01_03.

## INSTRUÇÃO_FORMS01_03 — Implementação da AJ-004 — 05/11/2026

A autorização específica sucede o impedimento da alteração direta registrado na INSTRUÇÃO_FORMS01_02, sem apagar aquele diagnóstico. Implementada a extensão [F1-C3-REV13-EXT-MEDIDAS-v1](../arquitetura/EXTENSAO_FORM1_REV13_MEDIDAS_V1.md), com fonte declarativa própria de catálogo/matriz e 129 IDs efetivos. A base REV13 permanece com 128 IDs; os outros 127 não mudam. A adoção pelo ARP preserva snapshot anterior, enunciado e resposta agregada; inicia 13.2 e 13.2.1 vazias. As duas respostas são facultativas e independentes.

Proteções: adoção explícita, autorização vigente, idempotência, concorrência, rollback, verificação da estrutura exibida no salvamento e recuperação local compatível com a versão. Consulta histórica usa a estrutura do snapshot, sem reinterpretá-lo pelo rascunho atual. JSON existente suficiente; nenhuma migração ou alteração do banco demonstrativo. Submissão institucional bloqueada.

Verificação: **32 testes focalizados aprovados** em 28,57 s e **624/624 testes aprovados na regressão integral** em 375,55 s. Zero falhas finais; um aviso preexistente de depreciação de `anyio.abc.BlockingPortal`. A primeira rodada focal apontou um valor incorreto no novo teste de navegação (`avancar`, em vez do comando existente `proximo`); corrigido no teste, sem alterar o comportamento da navegação. Testes somente no banco `lgpd_poc_teste`.

Comandos: `python -m pytest testes/test_extensao_medidas_form1.py testes/test_bloco13_form1_integral.py -q --tb=short -o addopts= -p no:cacheprovider`; depois `python -m pytest testes -q --tb=short -o addopts= -p no:cacheprovider`, ambos com `LGPD_BANCO_TESTE=lgpd_poc_teste`. A execução JavaScript em Node integra os testes focais. Referências locais da especificação válidas; as 13 ocorrências do backlog e o diagnóstico anterior foram preservados.

Aceitação visual **NÃO VERIFICADA**; roteiro de telas larga/estreita e teclado na especificação vinculada. A revisão do Bloco 12 e as outras ocorrências continuam fora deste incremento.

## INSTRUÇÃO_FORMS01_04 — AJ-001 e AJ-002 — 05/11/2026

Autorização expressa da revisão estrutural. Fase A documentou a compatibilidade do JSON e a composição independente com a extensão MEDIDAS; não foram necessárias tabelas, migrações ou alterações de contratos externos. Fase B implementou [F1-C3-REV13-EXT-GUARDA-v1](../arquitetura/EXTENSAO_FORM1_REV13_GUARDA_V1.md), preservando a REV13 de 128 IDs e MEDIDAS de 129. GUARDA isolada tem 139 IDs; a composição, 140. O catálogo/matriz declarativo é único e versionado.

Adoção explícita pelo ARP guarda snapshot completo e enunciados/respostas de 12.3, 12.4, 12.4.1, 12.5 e 12.5.1, inclusive valores condicionais inativos. Nenhum valor agregado é convertido. Procedimentos e evidências são independentes por operação; locais ficam condicionados à evidência daquela operação. Transferência admite modalidades coexistentes, complemento de Outra situação e destino/referência. “A confirmar” nas perguntas facultativas gera aviso não bloqueante; “Não se aplica” não ativa localização. Ausência de eliminação não é classificada como irregularidade. Rascunhos incompletos continuam permitidos.

Mantidos 12.1–12.2, FORMs 2–4, nuclear 2, permissões, snapshots, Cartilha, apresentação e banco demonstrativo. Submissão institucional bloqueada. Aceitação visual **NÃO VERIFICADA**; roteiro e arquivos na especificação. Verificação: **652/652 testes aprovados** em 599,18 s, incluindo 28 novos testes da extensão; um aviso preexistente de descontinuação Starlette/AnyIO. Sem push.

Comandos: `python -m pytest testes/test_extensao_medidas_form1.py testes/test_bloco12_form1_integral.py testes/test_pre_validacao_form1_integral.py -q --tb=short -o addopts= -p no:cacheprovider` (38 aprovados); `python -m pytest testes/test_extensao_guarda_form1.py -q --tb=short -o addopts= -p no:cacheprovider` (27 aprovados antes da inclusão do teste JavaScript); `node testes/apoio_extensao_guarda_form1.cjs` (aprovado); `python -m pytest testes -q --tb=short -o addopts= -p no:cacheprovider` (652 aprovados, incluindo o teste JavaScript). Todas as execuções Python usaram `LGPD_BANCO_TESTE=lgpd_poc_teste`.

## INSTRUÇÃO_FORMS01_05 — Verificação consolidada — 05/11/2026

### Base, isolamento e alcance

Base conferida: `9970803e7cd0cdfc8eb9cadaaed04b56e7877c88`, branch `main`, árvore limpa, sete commits à frente da **referência local** de `origin/main` (sem consulta remota). Esta rodada não modifica aplicação, testes, contratos, matrizes, migrações, documentos técnicos das extensões ou dados demonstrativos. As 13 ocorrências deste backlog e os resultados anteriores permanecem preservados.

Regressão integral concluída: **652/652 testes aprovados**, zero falhas e zero testes ignorados, em **372,66 s (6 min 12 s)**. Um aviso preexistente de descontinuação de `anyio.abc.BlockingPortal`, emitido pelo Starlette TestClient. Executada com `LGPD_BANCO_TESTE=lgpd_poc_teste` e `python -m pytest testes -q --tb=short -o addopts= -p no:cacheprovider`. O `conftest.py` recusa nomes sem sufixo `_teste`, recria o esquema exclusivamente nessa base e utiliza carga fictícia. O Registro demonstrativo `LGPD-2026-00004` não foi acessado nem modificado nesta rodada. A fronteira HTTP é exercitada pelo TestClient, sem representar inspeção visual de navegador.

### Matriz de evidências técnicas

Os cenários automatizados abaixo foram **aprovados nesta regressão**. Isso confirma os comportamentos técnicos exercitados, sem certificar a renderização real ou substituir o aceite funcional humano. Não foi necessário alterar nem acrescentar testes; a suíte existente cobre os cenários técnicos solicitados.

| Item | Verificação técnica e evidência reproduzível | Limite de aceitação |
|---|---|---|
| AJ-003 / ajuda 13.1 | `test_bloco13_form1_integral.py`: três explicações distintas, ajuda associada por `aria-describedby`, opções especiais isoladas aceitas e combinações com situações concretas ou entre especiais recusadas sem perder resposta anterior. Orientação em `AJUDAS_ALTERNATIVAS_FORM1`, sem link editorial inventado. | Compreensão pelo servidor, legibilidade e abertura por teclado em navegador NÃO VERIFICADAS. |
| AJ-005 / distribuição de pendências | `test_distribuicao_pendencias_painel.py`: soma igual ao contador, código/objeto identificados, vários Registros, zero, rascunho não iniciado, acesso ao rascunho correto, APA de outro ARP, perfil sem acesso e separação de conferência versus campos faltantes. | Expansão, foco real e disposição larga/estreita NÃO VERIFICADOS. O caso de zero isola a apresentação com substituição controlada do resultado da pré-validação; não prova existência de formulário completo. |
| AJ-004 / MEDIDAS | `test_extensao_medidas_form1.py`: adoção explícita autorizada, respostas vazias, independência de 13.2/13.2.1, facultatividade, persistência, versão histórica/enunciado/lacre preservados, recusa de aba antiga, idempotência, concorrência e rollback. | Usabilidade real da adoção e consulta histórica NÃO VERIFICADA nesta rodada. |
| AJ-001 / GUARDA: procedimentos e evidências | `test_extensao_guarda_form1.py`: quatro operações independentes, localização somente com evidência Sim/Em alguns casos, Não se aplica não ativa localização, A confirmar facultativo gera aviso não bloqueante, persistência e arquivamento de respostas fora de aplicação. Ausência de eliminação não vira irregularidade. | Leitura da matriz compacta, campos condicionais e teclado no navegador NÃO VERIFICADOS. |
| AJ-002 / GUARDA: transferência | Mesmo arquivo: modalidades múltiplas, Outra situação com complemento, destino, limites, opções forjadas/duplicadas recusadas, respostas inativas preservadas e nova semântica somente após adoção. | Apresentação responsiva e interação real NÃO VERIFICADAS. |
| Compatibilidade das quatro versões | Teste `test_quatro_perfis_preservam_128_129_e_acrescentam_somente_bloco12`, adoção em ambas as ordens, leitura de snapshots anteriores, preservação de campos não afetados e salvamento dos Blocos 11, 13 e 14 após composição. | A composição não autoriza conversão em lote nem altera a interpretação de snapshots antigos. |
| Integração e segurança | `test_ensaio_form1_integral.py`, testes de navegação, ordenação, pré-validação, leitura/preenchimento e demais testes da suíte: percurso técnico dos 14 blocos, autorizações, ocorrências, rascunhos, auditoria, concorrência, rollback e fluxo nuclear. | Navegação HTTP/DOM simulado não comprova posicionamento visual ou experiência ponta a ponta em navegador. |
| Submissão institucional | Testes das extensões e ensaio verificam `submissao_habilitada=False`; snapshots técnicos e conferência interna permanecem atos distintos da submissão. | Nenhuma aprovação institucional ou liberação de submissão decorre desta rodada. |

| Perfil efetivo | Identificadores | Compatibilidade verificada pelos testes |
|---|---:|---|
| `F1-C3-REV13` | 128 | Catálogo e matriz originais preservados. |
| `F1-C3-REV13-EXT-MEDIDAS-v1` | 129 | Separação do item 13.2 sem adoção automática de GUARDA. |
| `F1-C3-REV13-EXT-GUARDA-v1` | 139 | Revisão do Bloco 12 sem adoção automática de MEDIDAS. |
| `F1-C3-REV13-EXT-MEDIDAS-GUARDA-v1` | 140 | Composição independente, nas duas ordens de adoção. |

### Acessibilidade e limitação da inspeção visual

**ACEITAÇÃO VISUAL NÃO VERIFICADA.** A tentativa de criar uma aba `about:blank` pelo navegador integrado e a tentativa de inicializar o controle Windows (`@oai/sky`) falharam antes de acessar a aplicação, ambas com: `failed to write kernel assets: O sistema não pode encontrar o caminho especificado. (os error 3)`. É uma falha de inicialização das ferramentas; não há evidência de bloqueio da URL da aplicação nem de defeito visual provocado por ela. Nenhuma proteção foi contornada. Não foi iniciado servidor visual adicional, pois as duas ferramentas de inspeção ficaram indisponíveis.

Verificação de acessibilidade **parcial, técnica**: associação de rótulos/ajudas, IDs, `details/summary` nativos, `fieldset/legend`, estilos de foco e empilhamento abaixo de 800 px estão cobertos por testes ou conferência do código. O JavaScript de adoção/condicionais é exercitado em DOM simulado. Não houve teste real com teclado, leitor de tela, zoom ou larguras distintas; não se declara conformidade WCAG integral.

Cálculo de contraste dos pares de cores do código, sem captura de tela: azul `#075985` sobre branco **7,56:1**; azul escuro `#0C3B5A` sobre branco **11,74:1**; texto `#17212B` sobre branco **16,29:1** e sobre `#F4F7F9` **15,14:1**. Esses pares superam 4,5:1 para texto normal; o cálculo não verifica todas as sobreposições e estados renderizados.

### Roteiro de aceitação manual pendente

Executar somente em base de teste com dados fictícios, após terminar a suíte; não usar o Registro demonstrativo 00004. Registrar resultado, largura, perfil, versão e captura de cada cenário.

1. **Painel e 13.1 — tela larga (por exemplo, 1366 px) e estreita (390 px):** como ARP, expandir a distribuição por Tab/Enter ou Espaço; conferir soma, identificação e destino de cada Registro. Abrir Entenda esta pergunta e conferir as três explicações. Selecionar alternativas concretas e especiais, verificando exclusividade e foco. Como APA de outro ARP e perfil não autorizado, conferir ações e dados efetivamente permitidos.
2. **MEDIDAS:** preparar resposta agregada fictícia e uma apresentação anterior; adotar expressamente como ARP. Conferir novos campos vazios, legado com enunciado original e duas respostas diferentes. Salvar, recarregar e consultar o snapshot anterior pelo APA autorizado.
3. **GUARDA:** adotar em outro Registro fictício; conferir quatro operações. Usar procedimento Não e evidência Sim na mesma operação e preencher sua localização. Alterar evidência para Não se aplica/A confirmar; conferir que outras operações não mudam. Marcar duas modalidades e Outra situação, informar complemento/destino, salvar e recarregar; confirmar o legado consultável.
4. **Composição e navegação:** repetir adoções nas duas ordens, mantendo respostas já salvas na outra extensão; percorrer os 14 blocos, especialmente 11 → 12 → 13 → 14, retornar, consultar pendências e acessar as perguntas. Conferir aviso de edições locais antes de adotar e ausência de perda de respostas.
5. **Teclado, leitura e histórico:** em ambas as larguras, conferir rótulos, foco visível, ordem de tabulação, ausência de cortes e uso dos controles sem mouse. Consultar versões anteriores e atuais, verificar autoria e enunciados, e confirmar que nenhuma ação libera submissão institucional.

### Resultado e pendências

**Verificação técnica automatizada aprovada, sem regressões identificadas nesta rodada. Homologação consolidada parcial:** a homologação visual e o aceite funcional humano permanecem pendentes, sem aprovação presumida. AJ-001, AJ-002, AJ-003, AJ-004 e AJ-005 mantêm implementação tecnicamente verificada; não são encerradas como visualmente aceitas. Não foram identificados novos defeitos funcionais P0/P1 nos cenários executados, e nenhum item foi reprovado automaticamente. Limitação P1 desta rodada: falta de evidência visual/teclado real, a resolver pela execução do roteiro ou restabelecimento autorizado das ferramentas; não é um defeito da aplicação comprovado. Não há autorização para implementar correções nesta verificação. Nenhum push realizado.
