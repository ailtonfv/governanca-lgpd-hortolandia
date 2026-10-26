# Plano de estabilização antes do Bloco 5 — FORM 1 integral

**Data:** 26/10/2026

**Situação:** estabilização dos Blocos 1 a 4; não autoriza o Bloco 5

**Base preservada:** contrato nuclear 2 e contrato integral 3 candidato

## Correções executáveis desta rodada

1. **Preservação entre blocos.** Salvar novamente o Bloco 1 deve substituir somente os campos editáveis desse bloco. Participantes do Bloco 3, respostas dos demais blocos, metadados do envelope e histórico permanecem preservados.
2. **Aplicabilidade condicional.** Uma resposta cujo ramo deixou de ser aplicável sai do conjunto de respostas ativas e é mantida no histórico inativo, com o controlador e a versão da inativação. Payload forjado para ramo inativo é recusado.
3. **Participantes.** Participantes somente podem ser acrescentados quando `3.1 = Sim`. Se a resposta mudar, as ocorrências deixam o conjunto ativo sem serem apagadas do histórico.
4. **Navegação.** As quatro etapas permanecem visíveis. As Etapas 1 e 2 podem ser alternadas; as Etapas 3 e 4 ficam identificadas e desabilitadas até seus incrementos próprios.

## Canais transversais — desenho candidato, não implementado

O Serviço, Processo ou Atividade continua sendo a unidade de análise. Um mesmo Registro deverá poder relacionar mais de um canal quando todos fizerem parte do mesmo tratamento: Portal, 156, WhatsApp corporativo, atendimento presencial, Ouvidoria ou e-SIC. O canal não se transforma em objeto principal por ser porta de entrada.

A modelagem candidata é uma coleção de ocorrências de canal vinculadas ao Registro. Cada ocorrência deverá identificar o canal por código institucional e poderá conter somente os detalhes específicos daquele percurso. Os ramos de Ouvidoria e e-SIC deverão pertencer à ocorrência correspondente, e não funcionar como atributos globais ambíguos.

Antes de implementar, ainda é necessário decidir:

- quais respostas dos Blocos 2 e 8 são comuns ao tratamento e quais se repetem por canal;
- como representar um encaminhamento que começa em um canal e termina em outro;
- quando variações de execução configuram tratamentos autônomos e exigem Registros distintos;
- qual catálogo institucional identificará os canais e suas vigências.

Até essas decisões, o campo `2.1` permanece de escolha única e não deve ser interpretado como suporte definitivo a múltiplos canais.

## APA titular e substituição — desenho candidato, não implementado

Considera-se, para decisão institucional, um APA titular ativo por Secretaria e a possibilidade de substituição formal. A substituição deverá ser comando explícito, autorizado, idempotente, transacional e auditado, registrando Secretaria, titular anterior, substituto, autoridade responsável, fundamento, vigência e evento encadeado.

A troca não poderá:

- alterar retroativamente a autoria da abertura ou de atos anteriores;
- transferir automaticamente a responsabilidade do Registro para outra Secretaria;
- substituir automaticamente o ARP;
- conceder acesso a pessoa sem vínculo e autorização institucionais vigentes.

Permanecem pendentes a autoridade competente, a fonte da designação, as hipóteses de substituição, a vigência e a regra para coexistência temporária. Por isso, não foi criado modelo, migração, permissão ou comando nesta rodada.

## Critério para avançar

O Bloco 5 somente deve começar depois de a regressão confirmar as correções acima e de o desenho de canais ser decidido na extensão necessária ao próximo incremento. A estabilização não representa submissão integral nem aceite institucional adicional.
