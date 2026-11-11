# FORM 2 REV17.0 — Organização funcional e contrato conceitual candidato

**Produto 2 — INSTRUÇÃO_FORM02_02 — 06/11/2026**  
**Identificação proposta:** `F2-REV17-PLANEJAMENTO-v0.1`.  
**Situação:** candidato documental para avaliação. Não é contrato executável, número de contrato de persistência, definição aprovada de permissões ou autorização de implementação.

## 1. Resultado e limites

A [matriz completa](FORM2_REV17_MATRIZ_CORRESPONDENCIA_CANDIDATA.md) preserva **245 perguntas e subperguntas**, em 14 blocos de origem, incluindo `9W`, `11S` e `12A`. Cada enunciado possui classificação funcional, objetivo, correspondência justificada e área proposta. A contagem inclui os identificadores originais, não orientações editoriais ou alternativas sem ID.

Recomenda-se organizar o trabalho em **A — Tratamento analisado**, **B — Orientação para análise**, **C — Análise de legitimidade** e **D — Manifestação e encaminhamento**. São áreas funcionais, não quatro novos FORMs nem obrigação de quatro páginas. Os 14 blocos do mestre permanecem referências editoriais, sem reprodução automática como telas.

Esta entrega cria somente os quatro documentos de planejamento. Não altera o catálogo ou contrato do FORM 1, a matriz vigente, a Cartilha, código, banco, permissões ou submissão. Os FORMs 3 e 4 são apenas destinos conceituais de encaminhamento.

## 2. Fontes localizadas e versões efetivamente examinadas

### 2.1 Fontes externas ao checkout

Diretório **SAD**: `D:/Ailton/PMH/Cidades_Inteligentes/LGPD/Solution_Architecture_Document_(SAD)_Documento_de_Arquitetura_da_Solução/`.

O índice `INDICE_REVISOES_VIGENTES_2026-10-14_v2.docx` confirma as revisões abaixo para a série SAD. Ele é datado de 14/10/2026: não foi usado para inferir aprovação de decisões posteriores da PoC. O Documento-Mestre e a Cartilha foram identificados também pelo conteúdo interno, não somente pelo nome do arquivo.

| Sigla | Localização e versão lida | Uso nesta proposta |
|---|---|---|
| M17 | `D:/Ailton/PMH/Cidades_Inteligentes/LGPD/curso_senac_lgpd/FORMS/DOCUMENTO_MESTRE_FORMS_LGPD_HORTOLANDIA_REV17.0_2026-09-23.docx` — REV17.0, 23/09/2026 | Todas as perguntas e orientações do FORM 2, parágrafos XML 618–897; papéis dos quatro instrumentos e fronteiras com FORMs 3/4 |
| S02 | SAD + `02_Requisitos_Funcionais/SAD_02_REQUISITOS_FUNCIONAIS_REV17.docx` | RF-WFL-01 a 14: estados separados, encaminhamentos, responsabilidade, concorrência; distinção de tratamento autônomo |
| S03 | SAD + `03_Atores_Papeis_e_Permissoes/SAD_03_ATORES_PAPEIS_E_PERMISSOES_REV11.docx` | §§11.2–13: instância validadora provisória, competência, escopo, identidade, segregação; manifestação não equivale a validar versão |
| S04 | SAD + `04_Workflow_e_Estados/SAD_04_WORKFLOW_E_ESTADOS_REV12.docx` | §§8, 12.1–12.3: estados do instrumento, impedimentos, precedência e responsável pela próxima ação |
| S05 | SAD + `05_Modelo_de_Dados_e_Identificadores/SAD_05_MODELO_DE_DADOS_E_IDENTIFICADORES_REV11.docx` | §7: Instrumento, definição, rascunho, versão, análise; §8: execução de ações do FORM 4 separada do snapshot |
| S10 | SAD + `10_Decisoes_de_Arquitetura/SAD_10_DECISOES_DE_ARQUITETURA_REV16.docx` | DA-01/02/04, decisões do recorte nuclear e M1a: mesmo Registro, nomenclatura, evolução incremental e preservação do núcleo |
| C14 | SAD + `11_Cartilha_Apresentacoes/CARTILHA_LGPD_REV30_14_CONSOLIDADA_SAA_05-11-2026.docx` — capa REV30.14, 05/11/2026, “Versão para validação editorial” | Referência editorial/conceitual: finalidade, agentes, SAA/APA/ARP, consentimento, crianças, publicação, terceiros, direitos, guarda e riscos. Não aprova contrato ou competência |

Impressões SHA-256 dos documentos lidos, para identificação reprodutível da fonte:

| Fonte | SHA-256 |
|---|---|
| M17 | `c2c0b1f5386898e15d3575a1bac222bc588eb3cd3ecbc13eafc322082d5a8c52` |
| Índice SAD | `68b0b7d9d0d7ab3dbfefc21733b499e537a91e8ce320b9346077bbdcb7449f17` |
| S02 | `597f151e563bc4928823d1482cb96e9f524984e83e055d5e904128f12f68fefa` |
| S03 | `f2b4bad2f4f750fb1c7541efef1dedada98f0638895a5edc4bbcdc0ecfd05200` |
| S04 | `18bbdae5454ede6d20299a26a9d09c57cd6b66d659c967edc7dde4fc993710b4` |
| S05 | `1f57ecf419a1e2b58baa25e84c3a6a94271ef2785145f23bc6a3d5ca9695b558` |
| S10 | `5a444e5516c6cd5e3d9b36da97352fe52157dcf81524ab3e3c0ca807c5bd9d99` |
| C14 | `3bc5df4c2751fd2f24ec9abdded59e436d00aaf893b6b411aa6c364d801baadf` |

As referências legais de M17 e C14 foram identificadas como conteúdo das fontes. Este estudo não certifica sua vigência jurídica nem substitui exame pela área competente. Não foram criados links oficiais, âncoras ou páginas presumidas.

### 2.2 Fontes do repositório e estado observado

Base local: `main`, commit `664f4b3ca97f95139fdb0f66abf15cc18aac58a4`, nove commits à frente da **referência local** `origin/main`. Não houve consulta remota, commit ou push nesta tarefa. Havia seis arquivos modificados antes da análise; foram considerados como estado local e preservados, sem publicação implícita de seu conteúdo.

| Fonte | Conteúdo utilizado e limite |
|---|---|
| [AGENTS.md](../../AGENTS.md) e [contexto](../contexto/context.md) | Visão de quatro instrumentos, escopo atual, dados fictícios, não inferir competências nem liberação |
| [README](../../README.md), seção “Integração dos quatro FORMS” e registros dos incrementos/extensões | Diretrizes atuais, separação de conferência interna e submissão; referência à liberação do FORM 2 ainda pendente de definição |
| [Contrato candidato 3](../arquitetura/CONTRATO_FORM1_INTEGRAL_REV13_CANDIDATO.md) | Fronteira nuclear/Integral e 128 IDs. Sua abertura ainda registra implementação parcial dos Blocos 1–5: é texto histórico desatualizado, não evidência de que os demais blocos estejam ausentes hoje |
| [Catálogo F13](../../app/catalogos/form1_rev13.csv) | Enunciados e IDs originais do FORM 1; mapeamento sem equivalência por número ou nome |
| [Extensão MEDIDAS](../arquitetura/EXTENSAO_FORM1_REV13_MEDIDAS_V1.md) e [GUARDA](../arquitetura/EXTENSAO_FORM1_REV13_GUARDA_V1.md) | Definições optativas, adoção explícita e leitura histórica; fontes declarativas em `app/catalogos/form1_rev13_ext_medidas_v1.json` e `form1_rev13_ext_guarda_v1.json` |
| [Modelos](../../app/modelos.py), `VersaoForm1Integral`, `ConferenciaInternaForm1Integral`, `HistoricoConferenciaForm1Integral` | Snapshot técnico separado do núcleo, autoria, lacre e atos internos; **não** equivale a versão institucionalmente submetida |
| [Preparação de snapshot](../../app/submissao_form1_integral.py) | Preparação técnica interna, sem habilitação da submissão |
| [Instrumentos nucleares](../../app/instrumentos.py) | Infraestrutura de comandos, versões e análise; ainda importa validador do FORM 1 sintético. Não é adaptador pronto para FORM 2 |
| [Decisões consolidadas](CONSOLIDACAO_FORM1_DECISOES_PENDENCIAS_2026-10-31.md), [fluxo 8T](FLUXO_CONCLUSAO_FORM1_INTEGRAL_8T.md) e [inventário FORMS01_07](BACKLOG_AJUSTES_POC_AMPLIADA.md) | Diretrizes e limites anteriores; não confundir plano institucional do 8T com atos preparatórios efetivamente implementados |

Não foi localizado no repositório um catálogo executável ou implementação específica do FORM 2. `Instrumento`, `RascunhoInstrumento`, `VersaoInstrumento` e `AnaliseInstrumento` oferecem base genérica, mas não comprovam campos, permissões, rotas ou testes próprios do FORM 2. Este candidato não altera essa situação.

## 3. O que está assentado e o que permanece proposta

| Natureza | Diretriz |
|---|---|
| Decisão/limite vigente da PoC | Preservar Registro LGPD, contrato nuclear 2, versões e respostas do FORM 1; não implementar outros instrumentos sem autorização |
| Limite vigente | Conferência do APA é preparatória, sem aprovação jurídica ou liberação automática do FORM 2; SAA não cria perfil de acesso |
| Diretriz arquitetural documentada | Quatro instrumentos no mesmo Registro, versões e autoria próprias, referências históricas e rastreabilidade |
| Hipótese expressamente solicitada para este estudo | FORM 2 aponta para snapshot imutável específico do FORM 1, consulta fatos sem cópia desnecessária, identifica lacunas e não decide juridicamente sozinho |
| Proposta deste documento | Estrutura A–D, representação por operação, envelope conceitual, critérios de revisão e organização das perguntas |
| Dependente de decisão | Marco de entrada, atores competentes, matriz de permissões, obrigatoriedade, catálogos de respostas, conclusão e revisão após mudança do FORM 1 |

Há uma diferença substantiva de marco: README descreve liberação após **submissão válida** do FORM 1; S04 §12.2 prevê submissão do FORM 2 após FORM 1 **Validado**, admitindo rascunho antecipado como flexibilização ainda a validar. O 8T descreve conclusão institucional futura, enquanto a aplicação realiza conferência interna preparatória. Não selecionar um desses marcos silenciosamente. Ver D01 no Produto 3.

Também há diferença de governança: M17 fala em validação por participação e fila de cada unidade; S03/S02 distinguem manifestação em pendência de validação de versão, com edição limitada à própria manifestação. A implementação de fluxo intersecretarial e sua competência não estão autorizadas por esta análise. Ver D02/D03.

## 4. Organização funcional proposta

| Área | Conteúdo e perguntas | Comportamento candidato |
|---|---|---|
| **A — Tratamento analisado** | F2 1.1–1.3.1: cinco IDs; Registro, Secretaria, unidade, suficiência e lacunas. Consulta contextual aos fatos mapeados nos demais itens | Identificação do objeto, fonte exata, edição e data; fatos somente leitura; lacunas visíveis sem editar o FORM 1 |
| **B — Orientação para análise** | Orientações não numeradas do mestre, Cartilha e referências oficiais. Nenhuma das 245 perguntas é removida para esta área | Ajuda contextual integrada às perguntas de A/C/D, com edição e assunto; consulta sem perder trabalho. Sem tela obrigatória de leitura nem conclusão jurídica automática |
| **C — Análise de legitimidade** | 220 IDs dos blocos editoriais 2–13, incluindo todos os ramos | Grupos temáticos por finalidade/operação e participantes pertinentes; fato consultado, análise e evidência visualmente separados; condições aprovadas aplicadas sem transformar desconhecido em negativo |
| **D — Manifestação e encaminhamento** | F2 1.4–1.6 (autoria funcional) e 14.1–14.9, com subperguntas: vinte IDs | Autoria/representação verificáveis, conclusões, ressalvas, informações pendentes, áreas a consultar, propostas para FORM 3/4. Sem criar competência, homologação ou tarefa automática |

Organização possível de C, ainda não desenho de telas: (i) finalidade e necessidade; (ii) bases por operação, sensíveis e consentimento; (iii) titulares/crianças, representação, imagem e voz; (iv) compartilhamento, participantes e papéis; (v) infraestrutura, terceirização, Wi‑Fi e continuidade; (vi) entrega de informação, Ouvidoria/e-SIC e saúde; (vii) trabalho remoto e guarda externa; (viii) capacidade de atender direitos. A matriz mantém os IDs de origem mesmo quando o agrupamento muda.

### B — Referências editoriais conferidas

| Tema do FORM 2 | Seção existente em C14 | Limite da reutilização |
|---|---|---|
| Finalidade, necessidade, bases e fatos | §§2, 5.1–5.3 | Orienta análise, não escolhe base automaticamente |
| Agentes, parceria e SAA | §§3.1–3.3; 6.6 | Identidade do destinatário não determina Controlador/Operador; exige harmonizar F2 10.5 |
| Termos, ciência e consentimento | §§4.8, 7.2, 11.1 | Modelo orientativo não é requisito universal de consentimento |
| Crianças/adolescentes e saúde | §§6.2–6.3 | Ajuda conceitual, sem dados de pacientes ou estudantes |
| Imagem, voz, publicidade | §§6.1, 7.2 | Separar captação, uso e divulgação |
| Compartilhamentos e fornecimento de informação | §§4.4, 7.3, 8.1–8.3 | Não confundir dado sensível, informação restrita e classificação formal |
| Serviços pessoais, trabalho remoto e guarda | §§6.10, 8.4, 9.1–9.2 | Não presumir canal corporativo, equipamento institucional ou prazo único |
| Direitos e encaminhamentos | §§7.1, 10.1–10.3, 13 | Referência conceitual; risco e execução pertencem aos instrumentos próprios |

Esse quadro é correspondência editorial, **não comprovação de links navegáveis já disponíveis para FORM 2**. A futura ajuda deve ter identificador temático, edição, seção e destino verificado. Manter referências históricas à REV30.13; não substituir silenciosamente links do FORM 1 por REV30.14. Disponibilização local e somente leitura conforme autorização; publicação externa exige decisão própria.

## 5. Contrato conceitual mínimo proposto

Os nomes abaixo são descritores de planejamento, não esquema JSON/API criado ou migração autorizada. A escolha física deve preceder a implementação e demonstrar compatibilidade com a infraestrutura atual.

| Grupo | Conteúdo mínimo proposto | Invariante a verificar |
|---|---|---|
| Identidade | Registro LGPD, instrumento FORM 2, ciclo quando aplicável, definição candidata e revisão do modelo | Um mesmo Registro; IDs de F2 qualificados por instrumento e definição |
| Origem factual | ID de `VersaoForm1Integral`, número do snapshot, versão de rascunho de origem, contrato/revisão, perfil de extensões e lacre | Snapshot pertence ao mesmo Registro e pode ser consultado por quem tem acesso; sem referência a “última versão” variável |
| Escopo analítico | Operação ou conjunto explicitamente delimitado, finalidade, categorias de titulares/dados e participantes/destinatários referenciados | Cada fundamento declara seu alcance; nome da operação ou ID F1 7.1 sozinho não é chave suficiente |
| Respostas | ID F2 original, conteúdo de análise/esclarecimento, referência factual quando houver, escopo aplicável, situação da informação | Separar vazio, desconhecido, não aplicável e resposta substantiva; vocabulário final sujeito a decisão |
| Evidências | Tipo, referência institucional, localização permitida, vínculo com pergunta/operação/manifestação | Não copiar dados individuais, contratos inteiros ou logs de cidadãos; não disponibilizar evidência a perfil sem acesso |
| Manifestação | Autor autenticado, vínculo/representação, função exercida, competência autorizada, data, versão examinada, conclusão e ressalvas | Não preencher autor a partir de F1 0.1–0.3; não atribuir autoridade por ser APA/ARP/SAA/DPO/Jurídico/TI |
| Encaminhamentos | Achado, operação, pergunta de origem, área proposta, providência, prazo conhecido e motivo | Proposta não cria execução no FORM 4 nem avaliação automática no FORM 3; atos efetivos dependem de fluxo aprovado |
| Histórico próprio | Revisão de rascunho, versões imutáveis, manifestações e seus vínculos, motivo de revisão | Nunca alterar versão ou manifestação anterior para refletir nova informação |
| Garantias transacionais | Comando idempotente, versão lida, evento e auditoria na mesma transação das projeções/versão relacionadas | Repetição não duplica atos; concorrência não sobrescreve; falha reverte o comando inteiro |

### 5.1 Fundamentos distintos por operação

Proposta: cada conclusão ou fundamento aponta explicitamente para seu escopo, em vez de manter uma única base legal global do Registro. O vínculo pode abranger uma ou várias operações deliberadamente selecionadas, sem copiar todas as respostas para cada operação. A granularidade e a cardinalidade precisam ser aprovadas em D06.

Exemplo exclusivamente fictício: um serviço de oficinas municipais reúne inscrição, verificação de representação, comunicação ao participante e publicação de imagens. O FORM 2 poderá analisar inscrição e divulgação separadamente; nenhuma hipótese legal é preenchida automaticamente neste exemplo. Se a divulgação não estiver clara no FORM 1, registra-se lacuna; não se inventa o fato para justificar uma base.

F2 3.1/3.3/3.3.1, 4.3, 7.5/7.11.4, 8.6 e 10.7.8 devem poder apontar para esses escopos. As referências repetíveis de F1 3.3 e 10.2.1 devem identificar a ocorrência específica do snapshot. Uma operação pode envolver vários participantes, e a mesma entidade pode ter papéis diferentes em operações diferentes.

### 5.2 Reutilização técnica sem confundir contrato nuclear e Integral

`VersaoForm1Integral` já preserva ID, Registro, número, versão de rascunho, contrato 3, revisão da fonte, conteúdo canônico, lacre e autoria. É a origem factual técnica a estudar; a autorização para utilizá-la como marco institucional não decorre da existência da tabela. `VersaoInstrumento` é a estrutura nuclear distinta.

Os modelos genéricos de instrumento/versão/análise e os serviços de comandos/eventos oferecem padrões reutilizáveis. Entretanto, `app/instrumentos.py` usa `validar_conteudo` e a versão do FORM 1 sintético. Portanto, reutilizar seus comandos sem adaptador próprio e análise de isolamento arriscaria validar FORM 2 pelo contrato errado. A recomendação é definir primeiro a fronteira de adaptação, sem substituir validadores nucleares. Não há evidência suficiente nesta tarefa para escolher nova tabela, reaproveitar tabela ou afirmar que nenhuma migração será necessária.

### 5.3 Leitura histórica das extensões do FORM 1

| Perfil efetivo da origem | Leitura obrigatória da proposta |
|---|---|
| REV13 original, 128 IDs | Manter 13.2 agregada e 12.3/12.4 agregadas, com seus enunciados; informação insuficiente permanece insuficiente |
| MEDIDAS-v1, 129 IDs | 13.2 guarda física; 13.2.1 bloqueio de estações. Consultar cada uma sem presumir adoção por outro Registro |
| GUARDA-v1, 139 IDs | Procedimentos: 12.3 guarda/arquivamento, 12.3.1 eliminação, 12.3.2 devolução, 12.3.3 transferência; evidências 12.4/12.4.2/12.4.3/12.4.4 e respectivas localizações 12.4.1/12.4.2.1/12.4.3.1/12.4.4.1 |
| MEDIDAS-GUARDA-v1, 140 IDs | Compor explicitamente as duas definições, sem criar equivalência retroativa |

Para GUARDA, 12.5/12.5.1/12.5.1.1/12.5.2 devem ser lidos como existência de transferência, modalidades, complemento e destino, conforme a definição efetiva. O 12.5.1 original era destino textual: não converter por igualdade de ID.

Correspondências da matriz que citam os IDs agregados de guarda são **base REV13**, não regras automáticas para as extensões. Exemplos de desdobramento a especificar: F2 9.11/9.12 examina eliminação e prova (`12.3.1`, `12.4.2`, `12.4.2.1` em GUARDA); F2 12A.10 pode consultar devolução (`12.3.2`, `12.4.3`, `12.4.3.1`) e controles F1 8.6.4; F2 12A.6 consulta 13.2/13.2.1 em MEDIDAS, preservando exposição de 13.1. São subsídios, não respostas jurídicas equivalentes.

O snapshot, inclusive seu legado arquivado, permanece íntegro. Adoção posterior de extensão no rascunho do FORM 1 não altera a origem de uma análise do FORM 2.

## 6. Regras de consulta, rascunho e revisão propostas

1. **Consulta:** fatos mostram a versão e a origem; erro factual gera pedido de esclarecimento ou revisão do FORM 1, sem edição pelo FORM 2.
2. **Rascunho:** proposta de permitir incompletude com pendências explícitas; política definitiva própria do FORM 2 ainda depende de D04. Não importar a matriz REV13.
3. **Condicionais:** preservar condições expressas e formalizar as restantes; `A CONFIRMAR` não vira Não nem oculta obrigação por inferência. F2 7.1.2 exige considerar também dúvida.
4. **Manifestações:** registrar versão, escopo e autoria; uma manifestação não equivale automaticamente à conclusão integral ou aprovação institucional.
5. **Revisão factual:** nova versão F1 não substitui a referência anterior. Propor aviso de versão posterior e reavaliação explícita das operações afetadas; os critérios de relevância e os efeitos institucionais ficam em D07.
6. **Conclusão:** não implementar neste estudo; critérios, competências, pendências impeditivas e efeito sobre FORMs 3/4 dependem de decisão própria.

Possível redução de repetição: F2 5.7 e 13.9 tratam revogação; 8.9 e 13.6/13.11 usam evidências relacionadas; 6.5 e 10.9.8 podem compartilhar referência específica. Preservar todos os IDs e a diferença de escopo. Referência comum ou apresentação conjunta é proposta sujeita a validação, não autorização para eliminar perguntas ou propagar respostas.

## 7. Verificação desta entrega documental

Conferência automatizada da matriz contra a extração do mestre: 245 IDs únicos, distribuição por bloco, enunciados preservados e IDs F1 referenciados existentes no catálogo de 128 campos. Fontes, referências locais e diferenças históricas foram revisadas. Essa conferência verifica integridade documental; não é teste de aplicação, validação jurídica ou aceite visual.

Não foram executados testes da aplicação, migrações, consultas ao banco, commit ou push. Os arquivos preexistentes permanecem preservados. A sequência futura e seus critérios de aceite estão no [Produto 4](FORM2_REV17_INCREMENTOS_COMPLEXIDADE.md).
