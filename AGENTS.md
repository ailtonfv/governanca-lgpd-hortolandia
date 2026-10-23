# Instruções de trabalho para agentes de IA

Leia este arquivo antes de alterar código ou documentação. Em seguida, leia somente os resumos necessários em `docs/contexto/` e abra os documentos completos indicados por eles quando a tarefa exigir detalhe.

## Ordem de leitura

1. `docs/contexto/context.md` — produto, estágio e limites.
2. `docs/contexto/domain.md` — linguagem e regras do domínio.
3. `docs/contexto/architecture.md` — stack, camadas e padrões.
4. `docs/contexto/testing.md` — estratégia e execução dos testes.
5. `docs/contexto/design-system.md` — identidade visual e acessibilidade, quando houver interface.
6. `docs/contexto/glossary.md` — termos que precisem de definição.

## Regras que nunca podem ser inferidas ou flexibilizadas

- Use exclusivamente dados fictícios. Nunca grave nome, matrícula, CPF, senha, token ou outro dado pessoal real no código, testes, documentos, logs ou evidências.
- A Cartilha LGPD e os SADs são as fontes funcionais e arquiteturais oficiais. Os arquivos de contexto apenas resumem e apontam para essas fontes.
- Não invente regra ausente. Registre a dúvida e relacione-a à observação ou decisão arquitetural apropriada.
- A PoC ampliada não começa automaticamente. Ela exige decisão expressa após o aceite institucional do M1a.
- A PoC ampliada cobre o FORM 1 integral. Os FORMs 2, 3 e 4 permanecem na arquitetura para etapa posterior.
- Preserve histórico, autoria, idempotência, segregação de funções, atomicidade, auditoria e cadeia de eventos.
- Um Registro permanece sob responsabilidade de uma Secretaria. Participação de outra Secretaria não transfere automaticamente essa responsabilidade.
- Serviço, processo e atividade são objetos. Canal é uma dimensão transversal e só recebe Registro próprio quando realiza tratamento autônomo.
- Contexto de atuação não é finalidade, Secretaria, canal nem hipótese legal.
- O titular é representado por categorias. O sistema de mapeamento não cadastra pessoas titulares.
- Autenticação real e integração com cadastro funcional não serão improvisadas na PoC.

## Ao alterar código

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

