# Dashboard LGPD — Especificação, parte 1 (regras gerais, dados fictícios e Abertura) — 19/11/2026

Complementa `docs/planejamento/DASHBOARD_SETE_TELAS_CANDIDATA.md` (12/11), com as decisões de 18/11 sobre os FORMs 3 e 4. Onde houver conflito, vale este texto. Parte 2: telas 1 a 3. Parte 3: telas 4 a 6 e o resumo do Prefeito em detalhe.

## O que o agente faz agora com esta parte
1. Arquivar este texto como `docs/planejamento/DASHBOARD_ESPEC_PARTE1_2026-11-19.md`. Commit só de documentação, na branch atual, depois de terminar o Lote 12-A.
2. **Não implementar ainda.** Responder a seção "Perguntas ao agente" (no fim), sem código.
3. A implementação começa depois da vistoria do Lote 12, em branch própria (`lote-13-dashboard`), criada a partir da branch do Lote 12. Sem push e sem merge sem autorização.

## 1. Regras gerais (valem para as sete telas)
1. **Só leitura.** O dashboard não grava nada nem altera estado de FORM. Consulta o que os FORMs já registraram.
2. **Todo número abre a lista que o compõe** (regra da candidata). A soma da lista confere com o número.
3. **Ausência ≠ zero.** Sem fonte: "Não disponível". Sem avaliação: "Ainda não avaliado". Percentual sem denominador aprovado não aparece.
4. **Só conta o que vale.** Nota de risco conta apenas quando a nota conjunta foi confirmada (Secretaria + DPO). Proposta aguardando confirmação e "Sem consenso" aparecem em contagens separadas, com esse nome. Ação "executada" só conta como concluída depois da verificação pelo Comitê.
5. **Selo "Em deliberação"** em todo indicador que dependa de regra ainda não homologada, com a frase "Proposta em deliberação. Não equivale a homologação." Sem o código D11 na tela.
6. **Linguagem:** mesma regra do Lote 12-A. Explicação em português claro; código só entre parênteses.
7. **Modo de projeção:** nenhum dado pessoal, nenhum texto de manifestação, nenhuma evidência. Só contagens, faixas, Secretarias e identificadores (LGPD-2026-…, Rnn, Ann).
8. **Quem vê o quê (demonstração):**

   | Perfil | Vê |
   |---|---|
   | Prefeito | Todas as Secretarias, só agregados; o resumo do Prefeito |
   | DPO | Todas as Secretarias; metadados; abre o detalhe conforme a regra de finalidade e trilha |
   | Comitê (relator e verificador) | Todas as Secretarias, agregados; as ações que lhe cabem verificar |
   | Secretário | Só a própria Secretaria |
   | Beta (AAL) | Só os próprios Registros |

   O teste de segregação entre unidades é obrigatório (critério 4 da candidata).
9. **Prazos:** mostrar prazo e atraso. Não há escalonamento automático (decisão 9). A única notificação automática é a do item 3.3 (segunda prorrogação com parecer contrário mantido).
10. **Aparência:** mesmo design do sistema (tokens de `docs/design-system`). Não depender só de cor: toda faixa tem texto ("Crítico", "Alto"…). Matriz 5×5 com as mesmas cores do bloco 14 do FORM 3.
11. **Referência visual principal (aprovada por Ailton em 19/11):** o Painel LAI da CGU (centralpaineis.cgu.gov.br/visualizar/lai). Ele monitora o cumprimento de uma lei órgão por órgão, com prazos e omissões, que é a nossa lógica (Secretaria → risco → ação no prazo ou atrasada). Seguir o estilo: poucas cores, números grandes no topo, comparação entre unidades pelo mesmo critério. A comparação entre Secretarias aparece em ordem alfabética, com ordenação opcional pelo usuário. Não há título nem destaque do tipo "pior Secretaria".
12. **"Sobre este número"** (ideia da agência britânica UKHSA): ícone (i) em cada quadro e indicador. Abre quatro linhas: de onde vem o dado, a regra de cálculo, quem responde por ele (Secretaria, DPO ou Comitê) e quando foi atualizado. Um dashboard sem dono e sem fonte documentada perde a confiança.
13. **Gráfico ou tabela** (ideia do Our World in Data): toda tela de detalhe tem o botão "Gráfico / Tabela". A tabela também atende à acessibilidade.
14. **Duas datas no incidente:** data em que ocorreu e data em que foi comunicado, sempre separadas, nunca misturadas num só eixo.

15. **Filtros (inspirados no Painel LAI, pedido de Ailton em 19/11):**
   - Uma única faixa de filtros no topo, igual em todas as telas: **Secretaria**, **tipo de objeto** (serviço, processo, atividade), **período** (data do registro), **etapa** (FORM 1 a 4) e **faixa de risco**. A unidade de contagem é o Registro LGPD (ver parte 2, "Unidade de contagem").
   - Ao filtrar, todos os quadros e listas da tela se recalculam. Os filtros acompanham a navegação entre telas e a volta (regra da candidata).
   - O filtro ativo aparece escrito ("Mostrando: Saúde · 2026"), com "Limpar filtros" ao lado. O padrão é "Todas as Secretarias", sem filtro.
   - Permissões continuam valendo: para o Secretário, o filtro de Secretaria vem travado na própria. Filtrar nunca mostra conteúdo que o perfil não poderia abrir.
   - Com o filtro de uma Secretaria ativo, a tela 1 (Cobertura) mostra os Registros daquela Secretaria. Sem filtro, mostra as Secretarias lado a lado.
   - Na demonstração, roteiro sugerido: abrir com "Todas" e, em seguida, filtrar Saúde para mostrar o ciclo completo (casos 3 e 4).

### 1.1 Cores (aprovadas por Ailton em 19/11, conferidas no validador de daltonismo)
| Uso | Cor | Texto sobre a cor |
|---|---|---|
| Pequeno (1–3) | `#2e9e44` | branco |
| Moderado (4–6) | `#e2a90f` | escuro `#2b1d00` |
| Alto (8–12) | `#e3651d` | branco |
| Crítico (15–25) | `#b3261e` | branco |
| Base, títulos, destaque | `--azul-escuro #0c3b5a` | branco |
| Esteira dos FORMs | tons do azul-escuro, do claro (FORM 1) ao escuro (FORM 4) | conforme o tom |

Regras:
- As quatro cores de risco são as únicas cores fortes do dashboard e só significam faixa de risco.
- "Atrasada" não usa vermelho: borda grossa escura, ícone de relógio e a palavra "Atrasada".
- O amarelo tem contraste baixo sobre branco; por isso vem sempre com o nome escrito ao lado.
- Estrutura, eixos e textos de apoio ficam em cinza.
- O bloco 14 do FORM 3 passa a usar as mesmas quatro cores. Verificar se o Lote 12-A já as usa; se não, alinhar.

## 2. Conjunto de dados fictícios
Para a apresentação de 15/12. Carregar por script próprio, só em base `_teste` ou na cópia autorizada nominalmente. Nunca na 8009 ou na 8011 sem autorização. Todos os registros marcados como fictícios. Nomes de pessoas só genéricos ("Silva"); nenhum dado real.

| # | Secretaria | Caso (versão fictícia) | Tipo de objeto | Onde está | O que demonstra |
|---|---|---|---|---|---|
| 1 | Cultura | Oficina cultural | Serviço | FORM 2 concluído; sem encaminhamento | Fluxo completo sem risco |
| 2 | Cultura | Armário sem chave no acervo | Atividade | FORM 3: R01, inerente 20 (Crítico), residual 15 (Crítico), nota conjunta confirmada; **aguardando aceitação do Prefeito** | Crítico vai ao Prefeito |
| 3 | Saúde | Fichas na sala de espera | Processo | FORM 3: R01, 12 (Alto) → 4 (Moderado); FORM 4: ação concluída e verificada; aprendizado publicado | Ciclo inteiro até o aprendizado |
| 4 | Saúde | Computador ligado / documentos na mesa | Atividade | FORM 4 direto (encaminhamento só para providência); ação com prazo vencido após 1ª prorrogação | Atraso visível, sem escalonamento |
| 5 | Educação | Festival escolar | Atividade | FORM 2 em análise; participações do Jurídico e do DPO abertas | Várias participações num Registro |
| 6 | Educação | E-mail enviado ao "Silva" errado | Processo | FORM 4 como incidente; comunicação registrada dentro de 3 dias úteis | Fluxo de incidente |
| 7 | Assistência Social | Nome social | Serviço | FORM 3: proposta da Secretaria **aguardando confirmação do DPO** | Proposta ≠ nota válida |
| 8 | Meio Ambiente | Muda em calçada | Serviço | FORM 1: complementação solicitada; nova versão registrada | Versionamento |
| 9 | Comunicação | Imagem de servidor em outdoor | Atividade | FORM 3: **sem consenso**, encaminhado ao Comitê | Divergência vai ao Comitê |
| 10 | Assistência Social | Denúncia anônima revelada por entregador | Processo | FORM 4: 2ª prorrogação com parecer contrário do Comitê, mantida pelo Secretário → **Prefeito notificado** | A notificação automática |

Seis Secretarias, dez Registros (3 serviços, 3 processos, 4 atividades), todas as etapas representadas. O tipo de cada objeto é ilustrativo; se o catálogo fictício existente já classificar algum desses itens de outro modo, vale o catálogo. Datas relativas a 15/12/2026, para os prazos fazerem sentido no dia.

## 3. Tela de Abertura — "A Prefeitura em um olhar"
### 3.0 Grade 3 × 3 (aprovada por Ailton em 19/11)
Nove quadros do mesmo tamanho, exceto a esteira, que ocupa dois. Cada quadro leva à tela de detalhe indicada.

| Posição | Quadro | Leva a |
|---|---|---|
| 1 | Precisa da sua atenção (3.3), com moldura azul-escura | lista correspondente |
| 2 | Registros ativos | 3. Operação |
| 3 | Riscos com nota conjunta, por faixa (+ aguardando DPO, + sem consenso) | 4. Risco |
| 4–5 | Esteira dos quatro FORMs (3.1) | 3. Operação |
| 6 | Ações atrasadas | 5. Correção |
| 7 | Aprendizados publicados | 6. Aprendizados |
| 8 | Cobertura por Secretaria (só quantidade, sem universo aprovado) | 1. Cobertura |
| 9 | Circulação de dados ("Não disponível" enquanto não houver fonte) | 2. Circulação |

O quadro 1 aparece só para o Prefeito e o DPO. Para os demais perfis, essa posição mostra "Riscos aguardando avaliação" da sua Secretaria. A data de referência fica no rodapé (3.4), fora da grade.

**Teste dos 5 segundos (critério de vistoria):** mostrar a Abertura a alguém que não conhece o sistema e perguntar "o que precisa de atenção?". Se a pessoa não responder em 5 segundos, o desenho volta para ajuste.

### 3.1 Esteira dos quatro FORMs (visual principal)
Quatro colunas em sequência: Levantamento (FORM 1) → Análise (FORM 2) → Riscos (FORM 3) → Providências (FORM 4). Em cada uma, o número de Registros naquela etapa, dividido por situação:
- FORM 1: em preenchimento · aguardando complementação · confirmado;
- FORM 2: em análise · concluído;
- FORM 3: aguardando avaliação · proposta aguardando confirmação · nota conjunta confirmada · sem consenso;
- FORM 4: plano em elaboração · em execução · atrasada · aguardando verificação · concluída e verificada.

Um Registro aparece na etapa mais avançada em que está ativo. Se estiver ao mesmo tempo no FORM 3 e no FORM 4, conta nos dois, com a nota "um Registro pode estar em riscos e providências ao mesmo tempo". Participações não multiplicam a contagem.

### 3.2 Quatro números de topo
- Registros ativos (total de Registros distintos, com a divisão por serviço, processo e atividade no "Sobre este número");
- Riscos com nota conjunta confirmada, por faixa (Pequeno · Moderado · Alto · Crítico);
- Ações atrasadas;
- Aprendizados publicados.

Cada um abre a lista correspondente.

### 3.3 Resumo do Prefeito (faixa fixa no topo, só para Prefeito e DPO)
Título: "Precisa da sua atenção". Três linhas, sempre presentes, mesmo com zero, porque aqui zero é um dado real e verificado:
1. Riscos Críticos aguardando sua aceitação: **N** (no conjunto fictício: 1, caso 2);
2. Segundas prorrogações mantidas contra o parecer do Comitê: **N** (caso 10);
3. Avaliações sem consenso no Comitê: **N** (caso 9).

Cada linha abre a lista. Nenhum dado pessoal; só Registro, Secretaria e há quantos dias está assim.

### 3.4 Data de referência
Rodapé: "Situação em 15/12/2026 às hh:mm · dados fictícios de demonstração".

## 4. Regra de corte
Se em 1/12 o caminho dos FORMs 3 e 4 ainda não funcionar de ponta a ponta na cópia de demonstração, o dashboard se reduz a três telas: Abertura, 4 (Risco) e 5 (Correção). As demais ficam como especificação, sem tela.

## 5. Perguntas ao agente (responder sem código)
a) Para cada item da Abertura (3.1 a 3.3), quais tabelas e campos já existem para calcular. O que falta?
b) "Etapa mais avançada em que está ativo": há hoje um jeito confiável de saber isso para cada Registro, ou é preciso uma consulta nova?
c) O conjunto fictício da seção 2 pode ser carregado pelos fluxos reais (atos registrados com as contas de demonstração), em vez de inserção direta no banco? Preferimos o fluxo real, porque prova que o sistema faz o que a tela mostra. Estime o esforço.
d) Algum item desta parte contradiz o que já está implementado ou decidido?
