# FORM 2 REV17.0 — Complexidade e sequência candidata de implementação

**Produto 4 — INSTRUÇÃO_FORM02_02 — 06/11/2026**  
**Situação: proposta de planejamento; nenhum incremento de implementação está autorizado por este documento.**

Referências: [matriz completa](FORM2_REV17_MATRIZ_CORRESPONDENCIA_CANDIDATA.md), [organização/contrato conceitual](FORM2_REV17_ORGANIZACAO_CONTRATO_CANDIDATO.md) e [decisões pendentes](FORM2_REV17_DECISOES_PENDENTES.md).

## 1. Base da estimativa

O mestre contém **245 IDs**, mas eles não equivalem a 245 controles novos nem a 245 regras prontas. Há consulta de fatos já levantados, análise nova, esclarecimentos e ramos especializados. A matriz contém classificações sobrepostas: 105 itens com componente factual herdável, 148 com análise própria, 121 com esclarecimento, 18 com encaminhamento e seis explicitamente marcados para revisão. **Essas contagens não devem ser somadas nem tratadas como percentual de código reaproveitável.**

Reutilização possível: identidade e escopo, Registro, componentes de perguntas/consulta, navegação, ajudas versionadas, comandos, eventos, lacre, concorrência e padrões de testes. Reutilização que ainda precisa ser demonstrada: persistência genérica de instrumentos, fluxos de análise institucional, precondições de entrada e validação própria do FORM 2. O adaptador nuclear não pode simplesmente receber as perguntas novas.

Principais fatores de esforço: escopo analítico por operação; relação com ocorrências repetíveis; quatro definições históricas possíveis do FORM 1; ausência de catálogo completo de opções e condições; autoridade para manifestações; evidências; revisão de fatos e repercussão na análise. Não há base para prometer um número exato de horas ou prazo final antes das decisões D01–D04/D06.

Escala de complexidade por entrega: **baixa** — reutilização localizada e verificável; **média** — novo adaptador ou grupo de campos com dependências delimitadas; **alta** — múltiplas relações/condições ou garantia transacional e institucional. Uma entrega alta deve ser subdividida nos pontos de controle indicados, sem concentrar todo o trabalho em um commit final.

## 2. Incrementos pequenos e verificáveis

| Incremento candidato | Entrega delimitada e cobertura | Dependências | Complexidade / principal incerteza | Critério de encerramento |
|---|---|---|---|---|
| **F2-01 — Definição executável aprovada** | Transformar a matriz em catálogo/matriz próprios, mantendo 245 IDs; definir tipos, opções, condições, escopos e edição. Sem tela ainda | D04–D06, D09–D10 | **Alta**, pela política ainda incompleta. Separar catálogo, condições e validação estrutural em checkpoints | Cobertura 245/245; nenhuma pergunta eliminada; sem IDs inválidos, ciclos de condições ou conversão de fatos em conclusão; diferenças para mestre aprovadas e versionadas |
| **F2-02 — Consulta vinculada à origem** | Área A: selecionar/consultar snapshot elegível do mesmo Registro, referência imutável, metadados e lacunas. Sem atos de conclusão | D01–D02, D08 | **Média**, pela seleção do marco e definições históricas | Ler original, MEDIDAS, GUARDA e combinação; preservar lacres, canais e ocorrências; recusar origem de outro Registro/sem autorização; nenhuma criação em leitura |
| **F2-03 — Rascunho e escopo por operação** | Adaptador de respostas do FORM2, rascunho próprio e escopo de análise; versões, autoria, idempotência e controle otimista. Primeiro ensaio mínimo antes de ampliar conteúdo | F2-01/02; D06/D13 | **Alta**, por isolamento do núcleo e atomicidade. Separar persistência básica e concorrência/rollback | Salvar/retomar incompleto; duas operações independentes; nenhum uso do validador sintético; cliques repetidos, conflito e falha não corrompem dados |
| **F2-04 — Finalidade, bases, sensíveis e termos** | Conteúdo C dos blocos de origem 2–5: **46 IDs**, consultando fatos e explicitando análise. B integrado nesses grupos | F2-01/03; D04/D06/D14 | **Alta**, por bases diferentes e balanceamento; checkpoints finalidade, bases/sensíveis, termos | Duas bases em operações distintas; legítimo interesse e consentimento sem seleção automática; dúvida em aberto preservada; fatos de origem imutáveis |
| **F2-05 — Representação, crianças, imagem e voz** | Blocos 6–7: **37 IDs**, com captação/publicação e evidências de representação. Sem cadastro de titulares | F2-04; D09/D11 | **Alta**, por condicionais e finalidade de divulgação; separar representação e imagem/voz | Origem factual parcial gera esclarecimento; dúvida sobre sensíveis ativa exame devido; captação não autoriza publicação; sem nomes de cidadãos |
| **F2-06 — Compartilhamento, papéis e parcerias** | Blocos 8 e 10: **48 IDs**; destinatários/participantes por ocorrência, bases e papéis por operação | F2-03/04; D05/D06/D11 | **Alta**, por cardinalidade e papel contextual; checkpoints compartilhamento, parceria, evento com crianças | Duas entidades sem troca de respostas; mesma entidade com papéis diferentes por operação; CNPJ não exigido de Secretaria; classificação não inferida de contrato |
| **F2-07 — Infraestrutura e Wi-Fi** | Bloco 9: **24 IDs**, incluindo 9W; continuidade, saída de fornecedor e provas | F2-03/04; D10/D11 | **Média a alta**, conforme evidências disponíveis | Wi-Fi apenas quando pertinente; fatos de exportação não equivalem à obrigação contratual; encerramento e prova separados; sem ingestão de logs individuais |
| **F2-08 — Fornecimento de informação e saúde** | Bloco 11: **25 IDs**, incluindo 11S; Ouvidoria/e-SIC independentes e verificação de entrega | F2-03/04; D09/D10 | **Alta**, pela distinção procedimento/caso e restrições de acesso; separar canais e saúde | Não inventar canal por nome genérico; validar ramos com/sem/incerto; sem dados de pedidos individuais; sensibilidade não vira classificação de sigilo |
| **F2-09 — Trabalho remoto e direitos** | Blocos 12–13: **40 IDs**, incluindo 12A; guarda externa e capacidade de atender direitos | F2-03/04; D08/D11 | **Média a alta**, pela leitura das extensões e evidências; separar guarda externa e direitos | Prazo agregado não vira prazo específico; alta sensibilidade não vira DPS automático; não prometer eliminação/revogação irrestrita; original e extensões recuperáveis |
| **F2-10 — Manifestações e revisão** | Área D: bloco14 (**17 IDs**) + autoria1.4–1.6; histórico próprio, ressalvas e propostas de encaminhamento. Não desenvolver FORMs3/4 | Grupos anteriores; D01–D03, D07/D12 | **Alta**, depende de governança. Separar manifestação parcial, revisão e eventual conclusão autorizada | Autoridade/escopo conferidos; versão exata; revisão F1 não reescreve F2; sem autoatribuição, autovalidação proibida ou abertura automática de outros FORMs |
| **F2-11 — Aceitação integrada e documentação** | Conferir cobertura completa, teste ponta a ponta por perfil e operação, teclado/telas estreitas, vínculos da Cartilha, regressão e roteiro funcional | F2-01–10 estáveis; decisões de liberação resolvidas | **Média**, com reserva para defeitos comprovados | Jornada com duas operações e duas versões; todos os 245 IDs rastreáveis; isolamento nuclear; relatório distingue automático, manual e aceito; falhas impeditivas resolvidas |

Área A cobre cinco IDs; autoria de D cobre três; os grupos temáticos de C cobrem 220; bloco14 cobre 17: **245**, sem lacunas. B é transversal e não acrescenta perguntas.

Cada grupo de conteúdo pode encerrar um checkpoint técnico estável sem liberar o uso institucional. Uma dependência institucional pendente deve bloquear o ato dependente, não motivar uma regra improvisada. O conjunto completo não deve ser declarado entregue enquanto houver conteúdo original excluído ou não verificado.

## 3. Faixas de esforço para decisão, não compromisso de prazo

Neste estágio, a estimativa mais sustentada é por **complexidade e tamanho de checkpoint**, como na tabela, e não por produtividade suposta por pergunta. Como referência de planejamento, após definição do contrato:

- Checkpoint de baixa complexidade: aproximadamente **2–4 horas produtivas**.
- Checkpoint de média complexidade: aproximadamente **4–8 horas produtivas**.
- Checkpoint de alta complexidade: aproximadamente **8–16 horas produtivas**, devendo ser repartido quando abranger mais de um grupo independente.

As faixas representam trabalho conjunto de implementação, revisão e verificação técnica; **não são 100% tempo automático da ferramenta**, nem duração de sessão ou horas de calendário. Não se deve multiplicar a faixa alta mecanicamente pelos grupos: partes compartilham infraestrutura, outras dependem de decisões ainda abertas. Não há, nesta análise documental, medição que sustente um total confiável para conclusão institucional do FORM 2.

Recomendação de gestão: estimar o total depois de F2-01 e de uma prova autorizada F2-02/03; medir esforço real de um grupo temático antes de extrapolar os demais. Manter visíveis horas gastas, itens concluídos, remanescentes e alterações de escopo. Tempos de espera por aprovação institucional, validação jurídica, integração de identidade real, implantação institucional, piloto, dashboards e desenvolvimento dos FORMs 3/4 ficam fora dessas faixas.

## 4. Matriz mínima de verificações futuras

| Risco | Cenário verificável |
|---|---|
| Reinterpretar a origem | F1 S1 original analisado por F2 V1; F1 adota GUARDA e produz S2. V1 continua mostrando enunciados e respostas de S1; nova análise explicita S2 |
| Base global indevida | Operações fictícias de inscrição e divulgação têm análises distintas; alterar uma não preenche nem altera a outra |
| Misturar ocorrência | Dois destinatários e dois participantes com papéis diferentes; edição de uma análise não contamina outra ocorrência |
| Campos desconhecidos ocultados | Fato em branco/A CONFIRMAR, consentimento desconhecido e dúvida de revelação sensível; preservar a incerteza e não tratá-la como resposta negativa |
| Competência indevida | APA/ARP/SAA sem autorização própria não manifesta nem conclui FORM2; unidade participante não recebe acesso integral por mera indicação |
| Estado inconsistente | Duplo comando, mesma chave com conteúdo diferente, versão lida antiga e falha entre evento/projeção; nenhuma duplicação ou persistência parcial |
| Cópia de dados individuais | Respostas usam categorias de titulares e referências institucionais fictícias; nenhum caso real, log ou documento pessoal é importado |
| Ajuda quebrada | Seção e edição da Cartilha verificadas; retorno mantém respostas; ausência do arquivo produz orientação clara, não link falso |
| Confusão de instrumentos | Fatos do F1 somente leitura, análise identificada como FORM2; encaminhamento não simula FORM3/4; conferência APA não equivale à liberação |

**Nesta tarefa documental não houve execução desses cenários, testes da aplicação ou implementação.** Foram verificadas somente integridade da matriz e consistência das referências. O próximo passo recomendado é avaliar os Produtos 1–3 e autorizar separadamente a definição executável, sem iniciar código antes dessa decisão.
