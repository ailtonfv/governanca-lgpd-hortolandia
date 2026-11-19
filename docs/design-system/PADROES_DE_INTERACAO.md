# Padrões de interação

Levantamento documental de 18/11/2026. Base: `main` `9471a44`; branch `padrao-de-tela`. Este documento registra os padrões acordados e sua implementação encontrada; não altera telas nem autoriza regras em deliberação. Consulte também [cores e tokens](CORES_E_TOKENS.md), [AGENTS](../../AGENTS.md) e [SAD 10](../arquitetura/sad/SAD_10_DECISOES_DE_ARQUITETURA_REV17.md).

**Regra acordada não significa cobertura uniforme.** As ressalvas abaixo fazem parte do levantamento. Não aplicar a contagem de perguntas ativas do FORM 2 ao FORM 1 por inferência; obrigatoriedade por pergunta continua em deliberação (R17). Identificadores F1-/F2- são preservados; enunciados do catálogo não são reproduzidos neste documento.

## Evidências e limites

As capturas E01–E13 estão na pasta local [entrega-padrao-tela-20261118](<entrega-padrao-tela-20261118>). Não entram no GitHub: reproduzem conteúdo restrito do catálogo. Os links das capturas usam o nome do pacote local `entrega-padrao-tela-20261118`, independente do usuário ou da unidade de disco. Para abri-los, use uma cópia local deste documento ao lado da pasta do pacote autorizado, fora do repositório. Quem obtiver apenas o repositório precisará solicitar esse pacote; as imagens não estarão disponíveis no GitHub. Cada regra abaixo remete a uma captura do componente ou contexto correspondente; uma imagem não comprova autorização no servidor, persistência ou todas as variações de estado.

Foram obtidas páginas por GET da demonstração na porta 8008 e renderizadas localmente com os estilos e scripts da base, em 1366×768. Diálogos e seleção exclusiva foram acionados nessa reprodução local, sem enviar formulários ao servidor. E11 usa o componente real com dados sintéticos para ilustrar os três estados; E13 renderiza o trecho real da faixa de sucesso com mensagem sintética identificada; não é resultado de um novo ensaio de domínio. E10 mostra o conteúdo de uma resposta HTTP 403 real em uma moldura de evidência. Não houve mudança no banco nem interrupção de servidores. Os testes citados foram localizados no código, **não reexecutados neste lote documental**.

| Captura | Conteúdo |
|---|---|
| [E01](<entrega-padrao-tela-20261118/E01-central.png>) | Central, identidade fictícia, papel, ações e aviso da demonstração |
| [E02](<entrega-padrao-tela-20261118/E02-grade-form2.png>) | Cabeçalho, grade compacta do FORM 2, bloco atual, selos e navegação |
| [E03](<entrega-padrao-tela-20261118/E03-exclusividade.png>) / [E03b](<entrega-padrao-tela-20261118/E03b-exclusiva-marcada.png>) | Grupo de múltipla seleção antes/depois da alternativa exclusiva |
| [E04](<entrega-padrao-tela-20261118/E04-saida-sem-salvar.png>) | Diálogo de saída com alterações locais |
| [E05](<entrega-padrao-tela-20261118/E05-condicional.png>) | Campo condicional inativo e explicação |
| [E06](<entrega-padrao-tela-20261118/E06-origem.png>) | Referência à apresentação do FORM 1, resposta do AAL sem pré-marcação |
| [E07](<entrega-padrao-tela-20261118/E07-ajuda.png>) | Ajuda ao usuário separada e comentário recolhido |
| [E08](<entrega-padrao-tela-20261118/E08-grade-form1.png>) | Grade e ação de salvamento do FORM 1 |
| [E09](<entrega-padrao-tela-20261118/E09-confirmacao.png>) | Confirmação de atribuição, aberta localmente; ato não executado |
| [E10](<entrega-padrao-tela-20261118/E10-acesso-negado.png>) | Beta recusado no Painel do DPO, HTTP 403 |
| [E11](<entrega-padrao-tela-20261118/E11-estados.png>) | Estados, progresso e etiquetas do componente, em exemplo sintético |
| [E12](<entrega-padrao-tela-20261118/E12-retorno.png>) | Pendências com a origem, identidade e retorno ao bloco 3 |
| [E13](<entrega-padrao-tela-20261118/E13-faixa-sucesso.png>) | Faixa de sucesso: markup real, mensagem sintética, sem ato persistido |

Os nomes de arquivos nas tabelas seguintes são relativos a `app/`. Quando só o nome de um template é informado, está em `app/paginas/`; scripts e estilos ficam em `app/estaticos/`.

## Navegação

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| N1. Grade com todos os blocos, número, nome, situação e selos; sem rolagem lateral; quebra entre palavras e hifenização em português. P84/P98. | `_regua_fila_form2.html`, incluído em `participacao_form2.html`, `bloco_fila_form2.html`, `consolidacao_fila_form2.html` e `governanca_form2_v9.html` conforme o papel. `filas_form2.css` usa grid responsivo e `hyphens:auto`. Títulos vêm de `catalogo_form2_rev18.titulos_blocos_form2`. | E02/E11. Não foi detectada rolagem horizontal nas páginas capturadas a 1366×768; isso não substitui ensaio em larguras menores. |
| N2. Bloco atual azul, texto branco, “Você está aqui”, `aria-current="page"`; grade compacta dentro dos blocos. P98. | `_regua_fila_form2.html` e `.grade-form2-compacta` em `filas_form2.css`. `regua_form2.js` registra visita, que não equivale a preenchimento. | E02. `form1_rev22.html` e `_regua_form2.html` têm implementações distintas: não presumir a mesma etiqueta textual em todas as grades. E08 mostra a variante FORM 1. |
| N3. “Bloco anterior”, “Próximo bloco”, “Voltar à participação” e retorno ao bloco de origem quando disponível. P85. | Links locais em `bloco_fila_form2.html`; `governanca_form2_v9.html` usa `bloco_origem`, validado por `rotas_fila_form2.py`. O link de pendências transmite esse parâmetro. Há navegação própria em `form2_revisao.html` e `form1_rev22.html`. | E02/E12. E12 mostra “Voltar ao bloco 3”, obtido com `bloco_origem=3`; sem o parâmetro, esse retorno específico não aparece. |
| N4. Cabeçalho com “Central de Acesso (trocar servidor)”, oculto na própria Central. P87/P97/P106. | `_cabecalho_institucional.html`, incluído em `base.html`, compara o caminho com `/central` e preserva `conta_id`. | E02; E01 mostra a Central. Componente compartilhado, sem necessidade de copiar o link em cada template. |

**Duplicações da grade:** `_regua_form2.html` atende preparação/revisão, enquanto `form1_rev22.html` contém a grade FORM 1 diretamente e `registro.html` conserva navegação própria. Compartilhar estilos não equivale a compartilhar markup e semântica. Proposta futura: um componente visual parametrizado, recebendo estados calculados pelo domínio específico de cada FORM; preservar rotas, âncoras e diferenças funcionais.

## Situação e progresso

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| S1. “— Ainda não preenchido”; “◐ Em preenchimento · N de M perguntas ativas”; “✓ Todas as perguntas ativas respondidas”. P86/DA-45. | `respostas_form2.py`: `_contar_perguntas_ativas`, `contagem_perguntas_ativas`, `estados_regua_form2`. Exclui condicionais bloqueadas, comentários e leitura automática. A regra fica no domínio, inclusive para conjuntos. | E11 ilustra os três estados. E02 mostra o estado real observado. Não chamar esse cálculo de obrigatoriedade. FORM 1 tem estados próprios de respostas salvas. |
| S2. Barra proporcional acompanhada de informação acessível. P102/P108. | `_progresso_bloco_form2.html`: `role="progressbar"`, valores mínimo/máximo/atual e nome acessível; percentual vindo do domínio; espessura em `estilo.css`. Usado nas duas réguas FORM 2. | E11. Barra não significa confirmação, aprovação jurídica ou conclusão institucional. |
| S3. Etiquetas [D11] e [Guarda], dica e legenda, sem cobrir situação. P69/P108. | `_regua_fila_form2.html` gera etiquetas na variante compacta e texto por extenso na grande; `aguarda_temporalidade` em `respostas_form2.py` identifica o estado de guarda. CSS mantém os elementos no fluxo. | E02/E11. Guarda pendente de definição institucional é estado normal; não criar pendência para a origem por esse motivo. D11 não equivale a homologação realizada. |

Referências de teste: `test_lote5.py::test_p86_condicional_altera_total_sem_contar_historico_ou_comentario`, `test_lote6.py::test_p86_comentario_nao_cria_preenchimento`, `test_lote7.py::test_p102_progresso_proporcional`, `test_lote8.py::test_p108_etiquetas_legiveis` (todos em `testes/`).

## Perguntas, condições e ajudas

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| Q1. “A confirmar” fica sozinha; não pode coexistir com “Requer análise jurídica” ou outra alternativa. P83/DA-44. | `selecao_exclusiva.js` trata a interação; `respostas_form2._validar_valor` e o caminho `aplicar_revisao` validam no servidor. Não depender só de desmarcar caixas no navegador. | E03/E03b. Testes existentes: `test_lote5.py::test_exclusividade_no_dominio` e `test_exclusividade_do_catalogo_completo`. |
| Q2. Explicar “Disponível quando a resposta a … for …”; abrir imediatamente quando satisfeita; servidor rejeita alteração indevida em campo inativo. P52/D7. | `form2_rev212.aplicavel`, `condicoes_de_tela` e regras D7; macros de `_condicoes_form2.html`; `form2_revisao.js::atualizarCondicoes`. `rotas_fila_form2.salvar_bloco_fila` trata rejeição como 409. `_identificacao_form2.html` e `_unidade_guarda_form2.html` ainda têm textos condicionais próprios. | E05. Preservar respostas históricas não alteradas não é autorizar nova edição bloqueada. Teste `test_lote8.py::test_d7_post_bloqueado_sem_gravar`. |
| Q3. Exibir “No FORM N: …” da referência em análise, sem pré-marcar a resposta de quem confere. D6/P53/P65. | `fatos_abertura_form2.projetar_fatos_abertura`; `bloco_fila_form2.html` renderiza sete aberturas D6. F2-2.1/F2-2.9 têm quadros próprios; `_unidade_guarda_form2.html` também renderiza referências. | E06. O código atual projeta FORM 1; “FORM N” é padrão para extensão futura, não implementação dos FORMs 3/4. Teste `test_lote8.py::test_d6_sete_aberturas_sem_premarcacao`. |
| Q4. Não exibir códigos internos; resolver condições para linguagem comum. C2/C3. | `form2_rev212.condicoes_de_tela` resolve alternativas e fluxos; `_condicoes_form2.html` apresenta o resultado. Identificadores editoriais F1-/F2- permanecem visíveis. | E05. Testes `test_lote8.py::test_c2_condicoes_resolvem_opcoes_de_outros_blocos` e `test_c3_condicoes_de_fluxos_em_linguagem_comum`. |
| Q5. Ajuda ao usuário separada de especificação técnica; comentários recolhidos. C12/P59. | `form2_rev212.orientacoes_ao_usuario` e `montar_bloco`; renderização em `bloco_fila_form2.html` e `form2_revisao.html`. FORM 1 usa também `consultas_interface.instrucao_para_interface`: filtro separado, não componente único. | E07/E03. Teste `test_lote8.py::test_c12_ajuda_separada_da_especificacao`. Não publicar os enunciados/ajudas restritos como exemplos deste documento. |

## Atos, mensagens e saída

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| A1. Confirmação informa Registro, efeito e, em troca de responsável, quem sai/entra; botões lado a lado, principal azul. P93/P103. | Há diálogo genérico `#confirmar-ato` em `base.html` com `ato_registrado.js`. `confirmar_acao_fila.js` controla outros diálogos, cujo markup se repete em `filas_form2.html`, `participacao_form2.html`, `conferencia_form1_integral.html`, `form1_rev22.html` e `registro.html`. | E09. Captura é atribuição inicial, sem responsável anterior. O conteúdo é definido por ato; existência do modal não garante todos os dados em todos os caminhos. Consolidar o componente exige preservar textos e efeitos específicos. |
| A2. Faixa de sucesso com ato, autor e “registrada em DD/MM/AAAA às HHhMM”. P93. | `apresentacao_form2.data_local` formata data; `rotas_fila_form2.retorno_consultivo` monta retorno após conferir evento/ator. `filas_form2.html` usa `.mensagem.mensagem-sucesso`, `bloco_fila_form2.html` tem `.confirmacao-salvamento`; `registro.html` tem apresentação própria. | E13 mostra a faixa com mensagem sintética identificada, sem ato executado. **Retorno após persistência não reensaiado**. Autor pode estar em região separada; não há componente único que imponha ato+autor+data em todos os retornos. Falta conferir em tela. |
| A3. Saída com alterações: “Salvar e continuar / Sair sem salvar / Voltar ao bloco”; ação “Descartar alterações”. P101/DA-47. | `_saida_bloco_form2.html` e `form2_revisao.js`, compartilhados pelos fluxos de revisão/bloco do FORM 2. Botão de descarte está nos templates dos formulários. FORM 1 tem proteção própria em `form1_rev22.html`/`registro.html`. | E04, aberto sem enviar dados. Salvamento e falha no servidor não foram reensaiados; referência `test_lote7.py::test_p101_salvar_para_continuar_preserva_validacao`. |
| A4. Botão comunica ação, link comunica navegação; ação principal azul, foco e estados desabilitados perceptíveis. P93/P103 e padrão institucional. | `estilo.css`: `.botao-primario`, `.botao-secundario`, `.botao-link`, `.botao-link-secundario`; `.acoes-fila-form2` organiza ações. Links de navegação destacados podem ter aparência de botão, mas continuam âncoras com destino real. | E04/E09/E01. Não usar elemento visual clicável sem semântica, foco ou nome acessível. |

## Textos e identidade

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| T1. “Registro LGPD”, nunca “processo LGPD”; “Central de Acesso” uniforme. P54/P97. | `central.html`, `_cabecalho_institucional.html` e rótulos locais das páginas do Registro/participações. Nomenclatura não está em um dicionário único. “Processo” continua válido como tipo de objeto ou descrição do trabalho. | E01/E02/E09. Não substituir indiscriminadamente palavras do catálogo. |
| T2. Papel visível: APA titular/suplente, AAL, Encarregado de Dados (DPO). P30/P104. | `consultas_interface.projetar_fluxo_conferencia`, `usuarios_demonstracao`, `rotas_fila_form2.contexto_atuacao`; `central.html` e páginas operacionais exibem contextos próprios. `_links_instrumentos.html::identificacao_servidor` compartilha parte da identificação. | E01/E12. Papel depende do Registro/participação; não tratar o rótulo da conta como autorização global. |
| T3. Todos os nomes da demonstração identificados como fictícios. P31/P82.10. | Nomes da massa fictícia e `consultas_interface.rotulo_interface`; vários templates usam diretamente o nome recebido. Não há garantia central de sufixo aplicada a toda saída. | E01/E09/E12 ilustram saídas; cobertura universal não comprovada. Proposta: formatador comum de identidade demonstrativa, sem alterar nomes históricos. |
| T4. Linguagem comum; uma mesma informação uma vez por região. P75/P99/P105. | Aviso demonstrativo em `central.html`; links/retornos controlados por condições locais em `central.html`, `_cabecalho_institucional.html`, `governanca_form2_v9.html` e páginas de participação. | E01/E02/E12. O aviso pede conferir o servidor em sessão ao voltar a uma aba antiga; não explica parâmetros técnicos ao usuário. Duplicações não são prevenidas por um componente universal. |

## Acesso

| Regra e origem | Implementação encontrada e reutilização | Captura / limite |
|---|---|---|
| X1. Cada papel vê somente seus destinos e dados autorizados; servidor recusa acesso indevido mesmo por URL/POST direto. P91/P92. | `fila_form2.py` (`pessoa_ativa`, `autorizado`, comandos), `segregacao_form2_v9.py`, controles de `rotas_fila_form2.painel_dpo`; FORM 1 usa `consultas_interface.pode_consultar_registro`, `_pode_editar_form1_integral` e `permissoes.verificar_acao`. | E10: GET do DPO como Beta recusado com 403. Uma negativa não verifica toda a matriz. Teste localizado: `test_lote5.py::test_painel_exige_designacao_vigente`. |
| X2. `conta_id` simula identidade exclusivamente na demonstração; produção exige autenticação real. P92/P99 e AGENTS. | Propagação nas rotas e links, aviso em `central.html`. O parâmetro não é credencial e não deve ser apresentado como mecanismo de segurança de produção. | E01. Produção continua bloqueada; este documento não implementa autenticação. |

Decisões ainda pendentes de implementação, inclusive o alcance da DA-51, devem ser confrontadas com o SAD 10. Não declarar uma regra implementada só porque está aprovada na documentação.

## Uso no dashboard

Reaproveitar cabeçalho, identidade, textos, acesso pelo servidor, cores e mensagens. Um dashboard somente de leitura não tem grade de perguntas, “perguntas ativas” nem saída com alterações: os equivalentes são navegação por visões, filtros identificados, contagens com universo explícito e estado de carregamento/ausência de dados. Não transformar porcentagem de preenchimento em medida de conformidade. Se houver ato ou edição, aplicar confirmação, autoria, auditoria e proteção de alterações como nas demais telas.

As propostas de unificação e os limites por grupo estão no [relatório](RELATORIO_PADROES_DE_INTERACAO.md). Nenhuma proposta desta seção autoriza desenvolvimento do dashboard neste pedido.


## Componentes unificados no Lote 9 — 18/11/2026

Esta atualização substitui as ressalvas de ausência de componente único em A1, A2 e T3 no escopo abaixo. A descrição inicial e E01–E13 continuam sendo evidência da base anterior, não capturas do Lote 9. A grade do FORM 1 ficou fora deste lote.

| Regra | Componente único e uso | Verificação / limite |
|---|---|---|
| U1 — confirmação | `_confirmacao_ato.html::confirmacao`, usado em `filas_form2.html`, `participacao_form2.html`, `conferencia_form1_integral.html`, `form1_rev22.html` e `registro.html`. Parâmetros preservam IDs, alvo, texto principal/cancelamento e atributos dos scripts existentes; o corpo do ato fornece efeito e pessoas quando aplicável. | Comparação local antes/depois em `entrega-lgpd-lote9`. Diálogo de saída não salva e confirmação genérica de `base.html` têm contratos distintos e não foram incorporados por inferência. |
| U2 — faixa do ato | `_faixa_ato.html::faixa_ato`; filas, salvamento de bloco e Registro. `atos_interface.ato_registrado` verifica comando permitido, conta, evento e Registro/participação. Data em `apresentacao_form2.data_local`. | Não usar autor/data vindos da URL. Mensagens sem evento verificável não inventam autoria ou horário. Erro mantém tratamento de alerta. |
| U3 — identidade demonstrativa | `identidade_demonstrativa.identidade_demonstrativa`, filtro nos quatro ambientes Jinja; compatibilidade de nomes históricos da massa em `nomes_em_texto`. | Novas saídas de pessoa devem aplicar o filtro; mensagens compostas dos nomes fictícios existentes também são normalizadas. Não alterar Pessoa, eventos ou snapshots para acrescentar o sufixo. |

Regras novas permanecem no domínio: `complementos_form2` (D1), `alternativas_exclusivas` (D3), `classificacao_analise_form2` (D9), candidatos/recusas em `fila_form2` (DA-51). Scripts apenas acompanham a regra para orientar a interação. O relatório local separa teste automatizado, reprodução visual e vistoria de Ailton.

Os mesmos componentes U1/U2/U3 podem ser reutilizados no dashboard quando houver ato, mensagem ou identificação pessoal. A contagem de perguntas, condicionais e referência entre FORMs não se transfere automaticamente ao dashboard; seu equivalente são indicadores com fonte, período e condição de cálculo explícitos.


## Complemento aprovado — 19/11/2026

Reutilizar a convenção do FORM 1: `* Obrigatório` em vermelho; `** Obrigatório em alguns casos` em âmbar, passando a `*` quando a condição estiver ativa; `**** Facultativo/informativo` em cinza. Exibir também o texto por extenso. Campo inválido recebe `aria-invalid="true"`, moldura vermelha e mensagem associada. Não deduzir obrigatoriedade de perguntas: a classificação depende da R17 e da aprovação de Ailton.

Referência existente: `app/pre_validacao_form1_integral.py`, função `metadado_visual_obrigatoriedade`; classes `marcador-obrigatorio` e `indicador-obrigatoriedade-*`. Os atos dos FORMs 3/4 usam `app/validacao_atos34.py` para suas exigências já existentes e a macro `_campos_ato34.html` para a apresentação.

O bloco atual mantém azul-escuro e recebe borda grossa. Selos visíveis usam “Em deliberação” e “Guarda em definição”; códigos internos ficam apenas nas dicas e documentação. A deliberação é explicada por “Proposta em deliberação. Não equivale a homologação.”

Alternativa Outro solicita imediatamente “Qual?”, com até 200 caracteres. Nos FORMs 2, 3 e 4, a R17 permite salvar o complemento vazio e o exige no ato final; o comportamento do FORM 1 permanece preservado. As ações do rodapé ficam lado a lado: salvar o bloco identificado em destaque e descartar como secundária.

Códigos de instrumentos e perguntas servem como apoio entre parênteses nos comandos. A ação deve explicar seu destino em linguagem comum. Identificadores nas perguntas e no histórico continuam preservados.


## R17 — quatro regras aprovadas em 19/11/2026

Convenção comum aos quatro FORMs: salvar parcialmente; exigir pergunta principal ativa no ato final; exigir condicional somente quando ativa; manter respostas a confirmar como pendências visíveis, sem tratá-las como impeditivas. A aplicação deste lote alcança os FORMs 2, 3 e 4. O FORM 1 conserva sua matriz, fluxo e comportamento; não se libera submissão institucional.

- `* Obrigatório`, em vermelho, nas principais ativas. `** Obrigatório em alguns casos`, em âmbar, passa a `* Obrigatório neste caso` ao ativar. Informativas, calculadas e projeções de atos: `****`, somente leitura. Texto por extenso acompanha a cor.
- Obrigatoriedade é cobrada na conclusão e no encaminhamento, nunca no salvamento. Salvamento continua recusando respostas inválidas, alterações em campos inativos e operações sem permissão; não recusa mera ausência de preenchimento.
- “A confirmar” satisfaz preenchimento, permanece na lista superior e sua quantidade/identificadores ficam no evento do ato final. Não se classifica como impeditiva. Resposta histórica inativa continua sinalizada, sem reativação automática.
- Recusa de ato final mostra faltas agrupadas por bloco, com links. Não apaga respostas. Apenas atos futuros são conferidos; não se recalcula a validade de ingresso ou conclusão anterior.

Implementação única de conferência: `app/obrigatoriedade_forms.py`. Marcação reutiliza `metadado_visual_obrigatoriedade` do FORM 1, agora aceitando classe explícita para outros instrumentos; chamadas do FORM 1 continuam usando sua matriz. Macros `_marca_r17.html` e `_conferencia_r17.html`; interação `obrigatoriedade.js`, sem impor `required` aos formulários de salvamento parcial.

Exceções propostas: `app/r17_excecoes.json`, somente identificadores e motivos técnicos, carregadas como proposta. Ailton aprova a lista antes do merge. Relatório editorial e resumo dos enunciados ficam na entrega local restrita.

A conferência demonstrativa do FORM 2 e seus encaminhamentos passam pela R17; conclusão institucional continua bloqueada pelas regras existentes. Consultas de unidades especialistas não são a conclusão do questionário principal. FORM 3 confere ao concluir a avaliação; o envio de medida protetiva ao FORM 4 permanece disponível e registra a contagem, sem antecipar a conclusão do FORM 3; FORM 4 confere antes de registrar encerramento automático. Salvar bloco não aciona encerramento automático.

## Lote 12-C — espaçamento e navegação (19/11/2026)

Grupos de ações têm 1rem de separação vertical e .75rem entre controles, com alinhamento central e quebra de linha. Navegação usa links de aparência uniforme; o encaminhamento principal permanece em destaque. Tokens `--espaco-grupo-acoes` e `--espaco-entre-acoes`, em `estilo.css`. Grades não hifenizam automaticamente seus títulos; no cartão atual, o progresso é branco. Faixas de risco usam as cores aprovadas para o dashboard, sempre com nome escrito. A proposta de impacto é apenas consulta em deliberação: nenhuma escala, fórmula, competência ou regra de encaminhamento muda neste lote.
