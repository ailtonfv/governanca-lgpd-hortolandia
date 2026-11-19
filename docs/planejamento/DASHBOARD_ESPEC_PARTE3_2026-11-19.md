# Dashboard LGPD — Especificação, parte 3 (telas 4 Risco, 5 Correção, 6 Aprendizados e resumo do Prefeito) — 19/11/2026

Continua as partes 1 e 2. Valem todas as regras delas:
- só leitura;
- todo número abre a lista que o compõe;
- ausência não é zero;
- unidade de contagem: o Registro LGPD, com a divisão por tipo de objeto;
- filtros no topo;
- "Sobre este número" e botão "Gráfico / Tabela";
- cores aprovadas;
- nenhum nome de pessoa.

Base: `DECISOES_FORMS_3_4_2026-11-18.md`, decisões 1, 4, 6, 7, 8 e 9, A1 e A2.

**O que o agente faz agora:** arquivar como `docs/planejamento/DASHBOARD_ESPEC_PARTE3_2026-11-19.md` (só documentação) e responder às perguntas da seção 5, sem código.

## 1. Risco — "Quais riscos existem e quanto os controles os reduzem?"
**Visual principal:** a matriz 5 × 5, nas mesmas cores do bloco 14 do FORM 3. Cada casa mostra **quantos riscos** estão nela. Um seletor acima da matriz alterna **Inerente / Residual**, com Residual como padrão.

**Número-resumo:** "N riscos com nota conjunta confirmada: Crítico X · Alto X · Moderado X · Pequeno X".

**Abaixo da matriz, "Efeito dos controles":** uma linha por risco (Rnn), com uma bolinha no inerente, outra no residual e uma seta entre elas. Por exemplo: "LGPD-2026-00003 · R01 · 12 Alto → 4 Moderado". Sem redução, a linha diz "nenhuma redução". Só entram riscos com as duas avaliações confirmadas pelo mesmo método.

**Quadro separado, "Ainda não valem como nota":** fica fora da matriz e nunca entra nela.
- propostas aguardando confirmação (caso 7);
- sem consenso, encaminhadas ao Comitê (caso 9);
- encaminhados ao FORM 3 e ainda não avaliados, mostrados como "Ainda não avaliado", nunca 0.

**Situação da aceitação, por faixa (decisão 1):**

| Faixa | Quem aceita | Mostra |
|---|---|---|
| Pequeno, Moderado | Secretário | aceitos · aguardando aceitação |
| Alto | Secretário, com parecer prévio do DPO e ciência do Comitê | aceitos · aguardando parecer · aguardando aceitação |
| Crítico | Prefeito | aceitos · aguardando o Prefeito, com há quantos dias |

**Triagem de RIPD (decisão 7):** uma linha, "Riscos Alto ou Crítico com triagem de RIPD: indicada N · confirmada em conjunto N · RIPD em elaboração N". Leva o selo "Em deliberação" enquanto o fluxo do RIPD não estiver homologado.

**Regras:**
- Redução projetada não conta como alcançada. O residual só vale com os controles registrados como existentes.
- A redução nunca é somada nem tirada como média entre riscos diferentes. Cada risco é comparado só consigo mesmo.

**Tabela:** Registro · Rnn · Secretaria · tipo de objeto · inerente (P × I, faixa) · residual (P × I, faixa) · situação da nota · situação da aceitação.

## 2. Correção — "As providências estão sendo cumpridas?"
**Visual principal:** linha do tempo horizontal, uma faixa por ação (Ann), com uma linha vertical marcando "hoje". Em cada faixa:
- início: plano aprovado pelo Secretário;
- marca do prazo original;
- marca de cada prorrogação, com rótulo "1ª" ou "2ª";
- prazo vigente;
- fim: executada, verificada pelo Comitê ou cancelada com aprovação.

**Número-resumo:** "N ações: em execução X · atrasadas X · aguardando verificação X · concluídas e verificadas X · canceladas X".

**Situações (decisões 6, 8 e 9):**
- **Concluída e verificada:** só depois da verificação por membro do Comitê de outra Secretaria. "Executada" sozinha aparece como "Aguardando verificação", nunca como concluída.
- **Atrasada:** prazo vigente vencido, sem conclusão verificada e sem cancelamento aprovado. Usa borda grossa, relógio e a palavra, sem vermelho. Pedido de prorrogação ainda não aprovado não muda o prazo vigente.
- **2ª prorrogação:** mostra o parecer do Comitê (favorável ou contrário). Se foi contrário e o Secretário manteve, aparece a marca "Prefeito notificado" (caso 10).
- **Cancelada:** só com aprovação do Secretário; mostra o motivo resumido, sem dados pessoais.
- Sem escalonamento automático (decisão 9). A tela mostra prazo e atraso; quem age é a pessoa.

**Incidentes (FORM 4 como incidente):** faixa própria, com as três datas separadas: ocorrência, conhecimento e comunicação. Ao lado, a marca do prazo de 3 dias úteis contado do conhecimento e a da complementação em até 20 dias úteis (Resolução CD/ANPD nº 15/2024). O registro do incidente é guardado por pelo menos 5 anos, mesmo sem comunicação. O "Sobre este número" explica isso.

**Tabela:** Registro · Ann · Secretaria · origem (risco Rnn ou encaminhamento direto do FORM 2) · prazo original · prorrogações · prazo vigente · situação · verificada por (papel: "Comitê").

## 3. Aprendizados — "O que a Prefeitura mudou por causa disso?"
**Visual principal:** um cartão grande em destaque, com setas para o anterior e o próximo. Na projeção, o cartão é a tela.

**Conteúdo do cartão** (os 3 campos de aprendizado do FORM 4, decisão 6):
- o que aconteceu, em uma frase e sem dados pessoais;
- o que mudou no procedimento;
- onde e desde quando vale (Secretaria e unidade, data).

No rodapé do cartão: "Ligado a N Registros", referência da evidência autorizada (identificador, não o arquivo) e "Verificado pelo Comitê em …".

**Número-resumo:** "N aprendizados publicados".

**Regras:**
- Só conta mudança de procedimento **verificada**. Rascunho, ocorrência sem melhoria comprovada ou ação ainda não verificada não aparecem.
- **Publicação:** o DPO confere que não há dados pessoais e a Secretaria autoriza (decisão 6). Sem as duas, o cartão não existe no dashboard.
- Um aprendizado ligado a vários Registros conta uma vez.
- Com os dados fictícios: 1 cartão (caso 3, fichas na sala de espera). Para a palestra, o agente propõe o texto fictício do cartão, que Ailton aprova.

**Tabela:** aprendizado · Secretaria · desde · Registros ligados · evidência (identificador) · verificado em.

## 4. Resumo do Prefeito, em detalhe (quadro 1 da Abertura)
Título: **"Precisa da sua atenção"**. Aparece só para o Prefeito e o DPO. As três linhas aparecem sempre; aqui o zero é dado verificado ("0 — nada pendente").

| Linha | Conta | Ao clicar, a lista mostra |
|---|---|---|
| Riscos Críticos aguardando sua aceitação | riscos com residual Crítico, nota conjunta confirmada e sem aceitação do Prefeito | Registro · Rnn · Secretaria · residual · **há N dias aguardando** · botão "Abrir o ato no FORM 3" |
| Segundas prorrogações mantidas contra o parecer do Comitê | ações em que o Secretário manteve a 2ª prorrogação com parecer contrário do Comitê | Registro · Ann · Secretaria · prazo vigente · data da notificação |
| Avaliações sem consenso no Comitê | riscos marcados "sem consenso" ainda sem deliberação do Comitê | Registro · Rnn · Secretaria · há N dias no Comitê |

**Regras:**
- O dashboard **não registra a aceitação**. "Abrir o ato no FORM 3" leva ao bloco 14, onde o ato fica registrado com autoria e trilha. O dashboard continua só de leitura.
- "Há N dias aguardando" fica sempre visível, sem cor de alarme. A responsabilidade da autoridade (decisão 8) se apoia no registro de quanto tempo o assunto ficou com ela, não em destaque visual.
- A notificação ao Prefeito (2ª prorrogação contrária) é um evento do FORM 4. O dashboard mostra que ela ocorreu; não é ele quem envia.
- Para o DPO, o título muda para "Pendências com o Prefeito e o Comitê", para não sugerir que a decisão é do DPO.

## 5. Perguntas ao agente (responder sem código)
a) Risco: as avaliações inerente e residual de cada Rnn ficam gravadas com o método ou versão da escala, de modo que dê para garantir "mesmo método" na comparação?
b) Risco: a aceitação por faixa (Secretário, Prefeito) e o parecer prévio do DPO para Alto já existem como atos no Lote 12? Quais faltam?
c) Correção: o FORM 4 guarda prazo original, cada prorrogação (com parecer do Comitê) e prazo vigente como dados separados, ou só o prazo atual?
d) Correção: a verificação pelo Comitê e o cancelamento com aprovação já são atos registrados?
e) Aprendizados: os 3 campos de aprendizado, a conferência do DPO e a autorização da Secretaria já existem? Há onde guardar a referência da evidência sem guardar o arquivo?
f) Resumo do Prefeito: a notificação automática do caso 10 já é gravada como evento? A contagem "há N dias" pode sair da trilha de eventos, sem campo novo?
g) Algum item desta parte contradiz o que já está implementado ou decidido?
