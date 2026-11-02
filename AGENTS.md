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
- Cada tela operacional deve esclarecer onde o usuário está, qual papel exerce, o que precisa fazer, qual ação está disponível e o que acontecerá ao executá-la.
- Informações institucionais devem apoiar o trabalho sem dificultar o acesso às perguntas e ações principais. Distinguir claramente o FORM 1 Integral do questionário sintético legado.

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

