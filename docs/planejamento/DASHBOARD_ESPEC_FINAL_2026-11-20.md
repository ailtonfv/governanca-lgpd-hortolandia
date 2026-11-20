Dashboard LGPD — Especificação final para implementação (20/11/2026)
Substitui, para fins de implementação, as partes 1, 2 e 3 de 19/11 (arquivadas em `docs/planejamento/`). Incorpora as 16 respostas do agente (commit 873a7fd) e as decisões de Ailton de 19 e 20/11. Onde houver conflito, vale este texto.
Objetivo deste documento: permitir a implementação sem explorar o repositório além dos arquivos citados e sem decidir regras por conta própria. Se algo aqui não fechar com o código, parar e perguntar; não improvisar.
---
0. Como implementar (economia de esforço)
Branch `lote-13-dashboard`, criada depois do merge do Lote 12 (ou a partir da branch do Lote 12, se Ailton autorizar). Sem push de main, sem merge sem autorização.
Arquivos a ler (e só estes, salvo necessidade comprovada):
`app/modelos.py` (tabelas `registro`, `unidade`, `participacao_form2`, `identidade_forms34`, `evento`, `aviso_dpo`);
`app/fluxo_forms34.py` (reconstrução do estado dos FORMs 3/4 a partir dos eventos);
`app/permissoes_forms34.py` (escopo por perfil);
`app/fila_form2.py`, `app/consolidacao_form2.py` (estados do FORM 2, inclusive o novo ato "Concluir a análise" do 12-F);
`app/unidades_interface_form2.py` (`secretarias_ativas()`);
tokens em `docs/design-system`.
Não usar `app/projecoes_forms34.py` como cálculo pronto (resposta 1a/3a do agente).
Estrutura:
um módulo de consultas puro, `app/dashboard/consultas.py`: uma função por indicador; recebe o escopo do perfil e os filtros; devolve números e a lista que os compõe;
rotas `GET /dashboard` (Abertura) e `GET /dashboard/<tela>`; templates no padrão do sistema;
somente leitura: nenhuma rota do dashboard grava nada.
Testes: um teste por indicador, com cenário pequeno montado em base `_teste`; mais os testes de segregação por perfil (seção 2) e o teste "número = tamanho da lista".
Ordem de implementação (se o tempo acabar, para na ordem):
Abertura (seção 4);
Risco (seção 6);
Correção (seção 7);
Operação (seção 8);
Cobertura (seção 9);
Aprendizados (seção 10);
Circulação (seção 11).
Regra de corte em 1º/12: o que não estiver pronto mostra "Não disponível" no quadro da Abertura e fica representado no protótipo de Claude na demonstração.
---
1. Regras gerais (valem para todas as telas)
Só leitura. O dashboard consulta; os atos acontecem nos FORMs.
Todo número abre a lista que o compõe. O tamanho da lista confere com o número (testar).
Ausência ≠ zero.
Sem fonte: "Não disponível".
Sem avaliação: "Ainda não avaliado".
Zero só quando a contagem foi feita e deu zero.
Percentual só com denominador aprovado (hoje, nenhum).
Só conta o que vale.
Nota de risco conta apenas com nota conjunta confirmada (Secretaria + DPO).
Proposta e "sem consenso" ficam em contagens separadas, com esse nome.
Ação só é "concluída" depois da verificação.
Reavaliação pendente não retira a nota vigente (resposta 3a).
Selo "Em deliberação" em indicadores que dependem de regra não homologada: "Proposta em deliberação. Não equivale a homologação."
Linguagem: português claro; códigos só entre parênteses. Nomenclatura do 12-F: "Risco 1: <título> (R01)", "Ação 1: <título> (A01)".
Nenhum nome de pessoa em nenhuma tela. Aparece o papel (AAL, DPO, Jurídico, Comitê, Secretário, Gabinete).
Modo de projeção:
só contagens, faixas, Secretarias e identificadores;
nenhum texto de manifestação;
nenhuma referência de evidência;
nenhum texto livre, exceto o conteúdo de aprendizado autorizado para consulta (seção 10).
Datas: formato brasileiro (dd/mm/aaaa, hh:mm). Contagem de espera em dias corridos. Rodapé: "Situação em dd/mm/aaaa às hh:mm · dados fictícios de demonstração".
"Sobre este número" (ícone i) em cada quadro: de onde vem, regra de cálculo, quem responde (Secretaria, DPO, Comitê, Gabinete), quando foi atualizado.
Botão "Gráfico / Tabela" em toda tela de detalhe.
Referência visual: Painel LAI (CGU). Poucas cores, números grandes no topo, comparação entre Secretarias em ordem alfabética (ordenação opcional pelo usuário), sem ranking de "pior Secretaria".
1.1 Cores
Uso	Cor	Texto sobre a cor
Pequeno (1–3)	`#2e9e44`	branco
Moderado (4–6)	`#e2a90f`	`#2b1d00`
Alto (8–12)	`#e3651d`	branco
Crítico (15–25)	`#b3261e`	branco
Base, títulos	`#0c3b5a`	branco
Etapas (FORMs 1→4)	tons do azul-escuro, claro → escuro	conforme o tom
As quatro cores de risco só significam faixa de risco.
Toda faixa leva o nome escrito.
"Atrasada" não usa vermelho: borda grossa escura, ícone de relógio e a palavra.
1.2 Unidade de contagem e agregação
Unidade principal: o Registro LGPD, com a divisão por tipo de objeto (serviço · processo · atividade) no "Sobre este número". Tipos nunca se somam sem mostrar a divisão. Hierarquia não gera contagem em cascata.
Detalhe pode contar riscos (Rnn), ações (Ann) ou participações, sempre com o rótulo explícito ("riscos", "ações", "participações"), nunca como "Registros".
Registro com vários riscos — faixa: o Registro aparece na faixa do pior risco vigente (nota conjunta confirmada). A lista do detalhe mostra todos os riscos. A matriz 5×5 é exceção: nela cada ponto é um risco, com o rótulo "riscos". (Recomendação aprovada como padrão; Ailton pode revisar.)
Registro com vários riscos/ações — situação: vale a precedência definida em cada tela (a situação que mais pede atenção). Segmentos de uma mesma barra são mutuamente exclusivos; atraso é marca, não segmento somável.
Soma de filas ≠ total. Um Registro pode estar em mais de uma fila; o total municipal é sempre de Registros distintos.
1.3 Filtros (faixa única no topo, igual em todas as telas)
Filtros:
Secretaria;
tipo de objeto;
período (data de criação do Registro);
etapa (FORM 1 a 4);
faixa de risco.
Faixa de risco vem antes de etapa. Ao escolher uma faixa, as etapas FORM 1 e 2 mostram "—" com a nota "não se aplica" (faixa só existe a partir do FORM 3).
O filtro ativo aparece escrito ("Mostrando: Saúde · Alto"), com "Limpar filtros".
Os filtros acompanham a navegação entre telas.
"Ver como" (troca de perfil da demonstração) fica fora da faixa de filtros.
Permissões prevalecem: para o Secretário, o filtro de Secretaria vem travado na própria.
---
2. Perfis (demonstração)
Perfil	Vê	Quadro 1 da Abertura
Gabinete (substitui o perfil Prefeito)	todas as Secretarias, só agregados e listas sem texto	"Precisa da sua atenção"
DPO	todas as Secretarias; metadados; detalhe conforme regra de finalidade	"Pendências com o Gabinete e o Comitê" (não sugere que a decisão é do DPO)
Comitê (Relator, verificador)	todas as Secretarias, agregados; as ações que lhe cabem verificar	"Pendente para o Comitê"
Secretário	só a própria Secretaria	"Aguardando sua decisão"
AAL/ARP	só os próprios Registros	"Seus itens pendentes"
A conta antiga do Prefeito não registra atos; os atos antigos permanecem válidos e aparecem como "Prefeito (registro anterior)".
Testes obrigatórios: segregação entre Secretarias, e um Secretário não vê outra Secretaria nem pela URL.
---
3. Dados para a demonstração
O agente não carrega os dez casos (estimativa de 12–20 h). Fica assim:
Origem	Casos	Quem faz
Já no sistema	LGPD-2026-00005: R01 Crítico (residual 25), aceito; A01 executada, a verificar e concluir no 12-F	Ailton, em tela
Fluxo real, novo	Caso 1 (Cultura, oficina cultural, serviço): FORM 1 confirmado e FORM 2 com "Análise concluída", sem encaminhamento	agente, pelos atos reais
Fluxo real, novo	Caso 3 (Saúde, fichas na sala de espera, processo): R01 Alto (12) → residual Moderado (4), aceito pelo Secretário; A01 executada, verificada, aprendizado registrado, conferido e autorizado	agente, pelos atos reais
Protótipo de Claude	os demais casos (2, 4, 5, 7, 8, 9, 10)	só no protótipo, sem dados no sistema
Caso 6 (incidente) sai da massa: o módulo de incidentes ficou para depois de 15/12.
Datas dos atos são as reais (sem retrodatar). "Há N dias" mostrará valores pequenos; está correto.
Os textos fictícios dos casos 1 e 3 serão entregues por Claude, prontos para colar.
---
4. Abertura — "A Prefeitura em um olhar"
4.1 Grade 3 × 3
Posição	Quadro	Leva a
1	Quadro do perfil (seção 2), moldura azul-escura	lista correspondente
2	Registros ativos	Operação
3	Registros por faixa de risco (pior risco vigente) + "ainda não valem como nota"	Risco
4–5	Esteira dos quatro FORMs (ocupa dois espaços)	Operação
6	Ações atrasadas	Correção
7	Aprendizados autorizados para consulta	Aprendizados
8	Cobertura por Secretaria (quantidade)	Cobertura
9	Circulação de dados	Circulação
Critério de vistoria (teste dos 5 segundos): alguém que não conhece o sistema responde "o que precisa de atenção?" em 5 segundos.
4.2 "Precisa da sua atenção" (Gabinete) — três linhas sempre presentes
Linha	Regra de cálculo	Lista	Marco do "há N dias"
Riscos Críticos aguardando decisão do Prefeito	residual Crítico com nota conjunta confirmada, manifestações do DPO e do Comitê registradas, sem `aceitacao`	Registro · Risco · Secretaria · residual · há N dias · "Abrir o ato no FORM 3" (bloco 16)	data da última manifestação exigida (DPO ou Comitê), nesta rodada
Segundas prorrogações mantidas contra o parecer do Comitê	estado `ciencia_prefeito` registrado	Registro · Ação · Secretaria · prazo vigente · data da ciência	data do evento `f34_ciencia_prefeito`
Avaliações sem consenso aguardando o Comitê	`avaliacao_sem_consenso` ou `triagem_sem_consenso` da rodada atual, sem deliberação correspondente	Registro · Risco · Secretaria · há N dias	data do evento de sem consenso da rodada atual
Zero aqui é dado verificado: "0 — nada pendente".
Na linha 2, o texto é "ciência registrada no sistema", nunca "mensagem entregue".
Riscos Críticos ainda sem as manifestações exigidas aparecem numa linha auxiliar, "Em instrução (DPO/Comitê)", fora da contagem principal.
Plano de ação de risco Crítico aguardando aprovação também é decisão do Prefeito registrada pelo Gabinete: incluir como 4ª linha, "Planos aguardando aprovação", se o estado `plano` sem `plano_aprovado` para origem Crítica existir; senão, omitir a linha (não mostrar zero falso).
4.3 Esteira dos quatro FORMs
Quatro colunas. Em cada uma, o número de Registros naquela etapa, dividido em segmentos exclusivos:
Coluna	Segmentos (em ordem de precedência para Registro com vários itens)	Fonte
FORM 1	aguardando complementação · em preenchimento · confirmado	conferência do FORM 1, `complemento_form2`
FORM 2	em análise · análise concluída	`participacao_form2` principal + ato "Concluir a análise" (12-F)
FORM 3	sem consenso · proposta aguardando confirmação · aguardando avaliação · nota confirmada · avaliação concluída	estado de cada identidade `R`
FORM 4	plano em elaboração · em execução · aguardando verificação · concluída e verificada · cancelada	estado de cada identidade `A`
Atraso é marca sobre FORM 4 (ícone e contagem "dos quais N atrasados"), não segmento.
Um Registro aparece na etapa mais avançada em que está ativo. Se estiver no FORM 3 e no FORM 4 ao mesmo tempo, conta nos dois, com a nota "um Registro pode estar em riscos e providências ao mesmo tempo".
Reserva técnica de identidade não prova ingresso: considerar o evento de ingresso.
Consulta nova (resposta 1b): combinar a conferência do FORM 1, a principal do FORM 2 e as identidades R/A com o evento de ingresso e o estado atual.
---
5. Esqueleto comum das telas de detalhe
Topo: título em forma de pergunta, faixa de filtros, um número-resumo.
Centro: um visual principal.
Abaixo: a tabela equivalente.
Rodapé: data de referência.
---
6. Risco — "Quais riscos existem e quanto os controles os reduzem?"
Visual: matriz 5×5 (cores do bloco 14), cada casa com quantos riscos; seletor Inerente / Residual (padrão).
Número-resumo: "N Registros com risco avaliado; N riscos com nota conjunta: Crítico X · Alto X · Moderado X · Pequeno X".
Efeito dos controles: uma linha por risco, "Registro · Risco 1 (R01) · 12 Alto → 4 Moderado". Só entram riscos com inerente e residual confirmados e mesma metodologia (`metodologia` = `DEMO-5x5-20261118` nos dois lados). Sem redução: "nenhuma redução". Texto do "Sobre": "Avaliação registrada; não mede redução causal comprovada."
"Ainda não valem como nota" (fora da matriz):
propostas aguardando confirmação;
sem consenso sem nota vigente;
ingressados e ainda não avaliados ("Ainda não avaliado").
Reavaliação em curso aparece como marca na linha do risco, não tira o risco da matriz.
Decisão sobre o residual, por faixa:
Faixa	Quem decide	Mostra
Pequeno, Moderado	Secretário	decididos · aguardando
Alto	Secretário, com manifestação prévia do DPO e ciência do Comitê	decididos · aguardando manifestação · aguardando decisão
Crítico	Prefeito, registrado pelo Gabinete com documento formal	decididos · em instrução · aguardando decisão (há N dias)
Fontes: `aceitacao`, `manifestacao_dpo`, `manifestacao_comite`, `ciencia_comite`. A decisão nunca é inferida da nota nem da aprovação do plano.
Triagem de RIPD: "Riscos com triagem indicando RIPD: N · referência do RIPD informada: N · não informada: N". Selo "Em deliberação". Não existe o estado "RIPD em elaboração": não mostrar.
Tabela: Registro · Risco · Secretaria · tipo de objeto · inerente (P×I, faixa) · residual (P×I, faixa) · situação da nota · decisão · referência do RIPD (informada / não informada).
7. Correção — "As providências estão sendo cumpridas?"
Visual: linha do tempo, uma faixa por ação, com linha vertical "hoje". Marcas:
início = plano aprovado;
prazo original;
cada prorrogação aprovada ("1ª", "2ª");
prazo vigente;
fim (verificada, cancelada).
Prazo original = prazo do estado no evento da primeira aprovação do plano (não a primeira data de rascunho). Prorrogações reconstruídas pela sequência de eventos (pedidos, manifestações, decisões). Sem campo novo (resposta 3c).
Número-resumo (situações exclusivas): "N ações: plano em elaboração X · em execução X · aguardando verificação X · concluídas e verificadas X · canceladas X — das quais atrasadas X".
Regras:
Concluída e verificada: `verificada` com verificação aprovada. "Executada" aparece como "Aguardando verificação".
Atrasada (marca): prazo vigente < hoje, sem `verificada` e sem `cancelada`. Pedido de prorrogação não aprovado não muda o prazo vigente.
2ª prorrogação: mostra o parecer do Comitê; se contrário e mantido, marca "ciência ao Gabinete registrada".
Cancelada: mostra "cancelada com decisão do Secretário". Motivo não aparece na projeção (texto livre).
Aprovação do plano: Secretário; para origem Crítica, Prefeito registrado pelo Gabinete.
Incidentes: fora desta versão. Quadro com "Não disponível — o registro estruturado de incidentes será implementado após 15/12". Nenhum prazo legal calculado.
Tabela: Registro · Ação · Secretaria · origem (Risco n ou FORM 2) · prazo original · prorrogações · prazo vigente · situação · verificada por (papel: "Comitê").
8. Operação — "Onde os Registros estão esperando?"
Visual: barras horizontais, uma por fila (papel): AAL · Jurídico · DPO · Secretário · Comitê · Gabinete.
Cada barra conta Registros distintos naquela fila; participações aparecem no detalhe, rotuladas. Ao lado: "espera mediana N dias · maior espera N dias".
Número-resumo: "N Registros aguardando alguém · N participações abertas".
Nota fixa: "Um Registro pode estar em mais de uma fila; a soma das barras não é o total."
De onde vem cada fila:
Fila	Fonte	Entra em	Sai em
AAL (análise principal)	`participacao_form2` tipo principal	`entrada_em`	"Concluir a análise"
Jurídico, temáticas	`participacao_form2`	`entrada_em`	`concluida_em`
DPO (FORM 2)	`participacao_form2` tipo DPO (ciência em `aviso_dpo` não encerra)	`entrada_em`	`concluida_em`
DPO (FORMs 3/4)	eventos: proposta aguardando confirmação do DPO; manifestação solicitada	evento que abre	evento de confirmação/manifestação
Secretário	eventos: decisão do residual (até Alto), aprovação de plano (não Crítico), prorrogação, cancelamento	evento que deixa a decisão pronta	evento de decisão
Comitê	eventos: sem consenso, ciência/deliberação pendente, verificação pendente	evento que abre	deliberação / verificação
Gabinete	linhas da seção 4.2	marcos da 4.2	decisão registrada
Não inventar "assunção" para Comitê e Gabinete: a espera conta do evento que abre até o evento que fecha, pareando cada rodada.
Sem cor de atraso. Espera não é atraso.
"Prazos em curso" (quadro abaixo): só ações do FORM 4 com prazo vigente (dias restantes ou "Atrasada"). Incidentes: "Não disponível".
Tabela: fila · Registro · Secretaria · etapa · aberta desde · dias de espera · prazo (se houver).
Nunca listar pessoas: o detalhe da fila lista Registros.
9. Cobertura — "Quais Secretarias já mapearam seus serviços, processos e atividades?"
Visual: barras horizontais, uma por Secretaria de `secretarias_ativas()` (todas, inclusive as sem Registro). Barras comparativas, não empilhadas, para não contar duas vezes o mesmo Registro:
"Registros com levantamento confirmado (FORM 1)";
"Registros com análise concluída (FORM 2)".
Número-resumo: "N Secretarias com pelo menos um Registro, de M ativas". M vem da consulta, não da constante 18. A lotação do DPO e outras unidades não-Secretaria ficam fora.
Regras:
Secretaria sem Registro: "0 Registros" (zero real).
Sem percentual: "Mostramos quantidades. O percentual depende de um inventário de referência ainda não aprovado."
Registro conta na Secretaria responsável (`unidade_principal_atual_id`). Participação em Registro de outra Secretaria aparece em texto.
Com filtro de uma Secretaria: lista dos Registros dela, com tipo e etapa.
Tabela: Secretaria · serviços · processos · atividades · com levantamento confirmado · com análise concluída · participa em Registros de outras.
10. Aprendizados — "O que a Prefeitura mudou por causa disso?"
Visual: um cartão grande, com setas anterior/próximo.
Conteúdo do cartão = os três campos do 12-F:
Contexto (relato impessoal);
Diretriz de procedimento;
Aplicação e limites.
Rodapé:
"Autorizado para consulta em dd/mm/aaaa — Secretaria de …";
"Ação verificada pelo Comitê em dd/mm/aaaa";
Registro e Ação de origem (identificadores).
Só aparece aprendizado com verificação aprovada, conferência do DPO e autorização da Secretaria, na última versão autorizada.
Não mostrar "desde quando vale" (não há campo; não usar a data de publicação no lugar), "ligado a N Registros" (não há vínculo múltiplo; cada aprendizado pertence a uma ação) nem referência de evidência.
Registros antigos sem contexto: "Contexto não informado".
Número-resumo: "N aprendizados autorizados para consulta".
Tabela: aprendizado (diretriz resumida) · Secretaria · autorizado em · Registro · Ação.
11. Circulação — "Para onde os dados pessoais vão?" (versão simplificada)
A versão completa (relações deduplicadas, instrumentos e cláusulas) não é calculável com a estrutura atual (resposta 2a): falta identidade de fluxo, instrumento normalizado e classificação de cláusula. Não inferir lendo texto livre.
Versão para 15/12:
Visual: quadro com Secretarias nas linhas e tipos de destinatário declarados (categorias estruturadas de F1-10.2 e F2-8.1/8.2) nas colunas. Cada célula: número de Registros que declararam aquele tipo.
Indicador ao lado: "Registros que declaram instrumento formal com terceiros (F2-8.7): sim N · não N · a confirmar N · sem resposta N".
Título do "Sobre": "Contamos Registros que declararam cada tipo de destinatário. Não contamos relações, empresas ou contratos distintos, nem avaliamos cláusulas."
Se nem essa versão couber no prazo: "Não disponível", com esse mesmo texto.
---
12. Fora desta versão (não implementar)
relações de circulação deduplicadas e situação de cláusulas;
incidentes (datas, prazos legais);
envio ou comprovação de comunicados ao Gabinete;
vínculo de um aprendizado a vários Registros;
percentuais de cobertura;
"RIPD em elaboração" como estado.
13. Critérios de aceite
Cada indicador tem teste com cenário próprio, e o número coincide com a lista.
Segregação por perfil testada (inclusive acesso direto por URL).
Nenhuma rota do dashboard grava no banco (teste).
Modo de projeção sem texto livre e sem evidência (teste sobre o HTML).
"Não disponível" e "Ainda não avaliado" aparecem onde previsto; nenhum zero falso.
Vistoria em tela por Ailton, com o teste dos 5 segundos na Abertur