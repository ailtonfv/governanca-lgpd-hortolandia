# Consolidação candidata da navegação e governança LGPD

**Projeto:** Sistema Municipal de Governança LGPD — Hortolândia.  
**Data:** 06/11/2026, referência America/Sao_Paulo.  
**Origem:** INSTRUÇÃO_LGPD_2026_11_06, recebida após FORM02_12 e seu adendo.  
**Situação:** registro candidato de planejamento. A arquitetura de navegação e a proposta de Administração Central foram aprovadas funcionalmente pelo responsável da PoC. Este documento não autoriza sua implementação, não altera documentos canônicos e não atribui competências legais.

A próxima evolução separará a entrada institucional, o trabalho nos Registros e a consulta aos instrumentos. O painel existente será preservado. Dashboard gerencial e Administração Central de TI terão finalidades e autorizações distintas. Nesta sessão foi criado somente este documento; a implementação depende de nova instrução.

## 1. Arquitetura aprovada e situação da aplicação

| Área | Decisão funcional consolidada | Situação em 06/11/2026 |
|---|---|---|
| Central de Acesso LGPD | Será a página inicial. Apresentará os quatro FORMs e o Dashboard, seus objetivos e sua disponibilidade. A Secretaria será o contexto principal, selecionável somente entre vínculos autorizados. Não exibirá lista completa nem contadores de Registros. | Ainda não implementada. Hoje a entrada abre o Painel de Registros. |
| Painel de Registros | Preservará indicadores, Registros, pendências, responsáveis e ações autorizadas. Repetições da Central serão retiradas apenas na implementação futura, sem perda de informação operacional. | Implementado. FORM02_12 acrescentou orientação sobre os instrumentos e atalho por Registro. |
| Registro LGPD | Preservará a seção “Instrumentos deste Registro”, com acesso condicionado à autorização e ao estágio de cada instrumento. | Implementada e testada em FORM02_12; homologação visual desta entrega ainda pendente. |
| Administração Central de TI | Área distinta para administradores técnicos formalmente habilitados. | Proposta aprovada funcionalmente; sem área, permissões ou rotas implementadas por esta decisão. |
| Dashboard LGPD | Indicadores consolidados de governança, conforme abrangência e permissões do perfil. Não é a administração técnica. | Somente reserva visual “Planejado”, sem rota, consultas ou indicadores próprios. |

### Conteúdo da futura Central

| Instrumento ou acesso | Objetivo | Limite atual a apresentar |
|---|---|---|
| FORM 1 | Levantamento do tratamento | FORM 1 Integral implementado, com versões e extensões preservadas; submissão institucional bloqueada. |
| FORM 2 | Análise de legitimidade | Somente preparação demonstrativa autorizada, vinculada a snapshot identificado do FORM 1; não é parecer ou decisão. As 245 perguntas do planejamento não estão implementadas. |
| FORM 3 | Avaliação de riscos e controles | Planejado; sem comando de abertura ou edição nesta etapa. |
| FORM 4 | Providências e acompanhamento | Planejado; sem comando de abertura ou edição nesta etapa. |
| Dashboard LGPD | Indicadores gerenciais | Planejado; sem simulação de números como se fossem dados reais. |

O APA será identificado conforme atribuições e autorizações vigentes. Não será exigido ARP na Central. Dentro do Registro, o APA poderá assumir explicitamente o preenchimento ou designar outro servidor autorizado, mantendo os atos e controles já existentes. A seleção de Secretaria, a indicação de pessoa e a navegação não concedem permissões.

Os quatro FORMs pertencem ao mesmo Registro LGPD, com versões e responsabilidades próprias. Conferência pelo APA não se torna validação jurídica ou liberação automática dos demais instrumentos. As quatro etapas internas do FORM 1 não representam os quatro FORMs.

## 2. Administração técnica e Dashboard gerencial

| Aspecto | Administração Central de TI | Dashboard LGPD |
|---|---|---|
| Finalidade | Operação e administração técnica do sistema | Acompanhamento gerencial da governança |
| Abrangência futura | Visão técnica consolidada das 18 Secretarias | Indicadores consolidados dentro do alcance autorizado |
| Capacidades previstas | Administração autorizada de contas, vínculos e configurações; monitoramento de disponibilidade, integridade, auditoria e backups | Indicadores a especificar em incremento próprio |
| Acesso ao conteúdo | Sem acesso irrestrito automático a Registros, pareceres ou decisões | A agregação não dispensa controle de acesso aos dados e ao alcance dos indicadores |
| Segurança | Identidade individual reforçada, preferencialmente MFA; autorização no servidor e auditoria das operações privilegiadas | Controle de acesso específico por perfil e abrangência, a definir antes da implementação |

A administração técnica não confere competência jurídica, homologadora ou decisória. O desenho de autenticação reforçada e suas integrações deve ser especificado; a identidade simulada da PoC não atende, por si, a esse requisito institucional. Nenhuma conta administrativa, permissão privilegiada ou rota é criada por este planejamento.

## 3. Base técnica para a retomada

- FORM02_12 e adendo: **76/76 testes focalizados** e **729/729 na regressão integral**, sem falhas ou testes ignorados; aviso preexistente de depreciação Starlette/AnyIO. Evidências operacionais locais em `evidencias/form02_12/`, excluídas do Git.
- Os testes executaram em `lgpd_poc_teste`, com cliente HTTP de testes; não dependem das portas demonstrativas 8000/8001. Nenhuma regressão foi repetida nesta consolidação documental.
- Homologação visual de FORM02_11/12: **NÃO VERIFICADA integralmente**. Testes de HTML, DOM simulado, foco e estilos não substituem o aceite humano.
- A inspeção de processos confirmou duas instâncias de `app.main:app`, no mesmo checkout e configuradas para `lgpd_poc_v2`: porta 8000 sem recarregamento automático; porta 8001 com recarregamento automático. Ambas responderam com a navegação atualizada. O timeout inicial da 8000 não se repetiu na segunda leitura.
- **Recomendação operacional:** usar a instância já existente na porta **8001** para homologação. Não iniciar outro servidor nessa porta. Eventual encerramento da 8000 exige autorização separada; nenhuma instância foi encerrada na verificação de portas nem nesta consolidação.
- A migração 23 e as habilitações demonstrativas pertencem às entregas operacionais anteriores. Não foram reaplicadas, renovadas ou modificadas nesta tarefa. A vigência das habilitações deverá ser conferida na retomada; autorização temporária vencida não será renovada por inferência.

Preservações: contrato nuclear 2, REV13 e suas extensões, respostas, snapshots, lacres, permissões, históricos e banco demonstrativo. A submissão institucional permanece bloqueada.

## 4. Próximo incremento recomendado

**Após nova autorização:** implementar somente a Central de Acesso demonstrativa e seu percurso até o Painel de Registros, reutilizando a autorização e as projeções existentes. Não incluir Dashboard funcional, Administração Central ou novas perguntas do FORM 2 nesse incremento.

Antes de codificar, fechar a especificação mínima dos destinos dos cartões: um FORM que depende de Registro não pode abrir um instrumento sem identificar o Registro correspondente. A proposta é encaminhar a seleção ao painel operacional apropriado, mantendo o contexto de Secretaria e as restrições existentes. Não criar liberação institucional nem exigir ARP na entrada.

Pontos técnicos a definir nesse incremento:

1. Rotas e nomes de navegação: hoje `/` e o nome `inicio` representam o Painel de Registros. Tornar a Central a página inicial exige preservar os destinos explícitos “Voltar ao painel”, a saída segura e os endereços usados na homologação. Não basta trocar o conteúdo de `/` silenciosamente.
2. Contexto institucional: definir a apresentação de nenhum, um ou vários vínculos autorizados e vigentes. O servidor deve rejeitar Secretaria forjada ou fora do alcance, sem ampliar a visibilidade dos Registros.
3. Destinos dos cartões e estados indisponíveis: FORM 2 continua restrito às habilitações por pessoa/Registro; FORMs 3/4 e Dashboard continuam planejados. A Central não é um motor de workflow.
4. Preservação do painel: retirar somente repetições comprovadas da orientação inicial; manter todos os contadores e ações operacionais, sem duplicar as regras de projeção.

### Critérios de aceite propostos

- Central sem lista completa e sem contadores de Registros; objetivos dos instrumentos explícitos.
- Seleção de Secretaria limitada aos vínculos autorizados, inclusive em requisição adulterada.
- APA identificado corretamente; nenhuma exigência de ARP na Central e nenhuma designação automática.
- Percurso Central → Painel → Registro → instrumento autorizado e retorno ao destino correto, preservando alterações não salvas.
- APA acompanhante e preparador do FORM 2 mantêm suas capacidades atuais; concessões vencidas ou revogadas continuam recusadas.
- FORMs 3/4, Dashboard e Administração Central não recebem rotas funcionais ou poderes por consequência da navegação.
- Testes focais, regressão proporcional e homologação humana em tela larga/estreita e por teclado, separados no relatório.

<a id="nav_forms_01"></a>
### Atualização de 07/11/2026 — NAV_FORMS_01

A [diretriz de navegação dos quatro instrumentos](../arquitetura/ARQUITETURA_POC.md#nav_forms_01) define o percurso pela Central, instrumento, Registro autorizado e respectiva área de trabalho. O painel geral continua disponível diretamente na Central e como destino explícito na seleção do Registro.

- **FORMs 1 e 2.** Na homologação, percorrer ida e volta com a mesma identidade e Secretaria. Conferir separadamente as pendências factuais do FORM 1 e o acesso de acompanhamento ou preparação do FORM 2. Testar uma preparação atribuída, habilitação sem designação e ausência de acesso vigente. Uma mensagem específica de vencimento ou revogação dependerá de uma projeção autorizada para informar o motivo à própria pessoa.
- **Primeiro incremento futuro de cada FORM 3 e 4.** Antes de liberar acesso, definir os responsáveis e as ações autorizadas por Registro. Reutilizar o seletor e os retornos. Testar acesso permitido, negativa por acesso direto, Registro sem atividade e manutenção do contexto. Manter ambos como planejados até autorização própria. Os papéis APA, ARP e AAL não conferem responsabilidade automática nesses instrumentos.

## 5. Situação do Git e inventário pendente

Branch `main`; HEAD `664f4b3ca97f95139fdb0f66abf15cc18aac58a4`. Referência local `origin/main`: `26b9e97f0d6cdca4a19b342929128591947bab13`. Divergência **9 à frente / 0 atrás**, relativa à referência local, sem consulta nova ao GitHub. Não se afirma sincronização atual com o remoto.

### Nove commits locais ainda não enviados segundo a referência local

| Commit | Finalidade |
|---|---|
| `cea01e2` | Ordenação canônica das pendências |
| `e52c4af` | Distinção documental APA/SAA |
| `10bc4e9` | Backlog da ampliação |
| `c9af327` | Explicações das alternativas do Bloco 13 |
| `687dd3a` | Distribuição de pendências por Registro |
| `4d886aa` | Extensão MEDIDAS do item 13.2 |
| `9970803` | Extensão GUARDA do Bloco 12 |
| `1b070d5` | Verificação consolidada FORMS01_05 |
| `664f4b3` | Brasão institucional |

### Arquivos rastreados modificados antes desta consolidação

**15 arquivos**, sem alterações preparadas no índice:

```text
README.md
app/consultas_interface.py
app/estaticos/estilo.css
app/estaticos/posicao_form1.js
app/main.py
app/modelos.py
app/paginas/_ajuda_cartilha_form1.html
app/paginas/inicio.html
app/paginas/registro.html
docs/planejamento/BACKLOG_AJUSTES_POC_AMPLIADA.md
migracoes/aplicar.py
testes/apoio_posicao_form1.cjs
testes/test_bloco12_form1_integral.py
testes/test_bloco13_form1_integral.py
testes/test_snapshot_form1_integral.py
```

### Arquivos novos anteriores a esta consolidação

**28 arquivos ainda não rastreados:**

```text
app/apresentacao_form2.py
app/estaticos/form2_preparacao.css
app/estaticos/form2_preparacao.js
app/estaticos/instrumentos_registro.css
app/form2_preparacao.py
app/origem_form2.py
app/paginas/_consulta_historica_form2.html
app/paginas/_instrumentos_registro.html
app/paginas/_reserva_dashboard.html
app/paginas/form2_preparacao.html
app/rotas_form2_preparacao.py
demonstracoes/form2_preparacao.py
docs/planejamento/FORM02_05_ENTREGA_DEMONSTRATIVA.md
docs/planejamento/FORM2_GOV09_GOV10_DIRETRIZES_FORM02_05.md
docs/planejamento/FORM2_PRIMEIRO_INCREMENTO_DEMONSTRATIVO_ESPECIFICACAO_CANDIDATA.md
docs/planejamento/FORM2_REV17_DECISOES_PENDENTES.md
docs/planejamento/FORM2_REV17_INCREMENTOS_COMPLEXIDADE.md
docs/planejamento/FORM2_REV17_MATRIZ_CORRESPONDENCIA_CANDIDATA.md
docs/planejamento/FORM2_REV17_ORGANIZACAO_CONTRATO_CANDIDATO.md
docs/planejamento/GOV_FORMS_01_CONFIGURACAO_VERSIONAMENTO_CANDIDATO.md
docs/planejamento/GOV_FORMS_01_FLUXO_ENCAMINHAMENTOS_CANDIDATO.md
docs/planejamento/GOV_FORMS_01_MATRIZ_RESPONSABILIDADES_CANDIDATA.md
migracoes/preparacao_form2.py
testes/apoio_form2_preparacao.cjs
testes/apoio_navegacao_instrumentos.cjs
testes/test_apresentacao_form2.py
testes/test_form2_preparacao.py
testes/test_navegacao_instrumentos.py
```

Este documento acrescenta o **29º arquivo não rastreado**. Resultado esperado desta tarefa: 15 modificados e 29 novos; nenhum arquivo anterior editado ou descartado.

## 6. Proposta de organização e publicação

Os nove commits existentes devem ser preservados. As alterações ainda não commitadas abrangem entregas diferentes; não usar inclusão indiscriminada de todos os arquivos.

| Grupo candidato | Conteúdo a revisar e versionar futuramente | Cuidado de separação |
|---|---|---|
| Planejamento FORM 2 e governança | Quatro candidatos FORM2_REV17, especificação do primeiro incremento, diretrizes GOV09/GOV10 e três candidatos GOV_FORMS_01 | Confirmar destinação pública dos textos institucionais e revisar caminhos locais antes de incluir. |
| Ajustes anteriores do FORM 1 | CSS e ajuda de 13.1, testes dos Blocos 12/13 e trechos correspondentes do backlog | Não misturar com novas decisões da Central. Preservar os relatos datados como históricos. |
| Preparação demonstrativa e navegação do FORM 2 | Implementação FORM02_05, consulta legível FORM02_11, navegação FORM02_12/adendo, migração 23 já existente, testes e relatório de entrega | Domínio, rotas e template compartilham alterações. Separar por incremento somente se cada commit resultante for coerente e verificável. Se exigir reconstrução artificial de versões, preferir um conjunto funcional coerente, com escopo explícito, a commits intermediários quebrados. |
| Consolidação arquitetural | Este documento candidato | Não declarar a Central ou Administração Central implementadas. |
| Marco documental posterior | Revisão e consolidação do README | A alteração preexistente do README permanece local. Sua inclusão e eventual atualização aguardam o marco específico autorizado após revisão deste planejamento. |

A montagem dos commits futuros deve usar arquivos e trechos selecionados, com conferência do conteúdo preparado e dos testes apropriados à composição. O resultado 729/729 corresponde à árvore completa atual, não prova automaticamente cada divisão intermediária proposta.

### Triagem para repositório público

Foi realizada triagem textual das linhas acrescentadas pelos nove commits, do diff local e dos novos arquivos de texto, buscando padrões de chaves privadas, tokens, credenciais literais, URLs com senha, e-mails, CPFs e caminhos locais. **Não houve correspondências das categorias de credenciais, e-mails ou CPFs nessa triagem. Isso não certifica ausência universal de dados sensíveis nem autorização de publicação dos documentos.**

Achados e exclusões:

- Caminhos locais aparecem em `FORM2_REV17_ORGANIZACAO_CONTRATO_CANDIDATO.md` e `GOV_FORMS_01_MATRIZ_RESPONSABILIDADES_CANDIDATA.md`. Revisar a necessidade de expor a estrutura do ambiente antes de publicar; manter a rastreabilidade das fontes por referências apropriadas.
- O commit `10bc4e9` contém caminho local no backlog. Uma remoção apenas no HEAD não remove essa informação do histórico enviado. Antes do push, decidir se a exposição é aceitável ou autorizar expressamente um tratamento do histórico. Nenhuma reescrita está autorizada ou foi executada nesta tarefa.
- Os candidatos de planejamento contêm conteúdo institucional, inclusive a matriz de 245 perguntas. Confirmar sua destinação pública, sem inferir que autorização de desenvolvimento autoriza divulgação integral de qualquer fonte.
- `.env`, `evidencias/`, `documentos_locais/`, logs e dumps estão protegidos pelo `.gitignore`; não devem entrar nos commits. A Cartilha e seus derivados locais permanecem fora da publicação. Backups externos, manifestos de habilitação, relatórios de restauração e dados operacionais também ficam fora do lote público.
- Nenhum dump, banco local, chave privada ou arquivo `.env` apareceu no conjunto versionável examinado. Há DOCX/PPTX já rastreados no repositório, fora dos nove commits e das alterações desta rodada; não foram submetidos a nova auditoria de conteúdo. Entre os binários novos nos nove commits consta o brasão institucional, cuja revisão deve preservar a origem e o uso já documentados.
- A configuração local de `origin` não contém credencial embutida na URL. Isso não verifica autenticação, TLS ou o estado atual do remoto.

### Sequência segura, dependente de autorização futura

1. Revisar este planejamento, decidir a destinação pública dos documentos e tratar os achados acima, sem apagar histórico por iniciativa do agente.
2. Autorizar os grupos de commits; preservar alterações ainda fora do lote. Não modificar README antes de seu marco próprio.
3. Conferir conteúdo e exclusões, criar commits coerentes e revisar o estado final. Reaproveitar evidência válida; testar novamente se houver mudança de código ou composição que invalide a evidência.
4. Criar bundle completo fora do checkout, verificar sua integridade e a presença dos commits finais. Não declarar o lote protegido por bundles antigos sem conferir a cobertura.
5. Consultar e atualizar `origin/main` com TLS validado, usando Schannel por comando no Git for Windows, sem alterar configurações globais.
6. Confirmar que o remoto é ancestral da branch local. Interromper diante de divergência, autenticação ou TLS com problema; não usar force, desabilitar certificados ou sobrescrever trabalho remoto.
7. Após autorização de publicação, executar push normal e conferir igualdade dos commits e divergência 0/0. Registrar separadamente eventuais arquivos locais deliberadamente fora do lote.

## 7. Pendências e riscos para a próxima sessão

| Pendência ou risco | Encaminhamento mínimo |
|---|---|
| Homologação visual de FORM02_11/12 ainda pendente | Conferir Alfa/Épsilon, consulta/edição, retorno ao Registro, foco e telas estreitas na porta 8001; registrar aceite ou ressalvas. |
| Central ainda inexistente e dependência de nomes de rotas atuais | Aprovar especificação mínima e testes de compatibilidade antes de implementar. |
| Duas instâncias demonstrativas podem confundir a homologação | Usar a 8001 existente; qualquer encerramento da 8000 depende de autorização, sem iniciar duplicatas. |
| Habilitações temporárias podem vencer entre sessões | Verificar vigência e solicitar autorização específica se necessária renovação; não ampliar permissões. |
| Documentos antigos descrevem fases anteriores | Preservar datas e histórico. Consolidar README e referências no marco posterior, sem tratar inventário antigo como retrato atualizado do FORM 2. |
| Publicação de caminhos locais e conteúdo institucional | Decidir o tratamento antes de enviar os nove commits e os novos documentos ao GitHub público. |
| Administração Central e Dashboard ainda sem especificação executável | Incrementos próprios, com escopos de acesso, indicadores e autenticação definidos; nenhum acesso irrestrito ou poder decisório presumido. |

Não há impedimento para registrar estas decisões. A implementação da Central e a sincronização permanecem dependentes de nova autorização e das verificações indicadas. Nenhuma nova funcionalidade, migração, concessão de acesso, commit ou push foi executada nesta consolidação.

## Referências de continuidade

- [AGENTS.md](../../AGENTS.md) e [README.md](../../README.md), preservados.
- [Matriz de responsabilidades candidata](GOV_FORMS_01_MATRIZ_RESPONSABILIDADES_CANDIDATA.md).
- [Fluxo de encaminhamentos candidato](GOV_FORMS_01_FLUXO_ENCAMINHAMENTOS_CANDIDATO.md).
- [Configuração e versionamento candidatos](GOV_FORMS_01_CONFIGURACAO_VERSIONAMENTO_CANDIDATO.md).
- [Especificação do primeiro incremento do FORM 2](FORM2_PRIMEIRO_INCREMENTO_DEMONSTRATIVO_ESPECIFICACAO_CANDIDATA.md).
- [Entrega demonstrativa FORM02_05](FORM02_05_ENTREGA_DEMONSTRATIVA.md) e [diretrizes GOV09/GOV10](FORM2_GOV09_GOV10_DIRETRIZES_FORM02_05.md).
- [Backlog permanente](BACKLOG_AJUSTES_POC_AMPLIADA.md), com registros históricos preservados.
