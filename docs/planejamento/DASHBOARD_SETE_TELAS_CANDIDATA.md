# Dashboard LGPD: sete telas e critérios de demonstração

Proposta consolidada em 12/11/2026, a partir do roteiro recebido em 11/11 e da orientação posterior de sete telas. **Especificação candidata; dashboard ainda não implementado.** Os exemplos de apresentação são fictícios. Não ampliar o projeto para inventário geral ou economia financeira sem autorização específica.

## Composição

Cada canvas ocupa uma tela de apresentação de 1920 × 1080, sem rolagem vertical. Um gráfico principal por tela; detalhes aparecem somente ao selecionar um indicador. O Canvas 3 pode ter rolagem no modo operacional. Em telas pequenas, permitir adaptação e rolagem, sem comprimir texto ilegível. Ações à direita, teclado e foco visíveis. Não depender apenas de cor.

| Tela | Pergunta e visual principal | Unidade de contagem e fonte | Informação ainda ausente |
|---|---|---|---|
| Abertura | Prefeitura em um olhar; esteira dos quatro FORMs | Processos distintos por estado formal, separando participações | Resultado candidato não conta como validação concluída; evolução temporal exige série histórica |
| 1. Cobertura | Barras por Secretaria | Processos com levantamento confirmado, por todas as Secretarias ativas da tabela-mestre | Sem universo esperado aprovado, mostrar quantidade, não percentual |
| 2. Circulação | Diagrama origem–destino com indicador de instrumentos | Relações deduplicadas de circulação; contratos/instrumentos distintos com tratamento de dados | Dado não informado não significa ausência de contrato; cláusula declarada não é cláusula homologada |
| 3. Operação | Esteira por fila institucional | Participações abertas, idade da fila e tempo aguardando manifestação; processo pode ter várias participações | Não atribuir gargalo pessoal nem prazo legal a faixas visuais de espera |
| 4. Risco | Matriz 5 × 5, inerente e residual | Riscos identificados individualmente e avaliações com mesma metodologia/versionamento | Enquanto o FORM 3 não operar, mostrar sinais de atenção separadamente, sem notas inventadas |
| 5. Correção | Linha do tempo das ações | Ações com identificador, prazo vigente, verificação e evidência | Ação informada como executada não equivale a concluída com verificação |
| 6. Aprendizados | Um aprendizado em destaque, navegação entre cartões | Mudanças verificadas de procedimento, com referência de evidência autorizada | Não contar rascunho ou ocorrência sem melhoria comprovada |

## Métricas sem ambiguidade

- **Cobertura:** numerador e denominador precisam ter a mesma unidade, escopo e data. Carta de Serviços é uma possível fonte de referência; não representa automaticamente todo processo ou atividade interna. Resolver deduplicação e participação intersecretarial antes de somar.
- **Instrumentos com cláusula:** total de instrumentos distintos com tratamento de dados e cláusula identificada dividido pelo universo pertinente conhecido. Mostrar separadamente a quantidade ainda não examinada. Não apresentar presença de cláusula como conformidade jurídica.
- **Espera sem responsável:** entrada até assunção; para participação ainda aberta, entrada até o instante da consulta. **Espera pelo DPO:** abertura da participação própria até conclusão; não confundir com ciência.
- **Riscos reduzidos:** comparação de avaliações do mesmo risco, com método compatível, controles implementados e evidências. Redução projetada não conta como alcançada.
- **Atraso de ação:** prazo vigente vencido e ação não concluída com verificação nem cancelada com aprovação. Pedido de prorrogação sozinho não altera o prazo vigente.
- **Aprendizados:** uma mudança institucional verificável pode se ligar a vários processos sem ser contada várias vezes.
- Ausência de fonte aparece como **Não disponível** ou **A confirmar**, nunca zero. Percentual sem denominador é omitido.

## Navegação e visibilidade

Cada número clicável abre somente os processos ou participações que compõem aquele cálculo, com filtro e data de referência preservados. Voltar restaura a tela anterior. Agregação e detalhamento respeitam as permissões; conhecimento de um total não concede leitura do conteúdo. O DPO acompanha metadados e acessa conteúdo segundo a regra institucional de finalidade e trilha. TI não recebe acesso funcional por administrar infraestrutura. Não expor dados pessoais, manifestações ou evidências no modo de projeção.

## Ajustes necessários nos três casos de demonstração

1. **Oficina cultural:** confirmar o levantamento, ingressar no FORM 2, assumir e salvar análise candidata. Enquanto D11/conclusão estiverem pendentes, terminar como análise demonstrativa preparada, não como processo institucionalmente validado ou encerrado. O prazo de guarda fictício não é recomendação para processo real.
2. **Muda em calçada:** solicitar complementação, preservar a versão anterior do FORM 1, registrar nova versão e decisão explícita sobre a resposta. A indicação de ação no FORM 2 não prova que houve encaminhamento executado ao FORM 4. Demonstrar essa diferença até a integração existir.
3. **Festival escolar:** participações próprias das unidades, Jurídico e DPO, sob o mesmo processo. Concluir participação do DPO remove a espera por manifestação; não remove o processo do acompanhamento geral. Incerteza sobre localização do fornecedor não prova transferência internacional. Três riscos e ações são exemplos candidatos, não parecer jurídico ou riscos calculados automaticamente pela presença de crianças.

Os passos de avaliação, ações, verificação independente e encerramento dos casos 2/3 dependem dos FORMs 3/4 e das competências a deliberar. Não simular o avanço como se fosse gravação real no sistema.

## Critérios de aceite para implementação

1. Sete telas navegáveis, sem rolagem no modo de apresentação na resolução definida; testar também teclado e tela estreita.
2. Indicadores reconciliados com suas listas, sem dupla contagem por participação.
3. Falta de fonte distinta de zero; rascunho distinto de decisão homologada.
4. Testes de segregação entre unidades e recusa de acesso direto indevido.
5. Casos fictícios reproduzíveis, sem envio real de e-mail no ensaio.
6. Evidência visual e funcional de cada caso; não declarar conclusão dos quatro instrumentos enquanto etapas forem apenas propostas.

Não há decisão de implementação ou validação jurídica embutida nas sugestões de cores, faixas de espera ou cláusulas do documento de origem.
