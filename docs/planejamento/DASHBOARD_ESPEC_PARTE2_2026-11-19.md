# Dashboard LGPD — Especificação, parte 2 (telas 1 Cobertura, 2 Circulação e 3 Operação) — 19/11/2026

Continua a parte 1 (`DASHBOARD_ESPEC_PARTE1_2026-11-19.md`). Valem todas as regras gerais dela: só leitura; todo número abre a lista que o compõe; ausência não é zero; filtros no topo; "Sobre este número"; botão "Gráfico / Tabela"; cores aprovadas; Painel LAI como referência.

**O que o agente faz agora:** arquivar como `docs/planejamento/DASHBOARD_ESPEC_PARTE2_2026-11-19.md` (só documentação) e responder às perguntas da seção 4, sem código.

## Unidade de contagem (vale para as partes 1, 2 e 3)
A unidade é o **Registro LGPD**. O objeto de cada Registro é um **serviço**, um **processo** ou uma **atividade** do catálogo operacional (README, regra conceitual; AGENTS.md). Nas telas, "Registro" é o que se conta. Serviço, processo e atividade são o tipo do objeto e nunca se somam como se fossem a mesma coisa sem mostrar a divisão.
- Filtro adicional na faixa do topo: **tipo de objeto** (serviço · processo · atividade · todos).
- Onde houver total, o "Sobre este número" mostra a divisão por tipo ("10 Registros: 4 serviços, 4 processos, 2 atividades").
- A hierarquia (serviço realizado por processo; processo composto de atividades) não gera contagem em cascata: um serviço com três processos registrados conta quatro Registros, não um.
- Canal não é tipo de objeto e não é contado como Registro, salvo quando tiver Registro próprio por tratamento autônomo.

## Padrão comum às três telas
- Topo: título em forma de pergunta, faixa de filtros, um número-resumo.
- Centro: um único visual principal.
- Abaixo do visual: a tabela equivalente (botão "Gráfico / Tabela"), com as colunas indicadas em cada tela.
- Rodapé: data de referência e "dados fictícios de demonstração".
- Nenhum nome de pessoa em nenhuma das três telas. Quem aparece é o papel (AAL, DPO, Jurídico, Comitê, Secretário, Prefeito), nunca o servidor.

## 1. Cobertura — "Quais Secretarias já mapearam seus serviços, processos e atividades?"
**Visual principal:** barras horizontais, uma por Secretaria **ativa** da tabela-mestre (todas, não só as que têm registro). Cada barra tem dois segmentos em tons do azul-escuro:
- claro: levantamento confirmado (FORM 1);
- escuro: análise concluída (FORM 2).

**Número-resumo:** "N Secretarias com pelo menos um Registro, de M ativas".

**Regras:**
- Secretaria ativa sem nenhum registro aparece com "0 Registros". Aqui o zero é real (contagem conferida), não falta de fonte. A barra vazia mostra onde o trabalho ainda não começou.
- Sem universo esperado aprovado (quantos serviços, processos e atividades com dados pessoais cada Secretaria tem no catálogo operacional), **não há percentual**. O "Sobre este número" explica: "Mostramos quantidades. O percentual depende de um inventário de referência ainda não aprovado."
- Registro com participação de várias Secretarias conta uma vez, na Secretaria responsável pelo Registro. As demais mostram "participa em N Registros de outras Secretarias", em texto, fora da barra.
- Ordem alfabética; ordenação opcional por quantidade (decisão da parte 1).
- Com o filtro de uma Secretaria, a tela vira a lista dos Registros dela, com o tipo de objeto e a etapa de cada um.

**Tabela:** Secretaria · serviços · processos · atividades · com levantamento confirmado · com análise concluída · participações em Registros de outras Secretarias.

**Mensagem para a palestra:** começamos por algumas Secretarias, o método está provado, e a tela mostra com honestidade o caminho que falta.

## 2. Circulação — "Para onde os dados pessoais vão?"
**Visual principal:** quadro de origem e destino, mais simples que um diagrama de fluxo. Linhas: Secretaria de origem. Colunas: tipo de destino (outra Secretaria · outro órgão público · empresa contratada · titular ou público · não informado). Cada célula mostra a contagem de relações distintas, em tons do azul-escuro (quanto mais, mais escuro). Célula sem relação fica vazia, não com "0".

**Indicador ao lado (instrumentos):** para os destinos "empresa contratada" e "outro órgão público", uma barra com quatro partes:
- cláusula de proteção de dados identificada;
- sem cláusula identificada;
- instrumento ainda não examinado;
- instrumento não informado.

**Regras (da candidata, mantidas):**
- "Não informado" não significa que o contrato não existe.
- Cláusula identificada não é cláusula homologada. O texto da barra diz "identificada", nunca "conforme".
- Relações deduplicadas: o mesmo fluxo citado em dois Registros conta uma vez no quadro e aparece nas duas listas.
- Transferência internacional não é presumida. Se o FORM 2 marcar "a confirmar", a relação aparece com essa marca.

**Tabela:** origem · destino · tipo · instrumento (número/identificador) · situação da cláusula · Registros em que aparece.

**Regra de corte desta tela:** se os FORMs 1 e 2 não tiverem campos estruturados suficientes para montar o quadro (pergunta 4a), a tela fica com "Não disponível" e o "Sobre este número" explica o motivo. Na redução para três telas (parte 1, seção 4), esta é a primeira a sair.

## 3. Operação — "Onde os Registros estão esperando?"
**Visual principal:** barras horizontais, uma por **fila institucional** (papel, não pessoa):
AAL · DPO · Jurídico · Secretário · Comitê · Prefeito.

Cada barra mostra quantas participações estão abertas naquela fila. Ao lado, em texto: "espera mediana N dias · maior espera N dias".

**Número-resumo:** "N participações abertas em M Registros".

**Regras:**
- Conta-se **participação**, não Registro. Um Registro pode estar em várias filas ao mesmo tempo. A nota fixa da tela diz: "um Registro pode estar esperando em mais de uma fila".
- **Espera sem responsável:** da entrada até alguém assumir. **Espera pelo DPO:** da abertura da participação do DPO até a conclusão (ciência não encerra a espera). Definições da candidata, mantidas.
- **Não há cor de atraso nesta tela.** Espera não é atraso: não existe prazo legal para a maior parte das filas. As barras ficam em azul-escuro.
- **Exceção, os prazos que existem de fato,** em um quadro separado abaixo do gráfico, "Prazos em curso":
  - ação do FORM 4 com prazo vigente: dias restantes ou "Atrasada" (borda grossa, relógio e a palavra, como na parte 1);
  - incidente: comunicação em 3 dias úteis a partir do conhecimento e complementação em até 20 dias úteis (Resolução CD/ANPD nº 15/2024). Mostra a data em que ocorreu, a data de conhecimento e a data de comunicação, separadas.
- Não atribuir gargalo a pessoas: nada de "servidor X está com 5 Registros". O detalhe da fila lista os Registros, não quem os tem.

**Tabela:** fila · Registro · Secretaria · etapa · aberta desde · dias de espera · prazo (se houver).

**Com os dados fictícios, a tela deve mostrar:** o festival escolar (caso 5) esperando em Jurídico e DPO ao mesmo tempo; a proposta do nome social (caso 7) na fila do DPO; o caso 9 na fila do Comitê; o caso 2 na fila do Prefeito; e, em "Prazos em curso", a ação atrasada (caso 4) e o incidente do e-mail (caso 6) com as três datas.

## 4. Perguntas ao agente (responder sem código)
a) Circulação: quais campos dos FORMs 1 e 2 registram destino do dado, tipo de destinatário e instrumento (contrato, convênio, termo)? São estruturados ou texto livre? Dá para montar o quadro de origem e destino sem ler texto livre?
b) Operação: o modelo atual de participação registra abertura, assunção e conclusão com data e hora para todas as filas da lista? Alguma fila (Comitê, Prefeito) ainda não existe como participação?
c) Cobertura: existe hoje a lista de Secretarias ativas da tabela-mestre acessível ao sistema (as 18), ou só as que têm registro?
d) Incidente: o FORM 4 já guarda separadamente a data de ocorrência, a data de conhecimento e a data de comunicação?
e) Algum item desta parte contradiz o que já está implementado ou decidido?
