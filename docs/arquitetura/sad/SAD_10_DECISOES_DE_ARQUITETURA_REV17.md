# SAD 10 — Decisões de arquitetura — REV17

Edição textual da revisão local de 17/11/2026. Histórico preservado; sem enunciados do catálogo ou do Documento-Mestre.

SAD 10

Governança Municipal LGPD

Documento de Arquitetura da Solução

Decisões de Arquitetura

**Projeto** — Sistema de Governança Municipal LGPD

**Documento** — SAD 10 Decisões de Arquitetura

**Revisão** — REV17

**Data** — 17 de novembro de 2026

**Elaboração** — Ailton, DPO — autoria documental; referência institucional: Decreto Municipal nº 5.200/2023

Controle de revisões

**Revisão** — Resumo

**REV01 — 05/10/2026** — Versão inicial: registro formal das decisões tomadas até a Etapa D (DA-01 a DA-19) e das decisões em aberto (AB-01 a AB-07).

**REV02 — 06/10/2026** — DA-20: código do DGP ≠ unidade_id, com a confirmação da TI de 06/10/2026 como fundamento; DA-16 remete à DA-20; remissão ao SAD 05 REV06.

**REV03 — 06/10/2026** — Etapa E: DA-20 com a informação de que a TI não decide sucessão; DA-21 (comunicação com a ANPD via Encarregado); AB-08 a AB-10; DA-02 e DA-03 registram o SAD 06 alinhado desde a REV04; remissões às revisões vigentes.

**REV04 — 06/10/2026** — Etapa F: DA-22 (Comitê conforme o Decreto nº 5.357/2024), que substitui a DA-13, mantida como histórico; AB-04 com os seis itens do ato interno e validação com a Secretaria de Assuntos Jurídicos; AB-09 com a proposta de o Registro acompanhar a competência; remissões ao SAD 02 REV16, SAD 03 REV07, SAD 05 REV08 e SAD 08 REV08.

**REV05 — 06/10/2026** — Etapa G (G5): DA-23 (escopo da PoC em três camadas, decisão do Ailton); DA-24 (figuras derivadas das matrizes; a matriz prevalece em divergência); AB-04 com o texto da autoridade provisória do SAD 04 REV08; remissões ao SAD 04 REV08, SAD 05 REV09, SAD 08 REV09 e SAD 09 REV06.

**REV06 — 06/10/2026** — Etapa H (H1): DA-25 (comunicação de incidente por destino: N5A e N5B, estado Em comunicação, prazo e alerta contados de conhecimento_em, autoridade conforme AB-04), que substitui a DA-11, mantida como histórico; remissões ao SAD 03 REV08 e ao SAD 09 REV07. Fechamento da série.

**REV07 — 06/10/2026** — Etapa I (I4), descongelamento pontual para a PoC nuclear: DA-26 (modelo de eventos da PoC: cadeia por objeto, código estável, comando idempotente, domínio × auditoria, transação única, ator tipado); remissões ao SAD 04 REV09, SAD 05 REV10 e SAD 08 REV10.

**REV08 — 06/10/2026** — Etapa J (J4): DA-27 (contrato de integridade da cadeia: auditoria segmentada por período; hash SHA-256 sobre JSON canônico com hash_anterior como campo; payload canônico armazenado; versões de algoritmo e de esquema; troca abre novo segmento); remissões ao SAD 03 REV09, SAD 04 REV10 e SAD 08 REV11.

**REV09 — 06/10/2026** — Etapa K (K2): DA-28 (decisões técnicas da PoC, D-K: governança da máquina de estados, alcance por papel, PostgreSQL, stack, armazenamento de evidências e acesso técnico excepcional), provisória da PoC e sem valor para o Piloto; DA-23 com a divisão do M3 em M3A e P1 e a autorização própria do Piloto; remissões ao SAD 09 REV08.

**REV10 — 06/10/2026** — Etapa L, lote 1: DA-29 (agente externo pessoa jurídica ou natural), DA-30 (autoridade da comunicação de incidente como atribuição configurável), DA-31 (vínculos por tipo, para depois da PoC nuclear), DA-32 (G10 leva ao estado ativo recalculado) e DA-33 (escrita em sistemas externos proibida até decisão própria); remissões ao SAD 05 REV11 e ao SAD 06 REV07.

**REV11 — 08/10/2026** — Etapa L, lote 2: DA-34 (governança da configuração do workflow na PoC: só o Encarregado altera, sempre com nova versão; vale para Registros iniciados depois; segregação, imutabilidade das versões e cadeia de hash fora da configuração; regra do Piloto em aberto); remissões ao SAD 08 REV12 e ao SAD 09 REV09.

**REV12 — 08/10/2026** — DA-28 atualizada (Python 3.14; tecnologia do Piloto) e nova DA de transferência institucional (DA-35: encerramento da PoC, transferência institucional e independência tecnológica). Remissões ao SAD 09 REV10; autoria padronizada (O-55); referências às revisões vigentes.

**REV13 — 13/10/2026** — DA-36 (equivalência de Registros, papéis do objeto, catálogos operacional, de canais e de finalidades, canais como dimensão transversal, bloqueio e alerta de duplicidade), provisória da PoC; origem: O-80. Autoria conforme o O-77.

**REV14 — 13/10/2026** — DA-37 (cancelamento do Registro a partir de qualquer estado diferente de Cancelado, inclusive Suspenso e Concluído; catálogo de motivos; competência reforçada para Registro Concluído), provisória da PoC; origem: conferência da DA-36 e O-82. Na DA-36, frase final em Consequências remetendo à DA-37.

**REV15 — 14/10/2026** — DA-38 (contexto de atuação no lugar de 'finalidade' na regra de equivalência; catálogo de bases e conjuntos de dados como terceiro eixo transversal; famílias de contexto e advertência; relação 'é realizado por'; ordem de verificação), provisória da PoC; origem: O-83. Nas DA-36 e DA-37, frase final em Consequências remetendo à DA-38.

**REV16 — 14/10/2026** — DA-39 (decisões do Encarregado de 14/10/2026 para o M1a: um contexto por Registro; advertência de família e transversalidade; numeração anual; verificação de sobreposição em dois momentos; pedido idempotente estrito; devolução com pendência, congelamento por hash e P5/P6 restritos; percurso com medidas com ação obrigatória sintética), provisória da PoC; origem: revisão da Etapa 2c. Nas DA-26 e DA-38, frase final em Consequências remetendo à DA-39.

**REV17 — 17/11/2026** — Decisões DA-40 a DA-51 (P36, P69, P74, P79/P96, P83, P86, P91, P101, C1, D6 e D7); reafirmação do Registro macro por remissão às DA-17/DA-19; seção 3.1 de requisitos para transferência; proposta AB-11. Sem enunciados de catálogo ou do Mestre. Ajustes de 17/11/2026: AB-10 encerrada por remissão à DA-46; AB-12 em deliberação; Lote 8 aprovado e integrado ao main (17338bf); ADR 000 não alterado.

Prefeitura Municipal de Hortolândia

## 1 Introdução

O SAD 10 é o registro formal das decisões de arquitetura do Sistema de Governança Municipal LGPD, exigido pelo ADR 000 (G-26 e seção 4). Toda decisão que contrarie um guardrail, resolva divergência entre documentos ou fixe escolha ainda não definida nos SADs só produz efeito depois de registrada aqui, com justificativa e alternativas consideradas.

Este documento não substitui os SADs: cada ficha aponta os documentos e as revisões em que a decisão está refletida. Em caso de divergência entre uma ficha e um SAD, a divergência é corrigida por revisão do documento divergente ou por nova ficha, e nunca por interpretação local (ADR 000, seção 4).

## 2 Convenções

Identificação: DA-nn, sequencial e não reaproveitável. Decisões em aberto usam AB-nn e, quando decididas, recebem uma ficha DA própria.

Situação: vigente; provisória da PoC (não vale para Piloto ou Produção sem validação, ADR 000, G-28); a validar; substituída (indicando a ficha substituta).

Data: data em que a decisão foi tomada. Quando a data original não está documentada, usa-se a data da revisão que a registrou, com essa indicação.

Alterar uma decisão exige nova ficha que a substitua; a ficha anterior passa a "substituída" e permanece como histórico.

Decisões de tecnologia (G-01), físicas (SAD 09, seção 2) e as abertas nos demais SADs (por exemplo, SAD 08, D-08-01 a D-08-08; SAD 09, SAD09-01 a SAD09-10) serão registradas aqui quando tomadas.

## 3 Decisões registradas

### DA-01 — Nome do sistema, da Jornada e terminologia canônica

**ID** — DA-01

**Data** — 03/10/2026

**Situação** — Vigente

**Contexto** — Os documentos usavam nomes diferentes para o sistema, para a metodologia e para o objeto persistente, e a expressão "processo LGPD" confundia o registro com o processo administrativo.

**Decisão** — O sistema chama-se Sistema de Governança Municipal LGPD; a metodologia, Jornada de Conformidade LGPD; o objeto persistente, Registro LGPD, distinto do objeto da Jornada (processo, atividade ou serviço). O sistema de processos administrativos é o SEQUOIA. Os quatro instrumentos são os Instrumentos da Jornada (FORMs 1 a 4).

**Alternativas consideradas** — Manter "processo LGPD" (substituído no SAD 02 REV03) e grafias variadas do sistema de processos.

**Consequências** — Revisões de uniformização em toda a série; o termo "objeto da Jornada" continua em uso até a decisão AB-01.

**Documentos afetados** — ADR 000 REV06 (G-29 e G-30); SAD 01 REV05; SAD 02 REV16; SAD 03 REV09; SAD 04 REV10; SAD 05 REV11; SAD 09 REV10.

### DA-02 — Convenção de nomes de campos

**ID** — DA-02

**Data** — 03/10/2026 (data da revisão que a consolidou)

**Situação** — Vigente

**Contexto** — O modelo conceitual precisava de nomes estáveis para identificadores, datas e autoria, compartilhados com a auditoria.

**Decisão** — Campos conceituais usam sufixo _id para identificadores, _em para data e hora e _por para autoria.

**Alternativas consideradas** — Prefixo id_ (usado no SAD 06 até a REV03).

**Consequências** — Novas entidades seguem a convenção (por exemplo, registrado_em e registrado_por no Compartilhamento). O SAD 06 está alinhado desde a REV04 (seção 2.4, sufixo _id).

**Documentos afetados** — ADR 000 REV06 (G-31); SAD 05 REV11 (seção 2.4); SAD 08 REV12 (seção 7.2); SAD 06 REV07.

### DA-03 — Eliminação do SAD 11

**ID** — DA-03

**Data** — 03/10/2026

**Situação** — Vigente

**Contexto** — Havia previsão de um SAD 11 para diagramas e guia de instalação, o que criaria documentação gráfica paralela e sujeita a defasagem.

**Decisão** — A série vai do SAD 01 ao SAD 10. Os diagramas ficam na subpasta Diagramas de cada SAD, com o mesmo identificador e revisão; o guia de instalação da PoC fica na pasta 09.

**Alternativas consideradas** — Manter o SAD 11 como documento próprio de diagramas e instalação.

**Consequências** — Cada SAD responde pelos próprios diagramas. O SAD 06 está alinhado desde a REV04 (seção 16: guia de instalação na pasta 09).

**Documentos afetados** — ADR 000 REV06 (G-24; DC-05); SAD 01 REV05; SAD 09 REV10.

### DA-04 — PoC pelo núcleo, FORM 1 como camada adaptadora e marcos

**ID** — DA-04

**Data** — 03/10/2026

**Situação** — Vigente

**Contexto** — Condicionar o início da PoC ao contrato integral do FORM 1 atrasaria a validação do núcleo.

**Decisão** — A PoC começa pelo núcleo (chassi), independente do FORM 1, que entra como camada adaptadora. Marcos: M1a (chassi), M1b (fluxos de controle), M2 (entrada do FORM 1) e M3 (fluxo completo). O contrato do FORM 1 condiciona o M2, e não o início.

**Alternativas consideradas** — Começar pelo FORM 1 ponta a ponta, com o contrato como condição de início.

**Consequências** — Cada marco tem escopo, cenários e condição de entrada próprios; grupos novos do SAD 02 são distribuídos pelos marcos.

**Documentos afetados** — ADR 000 REV06 (G-27; DC-01); SAD 09 REV10 (seção 4A); SAD 04 REV10 (seção 3); SAD 05 REV11 (seção 17).

### DA-05 — Defaults provisórios de competência na PoC

**ID** — DA-05

**Data** — 03/10/2026

**Situação** — Provisória da PoC

**Contexto** — O SAD 04 remete transições críticas à competência formal, ainda não validada institucionalmente.

**Decisão** — Para a PoC valem as seções 10A, 11.1 e 11.2 do SAD 03. Jurídico e TI manifestam-se por pendência e não iniciam análise, não validam nem devolvem versão, salvo designação expressa como instância validadora. A reatribuição de análise cabe ao responsável pela instância validadora da unidade principal.

**Alternativas consideradas** — Jurídico e TI como instâncias validadoras ordinárias; definição de competências antes do início da PoC.

**Consequências** — Os defaults não viram regra do Piloto ou da Produção sem validação institucional (G-28).

**Documentos afetados** — ADR 000 REV06 (G-28; DC-02); SAD 03 REV09; SAD 08 REV12 (seção 5.2; D-08-05); SAD 09 REV10.

### DA-06 — Alcance por papel na PoC

**ID** — DA-06

**Data** — 03/10/2026

**Situação** — Provisória da PoC

**Contexto** — Era preciso definir o que cada papel enxerga para executar os cenários da PoC.

**Decisão** — Servidor: apenas Registros em que participa. Ponto focal: consulta e acompanhamento dos Registros de sua Secretaria, sem edição de conteúdo. Gestor, Encarregado, Comitê e perfil técnico permanecem pendentes (SAD09-04).

**Alternativas consideradas** — Servidor com visão de todos os Registros da unidade.

**Consequências** — Itens pendentes seguem no SAD 09 (SAD09-04).

**Documentos afetados** — ADR 000 REV06 (DC-03); SAD 03 REV09 (seção 26); SAD 09 REV10.

### DA-07 — Cancelar reabertura

**ID** — DA-07

**Data** — 03/10/2026

**Situação** — A validar

**Contexto** — O SAD 05 previa encerrar um ciclo aberto por engano sem cancelar o Registro, mas o SAD 04 não tem essa transição.

**Decisão** — "Cancelar reabertura" permanece a validar e fora da PoC até sua incorporação ao SAD 04.

**Alternativas consideradas** — Incorporar já uma transição G12 ao SAD 04.

**Consequências** — O SAD 05 mantém os campos marcados como a validar e fora da PoC.

**Documentos afetados** — ADR 000 REV06 (DC-04); SAD 05 REV11 (seção 6); SAD 09 REV10 (seção 32).

### DA-08 — Participação por unidade como pendência

**ID** — DA-08

**Data** — 04/10/2026

**Situação** — Vigente

**Contexto** — Várias unidades executam etapas do mesmo tratamento e precisam registrar sua parte no FORM 1 sem fragmentar o Registro.

**Decisão** — A participação é Pendência do tipo participação, encaminhada à fila institucional da unidade e assumida por agente autorizado. Não cria Registro, Instrumento nem nova dimensão de estado. A unidade principal consolida o FORM 1.

**Alternativas consideradas** — Nova dimensão de estado para a participação; um Registro por unidade.

**Consequências** — Pendência de participação aberta bloqueia a submissão do FORM 1; quem assume na fila segue o SAD 03 (10A).

**Documentos afetados** — SAD 02 REV16 (RF-PAR); SAD 03 REV09 (10A); SAD 04 REV10 (seção 10.2); SAD 05 REV11 (seção 9.1).

### DA-09 — Continuidade institucional em quatro situações

**ID** — DA-09

**Data** — 04/10/2026

**Situação** — Vigente; retorno assistido como default provisório da PoC

**Contexto** — O Registro precisa sobreviver à troca de servidor (G-07) sem perda de autoria nem de responsável.

**Decisão** — Quatro situações: ausência temporária, saída definitiva (inclui aposentadoria), mudança de função ou lotação e troca de chefia. O retorno da substituição é assistido: o sistema lista os itens e o titular confirma. A chefia imediata designa e reatribui (default da PoC).

**Alternativas consideradas** — Retorno automático ao titular; reatribuição pelo ponto focal.

**Consequências** — Eventos de designação e reatribuição sem transição de estado; a saída não programada segue em aberto (AB-02).

**Documentos afetados** — SAD 02 REV16 (RF-CON; RF-ING-07); SAD 03 REV09 (10A); SAD 04 REV10 (seção 14.1); SAD 05 REV11 (seção 12.1).

### DA-10 — Relato e incidente como jornada associada

**ID** — DA-10

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — Um incidente pode não ter Registro, ou afetar vários, e o relato de suspeita não deve ser tratado como incidente.

**Decisão** — Relato e incidente formam uma jornada associada, fora das três dimensões do Registro, com dois objetos e catálogos próprios (relato: Relatado, Em triagem, Descartado, Convertido em incidente; incidente: Em avaliação, Comunicado, Não comunicado, Encerrado) e cadeias próprias de eventos, ligadas à cadeia do Registro por evento_causa_id.

**Alternativas consideradas** — Um único objeto com ciclo N1 a N7; eventos de incidente na cadeia do Registro.

**Consequências** — Novas cadeias e critério de aceite de verificação (CA-08-22); o incidente pode motivar Reabrir (G10) sem depender dele.

**Documentos afetados** — ADR 000 REV06 (G-11); SAD 02 REV16 (RF-INC); SAD 04 REV10 (seção 16.1); SAD 05 REV11 (seções 10.1, 14.3 e 14.4); SAD 08 REV12 (seção 7.5).

### DA-11 — Decidir ≠ comunicar incidente

**ID** — DA-11

**Data** — 05/10/2026

**Situação** — Substituída pela DA-25 (06/10/2026); mantida como histórico

**Contexto** — A comunicação à ANPD e aos titulares é obrigação do controlador (LGPD, art. 48; Resolução CD/ANPD nº 15/2024, arts. 4º e 6º). O Decreto Municipal nº 4.822/2021 não delega essa decisão ao Encarregado.

**Decisão** — O Encarregado analisa, recomenda com fundamentação, prepara e protocola em nome do controlador (ou outro representante formalmente constituído, Res. 15/2024, art. 6º, § 5º). A autoridade definida em ato interno decide; na falta de ato, o Prefeito. A unidade afetada comunica imediatamente o Encarregado e não protocola na ANPD. Critérios: incidente confirmado, dados pessoais sujeitos à LGPD e risco ou dano relevante. Prazo: três dias úteis, contados do conhecimento, pelo controlador, de que o incidente afetou dados pessoais, com alerta desde a decisão. O envio (N5) exige decisão prévia.

**Alternativas consideradas** — Delegação da decisão ao Encarregado; decisão pelo Comitê; protocolo pela unidade afetada.

**Consequências** — Separação de recomendação, decisão e envio no modelo e na auditoria (CA-08-23).

**Documentos afetados** — ADR 000 REV06 (G-32); SAD 02 REV16 (RF-INC-02 a 06); SAD 03 REV09 (6.8 e 10A); SAD 04 REV10 (16.1); SAD 05 REV11 (14.4); SAD 08 REV12.

### DA-12 — Tratamento autônomo e processos transversais

**ID** — DA-12

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — Serviços usam canais e processos de apoio (156, Ouvidoria, e-SIC, protocolo no SEQUOIA) e alguns tratamentos merecem Registro próprio.

**Decisão** — Canais e serviços de apoio com sistema, base, regras de guarda ou operador próprios têm Registro próprio; o Registro do serviço aponta para eles pela relação utiliza_processo_transversal. O tratamento autônomo é decidido com critérios (Tabela 4.1 do SAD 02) e gera novo Registro relacionado ao anterior por desmembrado_de.

**Alternativas consideradas** — Repetir a descrição dos processos transversais em cada Registro; tipo novo originado_de_tratamento_autonomo.

**Consequências** — Catálogo de relações ampliado; decisão de tratamento autônomo registrada como evento.

**Documentos afetados** — SAD 02 REV16 (RF-PRC-14 e 15; Tabela 4.1); SAD 03 REV09 (10A); SAD 04 REV10 (16.6); SAD 05 REV11 (13.1).

### DA-13 — Papel do Comitê Municipal de Privacidade

**ID** — DA-13

**Data** — 05/10/2026

**Situação** — Substituída pela DA-22 (06/10/2026); mantida como histórico

**Contexto** — O Decreto Municipal nº 4.822/2021 cria o Comitê para elaborar o Programa de Governança (art. 2º).

**Decisão** — O papel do Comitê fica restrito ao Programa, sem decisão operacional de casos. Triagem de relato e aprovação de minuta de RIPD pelo Comitê não são recomendadas.

**Alternativas consideradas** — Comitê como instância de triagem ou de aprovação de RIPD.

**Consequências** — O papel em transições críticas continua a validar e fora da PoC.

**Documentos afetados** — SAD 03 REV06 (6.11 e 26); SAD 08 REV07 (5.2).

### DA-14 — Carta de Serviços como referência de consulta

**ID** — DA-14

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — A importação da Carta de Serviços como lista mestra exigiria confirmação item a item antes de originar Registro.

**Decisão** — A Carta de Serviços e o Plano de Classificação são referências de consulta, vinculadas ao Registro (RF-PRC-12 e 13). RF-PRC-10 e 11 foram excluídos, sem reaproveitamento dos IDs. O SAD 01 mantém "Fonte (lista mestra)" no sentido de catálogo de referência.

**Alternativas consideradas** — Importação controlada com confirmação pela Secretaria (antigos RF-PRC-10 e 11).

**Consequências** — Entidade Referência de catálogo no SAD 05; listas de referência em M2.

**Documentos afetados** — SAD 02 REV08 a REV14; SAD 05 REV11 (13.4); SAD 09 REV10 (4A.3 e 4A.5).

### DA-15 — Permissão efetiva, perfil de acesso e separação de artefatos

**ID** — DA-15

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — O termo "perfil" era usado tanto para o acesso do usuário quanto para a configuração técnica.

**Decisão** — O acesso do usuário segue a permissão efetiva (SAD 03, seção 12); "perfil de acesso" designa apenas o pacote técnico de permissões (SAD 03, 4.13). RACI, matriz de permissões e regras de escopo são artefatos distintos (SAD 03, 11.3); a matriz é versionada.

**Alternativas consideradas** — Conceito único de perfil; matriz única com RACI, ação e escopo.

**Consequências** — Requisitos do SAD 02 reescritos; entidade de matriz versionada no SAD 05 (12.2).

**Documentos afetados** — SAD 02 REV08 e REV09; SAD 03 REV09 (4.13, 11.3); SAD 05 REV11 (12.2); SAD 08 REV12.

### DA-16 — Fontes de entrada e cadastros institucionais

**ID** — DA-16

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — O sistema recebe formulários externos, cadastros institucionais e referências a sistemas de processos, com regras diferentes.

**Decisão** — Três tipos de entrada (SAD 02, Tabela 5.1). Do cadastro de pessoal, só identificador, nome, matrícula, função, lotação e situação e datas do vínculo, sem CPF quando a matrícula bastar. Unidades com vigência e histórico; o código do DGP não é o identificador da unidade (DA-20). Referência a SEQUOIA e DOCS com número, data de consulta e hash, sem copiar conteúdo. Integração preferencialmente por API ou camada intermediária.

**Alternativas consideradas** — Receber o cadastro funcional completo; copiar documentos do SEQUOIA e do DOCS.

**Consequências** — Requisitos RF-ING ajustados e criados; uso da estrutura real de unidades na PoC depende de decisão (AB-07).

**Documentos afetados** — SAD 02 REV10 a REV14 (5.10; 8.1); SAD 05 REV11 (12, 12.3, 13.2); SAD 06 REV07; SAD 08 REV12.

### DA-17 — Solicitações de titulares e demandas externas

**ID** — DA-17

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — Pedidos de titulares chegam por canais existentes e demandas externas (ANPD, Judiciário, controle) envolvem tratamentos inventariados.

**Decisão** — Ambas são jornadas associadas com identificador e cadeia de eventos próprios, vinculadas ao Registro sem registrar identidade de titulares ou de partes; o conteúdo fica no sistema de origem. Na PoC, entram no marco M3, apenas como vínculo; o fluxo completo de atendimento continua fora.

**Alternativas consideradas** — Tratá-las dentro da jornada de incidente; deixá-las fora da PoC.

**Consequências** — Prefixos RF-TIT e RF-DEX no SAD 02; entidades no SAD 05 (14.6).

**Documentos afetados** — SAD 02 REV11 a REV15 (5.19 e 5.20; RF-DEX-07); SAD 03 REV09 (10A); SAD 05 REV11; SAD 09 REV10 (4A.4 e 4A.5).

### DA-18 — Triagem, minuta de RIPD e decisões verificáveis

**ID** — DA-18

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — Triagem de risco, minuta de RIPD e tratamento autônomo poderiam ser lidos como decisões automáticas.

**Decisão** — A solução apresenta critérios e sugestões, exige decisão fundamentada de papel competente e registra a decisão como evento. A minuta de RIPD não substitui a aprovação.

**Alternativas consideradas** — Classificação automática de risco; minuta tratada como RIPD final.

**Consequências** — Requisitos RF-PRC-15 e RF-TRI-03 reescritos; eventos de decisão no catálogo.

**Documentos afetados** — SAD 02 REV12 a REV14; SAD 04 REV10 (16.4 a 16.6); SAD 05 REV11 (14.5).

### DA-19 — Minimização: inventário e autoria de documentos

**ID** — DA-19

**Data** — 05/10/2026

**Situação** — Vigente

**Contexto** — A Etapa C aplicou a regra de minimização também à autoria dos documentos da série.

**Decisão** — RF-MIN-01 vale para o inventário dentro do sistema (funções e categorias de agentes, não CPF ou matrícula). A autoria de documento oficial pode trazer o nome do elaborador e a função; não se registram matrícula nem CPF. O SAD 08 mantém, por decisão, apenas a função e o ato de designação.

**Alternativas consideradas** — Vedar nome do elaborador em todos os documentos.

**Consequências** — O ADR 000 e este SAD 10 trazem nome e função; o SAD 08 traz função e ato.

**Documentos afetados** — SAD 02 REV16 (RF-MIN-01); ADR 000 REV06; SAD 08 REV12; SAD 10 REV01.

### DA-20 — Código do DGP ≠ unidade_id

**ID** — DA-20

**Data** — 06/10/2026

**Situação** — Vigente

**Contexto** — O DGP (Departamento de Gestão de Pessoas) controla e altera os códigos e nomes das unidades, e a hierarquia está embutida no próprio código. A TI confirmou em 06/10/2026: o código muda quando a unidade muda de posição na hierarquia e se mantém enquanto a unidade se mantém; as reorganizações são frequentes; o DGP mantém registro das mudanças de código e estrutura; não há data de vigência formal por código. A TI não decide sucessão de unidades; apenas executa a carga da estrutura.

**Decisão** — O código hierárquico do DGP é o código oficial da unidade, mas não é o identificador estável do sistema. O sistema mantém unidade_id próprio, guarda o histórico de códigos e nomes com vigência atribuída a partir do registro de mudanças do DGP e persiste a unidade superior como relação temporal. Cada mudança gera nova vigência, preservando o unidade_id. Quando o DGP não indicar a correspondência entre código antigo e novo, a vinculação é feita por ato registrado (evento), sem inferência automática.

**Alternativas consideradas** — Usar o código do DGP como chave da unidade; derivar a hierarquia sempre do código vigente.

**Consequências** — A carga da estrutura organizacional importa também o registro de mudanças do DGP; reorganizações não reescrevem o histórico (SAD 03, seção 4.9). Ficam a validar com a TI ou o DGP: se o registro de mudanças traz a data de cada alteração e se indica a correspondência entre código antigo e novo, inclusive em desmembramento e fusão (SAD 06, seção 15). A relação de sucessão entre unidades é registrada por evento, sem inferência automática (SAD 05, seção 12.4); a competência pela sucessão de Registros LGPD e a reorganização como situação de continuidade estão em aberto (AB-08 e AB-09).

**Documentos afetados** — SAD 02 REV16 (RF-ING-03); SAD 03 REV09 (4.7 a 4.9); SAD 05 REV11 (12, 12.3 e 12.4); SAD 06 REV07 (seções 5, 6, 6.1 e 15).

### DA-21 — Comunicação com a ANPD via Encarregado

**ID** — DA-21

**Data** — 06/10/2026

**Situação** — Vigente; remissão sobre substituição atualizada em 17/11/2026 pela DA-46 e pelo encerramento da AB-10.

**Contexto** — Correspondências da ANPD (ofícios, requisições, fiscalizações) podem chegar a qualquer unidade, inclusive por protocolo no SEQUOIA. O Encarregado recebe as comunicações da autoridade nacional e adota providências (LGPD, art. 41, § 2º, II).

**Decisão** — Toda comunicação com a ANPD, enviada ou recebida, passa pelo Encarregado (LGPD, art. 41, § 2º, II; Resolução CD/ANPD nº 15/2024). Quem receber correspondência da ANPD encaminha imediatamente ao Encarregado, que a registra como demanda externa vinculada aos Registros e incidentes envolvidos. Nenhuma unidade responde à ANPD diretamente, salvo representação formal; nesse caso, o ato também é registrado no sistema.

**Alternativas consideradas** — Resposta direta pela unidade que recebeu a correspondência, com ciência posterior ao Encarregado.

**Consequências** — Novo requisito RF-DEX-07; guardrail G-32 ampliado; registro na PoC em M3 junto com RF-DEX. Atualização de Ailton, DPO, em 17/11/2026: a documentação não presume substituição do Encarregado; aplicar a DA-46. AB-10 encerrada.

**Documentos afetados** — ADR 000 REV06 (G-32); SAD 02 REV16 (RF-DEX-07); SAD 03 REV09 (6.8); SAD 09 REV10 (4A.5).

### DA-22 — Comitê Municipal de Privacidade conforme o Decreto nº 5.357/2024

**ID** — DA-22

**Data** — 06/10/2026

**Situação** — Vigente quanto à competência geral; transições críticas em aberto (AB-05). Substitui a DA-13

**Contexto** — A DA-13 baseou-se apenas no art. 2º do Decreto Municipal nº 4.822/2021 (elaborar o Programa de Governança). O Decreto nº 5.357/2024 inseriu no Decreto nº 4.822/2021 o art. 1º-A e o inciso V do art. 2º: Comitê permanente; por Secretaria, um titular ocupante de cargo efetivo e um ou dois suplentes; permanência mínima de quatro anos; atuação orientativa, consultiva e deliberativa em assuntos relacionados à LGPD. Cronologia: Decreto nº 4.818/2021 (revogado) → 4.822/2021 → 4.914/2021 (art. 1º, composição; art. 2º, Encarregado) → 5.200/2023 → 5.357/2024.

**Decisão** — O Comitê é instância colegiada permanente, com atuação orientativa, consultiva e deliberativa em assuntos relacionados à LGPD (Decreto nº 4.822/2021, com a alteração do Decreto nº 5.357/2024). Os atos municipais não especificam sua participação nas transições da Jornada; na PoC, o Comitê não conclui, suspende, reabre nem cancela Registros até regra de governança aprovada (AB-05). O Comitê não substitui a competência administrativa das unidades nem a decisão da autoridade competente sobre cada objeto. A nomeação de integrante do Comitê e a designação de ponto focal são atos distintos e independentes. Os documentos citam apenas os atos, sem nomes de integrantes.

**Alternativas consideradas** — Manter a DA-13 (papel restrito à elaboração do Programa); Comitê como instância de triagem, de aprovação de RIPD ou de decisão de casos.

**Consequências** — A DA-13 passa a substituída. SAD 03 revisa 6.11, 26, 29, RACI (coluna Comitê) e matrizes; SAD 05 modela a nomeação no Comitê como entidade própria, com ato, vigência e titular ou suplente.

**Documentos afetados** — SAD 03 REV09 (6.5, 6.11, 9, 26 e 29); SAD 05 REV11 (12.5); SAD 08 REV12 (5.2).

### DA-23 — Escopo da PoC em três camadas

**ID** — DA-23

**Data** — 06/10/2026

**Situação** — Vigente (decisão do Ailton)

**Contexto** — A PoC estava organizada em marcos sucessivos (M1a, M1b, M2 e M3), e o marco M3 reunia o FORM 1 real de ponta a ponta e todas as jornadas associadas (relato, incidente, titulares, demandas externas, triagem e RIPD), o que tornava a primeira entrega longa e misturava o núcleo com temas que dependem de integrações, prazos e regras institucionais ainda abertas.

**Decisão** — O escopo é organizado em três camadas. PoC nuclear (primeira entrega): Registro, FORM 1 sintético simplificado, versão, submissão, análise com segregação, devolução com pendência, validação, conclusão, pendência intersecretarial, eventos com cadeia de hash e reconstrução da trilha. PoC ampliada: suspensão, cancelamento, reabertura, substituição e continuidade, ingestão externa completa. Piloto: incidente e relato, titulares, RIPD, integrações reais, prazos e notificações. Os marcos M1a a M3 permanecem como unidades de execução, lidas como mapeamento das camadas, e cada cenário do SAD 04 recebe a camada em que é testado. Acréscimo de 06/10/2026 (Etapa K): o M3 divide-se em M3A, que conclui a PoC ampliada com dados sintéticos, e P1, Piloto controlado com dados reais; o P1 tem autorização própria e condições de entrada — segurança mínima para dados reais (SAD 08, coluna Piloto), matriz definitiva de competências, ambientes segregados, autenticação institucional, plano de incidente, responsáveis operacionais e critérios de encerramento.

**Alternativas consideradas** — Manter os marcos M1a a M3 como única organização do escopo; incluir incidente e titulares na primeira entrega.

**Consequências** — SAD 09 REV09 reorganiza a seção 4A sem renumerar e cria a seção 4A.6 (camada de cada cenário A1 a A36); os cenários CA-08-22 e CA-08-23 do SAD 08 passam ao Piloto; SAD 04 REV10 atualiza as seções 3 e 21.

**Documentos afetados** — SAD 09 REV10 (4A, 4A.4, 4A.6, 4A.7 e 4B); SAD 04 REV10 (3, 21 e 22).

### DA-24 — Figuras derivadas das matrizes

**ID** — DA-24

**Data** — 06/10/2026

**Situação** — Vigente

**Contexto** — Na leitura do SAD 04 REV10, as Figuras 2 e 4 divergiam das matrizes canônicas: Suspender e Cancelar não partiam de todos os estados ativos; Retomar levava a Em andamento; Reatribuir, Retomar e Cancelar da pendência tinham destinos ou origens diferentes da matriz. A Figura 1 ligava incidente, direito do titular e revisão periódica a FORMs específicos, e não ao Registro.

**Decisão** — Diagramas de estados e transições são gerados por código (Graphviz ou Mermaid, exportados em PNG) a partir das matrizes canônicas, para que o desenho derive da tabela. Em caso de divergência entre figura e matriz, prevalece a matriz. Toda figura tem texto alternativo; figura não gerada da matriz é identificada como ilustrativa na legenda.

**Alternativas consideradas** — Redesenho manual das figuras; manter as imagens anteriores com legenda indicando a divergência.

**Consequências** — SAD 04 REV10: Figuras 1, 2 e 4 geradas por código; Figuras 3 e 5 identificadas como ilustrativas; regra de prevalência na seção 2.4. Os diagramas D02-01 a D02-04 do SAD 02 continuam como desenho até revisão própria.

**Documentos afetados** — SAD 04 REV10 (2.4; Figuras 1 a 5).

### DA-25 — Comunicação de incidente por destino

**ID** — DA-25

**Data** — 06/10/2026

**Situação** — Vigente; autoridade conforme AB-04. Substitui a DA-11

**Contexto** — A DA-11 separou recomendação, decisão e envio, mas tratava a comunicação como um envio único (N5), com alerta a partir da decisão. A Resolução CD/ANPD nº 15/2024 trata de forma distinta a comunicação à ANPD e a comunicação aos titulares, e a leitura do SAD 04 REV07 mostrou a necessidade de decisão, envio e estado próprios para cada destino.

**Decisão** — A decisão registra, separadamente e com fundamentação, comunicar ou não à ANPD e comunicar ou não aos titulares. Cada envio exige decisão "sim" para aquele destino: N5A, comunicação à ANPD (pode ser preliminar, com complementação N10); N5B, comunicação aos titulares (com comprovação N11). Estados: "Em comunicação" enquanto houver envio decidido e não feito; "Comunicado" quando todos os envios decididos estiverem concluídos; "Não comunicado" quando a decisão for "não" para os dois destinos. Prazo e alerta são contados de conhecimento_em, data em que o controlador tomou conhecimento de que o incidente afetou dados pessoais; recomendação, decisão e protocolo não reiniciam nem suspendem a contagem. Mantém-se da DA-11: o Encarregado analisa e recomenda (N8) e protocola em nome do controlador, ou outro representante formalmente constituído; a unidade afetada comunica imediatamente o Encarregado e não protocola na ANPD. Autoridade: definida em ato interno; até a edição do ato, regra provisória aprovada pela governança municipal; default da PoC, o Prefeito, sem caráter de regra de produção (AB-04).

**Alternativas consideradas** — Manter a DA-11 (envio único N5, alerta a partir da decisão).

**Consequências** — N5 substituído por N5A e N5B; novos N8 a N11 e estado Em comunicação no SAD 04; registros próprios de comunicação, complementação e comprovação no SAD 05; tentativa de envio sem decisão "sim" para o destino negada e registrada no log técnico (SAD 08, CA-08-23).

**Documentos afetados** — SAD 04 REV10 (16.1, 17.2, A21, A25 a A27); SAD 05 REV11 (10, 14.4 e 16); SAD 03 REV09 (10A); SAD 08 REV12; SAD 09 REV10 (4A.6).

### DA-26 — Modelo de eventos da PoC

**ID** — DA-26

**Data** — 06/10/2026

**Situação** — Vigente para a PoC nuclear

**Contexto** — A leitura do SAD 05 REV11 encontrou falhas que bloqueavam a PoC nuclear: sequência definida só por Registro, enquanto relato e incidente têm cadeias próprias; código da transição misturado ao nome do evento; idempotência por comando_id único por evento, incompatível com comandos que geram mais de um evento; eventos de auditoria (consultas, downloads, tentativas negadas) na mesma trilha do workflow; ausência de regra de consistência entre evento e projeção; e ator sem tipo, com nomes diferentes para a mesma pessoa.

**Decisão** — (1) Cadeia por objeto: cadeia_tipo (registro, relato, incidente, demais jornadas), cadeia_id e sequencia_cadeia, com (cadeia_id, sequencia_cadeia) único e o mesmo nome no SAD 04, no SAD 05 e no SAD 08; registro_id e ciclo_id conforme cadeia_tipo. (2) Código estável: codigo_evento igual ao código do SAD 04, gravado no momento do evento, separado de tipo_evento, versao_esquema_evento e versao_regra. (3) Comando idempotente: entidade Comando; um comando produz um ou mais eventos, com ordem_no_comando; repetir o comando_id devolve o resultado original sem eventos novos. (4) Domínio × auditoria: eventos de domínio formam a trilha do workflow, com cadeia e hash; eventos de auditoria (consultar, imprimir, baixar, exportar, tentativa negada, alterar conta, papel ou matriz) têm registro próprio, sem Registro nem Ciclo. (5) Transação única: validar pré-condições, gravar evento, incrementar sequencia_cadeia, criar snapshot e atualizar projeções na mesma transação; projeções reconstruíveis, com reconstrução e comparação como teste. (6) Ator tipado: ator_id e ator_tipo (pessoa, conta de serviço, integração, sistema); decisões administrativas exigem pessoa autenticada.

**Alternativas consideradas** — Manter sequencia_registro e seq_cadeia; inferir o código pelo nome do evento; comando_id único por evento; manter consultas e tentativas negadas na trilha do workflow; atualizar projeções fora da transação do evento.

**Consequências** — SAD 05 REV11 reescreve a seção 10 e cria as seções 10.2 a 10.6, o Rascunho como entidade (7.3) e os diagramas D05-03 e D05-04; SAD 04 REV10 alinha a seção 17.1; SAD 08 REV12 adota sequencia_cadeia e separa o evento de auditoria. A estratégia definitiva para relações polimórficas fica para depois da PoC (LISTA_OBSERVACOES_POS_POC, O-06). O item 3 é detalhado pela DA-39, item 5 (pedido idempotente estrito).

**Documentos afetados** — SAD 04 REV10 (17.1); SAD 05 REV11 (7.3, 10 a 10.6, 16 a 18); SAD 08 REV12 (7.1, 7.2, 7.5, SEG-05, SEG-06, SEG-19 e SEG-36).

### DA-27 — Contrato de integridade da cadeia

**ID** — DA-27

**Data** — 06/10/2026

**Situação** — Vigente desde a PoC nuclear

**Contexto** — A leitura do SAD 08 REV12 mostrou ambiguidade no cálculo do hash (o hash_anterior era combinado à representação canônica sem regra explícita, e o payload não era guardado) e uma cadeia única SISTEMA para todos os eventos de auditoria, sem fechamento nem ligação por período e sem previsão para troca de algoritmo ou de esquema.

**Decisão** — (1) Auditoria segmentada por período: os eventos de auditoria ficam em segmentos — na proposta, mensais (por exemplo, AUDITORIA-2026-10) —, cada um com manifesto de fechamento e ligação criptográfica ao segmento anterior; a estrutura vale desde a PoC. (2) Hash SHA-256 sobre a serialização canônica JSON (RFC 8785, JCS) de um objeto que inclui hash_anterior como campo; UTF-8, chaves ordenadas, sem espaços, datas ISO 8601 UTC com precisão fixa, null explícito e lista fechada de campos. (3) O payload canônico efetivamente hasheado é armazenado com o evento, e não reconstruído depois. (4) versao_algoritmo_hash e versao_esquema_evento ficam no evento. (5) Mudança de algoritmo ou de esquema abre novo segmento, sem recalcular os anteriores.

**Alternativas consideradas** — Manter a cadeia única SISTEMA; recalcular o hash a partir dos campos sem guardar o payload; recalcular cadeias inteiras na troca de algoritmo.

**Consequências** — SAD 08 REV12: seção 7.5 reescrita, SEG-40 (segmentos) e SEG-41 (payload e versões), CA-08-29 e CA-08-30. As classes de retenção por segmento e os testes de troca de algoritmo e de esquema ficam para depois da PoC nuclear (LISTA_OBSERVACOES_POS_POC).

**Documentos afetados** — SAD 08 REV12 (7.1, 7.2, 7.5, SEG-19, SEG-20, SEG-40, SEG-41, CA-08-29 e CA-08-30); SAD 05 REV11 (10).

### DA-28 — Decisões técnicas da PoC (D-K)

**ID** — DA-28

**Data** — 06/10/2026

**Situação** — Provisória da PoC; sem valor para o Piloto (decisão do Ailton)

**Contexto** — O SAD 09 REV09 condicionava a entrada do M1a às decisões SAD09-02, 04, 06, 07, 08 e 09, todas abertas, o que impedia o início do código.

**Decisão** — SAD09-02: as matrizes do SAD 04 são a fonte canônica; na PoC viram configuração versionada (versao_regra); mudança só por revisão do SAD 04 e nova versão da configuração. SAD09-04: matriz do SAD 03 REV09 como default provisório da PoC (DA-05, DA-06), sem valor para o Piloto. SAD09-06: PostgreSQL desde a PoC nuclear (software livre, sem custo de licença, adequado a uma futura adoção pela Prefeitura); testes de concorrência e de transação única sobre ele; instância local na PoC; no Piloto, conforme a tecnologia definida pela equipe designada (PostgreSQL recomendado; outro banco, se justificado, com SQL padrão). SAD09-07: Python 3.14 (decisão do Encarregado em 08/10/2026; IMPLEMENTAR_POC_2026-10-08; antes, Python 3.12), FastAPI, SQLAlchemy, PostgreSQL, páginas renderizadas no servidor (Jinja2) e pytest; dependências travadas em arquivo de lock; código legível, comentado e em passos pequenos, também para a capacitação do Encarregado em Python. SAD09-08: evidências em diretório local fora da área da aplicação, arquivo nomeado pelo próprio hash SHA-256, metadados e vínculo no banco, nada apagado. SAD09-09: acesso técnico excepcional não se aplica à PoC (dados fictícios, operador único); acesso direto ao banco anotado no diário da PoC; regra definitiva no Piloto. A stack vale para a PoC nuclear e a ampliada. O Piloto define tecnologia própria (PHP ou outra tecnicamente justificada; PostgreSQL recomendado, outro banco se justificado, com SQL padrão), condicionada à aprovação no conjunto de testes de aceite da PoC, ao contrato OpenAPI e aos exemplos de referência do hash (SAD 09 REV09, seção de encerramento e transferência).

**Alternativas consideradas** — Manter as decisões abertas até o Piloto; banco embarcado na PoC nuclear; armazenamento de evidências no próprio banco.

**Consequências** — SAD 09 REV09: seção 33 passa a decisões e prazos por marco; condição de entrada do M1a atendida; seções 9.1, 21 e 24 registram as decisões. Nenhuma delas vale para o Piloto sem nova decisão.

**Documentos afetados** — SAD 09 REV10 (4A.1, 9.1, 21, 24, 33 e 35); SAD 03 REV09; SAD 04 REV10; SAD 05 REV11.

### DA-29 — Agente externo pessoa jurídica ou pessoa natural

**ID** — DA-29

**Data** — 06/10/2026

**Situação** — Vigente (decisão do Ailton, Etapa L)

**Contexto** — O SAD 05 admitia apenas agentes externos identificados sem dados de pessoas físicas, mas a LGPD (art. 5º, VII) admite operador pessoa natural, e há tratamentos com prestadores pessoas naturais.

**Decisão** — O agente externo pode ser pessoa jurídica ou pessoa natural (LGPD, art. 5º, VII). Da pessoa natural guardam-se apenas os dados necessários à identificação contratual, com minimização.

**Alternativas consideradas** — Manter só pessoa jurídica; registrar pessoa natural como observação textual.

**Consequências** — SAD 05 REV11 (13.6) acrescenta tipo_pessoa e a regra de minimização.

**Documentos afetados** — SAD 05 REV11 (13.6); SAD 02 (RF-AGE, RF-MIN-01).

### DA-30 — Autoridade da comunicação de incidente como atribuição configurável

**ID** — DA-30

**Data** — 06/10/2026

**Situação** — Vigente (decisão do Ailton, Etapa L); a autoridade em si continua em aberto (AB-04)

**Contexto** — A autoridade que decide comunicar incidente depende de ato interno ainda não editado (AB-04); havia risco de gravar "Prefeito" como valor fixo no banco ou no código.

**Decisão** — A autoridade que decide a comunicação de incidente é atribuição configurável, fundamentada em ato ou decisão de governança, com vigência; nunca valor fixo. A decisão registra a atribuição vigente na data. O default da PoC (o Prefeito, AB-04) é registrado como atribuição provisória, sem caráter de produção.

**Alternativas consideradas** — Valor fixo no código; campo de texto livre na decisão.

**Consequências** — SAD 05 REV11 (14.4) acrescenta a entidade Atribuição da autoridade. Não decide AB-04.

**Documentos afetados** — SAD 05 REV11 (14.4); SAD 04 REV10 (16.1).

### DA-31 — Vínculos por tipo como estratégia definitiva das relações polimórficas

**ID** — DA-31

**Data** — 06/10/2026

**Situação** — Proposta recomendada, aceita para depois da PoC nuclear; na PoC vale a validação na camada de domínio (SAD 05, 10.6)

**Contexto** — Pares objeto_tipo + objeto_id não têm integridade referencial no banco; a PoC compensa com validação na camada de domínio (DA-26). Ficou pendente a estratégia definitiva.

**Decisão** — Depois da PoC nuclear, os vínculos — evidência, pendência, relação entre objetos — passam a tabelas de vínculo por tipo, cada uma com chave estrangeira real. Nos eventos, objeto_tipo + objeto_id permanece como referência descritiva, sempre validada.

**Alternativas consideradas** — Entidade raiz "Objeto da Jornada" comum a todos os objetos (não recomendada: concentra tipos sem regra comum); manter só a validação na camada de domínio.

**Consequências** — SAD 05 REV11 (10.6) registra a proposta; a mudança física ocorre depois da PoC nuclear.

**Documentos afetados** — SAD 05 REV11 (10.6).

### DA-32 — Reabrir (G10) leva ao estado ativo recalculado

**ID** — DA-32

**Data** — 06/10/2026

**Situação** — Vigente (decisão do Ailton, Etapa L); aplicação no SAD 04 no lote 3

**Contexto** — G10 levava a Em andamento por regra fixa, mas, com ações do FORM 4 ativas, o recálculo da seção 6.3 do SAD 04 pode indicar Em execução (cenário A32).

**Decisão** — G10 (Reabrir) passa a "estado ativo recalculado (seção 6.3)", como as demais transições cujo resultado depende de outros Instrumentos ou ações.

**Alternativas consideradas** — Manter G10 → Em andamento fixo.

**Consequências** — SAD 04 revisa a matriz G, a seção 6.2, a Figura 2 e o cenário A32 (lote 3 da Etapa L).

**Documentos afetados** — SAD 04 (6.2, 7, Figura 2, A32).

### DA-33 — Escrita em sistemas externos proibida até decisão própria

**ID** — DA-33

**Data** — 06/10/2026

**Situação** — Vigente (decisão do Ailton, Etapa L)

**Contexto** — Chamada de escrita em sistema externo pode falhar de forma parcial e invisível; ainda não há desenho de confirmação e reconciliação.

**Decisão** — Até decisão registrada no SAD 10, é proibida a escrita em sistemas externos. Quando for autorizada, o desenho mínimo inclui caixa de saída transacional, operação externa idempotente, confirmação, reconciliação e compensação manual.

**Alternativas consideradas** — Permitir escrita pontual com retentativa simples.

**Consequências** — SAD 06 REV07 (8.2, 15 e diagrama D06-01).

**Documentos afetados** — SAD 06 REV07 (8.2 e 15); SAD 09 REV10 (4B).

### DA-34 — Governança da configuração do workflow na PoC

**ID** — DA-34

**Data** — 08/10/2026

**Situação** — Provisória da PoC (decisão do Ailton, Etapa L); regra do Piloto em aberto

**Contexto** — A DA-28 fez das matrizes do SAD 04 a fonte canônica e da configuração uma versão registrada (versao_regra), mas não definiu quem altera a configuração, a vigência de uma nova versão nem o que nunca pode mudar por configuração (lista de observações, O-51).

**Decisão** — Na PoC, só o Encarregado altera a configuração do workflow, sempre gerando nova versão registrada (versao_regra). A nova versão vale para Registros iniciados depois dela; Registros em andamento seguem a versão em que começaram. Segregação de funções, imutabilidade das versões submetidas e cadeia de hash nunca podem ser alteradas por configuração, só por revisão dos SADs. A regra para o Piloto fica em aberto.

**Alternativas consideradas** — Aplicar a nova versão a todos os Registros ativos; permitir alteração da configuração pela administração técnica.

**Consequências** — SAD 09 REV09 (9.1 e 33) registra a regra; o cenário POC-TS-011 testa Registros antigos ativos após mudança de versão.

**Documentos afetados** — SAD 09 REV10 (9.1, 27.2 e 33); SAD 04 REV10; SAD 05 REV11 (12.2).

### DA-35 — Encerramento da PoC, transferência institucional e independência tecnológica

**ID** — DA-35

**Data** — 08/10/2026

**Situação** — Aprovada (decisão do Ailton, Etapa M)

**Contexto** — O SAD 09 previa um Relatório de Transição da PoC para o Piloto, mas não definia como a PoC se encerra, quem recebe o código e os artefatos, o que acontece se nenhuma unidade for designada, nem se o Piloto fica preso à tecnologia da PoC (lista de observações, O-75).

**Decisão** — Um único relatório, o Relatório de Encerramento e Transferência Técnica, encerra a PoC ampliada e reúne versões, resultados, evidências, código, artefatos técnicos, limitações, dívidas técnicas e recomendações. A transferência é formalizada por termo de recebimento assinado pela autoridade da unidade recebedora, arquivado na pasta 09_PoC_e_Validacao_Tecnica, com remissão neste SAD 10; pode ser antecipada para depois da PoC nuclear por decisão registrada. Durante a PoC, o repositório fica privado na conta do Encarregado no GitHub e, na transferência, passa com o histórico à conta ou organização indicada pela unidade recebedora; titularidade, licença, credenciais a substituir e destino da massa sintética e das evidências constam do termo. Sem unidade designada, a PoC é encerrada com os artefatos preservados e o repositório arquivado, privado e sem uso operacional, sem uso com dados reais. O Encarregado não assume operação, manutenção ou desenvolvimento permanente do sistema. O Piloto pode adotar outra tecnologia (DA-28), desde que aprovada no conjunto de testes de aceite da PoC, no contrato OpenAPI e nos exemplos de referência do hash.

**Alternativas consideradas** — Manter dois relatórios (validação e transição); deixar a custódia do repositório e a continuidade sem regra até o Piloto; exigir que o Piloto use a mesma tecnologia da PoC.

**Consequências** — SAD 09 REV10 cria a seção 37, acrescenta à tabela da seção 4B as linhas de linguagem, banco, testes, documentação e resultado esperado, e renomeia o entregável para Relatório de Encerramento e Transferência Técnica; DA-28 registra a tecnologia do Piloto.

**Documentos afetados** — SAD 09 REV10 (4B, 31 e 37); DA-28.

### DA-36 — Equivalência de Registros, catálogos e canais

**ID** — DA-36

**Data** — 13/10/2026

**Situação** — Provisória da PoC (ADR 000, G-28). Vale para a PoC nuclear e a PoC ampliada; a validar antes do Piloto.

**Contexto** — O G1 (SAD 04, seção 7) exige a "inexistência de Registro equivalente ativo", mas a série não define o que torna dois Registros equivalentes, nem o que significa "ativo" para esse fim. A comparação pelo nome digitado falha ("Emissão de IPTU", "IPTU" e "Serviço de IPTU" podem ser o mesmo serviço). A pesquisa prévia na tela não impede que dois usuários, ao mesmo tempo, recebam "não encontrado" e criem dois Registros. O SAD 02 permite que vários serviços de mesma finalidade integrem um único Registro (RF-PRC-13) e que um objeto tenha tratamentos autônomos (RF-PRC-15), o que impede uma chave única por Registro. Os canais de atendimento eram tratados como "processos transversais" (RF-PRC-14), sem distinguir a estrutura operacional da porta de entrada do cidadão. A Carta de Serviços e o Plano de Classificação são referências de consulta (SAD 05, 13.4), e não fornecem identificadores para processos, atividades e canais.

**Decisão** — (1) Regra de duplicidade. Não pode haver dois Registros em situação bloqueadora que descrevam o tratamento do mesmo objeto para a mesma finalidade. Cada combinação entre objeto e finalidade pode ser assunto de, no máximo, um Registro em situação bloqueadora. Um Registro pode abranger vários objetos, e um objeto pode participar de Registros distintos quando as finalidades forem materialmente diferentes. O mesmo objeto prestado por várias Secretarias é um só Registro, com uma unidade principal e as demais como participantes (RF-PRC-06). / (2) Situação bloqueadora. Em andamento, Em validação e Em execução: bloqueiam. Suspenso: bloqueia e orienta retomada (G8) ou cancelamento (G11). Concluído: bloqueia nova criação e orienta reabertura (G10). Cancelado: permite novo Registro, com vínculo ao anterior. A inclusão de Suspenso e Concluído vai além da expressão literal "ativo" do G1 e é coerente com a preservação do mesmo Registro e de seus ciclos. / (3) Papel do objeto no Registro. PRINCIPAL: o objeto abrangido que identifica o Registro; exatamente um por Registro. ABRANGIDO: objeto cujo tratamento de dados pessoais é efetivamente descrito pelo Registro, incluindo, conforme aplicável, finalidade, operações, titulares, dados, compartilhamentos, retenção, riscos e controles. APOIO: objeto que viabiliza, executa uma função auxiliar, fornece informação ou serve de canal, mas cujo tratamento próprio não é descrito pelo Registro. RELACIONADO: objeto ligado ao tratamento apenas por contexto (dependência, precedência ou referência), sem o viabilizar nem executar parte dele. Só PRINCIPAL e ABRANGIDO entram na regra de duplicidade; APOIO e RELACIONADO podem aparecer em vários Registros. O vínculo tem situação (ativo ou encerrado) e nunca é apagado; a troca de papel é ato próprio, com justificativa e evento. / (4) Cobertura parcial e finalidade. Se o Registro trata apenas uma parte operacional de um objeto, essa parte deve ser identificada no catálogo como etapa ou atividade própria, somente quando for divisão real e estável do processo, e não para contornar a regra de duplicidade. Se a separação decorrer de finalidades distintas, poderão existir Registros diferentes para o mesmo objeto, desde que cada Registro declare a finalidade abrangida, escolhida do catálogo de finalidades: mudar o texto da finalidade não cria novo Registro. / (5) Catálogos. O catálogo operacional lista os serviços, processos e atividades da Prefeitura que tratam, ou podem tratar, dados pessoais, com as relações entre eles (o serviço depende de processos; o processo compõe-se de atividades). O catálogo de canais lista as portas de atendimento. O catálogo de finalidades lista as finalidades com identificadores canônicos. Cada item tem identificador canônico, tipo, nome oficial, relações, referência à Carta de Serviços ou ao Plano de Classificação quando houver, e situação (ativo ou desativado; nunca apagado). Os catálogos são mantidos por curadoria de papel competente, sempre com justificativa e evento; os Registros escolhem itens dos catálogos e não os digitam. O catálogo não é cópia importada da Carta de Serviços, que permanece referência de consulta (SAD 05, 13.4), e não contém dados pessoais. / (6) Canais como dimensão transversal. O canal não pertence à hierarquia serviço, processo e atividade. Relaciona-se com os serviços por associação muitos para muitos (serviço–canal: serviço, canal, vigência e observação): o serviço é atendido pelo canal; o canal atende o serviço. O canal só possui Registro próprio quando realiza tratamento autônomo (por exemplo: gestão de senhas e filas; agendamento; cadastro prévio; gravação de chamadas; videomonitoramento; identificação do atendente e do cidadão; armazenamento temporário em sistema próprio; geração de protocolo transversal); nesse Registro é PRINCIPAL e, nos Registros dos serviços atendidos, APOIO. Sem tratamento autônomo, aparece apenas como APOIO. O simples recebimento e encaminhamento de documentos do serviço não caracteriza tratamento autônomo do canal. O Registro do canal descreve só o tratamento comum e autônomo do próprio canal; o que o atendente faz com os dados do serviço pertence ao Registro do serviço. / (7) Dois controles. Bloqueio determinístico: aplica a regra do item (1) dentro da transação do G1, com trava no próprio banco de dados, de modo que dois pedidos simultâneos para o mesmo objeto e finalidade resultem em um único Registro; a pesquisa prévia na tela é auxiliar e não substitui a trava. Alerta de possível sobreposição: objetos diferentes, mas relacionados no catálogo, ou com mesma finalidade, titulares ou conjunto de dados, geram aviso para a governança avaliar; o alerta não bloqueia, não funde Registros (SAD 05, 5.3) e a avaliação é registrada como decisão, nos moldes de decidir_tratamento_autonomo (SAD 04, 16.6). O alerta por finalidade, titulares e dados depende do conteúdo do FORM 1. / (8) Resposta à tentativa de duplicação. A recusa informa o Registro existente, o objeto, o estado, a unidade, o responsável e as ações possíveis (abrir, solicitar acesso, retomar, cancelar ou reabrir, conforme o estado). A tentativa gera evento de auditoria (tentativa negada), nunca evento de domínio, pois nenhum Registro foi criado. A repetição do mesmo comando devolve o resultado original (DA-26). / (9) G1 e FORM 1. O G1 cria o Registro, o ciclo 1 e a instância do FORM 1 no estado Não iniciado; iniciar o preenchimento é comando posterior (SAD 04, cenário A1). / (10) Cenários mínimos de aceitação: 1) dois usuários tentam criar, ao mesmo tempo, Registros para o mesmo objeto e finalidade: só um é criado; 2) descrições diferentes com o mesmo objeto e finalidade: a segunda criação é bloqueada; 3) objetos com o mesmo nome, mas identificadores ou tipos diferentes: a criação é permitida; 4) Registro equivalente Suspenso: bloqueada; 5) Registro equivalente Concluído: o sistema orienta a reabertura; 6) Registro equivalente Cancelado: permitida, com vínculo ao anterior; 7) repetição do mesmo comando: resultado original, sem novo Registro; 8) duplicidade descoberta depois: o duplicado é Cancelado e vinculado ao prevalente (duplicado_de, SAD 05, 5.3 e 13.1).

**Alternativas consideradas** — Comparar Registros pelo nome digitado; confiar apenas na pesquisa prévia na tela; uma única chave de equivalência no Registro; chave composta com todos os objetos do Registro; escopo de tratamento em texto livre; manter "ativo" literal no G1 (permitindo novo Registro para objeto Suspenso ou Concluído); canal como quarto tipo de objeto; canal como processo transversal no mesmo catálogo de serviços, processos e atividades.

**Consequências** — A PoC testa a regra com catálogos fictícios: a trava experimental por objeto já está implementada (cenários 1, 2, 3 e 7); papéis, finalidade, catálogo de canais e alerta seguem em implementação; os cenários 4, 5, 6 e 8 dependem dos atos de suspender, concluir e cancelar. Os SADs afetados serão alterados em revisão consolidada depois da PoC, com base no relatório de conferência cruzada desta etapa. Ficam em aberto: quem exerce a curadoria dos catálogos, a carga inicial e a lista inicial de finalidades. O cancelamento a partir de Suspenso e Concluído, pressuposto no item 2 e no cenário 8, é regulado pela DA-37. Nos itens 1, 4, 5 e 7, 'finalidade' deve ser lida como 'contexto de atuação', e 'contexto institucional' como 'no âmbito do Município', conforme a DA-38.

**Documentos afetados** — SAD 02 (RF-PRC-05, 08, 12, 13 e 14; requisito novo de curadoria dos catálogos); SAD 03 (papel ou permissão de curadoria); SAD 04 (seção 7, G1; cenários de aceitação); SAD 05 (5.1, 5.3 e 13.4; catálogos operacional, de canais e de finalidades; relação serviço–canal; vínculo Registro–objeto com papel e finalidade); SAD 08 (eventos de auditoria da curadoria dos catálogos; tentativa negada de criação); SAD 09 (critérios de aceite da duplicidade). Origem: LISTA_OBSERVACOES_POS_POC, O-80.

### DA-37 — Cancelamento do Registro a partir de Suspenso e Concluído

**ID** — DA-37

**Data** — 13/10/2026

**Situação** — Provisória da PoC (ADR 000, G-28). Vale para a PoC nuclear e a PoC ampliada; a validar antes do Piloto.

**Contexto** — O G11 (SAD 04, seção 7) admite cancelar o Registro a partir de "qualquer estado ativo", que no catálogo do SAD 04 compreende apenas Em andamento, Em validação e Em execução. Assim, o G11 não alcança Suspenso nem Concluído, o que torna inexequíveis: a orientação da DA-36 para cancelar um Registro suspenso; o cancelamento de duplicidade descoberta depois da suspensão; e o cancelamento de duplicidade descoberta depois da conclusão (DA-36, item 2 e cenário 8). Os caminhos intermediários seriam artificiais e distorceriam a trilha: Suspenso → Retomar → Cancelar exigiria simular a superação de uma condição que pode persistir; Concluído → Reabrir → Cancelar criaria um novo ciclo apenas para cancelar um Registro reconhecidamente duplicado. A causa do cancelamento, especialmente duplicidade ou abertura indevida, pode ser descoberta em qualquer momento da vida do Registro, e o estado em que a descoberta ocorre não deve impedir a correção.

**Decisão** — (1) Nova redação do G11. Estado atual: qualquer estado diferente de Cancelado (Em andamento, Em validação, Em execução, Suspenso ou Concluído). Ação: Cancelar. Pré-condição: motivo escolhido do catálogo de motivos de cancelamento (item 3). Registro produzido: motivo, estado anterior, autor, competência, Registro prevalente ou substituto, se houver, e cancelamento derivado das pendências abertas. Próximo estado: Cancelado. / (2) Concluído → Cancelado é transição excepcional de correção administrativa. Concluído é terminal para o fluxo ordinário, mas não imutável (já admite a reabertura, G10). O cancelamento posterior deve: preservar todos os ciclos, versões e eventos anteriores; registrar que o Registro já havia sido concluído; identificar o Registro prevalente, quando houver; retirar o Registro dos indicadores de conclusão, com retificação registrada; não criar novo ciclo; e não apagar nem sobrescrever a conclusão histórica. / (3) Catálogo de motivos de cancelamento. O motivo é escolhido de lista controlada, e não digitado: duplicidade; abertura indevida; perda ou extinção do objeto; outros que a curadoria venha a incluir, sempre com justificativa e evento (DA-36, item 5). A justificativa em texto complementa o motivo, mas não o substitui. / (4) Competência. Cancelar Registro Concluído é decisão de papel competente, registrada como decisão (nos moldes de decidir_tratamento_autonomo, SAD 04, 16.6), e não pode ser praticada isoladamente por quem concluiu o Registro (segregação de funções). Para os demais estados, vale a competência já prevista no G11. / (5) Pendências. O evento derivado cancela todas as pendências vinculadas que não estejam em estado terminal, inclusive as marcadas como pós-conclusão, com referência ao evento de cancelamento do Registro. / (6) Efeito sobre a regra de duplicidade (DA-36). No cancelamento por duplicidade, os vínculos do Registro cancelado com os objetos são encerrados, e o objeto e a finalidade permanecem com o Registro prevalente: nada é liberado. Nos demais motivos, a combinação objeto–finalidade só fica livre para novo Registro depois de efetivado o G11, e o novo Registro mantém vínculo com o cancelado.

**Alternativas consideradas** — Manter o G11 restrito aos estados ativos e enfraquecer a DA-36 (item 2 e cenário 8); exigir Suspenso → Retomar → Cancelar; exigir Concluído → Reabrir → Cancelar; admitir motivo de cancelamento em texto livre ("outro fundamento").

**Consequências** — A PoC implementa o G11 com esta redação quando os atos de suspender, concluir e cancelar forem construídos, cobrindo os cenários 4, 5, 6 e 8 da DA-36 e o cancelamento a partir de Suspenso e Concluído. O SAD 04 será alterado na revisão consolidada pós-PoC (O-82). Em aberto: qual papel exerce a competência do item 4 e a regra de retificação dos indicadores (SAD 07). No item 6, 'objeto e a finalidade' e 'combinação objeto–finalidade' devem ser lidos como 'objeto e contexto de atuação', conforme a DA-38.

**Documentos afetados** — SAD 04 (seção 7, linha G11; Figura 2 e legenda, retirando a afirmação de que Cancelar parte apenas de estado ativo; seção 6.4, admitindo o cancelamento administrativo a partir de Suspenso e Concluído; regra de pendências no cancelamento; cenários de aceitação, com duplicidade descoberta nos estados ativo, Suspenso e Concluído); SAD 03 (competência do item 4); SAD 05 (catálogo de motivos de cancelamento; vínculo Registro–objeto encerrado no cancelamento); SAD 07 (retificação dos indicadores de conclusão); SAD 08 (eventos da curadoria do catálogo de motivos); SAD 09 (critérios de aceite). Remissão: DA-36, item 2 e cenário 8.

### DA-38 — Contexto de atuação, bases e conjuntos de dados e ordem de verificação da equivalência

**ID** — DA-38

**Data** — 14/10/2026

**Situação** — Provisória da PoC (ADR 000, G-28). Vale para a PoC nuclear e a PoC ampliada; a validar antes do Piloto.

**Contexto** — A DA-36 definiu a equivalência entre Registros pela combinação de objeto e "finalidade", escolhida de catálogo. Na LGPD, porém, finalidade tem sentido preciso: "realização do tratamento para propósitos legítimos, específicos, explícitos e informados ao titular" (art. 6º, I), declarada no FORM 1, com versões e validação. Usar a mesma palavra para uma classificação cadastral de prevenção de duplicidade induziria confusão entre o propósito do tratamento e o recorte administrativo em que ele é descrito. A conferência da DA-36 mostrou ainda que certos itens, como o Cadastro imobiliário, não são serviço, processo nem atividade, mas bases de dados usadas por várias atividades, e que a granularidade do catálogo de contextos permitiria fragmentar artificialmente o mesmo tratamento.

**Decisão** — (1) Contexto de atuação. O catálogo antes chamado "de finalidades" passa a ser o catálogo de contextos de atuação (códigos CTX-). Definição: contexto de atuação é a classificação cadastral que identifica o recorte administrativo e funcional no qual o tratamento associado a um objeto é descrito pelo Registro LGPD. É utilizado para distinguir tratamentos autônomos envolvendo o mesmo objeto e para prevenir Registros duplicados. Não substitui a finalidade do tratamento exigida pela LGPD, não representa a hipótese legal e não corresponde necessariamente a uma Secretaria ou unidade organizacional. Pergunta-teste: "Em qual frente concreta de atuação administrativa este objeto está sendo utilizado ou executado neste Registro?" São inadequados contextos amplos demais (Administração, Prefeitura, Interesse público, Gestão municipal, Atendimento, Cumprimento legal) e nomes de unidades. / (2) Finalidade. A palavra "finalidade" fica reservada ao sentido da LGPD (art. 6º, I), declarada no FORM 1, sempre dentro de um contexto de atuação. / (3) Regra de equivalência. Não pode haver dois Registros em situação bloqueadora (DA-36, item 2) nos quais o mesmo objeto, no mesmo contexto de atuação, apareça como PRINCIPAL ou ABRANGIDO. Na definição de equivalência, "contexto institucional" passa a "no âmbito do Município". / (4) Contexto distinto não prova autonomia. A escolha de contextos diferentes permite a análise separada, mas não prova, por si só, que existem tratamentos autônomos. A autonomia é decidida na análise do tratamento (finalidade, dados, titulares, hipótese legal, riscos; SAD 02, RF-PRC-15). / (5) Várias Secretarias. O mesmo objeto prestado por várias Secretarias é um só Registro, com uma unidade principal e as demais como participantes (SAD 02, RF-PRC-06), quando se tratar do mesmo objeto, no mesmo contexto de atuação e sem tratamentos materialmente autônomos. / (6) Famílias de contexto. O prefixo do código (TRIB, URB, ATD, RH…) forma uma família. O mesmo objeto associado a contextos diferentes da mesma família gera advertência, e não erro: "Este objeto está associado a mais de um contexto da mesma família. Confirme se ele é transversal ou escolha um contexto principal." A advertência se resolve definindo um contexto principal e os demais como secundários, marcando o objeto como transversal, registrando justificativa curta ou removendo a associação feita por engano; a resolução é registrada em evento. Entre famílias diferentes não há advertência. Só famílias expressamente configuradas como mutuamente exclusivas impedem duas classificações simultâneas. / (7) Bases e conjuntos de dados. O catálogo de bases e conjuntos de dados (banco de dados, planilha, arquivo físico ou sistema) é o terceiro eixo transversal, ao lado do catálogo operacional e do catálogo de canais (DA-36, item 6). A base ou conjunto de dados, enquanto ativo informacional, não é assunto de Registro e não entra na regra do item 3. As atividades que criam, mantêm ou utilizam a base podem constituir tratamentos documentados em Registros, ligadas à base pela relação "utiliza" (muitos para muitos). A atividade continua sendo o elemento central para finalidade, hipótese legal, titulares, compartilhamentos e retenção. / (8) Relações do catálogo operacional. O serviço "é realizado por" um ou mais processos, e o processo realiza um ou mais serviços (muitos para muitos); o processo "compõe-se de" atividades. A expressão "depende de" fica reservada a dependência efetiva (técnica, organizacional, informacional ou operacional). / (9) Ordem de verificação. Na criação do Registro (G1), depois da triagem que define o objeto (canal com ou sem tratamento autônomo, DA-36, item 6; parte operacional cadastrada como atividade, DA-36, item 4), as verificações seguem esta ordem: (a) equivalência bloqueadora (item 3), que, se presente, bloqueia e torna dispensáveis as seguintes; (b) família de contexto (item 6), que gera advertência com justificativa; (c) objetos relacionados e semelhança material (mesma finalidade, titulares ou dados), que geram alerta à governança (DA-36, item 7); (d) resultado: bloquear, criar com justificativa ou criar.

**Alternativas consideradas** — Manter "finalidade" como nome da classificação; usar a Secretaria ou unidade como critério de distinção; tratar a base de dados como objeto do catálogo operacional (serviço, processo ou atividade); bloquear o mesmo objeto em contextos da mesma família; emitir advertência também entre famílias diferentes.

**Consequências** — A PoC implementa o catálogo de contextos de atuação (fictício), o papel e o contexto de cada objeto no Registro, a trava por objeto e contexto para PRINCIPAL e ABRANGIDO, exatamente um PRINCIPAL por Registro, a advertência de família com justificativa e o catálogo fictício de bases e conjuntos de dados. A carga inicial e a curadoria dos catálogos continuam em aberto (O-80). Os SADs afetados serão ajustados na revisão consolidada pós-PoC (O-81 a O-83). O item 6 (forma 'contexto principal/secundário') e o item 9(c) (momento da comparação material) foram revistos pela DA-39, itens 2 e 4.

**Documentos afetados** — SAD 02 (RF-PRC-06, RF-PRC-08, RF-PRC-13 a 15: terminologia e condição do item 5); SAD 04 (G1: ordem de verificação, advertência e alerta); SAD 05 (catálogo de contextos de atuação, catálogo de bases e conjuntos de dados, relações "é realizado por" e "utiliza", papel e contexto no vínculo Registro–objeto; 5.3 e 13.1); SAD 08 (eventos de curadoria dos catálogos e de resolução da advertência); SAD 09 (critérios de aceite da equivalência). Remissões: DA-36, itens 1, 2, 4, 5, 6 e 7; DA-37, item 6.

### DA-39 — Decisões do Encarregado para o fechamento do M1a

**ID** — DA-39

**Data** — 14/10/2026

**Situação** — Provisória da PoC (ADR 000, G-28). Vale para a PoC nuclear e a PoC ampliada; a validar antes do Piloto.

**Contexto** — A revisão da Etapa 2c (prevenção de duplicidade no G1) e a conferência do recorte do M1a no SAD 04 e no SAD 09 mostraram pontos que o código não podia resolver sozinho: a cardinalidade do contexto de atuação; a resolução da advertência de família; o formato do código humano do Registro; a impossibilidade de comparar finalidade, titulares e dados no G1, quando o FORM 1 ainda está Não iniciado; a idempotência apenas parcial dos pedidos; a ausência de regra operacional para a pendência criada pela devolução (I6), que podia deixar o elaborador sem saída quando a resposta fosse insuficiente; e o percurso com medidas (G6), previsto no M1a sem ação obrigatória disponível.

**Decisão** — (1) Um contexto por Registro (D1). Cada Registro possui exatamente um contexto de atuação, aplicável a todos os seus objetos PRINCIPAL e ABRANGIDO. Objetos APOIO e RELACIONADO não ganham contexto próprio naquele Registro. Outro contexto exige outro Registro e análise de autonomia. A mudança posterior de contexto não é edição direta: exige comando governado, nova verificação de duplicidade e evento. O banco garante que o contexto do vínculo é sempre o do Registro. / (2) Advertência de família e transversalidade (D2). A advertência pode ser resolvida pela correção ou desistência do pedido, por justificativa específica de autonomia do tratamento ou por declaração vigente de transversalidade do objeto naquela família. A justificativa específica é apresentada pelo elaborador e vale somente para o pedido. A transversalidade é decisão da governança de proteção de dados (na PoC, o Encarregado), aplica-se à combinação objeto–família e resolve automaticamente advertências futuras enquanto vigente, sem afastar a equivalência bloqueadora nem os alertas de sobreposição. Fica retirada a forma "contexto principal/secundário" prevista na DA-38, item 6. Cada declaração registra objeto, família, decisão, justificativa, autoridade, início, término eventual e evento; o encerramento não tem efeito retroativo. / (3) Numeração anual (D4). O código humano do Registro terá o formato LGPD-AAAA-NNNNN, em que AAAA corresponde ao ano civil da criação, apurado no fuso oficial America/Sao_Paulo, e NNNNN corresponde a uma sequência reiniciada a cada ano. Reabertura e novos ciclos preservam o código original. Números atribuídos não são reutilizados após cancelamento. Lacunas por falha ou concorrência são aceitáveis. O UUID permanece como identificador técnico permanente. O banco garante unicidade do código e do par (ano, número). / (4) Sobreposição em dois momentos. No G1, a triagem é estrutural: objeto, contexto, família, relações catalogadas e bases de dados comuns. A semelhança material (finalidade, titulares, categorias de dados, compartilhamentos) é verificada na submissão do FORM 1 (I3) e a cada nova versão submetida; gera alerta à governança, examinado na análise, sem bloqueio automático. Corrige a DA-38, item 9(c), que situava essa comparação no G1. / (5) Pedido idempotente estrito (detalha a DA-26, item 3). Todo ato que altera dados exige a chave do pedido (comando_id) e grava o lacre canônico dos parâmetros. A mesma chave com os mesmos parâmetros devolve o resultado original, idêntico, com indicador separado de reexecução, sem criar eventos. A mesma chave com parâmetros diferentes é recusada como reutilização indevida e registrada na auditoria. Pedidos simultâneos com a mesma chave são resolvidos pelo banco: um vence, o outro recebe o resultado do primeiro. Recusas do banco são interpretadas pelo nome da regra violada; qualquer recusa não prevista é tratada como defeito, e não como decisão de negócio. / (6) Devolução e pendência (Opção A). A pendência criada automaticamente por I6 (P1, na mesma transação) é dirigida à unidade responsável pelo preenchimento e é bloqueante para nova submissão; não bloqueia o ajuste do rascunho. O elaborador assume (P2), corrige e responde (P3); P3 registra o lacre (hash) do rascunho corrigido e bloqueia novas alterações enquanto a pendência estiver Respondida. A pessoa autorizada da instância de validação examina a resposta: se suficiente, aceita (P4), encerrando a pendência; se insuficiente, devolve a mesma pendência (P5), com motivo obrigatório, e o elaborador a retoma (P6), o que desbloqueia o rascunho para nova correção e nova resposta. P5 não cria outra pendência. Somente após P4 o elaborador pode executar I3, e somente se o lacre do rascunho for igual ao aceito; havendo diferença, I3 é negado e exige nova resposta. P4 não valida a nova versão: a validação continua sujeita a I13 e I5. As respostas anteriores permanecem no histórico. / (7) Escopo de pendências no M1a. O M1a implementa P1 a P4 como fluxo básico e P5 e P6 apenas no percurso restrito da pendência criada por I6. A aplicação geral de P5 e P6 e os atos P7 a P9 permanecem no M1b; o núcleo de P10 nasce no M1b.1, com o cancelamento do Registro. / (8) Percurso com medidas no M1a. O M1a cria uma ação obrigatória sintética mínima (estado, responsável, evidência e vínculo com Registro, ciclo e Instrumento) e exercita I5 → G4 → Em execução → conclusão da ação → G6 → Concluído. O FORM 4 completo não integra o M1a. A mesma ação é reutilizada no M1b.2 (cenário A32).

**Alternativas consideradas** — Contexto por objeto; contexto principal e secundário; transversalidade global ou por Registro; sequência global do código com ou sem o ano; comparação material no G1; repetição do pedido respondida com mensagem genérica; Opção B (reenvio liberado após P3, com P4 exigido antes de I5), afastada porque deixaria pendência sem encerramento quando a nova versão também fosse insuficiente; Opção A sem P5/P6, afastada porque deixaria o elaborador sem saída diante de resposta insuficiente; percurso com medidas apenas no M1b.

**Consequências** — A PoC implementa os itens 1 a 5 na Etapa 2d (base da PoC lgpd_poc_v2, testes automatizados em base própria) e os itens 6 a 8 no núcleo do M1a. O SAD 04 é ajustado na REV12 (Etapa Q) para G1, G4, G5, eventos derivados, concorrência no I13, pendência criada por I6 e cenário A2. O SAD 09 é ajustado para o recorte do M1a. Permanecem em aberto as regras de prazo (O-84), condição de entrada do M1b.1.

**Documentos afetados** — SAD 02 (RF-PRC: contexto e papéis; revisão pós-PoC); SAD 03 (competência da governança para transversalidade); SAD 04 (seções 6.3, 7, 8.3, 11, 22); SAD 05 (contador anual, vínculo Registro–objeto, transversalidade, hash do rascunho na pendência); SAD 08 (lacre dos parâmetros do pedido; auditoria da reutilização de chave); SAD 09 (4A.1, seção 14, cenário A2). Remissões: DA-26, item 3; DA-36; DA-38, itens 6 e 9.

### Atualização de novembro de 2026

As decisões abaixo registram a deliberação de Ailton, DPO. Vigência da regra não significa aceite da interface nem implantação em produção. Lote 8 aprovado na vistoria de 17/11/2026 e integrado ao main (17338bf). Os limites do G-28 permanecem.

### DA-40 — APA como gestor da fila

**ID** — DA-40 (P36)

**Data** — 15/11/2026

**Situação** — Vigente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Tornar explícita a responsabilidade pela distribuição do trabalho na unidade.

**Decisão / regra** — O APA da unidade indica e reatribui o AAL; o acúmulo com o papel de gestor da fila é permitido.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Atribuição e reatribuição exigem confirmação e registro de autoria, data e motivo, sem afastar habilitação, escopo de unidade nem segregação por pessoa. Complementa a DA-05 no FORM 2.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-41 — Guarda documental em definição institucional

**ID** — DA-41 (P69)

**Data** — 16/11/2026

**Situação** — Vigente até a definição do grupo de trabalho

**Decisor** — Ailton, DPO

**Contexto / motivo** — A ausência de tabela aprovada não é falha da Secretaria.

**Decisão / regra** — Disponibilizar o estado “Aguarda definição institucional (grupo de trabalho de guarda documental)”, sem criar pendência para a origem por esse motivo.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Indicar a situação da guarda na grade. A etiqueta textual [Guarda] está disponível. Lote 8 aprovado na vistoria de 17/11/2026 e integrado ao main (17338bf). Nenhum prazo é inventado.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-42 — Manifestação consultiva de ofício do DPO

**ID** — DA-42 (P74)

**Data** — 16/11/2026

**Situação** — Vigente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Permitir orientação sem depender de consulta anterior.

**Decisão / regra** — O DPO pode registrar manifestação por iniciativa própria, de caráter consultivo.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Preservar autoria, data e hora; a manifestação não transfere competência decisória nem permite ao DPO preencher as respostas do AAL.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-43 — Conferência por pessoa distinta do apresentante

**ID** — DA-43 (P79 + P96)

**Data** — 16–17/11/2026

**Situação** — Vigente; exceção em deliberação

**Decisor** — Ailton, DPO

**Contexto / motivo** — Preservar a segregação por identidade institucional estável, inclusive no acúmulo de papéis (G-17).

**Decisão / regra** — Quem apresenta o FORM 1 não o confere. Se o APA titular apresentou, confere o APA suplente habilitado. Sem suplente habilitado, mostrar “Aguardando definição de quem fará a conferência”.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Recusar autoconferência. A dispensa da conferência foi descartada. A alternativa de segundo ato explícito pela mesma pessoa permanece em deliberação e não está autorizada.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-44 — Combinações de respostas na análise jurídica

**ID** — DA-44 (P83)

**Data** — 17/11/2026

**Situação** — Vigente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Distinguir ausência de informação de dúvida de enquadramento.

**Decisão / regra** — “A confirmar” só pode ser selecionada sozinha. “Requer análise jurídica” pode aparecer sozinha ou com hipóteses candidatas, nunca junto de “A confirmar”.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — O servidor recusa combinações inválidas e a F2-3.4 apresenta alerta. A regra não homologa hipóteses jurídicas.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-45 — Contagem de perguntas ativas

**ID** — DA-45 (P86)

**Data** — 17/11/2026

**Situação** — Provisória até a decisão da R17

**Decisor** — Ailton, DPO

**Contexto / motivo** — A obrigatoriedade por pergunta permanece em deliberação (R17).

**Decisão / regra** — A situação do bloco usa N de M perguntas ativas; excluir condicionais bloqueadas, comentários e o item automático em leitura. Centralizar o cálculo numa única regra do domínio.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Exibir “Ainda não preenchido”, “Em preenchimento · N de M perguntas ativas” ou “Todas as perguntas ativas respondidas”. Contagem não autoriza conclusão nem homologação.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-46 — Designação formal e painel do DPO

**ID** — DA-46 (P91)

**Data** — 17/11/2026

**Situação** — Vigente; responsável pelo cadastro em produção pendente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Vincular o acesso à designação institucional, sem concedê-lo por rótulo genérico de perfil.

**Decisão / regra** — Não há substituto nem suplente do DPO. A designação do Encarregado depende de ato formal publicado no Diário Oficial; a documentação não presume substituição. O acesso ao painel depende da designação formal registrada, com uma designação vigente.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Painel exclusivo do DPO designado. Quem cadastrará a designação em produção ainda precisa ser definido. A AB-10 fica encerrada por decisão de Ailton, DPO, em 17/11/2026, com remissão a esta DA-46. Não se presume substituição nem se cria ato municipal.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-47 — Saída do bloco com alterações

**ID** — DA-47 (P101)

**Data** — 17/11/2026

**Situação** — Vigente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Evitar perda involuntária de preenchimento (G-14).

**Decisão / regra** — Ao sair com alterações, oferecer “Salvar e continuar”, “Sair sem salvar” e “Voltar ao bloco”; disponibilizar “Descartar alterações”.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — A escolha explícita controla o salvamento ou descarte; salvar não equivale a concluir o Instrumento.

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-48 — Lista automática de informações a confirmar

**ID** — DA-48 (C1)

**Data** — 17/11/2026

**Situação** — Vigente; classificação de impeditivos em deliberação

**Decisor** — Ailton, DPO

**Contexto / motivo** — Dar visibilidade às informações ainda não confirmadas sem transformar o levantamento em decisão automática.

**Decisão / regra** — F2-14.2 e F2-14.8 mostram a quantidade e a lista dos itens marcados “A confirmar”, agrupados por bloco e com link para cada pergunta. A resposta Sim/Não da F2-14.8 cabe ao AAL, sem pré-marcação.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — O sistema não classifica nenhum item como impeditivo e não libera conclusão institucional. Lote 8 aprovado na vistoria de 17/11/2026 e integrado ao main (17338bf).

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-49 — Consulta da origem nas perguntas de abertura

**ID** — DA-49 (D6)

**Data** — 17/11/2026

**Situação** — Vigente

**Decisor** — Ailton, DPO

**Contexto / motivo** — Permitir que o AAL confira a origem preservada antes de responder.

**Decisão / regra** — F2-4.1, F2-5.1, F2-6.1, F2-7.1, F2-8.1, F2-9.1 e F2-11.1 mostram a informação correspondente da apresentação do FORM 1 em análise, sem pré-marcar a resposta.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Quando não houver resposta na origem, informar essa ausência. Lote 8 aprovado na vistoria de 17/11/2026 e integrado ao main (17338bf).

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-50 — Condições do bloco 10

**ID** — DA-50 (D7)

**Data** — 17/11/2026

**Situação** — Vigente; incorporar na próxima revisão do Mestre

**Decisor** — Ailton, DPO

**Contexto / motivo** — Divergência aprovada em relação ao Mestre: as condições aprovadas não constam integralmente na fonte vigente.

**Decisão / regra** — D7 — condição acrescentada pelo DPO em 17/11/2026: F2-10.3 e 10.4 dependem de F2-10.2 = Sim; F2-10.9.7 a 10.9.10 dependem de F2-10.9.6 = Sim. Incorporar na próxima revisão do Mestre.

**Alternativas consideradas** — Não se registra deliberação de alternativa adicional. As opções descartadas e as que continuam pendentes constam expressamente da regra e de seus efeitos.

**Consequências / efeito no sistema** — Bloquear perguntas inativas na tela e no servidor (409), excluindo-as da contagem de perguntas ativas. Lote 8 aprovado na vistoria de 17/11/2026 e integrado ao main (17338bf).

**Documentos afetados** — Cartilha, README e documentação de operação. SAD 10; atualização aprovada em 17/11/2026. ADR 000 consultado como referência, não alterado.

### DA-51 — Segregação do AAL no mesmo Registro

**ID** — DA-51 (P41)

**Data** — 17/11/2026

**Situação** — Decidida; implementada na branch correcoes-lote9 em 18/11/2026, aguardando vistoria e merge

**Decisor** — Ailton, DPO

**Contexto / motivo** — Segregação: quem atesta os fatos não valida a legitimidade; complementa a G-17. Perfil: o APA, em regra, delega o levantamento ao ARP; o AAL traz a leitura técnica e jurídica e, com o DPO, atua quando há problema.

**Decisão / regra** — Quem apresentou ou confirmou a versão do FORM 1 não pode ser AAL do mesmo Registro. O APA não pode indicar a si mesmo como AAL. Sem outro servidor habilitado, o estado será “Aguardando definição de quem fará a análise”.

**Alternativas consideradas** — Não autorizar autoindicação nem flexibilizar a segregação por falta de outro servidor habilitado.

**Consequências / efeito no sistema** — Implementação do Lote 9 no domínio e na seleção de candidatos, com recusa no servidor e estado informativo nas filas e no painel do DPO. Preservada a segregação por pessoa canônica já vigente. Não confundir a definição de quem fará a análise com a definição de quem fará a conferência do FORM 1.

**Documentos afetados** — SAD 10 e Cartilha, seção 3.1. ADR 000 consultado como referência à G-17, não alterado. Código na branch correcoes-lote9; aceite humano pendente.

### Registro macro — reafirmação de 15/11/2026

Ailton, DPO, reafirmou a minimização já registrada na DA-17 (conteúdo individual permanece no sistema de origem) e na DA-19 (inventário por funções e categorias). Casos individuais não entram no sistema; o Registro apenas pode mencionar sua existência. Situação: vigente. Motivo: evitar transformar o inventário em cadastro de pessoas ou de expedientes. Efeito: orientar o preenchimento macro, sem nova ficha DA que duplique essas decisões.

### 3.1 Requisitos para a transferência à TI

Complemento da DA-35 e remissão à seção 37 do SAD 09. Registro de 17/11/2026, por Ailton, DPO. São condições a verificar para produção; não constituem autorização de implantação.

PROD-01 — Identidade. Em produção, o acesso será por autenticação real; conta_id é exclusivo da demonstração. Motivo: impedir simulação de identidade no ambiente institucional. Conferir autenticação, autorização e identificação estável antes da entrada em produção.

PROD-02 — Auditoria concorrente (P81). A numeração sequencial dos eventos da cadeia de auditoria deve permanecer sem lacunas nem duplicidades sob acessos simultâneos. Motivo: preservar rastreabilidade. Verificar atomicidade e concorrência no ambiente de destino. Não altera a numeração anual do código do Registro da DA-39, item 3, que admite lacunas.

PROD-03 — Designação do DPO. Definir a autoridade ou função responsável pelo cadastro da designação em produção. Situação: pendente de definição; não atribuir essa competência por configuração. Conferir o procedimento e seu registro antes da entrada em produção.

Limites de texto e de conjuntos repetíveis não recebem decisão nesta revisão: aguardar a deliberação D5. As decisões D1–D5 e D8–D13 não são resolvidas por este complemento.

## 4 Decisões em aberto

Os itens em aberto não devem ser resolvidos por interpretação nos SADs. A AB-10 é mantida nesta lista apenas como registro encerrado, com remissão à DA-46.

**ID** — Decisão pendente | Documentos afetados

**AB-01** — Substituir "objeto da Jornada" por "unidade de análise". Se aprovado, começa pelo SAD 01 e pelo ADR 000 (G-30). | SAD 01; ADR 000; SAD 02 (seção 8); SAD 05

**AB-02** — Tratar a saída não programada como quinta situação de continuidade. | SAD 04 (14.1 e 20); SAD 02 (seção 8)

**AB-03** — Acesso da Controladoria ao vínculo com a apuração disciplinar. Default da PoC: não acessa, salvo designação. | SAD 03 (10A e 26); SAD 08 (5.2)

**AB-04** — Ato interno que define a autoridade que aprova a comunicação de incidente, considerando o prazo de três dias úteis contados do conhecimento pelo controlador. Autoridade definida em ato interno. Até a edição do ato, aplica-se regra provisória aprovada pela governança municipal; o default da PoC é o Prefeito, sem caráter de regra de produção — não é conclusão extraída da LGPD nem da Resolução CD/ANPD nº 15/2024. A validar com a Secretaria de Assuntos Jurídicos. O ato deve tratar de: (1) autoridade decisória; (2) substituição em ausências; (3) fluxo de aprovação emergencial; (4) prazo interno para decidir; (5) comunicação preliminar; (6) documentação da decisão de não comunicar. | SAD 03 (6.8, 10A e 26); SAD 04 REV10 (16.1 e 20)

**AB-05** — Papel do Comitê Municipal de Privacidade em transições críticas (concluir, suspender, reabrir, cancelar). | SAD 03 (6.11 e 26); SAD 08 (D-08-05)

**AB-06** — Numeração da seção 5.18 (Compartilhamento) do SAD 02. | SAD 02

**AB-07** — Uso de nomes e códigos reais das Secretarias na estrutura de unidades da PoC (SAD 02, seção 8.1, remete a decisão a este SAD 10). Incluído para registro; não decidido. | SAD 02 (8.1); SAD 09

**AB-08** — Reorganização de unidades (mudança de código, extinção, desmembramento, fusão) como situação de continuidade. Distinta da AB-02 (saída não programada de pessoa). | SAD 02 (5.4B); SAD 04 (14.1)

**AB-09** — Competência pela sucessão de Registros LGPD em reorganização. Default provisório proposto, por analogia com a prática do Protocolo no SEQUOIA: unidade extinta sem sucessora passa Registros, pendências e participações à unidade superior, com alerta "sucessão pendente", até decisão competente. Pendência ligada a prazo da ANPD não espera a sucessão: o Encarregado aciona de imediato a unidade superior ou sucessora. Proposta de 06/10/2026, a validar: o Registro LGPD acompanha a competência definida na Lei Municipal nº 4.148/2023 (Anexo II) e alterações; a vigência da mudança vem do ato; a transferência à unidade superior, com alerta "sucessão pendente", só se aplica quando o ato não indicar a sucessora. | SAD 03 (18); SAD 05 (12.4); SAD 06 (6.1)

**AB-10** — Encerrada por decisão de Ailton, DPO, em 17/11/2026. Não há substituto nem suplente do DPO. A designação do Encarregado depende de ato formal publicado no Diário Oficial; a documentação não presume substituição. | SAD 10 (DA-46); remissão da DA-21 atualizada. SAD 03 não alterado nesta revisão.

### AB-11 — D-FORM3-DPO

Data: 15/11/2026. Proponente e responsável pela deliberação: Ailton, DPO. Situação: em deliberação; não é regra implementada.

Proposta: DPO consultivo no FORM 3, com catálogo-base de riscos e manifestação obrigatória nos níveis Alto/Crítico; o DPO não pontua nem aceita risco.

Motivo: esclarecer a participação consultiva na avaliação de riscos sem atribuir aceitação do risco ao DPO. Efeito pretendido: consulta e registro de manifestação, condicionados à aprovação. Alternativa: manter a proposta sem efeito no sistema até decisão. Documentos afetados: SADs 02, 03, 04 e 09, Cartilha e materiais do FORM 3.

### AB-12 — Requisitos de habilitação do AAL

Data: 17/11/2026. Registro solicitado por Ailton, DPO. Situação: em deliberação.

Requisitos de habilitação do AAL (formação jurídica, capacitação em LGPD, outros): em deliberação; a PoC não verifica requisitos. O perfil recomendado é orientação, não requisito formal aprovado.

Motivo: distinguir recomendação de perfil e critérios institucionais de habilitação. Efeito: nenhum requisito novo é implementado no sistema. Documentos afetados: SAD 10 e Cartilha, seção 3.1; demais SADs e ADR 000 não alterados.

## 5 Referências

ADR 000 — Princípios e Guardrails do Projeto, REV07.

SAD 01 REV06; SAD 02 REV17; SAD 03 REV11; SAD 04 REV12; SAD 05 REV11; SAD 06 REV07; SAD 08 REV12; SAD 09 REV12; Cartilha LGPD vigente.

Lei nº 13.709/2018 (LGPD); Resoluções CD/ANPD nº 15/2024 e nº 18/2024.

Decretos Municipais nº 4.818/2021 (revogado), nº 4.822/2021, nº 4.914/2021, nº 5.200/2023 e nº 5.357/2024; Lei Municipal nº 4.148/2023.


## Registro de execução das decisões do Lote 9 — 18/11/2026

Decisor: Ailton, DPO, instruções de 18/11/2026 às 07h43. Escopo demonstrativo, branch `correcoes-lote9`; sem aprovação de produção e sem merge até autorização própria. O documento restrito de origem permanece na entrega local.

- **DA-51:** regra implementada, preservando a separação entre análise do FORM 2 e conferência do FORM 1 (P79). Nenhuma exceção por falta de agente foi criada.
- **D1:** os 18 complementos aprovados admitem salvamento parcial. Enquanto faltarem, exibem orientação, não contam como pergunta respondida e impedem registrar a consolidação demonstrativa. Isso não classifica respostas “A confirmar” como impeditivas. Conclusão institucional permanece bloqueada.
- **D3:** alternativas mutuamente exclusivas são verificadas no domínio dos dois FORMs e na interação. Identificadores e respostas históricas permanecem intactos.
- **D9/D2:** distinguir análise jurídica e técnica onde a classificação é clara. Casos mistos são relacionados no relatório local para decisão. Atalhos apenas preparam consulta; o AAL decide e confirma seu envio.
- **D8/D10/D11:** alterações de apresentação aprovadas, sem renumerar campos nem estender selo jurídico à grade inteira por inferência.
- **C8:** seleção de Secretaria da lista existente e função em texto curto; não foi inventado cadastro institucional de funções.
- **D5 — limites provisórios:** 99 conjuntos e limites de texto curto de 200, longo de 1000 e comentário de 2000 caracteres são limites provisórios da PoC, não regras de produção. Exceções explícitas do catálogo continuam preservadas. Este registro não altera código nem aprova limites definitivos.
- **D12:** fontes oficiais da ANPD propostas somente no relatório local; inclusão nas telas depende de aprovação de Ailton.

U1/U2/U3 consolidam apresentação e identificação demonstrativa. Não alteram autoria persistida, efeitos dos atos ou permissões. Cartilha, palestra, catálogo privado e Documento-Mestre não foram modificados por este registro.


## Complemento D9 — decisão de Ailton, DPO, 18/11/2026, 09h40

Análise jurídica quando a pergunta exige interpretar norma ou fundamento; análise técnica quando exige conhecer o processo, os dados ou os sistemas. Classificação técnica: F2-2.5, F2-2.6, F2-2.8, F2-2.9, F2-2.9.3, F2-8.4, F2-8.5, F2-11S.8 e F2-14.5. Classificação jurídica: F2-4.5, F2-6.6, F2-7.4.2.1 e F2-11.7. Preservar códigos salvos; alterar somente rótulos e destinos oferecidos pelo atalho, mantendo o DPO. O atalho prepara a consulta; não a envia automaticamente.
