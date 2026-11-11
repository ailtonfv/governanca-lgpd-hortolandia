# Instruções de trabalho para agentes de IA

Leia este arquivo antes de alterar código ou documentação. Em seguida, leia somente os resumos necessários em `docs/contexto/` e abra os documentos completos indicados por eles quando a tarefa exigir detalhe.

## Ordem de leitura

1. `docs/contexto/context.md` — produto, estágio e limites.
2. `docs/contexto/domain.md` — linguagem e regras do domínio.
3. `docs/contexto/architecture.md` — stack, camadas e padrões.
4. `docs/contexto/testing.md` — estratégia e execução dos testes.
5. `docs/contexto/design-system.md` — identidade visual e acessibilidade, quando houver interface.
6. `docs/contexto/glossary.md` — termos que precisem de definição.

## Visão do produto e fase autorizada

- O produto é o Sistema Municipal de Governança LGPD. Os quatro instrumentos integram o mesmo ciclo e o mesmo Registro LGPD: FORM 1 — levantamento factual do tratamento; FORM 2 — análise e validação jurídica e institucional; FORM 3 — avaliação de riscos e controles; FORM 4 — providências, responsáveis, prazos, evidências e acompanhamento. Não são sistemas independentes.
- A PoC ampliada atualmente autorizada concentra-se no FORM 1 Integral, com meta de demonstração em meados de dezembro de 2026. O produto completo terá os quatro FORMs integrados, recursos de governança, relatórios e dashboards; o piloto fica fora do escopo. A visão do produto completo não autoriza automaticamente sua implementação nesta fase.
- A implementação atual concentra-se no FORM 1 Integral REV13, com 128 campos e 14 blocos. O ciclo de apresentação pelo ARP, conferência pelo APA, devolução, reapresentação e confirmação interna está implementado.
- A submissão institucional permanece bloqueada. Os FORMs 2, 3 e 4 pertencem à arquitetura futura e exigem autorização específica para implementação, assim como novos relatórios e dashboards.
- Esta atualização de 02/11/2026 explicita a distinção entre a visão do produto completo e o escopo atual da PoC ampliada, concentrado no FORM 1 Integral. Limites de incrementos, contratos e permissões continuam vigentes; divergências com resumos e documentos anteriores devem ser registradas, sem alterar essas fontes automaticamente.

## Experiência do servidor e critérios de aceitação

- Código implementado não significa funcionalidade aceita. Distinguir: **implementado** — código desenvolvido e testes automatizados executados; **verificado funcionalmente** — comportamento confrontado com requisitos aprovados; **aceito** — utilização demonstrada e validada para o escopo previsto.
- Não declarar facilidade de uso apenas pela aprovação de testes automatizados. Quando a inspeção visual não puder ocorrer, registrar explicitamente **NÃO VERIFICADA**.
**Padrão institucional de ações e navegação.**

- Nos quatro FORMs, no Dashboard, na Administração Central e nas telas compartilhadas, alinhar os comandos à direita da respectiva região. Em telas estreitas, permitir a largura total. Manter ordem lógica de leitura e teclado, foco visível e permissões vigentes.
- Cada cartão de Registro deve destacar uma ação principal conforme o papel e o estado, com nomenclatura uniforme, próxima providência e ações secundárias distintas. Cada destino de retorno deve aparecer uma única vez na região.
- Cada tela operacional deve esclarecer onde o usuário está, qual papel exerce, o que precisa fazer, qual ação está disponível e o que acontecerá ao executá-la.
- Informações institucionais devem apoiar o trabalho sem dificultar o acesso às perguntas e ações principais. Distinguir claramente o FORM 1 Integral do questionário sintético legado.

## Identificação visível das perguntas — decisão de 11/11/2026

- Exibir cada pergunta e referência a pergunta no formato `F{número do FORM}-{identificador editorial} — enunciado`. Exemplos: `F1-1.2`, `F2-1.2`, `F2-9W.1`. Conservar integralmente o identificador editorial: no FORM 3, o item `3.55` aparece como `F3-3.55`; no FORM 4, `4.25` aparece como `F4-4.25`.
- Aplicar o padrão aos rótulos de preenchimento, consultas de origem e histórico, pendências, consolidação, ajudas e referências cruzadas, inclusive nos documentos gerados em novas versões. Uma pergunta da origem FORM 1 mantém o prefixo `F1-` quando exibida dentro do FORM 2.
- Acrescentar o prefixo uma única vez. Um identificador já qualificado, como `F2-1.2`, não pode virar `F2-F2-1.2`. Preservar os sufixos dos ramos temáticos e distinguir o número do conjunto repetido do identificador da pergunta.
- Esta é uma regra de apresentação. Não renomear chaves de banco, catálogo privado, parâmetros dos formulários, contratos, eventos, snapshots ou âncoras existentes. Não migrar respostas nem reescrever documentos históricos publicados por causa do prefixo visual.
- Manter a régua com números de blocos (1 a 14); ela identifica blocos, não perguntas. Não alterar o Identificador LGPD do processo.
- Centralizar a formatação em recurso reutilizável da apresentação, evitando regras divergentes entre telas. Conferir também os nomes acessíveis e preservar o funcionamento dos links.
- Critério de conferência: a mesma pergunta tem o mesmo identificador visível no preenchimento, na consulta histórica e na pendência; prefixo não duplicado, ramos preservados e respostas antigas continuam acessíveis.
- Situação em 11/11/2026: aplicada às telas do FORM 1 (preenchimento, consulta, conferência e pendências) e às referências de origem exibidas no FORM 2. Formatação centralizada em macro de apresentação. Documentos publicados permanecem intactos; revisão das demais saídas e aplicação futura aos FORMs 3 e 4 devem ser registradas separadamente.

## Regras que nunca podem ser inferidas ou flexibilizadas

- Use exclusivamente dados fictícios. Nunca grave nome, matrícula, CPF, senha, token ou outro dado pessoal real no código, testes, documentos, logs ou evidências.
- A Cartilha LGPD e os SADs são as fontes funcionais e arquiteturais oficiais. Os arquivos de contexto apenas resumem e apontam para essas fontes.
- Não invente regra ausente. Registre a dúvida e relacione-a à observação ou decisão arquitetural apropriada.
- O avanço da PoC ampliada e o início de incrementos adicionais exigem autorização expressa; a visão completa do produto não amplia o incremento autorizado.
- Somente APA autorizado abre o Registro LGPD. Pode assumir o preenchimento ou designar outro ARP mediante ato explícito, autorizado e auditável; a indicação não concede acesso automaticamente.
- O ARP preenche e apresenta para conferência. O APA confere, devolve ou confirma internamente. Esses atos não equivalem à submissão institucional, homologação ou validação jurídica.
- A T.I. administra e monitora segundo suas permissões, sem receber obrigatoriamente formulários nem obter acesso adicional ao conteúdo por esse motivo.
- Contratos e matrizes permanecem versionados. A matriz de obrigatoriedade ainda depende de aprovação institucional; não liberar submissão institucional sem autorização específica.
- Preserve histórico, autoria, idempotência, segregação de funções, atomicidade, auditoria e cadeia de eventos.
- Um Registro permanece sob responsabilidade de uma Secretaria. Participação de outra Secretaria não transfere automaticamente essa responsabilidade.
- Serviço, processo e atividade são objetos. Canal é uma dimensão transversal e só recebe Registro próprio quando realiza tratamento autônomo.
- Contexto de atuação não é finalidade, Secretaria, canal nem hipótese legal.
- O titular é representado por categorias. O sistema de mapeamento não cadastra pessoas titulares.
- Autenticação real e integração com cadastro funcional não serão improvisadas na PoC.

## Governança das referências FORM 1 × Cartilha LGPD

A Cartilha LGPD é uma referência institucional versionada, integrada às ajudas contextuais do FORM 1 Integral REV13.

**Regras obrigatórias para qualquer agente que modificar a Cartilha, as ajudas contextuais ou seus vínculos:**

1. Preservar identificadores temáticos estáveis, sem depender exclusivamente de números de página.
2. Manter explícita a versão da Cartilha associada a cada referência.
3. Ao incorporar nova revisão, verificar a correspondência entre as perguntas REV13, os assuntos e as seções efetivamente existentes.
4. Executar testes automatizados dos vínculos navegáveis, verificando a disponibilidade e a correspondência dos destinos.
5. Não substituir silenciosamente referências históricas nem eliminar versões anteriores sem decisão expressa e avaliação dos impactos.
6. Quando uma seção for renomeada, dividida, reunida ou excluída, atualizar o mapa de correspondência e registrar a alteração.
7. Não inventar links, âncoras, páginas ou conteúdos inexistentes.
8. Preservar a possibilidade de consultar a Cartilha sem perder respostas ou interromper o preenchimento do FORM 1.
9. Atualizar o README.md quando houver alteração efetiva no funcionamento.
10. Distinguir sempre uma regra documentada de uma funcionalidade efetivamente implementada e testada.

**Critério de aceite:** nenhuma atualização da integração FORM 1 × Cartilha poderá ser considerada concluída sem a verificação dos vínculos afetados e o registro dos resultados.

A publicação externa da Cartilha exige autorização institucional específica. Sua disponibilização na PoC permanece local e somente para leitura, conforme a configuração vigente.

## Publicação e continuidade técnica da PoC

O repositório público `ailtonfv/governanca-lgpd-hortolandia` deverá reunir progressivamente o código versionado dos quatro FORMs e do dashboard demonstrativo, os testes automatizados e a documentação técnica publicável. A meta é permitir a continuidade técnica pela Prefeitura em outra estação de desenvolvimento.

- Publicar seletivamente o que estiver implementado e verificado, após revisão de segurança de todos os commits a enviar.
- Manter fora do GitHub Documentos-Mestres protegidos, catálogos privados (inclusive o catálogo operacional de 250 perguntas do FORM 2), dados pessoais reais, segredos, credenciais e outros artefatos restritos.
- Usar conteúdo sintético nos testes públicos. Instalações sem os catálogos privados devem indicar quais unidades estão indisponíveis e preservar o restante da navegação autorizada.
- Distinguir implementação, testes, homologação humana e publicação. A implantação institucional em produção depende de decisão própria.
- Preservar o vínculo dos quatro instrumentos ao mesmo Registro LGPD.

## Ao alterar código

- Antes de modificar, identificar o requisito funcional, inspecionar a implementação existente, determinar a causa do problema e propor a menor correção necessária, com testes e critérios objetivos de aceite. Preservar contratos, dados históricos e permissões.
- Não confundir correção de defeito com ampliação de escopo nem apresentar uma implementação parcial como atendimento integral do requisito.
- Mantenha as regras no domínio, não nas páginas HTML nem no banco.
- Use uma transação para evento, auditoria, snapshot e projeção relacionados ao mesmo comando.
- Use `comando_id` para idempotência e controle otimista quando houver versão lida.
- Execute testes somente no banco cujo nome termina em `_teste`.
- Escreva testes no padrão Arrange–Act–Assert e inclua negações, concorrência e rollback quando aplicáveis.
- Atualize contrato, README, matriz de aceite ou diário quando a mudança alterar comportamento documentado.

## Antes de concluir uma tarefa

- Confirme o escopo e os documentos de origem.
- Verifique que não entrou dado pessoal real.
- Execute os testes proporcionais ao risco.
- Registre resultado, limitação e decisão pendente sem declarar aceite institucional antes da ata.

