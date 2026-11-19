# Dashboard — respostas às 16 perguntas

Conferência documental do código `1e14e96`, em 19/11/2026. Nenhuma tela, consulta de dashboard, carga ou regra foi implementada. As três especificações foram arquivadas integralmente; o sufixo de download “(1)” da parte 2 foi retirado do nome do arquivo, conforme o destino indicado no documento.

Prevalecem as decisões posteriores: a unidade dos indicadores principais é o **Registro LGPD**, com divisão por tipo; o quadro de atenção destina-se ao **Gabinete**, não a uma conta do Prefeito. Quantidades de riscos, ações, relações e participações, quando necessárias no detalhe, devem ser identificadas como tais e não apresentadas como número de Registros. Não se presume a regra de agregação de vários riscos de um mesmo Registro.

As referências ao Prefeito nas fontes arquivadas são históricas: a competência da decisão permanece, mas o registro é pelo Gabinete, com documento formal. O módulo específico de relatórios/comunicados ao controlador foi adiado para depois de 15/12; não confundir o planejamento do quadro do dashboard com autorização para construir esse módulo.

## Fontes técnicas comuns

- `app/modelos.py`: tabelas e campos relacionados abaixo.
- `app/fila_form2.py`, `app/consolidacao_form2.py`: participação e consolidação demonstrativa, sem conclusão institucional da principal.
- `app/fluxo_forms34.py`: estado dos FORMs 3/4 reconstruído dos eventos; não existe tabela relacional de risco com todos os campos abaixo como colunas.
- `app/avaliacao_risco34.py`: método e notas; `app/permissoes_forms34.py`: acesso por unidade/pessoa.
- `app/projecoes_forms34.py`: projeção técnica inicial, insuficiente para os indicadores; ainda devolve valores ausentes para risco e prazo. Não usá-la como cálculo pronto do dashboard.
- `app/unidades_interface_form2.py`: Secretarias ativas; `app/rev22_form1.py` e `app/form2_rev212.py`: estrutura das respostas versionadas.

## Parte 1 — quatro respostas

### 1a. Fontes dos indicadores da Abertura

| Indicador | Tabelas/campos existentes | O que falta ou exige cuidado |
|---|---|---|
| Registros ativos e tipos | `registro.id`, `codigo_lgpd`, `tipo_objeto`, `unidade_principal_atual_id`, `criado_em`, `estado_atual`; `ciclo.situacao` | Consulta única, escopo autorizado e definição explícita de ativo no ciclo demonstrativo. Não usar número de identidades R/A como total de Registros. |
| FORM 1: preenchimento, confirmação, complemento | `rascunho_form1_integral.conteudo`, `versao_rascunho`, `salvo_em`; `historico_conferencia_form1_integral.situacao`, `confirmada_em`, `snapshot_id`; `complemento_form2.estado`, vínculos de snapshots; eventos | Escolher versão e ciclo corretos; a confirmação anterior e uma complementação atual podem coexistir. Não reduzir isso a uma única situação sem regra. |
| FORM 2: em análise/concluído | `participacao_form2.registro_id`, `tipo`, `estado`, `entrada_em`, `assumida_em`, `concluida_em`, `conteudo` | A principal **não pode ser concluída** pelo fluxo atual. `consolidacao_demonstrativa_v1` em `conteudo` não equivale a conclusão; consultas temáticas concluídas não concluem o Registro. |
| FORM 3: sem avaliação, proposta, nota vigente, sem consenso | `identidade_forms34` (`tipo=R`, `registro_id`, `id`); `evento.conteudo.estado`: `avaliacao`, `avaliacao_confirmacoes`, `avaliacao_sem_consenso`, `reavaliacao`, `situacao` | Agregação por Registro e tratamento de várias situações simultâneas. Uma reavaliação pendente não retira a nota conjunta vigente da matriz. |
| FORM 4: plano, execução, atraso, verificação, conclusão | Identidade `tipo=A`; estado: `plano`, `plano_aprovado`, `execucao`, `prazo`, `verificada`, `verificacao`, `encerrada`, `cancelada`, `decisoes_pendentes` | Consulta e agrupamento por Registro. Atraso é condição que pode coexistir com espera de verificação; não somar categorias sobrepostas. |
| Faixas de risco | Estado `avaliacao.inerente/residual` com probabilidade, impacto, nota, faixa, metodologia; confirmações por Secretaria e DPO | Decidir como um Registro com vários riscos ocupa faixas/células; não escolher automaticamente o maior. Detalhe pode listar Rnn. |
| Aprendizados publicados | Estado `aprendizagem`, `aprendizagem_conferida`, `aprendizagem_autorizada`, `verificada` | Agregação e vínculo transversal ausentes. Publicação não é simples existência de texto. |
| Cobertura | `unidade.id/nome/ativa`, lista institucional; Registro e confirmação do FORM 1 | Consulta por Secretaria incluindo as sem Registro; não há denominador aprovado para percentual. |
| Circulação | Respostas versionadas dos FORMs 1/2 (ver 2a) | Sem identidade normalizada do fluxo/instrumento para deduplicação confiável; quadro completo ainda não calculável. |
| Críticos aguardando decisão | Nota residual vigente Crítico e ausência de `aceitacao`; eventos de confirmação e manifestações | Consulta, marco inicial da espera e distinção entre aguardando instrução e pronto para decisão; registro da decisão pelo Gabinete. |
| Segunda prorrogação contrária mantida | Estado `ciencia_prefeito`, `prorrogacoes`; evento `f34_ciencia_prefeito` | Consulta por Registro; ciência registrada não prova entrega de mensagem ao Gabinete. |
| Sem consenso no Comitê | Estado `avaliacao_sem_consenso`/`triagem_sem_consenso`, inclusive `reavaliacao`, e manifestações por finalidade | Identificar divergência ainda aberta, sem contar deliberação antiga como resolução da atual; derivar início pelos eventos. |

### 1b. Etapa mais avançada

**É necessária consulta nova**, não necessariamente migração. `registro.estado_atual` não representa sozinho os quatro instrumentos. A consulta deve combinar a principal do FORM 2, a conferência do FORM 1 e identidades R/A com eventos de ingresso e estado atual. Reserva técnica de identidade não prova ingresso. FORM 3 e FORM 4 simultâneos precisam da exceção explícita prevista na especificação. Falta definir qual situação prevalece quando vários riscos/ações do mesmo Registro estão em estados diferentes.

### 1c. Carga dos dez casos por fluxos reais

É viável para os atos existentes, preservando comandos, autoria, versão e histórico; não por inserção direta dos estados. Entretanto, **o conjunto inteiro não é reproduzível hoje exatamente como escrito**: caso 1 exige conclusão principal do FORM 2 ainda bloqueada; caso 6 exige módulo de incidente adiado. Os demais exigem completar perguntas ativas, habilitações fictícias e competências de cada unidade. O caso 10 depende das duas prorrogações e manifestação contrária pelos atos reais.

Estimativa de planejamento, não medição: **12–20 horas de trabalho do agente** para preparar, carregar e conferir os oito casos restantes, após aprovação dos fatos e da cópia; não inclui implementar incidentes/conclusão do FORM 2 nem o dashboard. Datas de atos devem ser verdadeiras: ajustar prazos fictícios em relação a 15/12 não autoriza retrodatá-los. Não foi feita carga nesta tarefa.

### 1d. Contradições e decisões necessárias

- Substituir o perfil operacional Prefeito por Gabinete; não conceder ao DPO competência decisória pelo título do quadro.
- A fonte chama alguns indicadores de riscos/ações, mas a decisão posterior define Registro como unidade principal: resolver deduplicação e faixas antes da implementação.
- O caso 1 não pode ser declarado FORM 2 concluído; caso 6 e comunicados ao controlador permanecem fora do corte atual.
- Reavaliação sem consenso mantém a nota vigente: só a proposta fica fora da matriz.
- A tabela dos dez exemplos soma **3 serviços, 3 processos e 4 atividades**, coerente com seu rodapé; o exemplo “4/4/2” da parte 2 é apenas ilustrativo e não deve virar resultado dessa massa.

## Parte 2 — cinco respostas

### 2a. Circulação e instrumentos

| Fonte | Estrutura disponível | Limite |
|---|---|---|
| FORM 1, F1-10.1, 10.2, 10.3–10.5, 10.7–10.9 | Escolhas estruturadas; tipo de destinatário em F1-10.2, repetição por destinatário no bloco 10 | Nome/identificação do destino em F1-10.2.1 e finalidade em F1-10.6 são textos; F1-10.7.1 também é descritivo. Não há identidade global de fluxo. |
| FORM 2, F2-8.1/8.2 | Presença e categorias estruturadas, com complemento textual | Categoria não identifica uma empresa, órgão ou fluxo único. |
| FORM 2, F2-8.7/8.7.1/8.7.2 | Presença estruturada; identificação/localização do instrumento em texto | Não há tabela normalizada de instrumentos nem chave compartilhada entre Registros. |
| FORM 2, F2-9.6 e desdobramentos, 9.7/9.7.1/9.7.2, 9.10 | Respostas estruturadas sobre aspectos contratuais e transferência; complementos | Não equivalem diretamente às quatro situações da barra de cláusulas; ausência de resposta não prova ausência de cláusula. |
| FORM 2, F2-10.2.1–10.4 | Identificação textual, indicador de pessoa jurídica, CNPJ quando aplicável, formalização e instruções | CNPJ não identifica cada contrato nem define sozinho uma relação de circulação. |

Persistência: `versao_form1_integral.conteudo` para a versão conferida/em análise, não o rascunho mais recente; `participacao_form2.conteudo.rascunho_form2_rev21_2` por bloco, chaves `opcao:`/`texto:` e conjuntos `#N`. A extração deve reutilizar os leitores do contrato, não presumir um JSON uniforme entre revisões.

**Resposta:** dá para contar declarações por categoria sem interpretar texto livre, mas não montar com segurança o quadro pedido de relações/instrumentos distintos entre Registros. Faltam chave de relação, instrumento normalizado e classificação explícita da barra contratual. Aplicar o corte “Não disponível”, ou obter aprovação para um quadro mais simples de Registros que declararam cada categoria; não inferir vínculo lendo nomes/textos.

### 2b. Datas nas filas

`participacao_form2` registra `entrada_em`, `assumida_em`, `concluida_em`, `tipo`, `unidade_id`, `estado`, `registro_id`. Tipos são principal, temática, jurídico e DPO. Ciência em `aviso_dpo` não encerra participação. Secretaria/Secretário, Comitê e Gabinete **não são participações dessa tabela** nos FORMs 3/4: são pendências derivadas de `evento.tipo_evento`, `ocorrido_em`, `conteudo.estado` e confirmações/manifestações. As datas dos atos existem; falta consulta que defina entrada/saída de cada espera, sem inventar assunção do Comitê/Gabinete.

### 2c. Secretarias ativas

Sim: `unidade(id,nome,ativa)` mais a lista institucional `SECRETARIAS` em `carga_ficticia/pessoas.py`; `secretarias_ativas()` filtra ambas. Isso permite incluir as 18 previstas mesmo sem Registro, desde que carregadas e ativas. Não contar automaticamente toda unidade ativa como Secretaria: a lotação do DPO é exemplo de unidade que deve ficar fora. O total exibido deve vir da consulta real, não da constante 18.

### 2d. Datas de incidente

**Não há fluxo estruturado de incidente do FORM 4** com ocorrência, conhecimento, comunicação e complementação separados. `evento.ocorrido_em` é data do ato do sistema, não prova a data do incidente. Textos e referências de evidência não substituem esses campos. Módulo adiado; apresentar “Não disponível”, sem calcular prazos legais nem fabricar data. Não foi feita análise jurídica dos prazos transcritos na especificação.

### 2e. Contradições

- A tela de Operação manda contar participações; a decisão posterior manda contar Registros. Proposta para aprovação: número principal e cada fila com Registros distintos; participações como detalhe identificado. Um Registro pode aparecer em mais de uma fila; a soma das filas não é o total municipal.
- Barras empilhadas de FORM 1 confirmado e FORM 2 concluído podem contar duas vezes o mesmo Registro. Falta definir segmentos exclusivos ou barras comparativas não somáveis.
- Circulação deduplicada, cláusulas e incidentes excedem a estrutura atual; não inferir fontes.
- Gabinete substitui a conta operacional do Prefeito, sem trocar a autoridade que decide. Espera não é atraso legal.

## Parte 3 — sete respostas

### 3a. Método da nota

Sim. Cada avaliação contém `inerente.metodologia` e `residual.metodologia`, hoje `DEMO-5x5-20261118`, junto de probabilidade, impacto, nota e faixa; o JSON está em `evento.conteudo.estado.avaliacao`. Confirmar ambos os lados em `avaliacao_confirmacoes`, conferir a metodologia das duas notas e excluir proposta inicial sem consenso. `reavaliacao` é separada: a avaliação vigente permanece. Não comparar revisões de método diferentes nem substituir a vigente pela proposta mais recente.

### 3b. Aceitação e pareceres

Implementados: `manifestar_dpo`, `manifestar_comite` e `aceitar_residual`. Pequeno/Moderado: Secretário; Alto: Secretário com manifestação prévia do DPO e registro de ciência do Comitê; Crítico: Gabinete registra decisão do Prefeito com documento, após manifestações de DPO e Comitê para residual. Fontes: estado `aceitacao`, `manifestacao_dpo`, `manifestacao_comite`, `ciencia_comite`, eventos correspondentes. Faltam apenas as consultas/agregações do dashboard para esse recorte, não novos atos. Aceitação não é inferida de nota ou aprovação do plano.

### 3c. Prazo original e prorrogações

Estado corrente guarda `prazo` e contador `prorrogacoes`; pedido fica em `decisoes_pendentes.prorrogacao` até a decisão. **Não há coluna separada de prazo original nem lista histórica pronta no estado atual.** Os eventos preservam os estados do planejamento, pedidos, manifestações e decisões. Uma consulta pode reconstruir prazo na primeira aprovação, pedidos aprovados/rejeitados e prazos efetivos por sequência; não usar a primeira data de rascunho do plano como prazo original aprovado. Parecer da segunda prorrogação está na manifestação por finalidade. Não é necessária migração só para ler essa trilha.

### 3d. Verificação e cancelamento

Sim: `executar_medida`, `verificar`, `pedir_cancelamento` e `cancelar`. Estado `verificacao.aprovada/evidencia/pessoa_id/em`, `verificada`, `cancelada` e `encerrada`; eventos identificam cada ato. Verificador independente de outra Secretaria; cancelamento pelo Secretário, com pareceres aplicáveis. Execução não conclui. Encerramento automático exige verificação e ausência de decisões pendentes, além da R17. O achado de cobrança R17 no ato do verificador continua reservado ao próximo lote; não foi corrigido nesta análise.

### 3e. Aprendizados e evidência

**Parcial.** Há `aprender`, `conferir_aprendizagem` (DPO) e `autorizar_aprendizagem` (Secretaria), após verificação. Estado `aprendizagem` contém **diretriz, escopo e versão**, não os três campos independentes descritos no cartão. Confirmações guardam autor/data. Evidências são referências textuais em `execucao.evidencia` e `verificacao.evidencia`; não são arquivos.

Faltam campos separados para “o que aconteceu”, início de vigência e vínculo do aprendizado a vários Registros, além de referência especificamente autorizada para divulgação. Não usar automaticamente a data da publicação como “desde quando vale” nem expor referência operacional por ela existir. Hoje o aprendizado fica ligado à Ação e ao Registro; deduplicar o mesmo aprendizado entre ações/Registros exige identidade e vínculos ainda inexistentes. Na projeção, o cartão deve conter apenas conteúdo autorizado e não dados pessoais; há conflito com a regra geral que proíbe qualquer evidência na projeção, a resolver antes de mostrar a referência.

### 3f. Ciência automática e dias de espera

Sim: a segunda prorrogação aprovada contra manifestação contrária grava `f34_ciencia_prefeito` e `estado.ciencia_prefeito` com data e motivo. **É ciência registrada no sistema, não comprovante de envio/recebimento externo.** O dashboard não deve dizer que uma mensagem foi entregue ao Gabinete.

Datas de espera podem ser derivadas de `evento.ocorrido_em`, sem campo novo, desde que se defina o marco: nota confirmada ou documentação completa para decisão; evento de sem consenso atual até manifestação correspondente; prorrogação contrária na data da decisão. É preciso parear eventos de cada rodada e reinícios, não simplesmente usar a primeira ocorrência histórica. Usar dias corridos se esse for o critério aprovado; dias úteis de incidente dependem de módulo/calendário próprios.

### 3g. Contradições e ajustes de especificação

- Matriz por quantidade de riscos, cronograma por ação e total de aprendizados são detalhes legítimos, mas divergem da unidade principal Registro: explicitar os dois níveis e decidir agregação; um Registro pode ter vários Rnn/Ann.
- “Sem consenso fora da matriz” vale para proposta sem nota vigente. Reavaliação divergente não remove a nota anterior confirmada.
- Aprovação de plano não é sempre pelo Secretário: plano Crítico é decisão do Prefeito registrada pelo Gabinete.
- O atalho de aceitação deve levar ao **bloco 16 do FORM 3**, onde o ato está disponível, não ao bloco 14 da avaliação.
- O sistema registra referência do RIPD, não acompanha/conclui o documento. “RIPD em elaboração” não tem estado próprio confiável; mostrar referência informada/não informada, com triagem separada.
- Cancelamento/motivo e referências de evidências não devem ir integralmente à projeção sem filtragem e autorização; texto livre não é automaticamente anonimizado.
- Incidentes e entrega externa de comunicados continuam fora do corte; ciência interna não equivale a notificação entregue.
- “Verificação aprovada” e “concluída com verificação” podem diferir enquanto houver pendência; a regra de atraso atual considera `verificada` e `cancelada`. Não equiparar todas as situações nem somar atraso a categorias que já o incluem.
- A declaração de controle implementado sustenta a nota residual, mas não prova medição causal da redução. Descrever como avaliação registrada, sem prometer impacto comprovado.

## Entrega

Arquivadas as três fontes e respondidas as 16 perguntas (4 + 5 + 7). Somente documentação, em commit separado na branch do Lote 12. Sem nova carga, migração, alteração de código ou reinício da 8013. Não executados testes da aplicação: houve conferência documental de campos, fluxos e diff. A definição de agregação por Registro e as lacunas acima precedem a implementação do dashboard.
