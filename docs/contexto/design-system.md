# Diretrizes do sistema visual

## Objetivo

Criar uma interface municipal clara, acolhedora, confiável e acessível. A identidade deve ajudar o servidor a compreender estado, responsabilidade e próxima ação sem enfraquecer a sobriedade institucional.

Este documento orienta a evolução visual da PoC ampliada. Ele não substitui o manual oficial de identidade da Prefeitura.

## Princípios

- Clareza antes de decoração.
- Uma ação principal evidente por etapa.
- Linguagem funcional próxima do servidor.
- Estado nunca comunicado somente por cor.
- Ajuda contextual junto do campo que provoca dúvida.
- Movimento somente para indicar continuidade, mudança ou confirmação.
- Brasão preservado sem distorção e com área de respiro.

## Base visual já existente

| Token atual | Valor | Uso |
|---|---|---|
| Azul principal | `#075985` | links, ação primária e seleção |
| Azul escuro | `#0C3B5A` | cabeçalho e títulos |
| Verde | `#166534` | sucesso e próxima ação |
| Fundo | `#F4F7F9` | superfície geral |
| Texto | `#17212B` | conteúdo principal |
| Borda | `#D6E0E6` | separação de campos e blocos |
| Branco | `#FFFFFF` | superfícies de leitura |

Estados atuais usam também vermelho para bloqueio, âmbar para atenção, verde para sucesso e azul claro para estados informativos.

## Evolução proposta para a PoC ampliada

Organizar os estilos em tokens e componentes, sem mudar a regra do domínio:

```text
app/estaticos/
├── tokens.css       cores, tipografia, espaços, raios e sombras
├── components.css   botões, campos, mensagens, tabelas e etapas
├── motion.css       transições e preferência por movimento reduzido
└── estilo.css       composição das páginas
```

Não criar essa divisão até existir um incremento próprio com comparação visual e testes de regressão da interface.

## Componentes prioritários

- cabeçalho institucional;
- identificação do agente e da Secretaria;
- indicador de etapa;
- campo com ajuda e exemplo;
- seleção de serviço, processo ou atividade;
- estado do Registro e do FORM;
- mensagem de sucesso, atenção, bloqueio e erro;
- tabela responsiva;
- linha do tempo de atos;
- cartão de pendência e próxima ação;
- diálogo de confirmação para atos irreversíveis.

## Acessibilidade

- WCAG AA é o mínimo para contraste, teclado, foco e leitura por tecnologia assistiva.
- Buscar contraste AAA para textos essenciais quando a identidade visual permitir.
- Preservar foco visível e ordem lógica de tabulação.
- Associar ajuda e erro ao campo com atributos semânticos.
- Não esconder conteúdo essencial em `hover`.
- Usar texto e ícone além da cor.
- Manter alvos confortáveis em telas pequenas.

## Movimento

- Duração recomendada: 150 a 250 ms.
- Usar em confirmação de salvamento, expansão de seção e mudança de etapa.
- Evitar movimento contínuo, parallax, piscadas ou animação que atrase o trabalho.
- Respeitar obrigatoriamente:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

## Referências visuais

O processo pode usar um pequeno painel de referências escolhido pelo responsável do produto. A IA deve extrair características como temperatura das cores, contraste, densidade, formas e sensação geral; não deve copiar marcas, telas ou ilustrações de terceiros.

Para este sistema, as referências devem transmitir:

- serviço público e confiança;
- organização e rastreabilidade;
- acolhimento sem informalidade excessiva;
- leitura simples em ambientes administrativos;
- consistência com a Cartilha LGPD e a Prefeitura de Hortolândia.

## Validação de um incremento visual

1. comparar antes e depois em desktop e largura reduzida;
2. testar teclado e foco;
3. verificar contraste;
4. conferir mensagens, erros e estados vazios;
5. executar testes HTTP existentes;
6. validar que nenhuma regra migrou para CSS ou JavaScript;
7. registrar a decisão visual e as limitações.

## Documentação completa

- [`docs/design-system/README.md`](../design-system/README.md) — finalidade, situação e guardrails.
- [`docs/design-system/CORES_E_TOKENS.md`](../design-system/CORES_E_TOKENS.md) — paleta aplicada e evolução semântica proposta.
- [`docs/design-system/DECISOES_VISUAIS.md`](../design-system/DECISOES_VISUAIS.md) — histórico e decisões pendentes.

