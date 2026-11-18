# Sistema visual da PoC LGPD

## Finalidade

Esta pasta reúne as decisões visuais completas e versionadas do Sistema Municipal de Governança LGPD. O resumo de leitura rápida para agentes está em [`../contexto/design-system.md`](../contexto/design-system.md); a implementação vigente está em [`../../app/estaticos/estilo.css`](../../app/estaticos/estilo.css).

O sistema visual deve tornar estado, responsabilidade e próxima ação compreensíveis para o servidor, com sobriedade institucional e acessibilidade. Ele não substitui o manual oficial de identidade da Prefeitura de Hortolândia.

## Situação

- A PoC nuclear M1a permanece como referência aceita e estável.
- A paleta básica e os componentes atuais já estão aplicados em `estilo.css`.
- A separação em tokens, componentes, movimento e composição é proposta para incremento próprio da PoC ampliada.
- Nenhuma biblioteca externa de componentes ou animações foi escolhida.
- A PoC ampliada depende de decisão expressa e não começa por causa desta documentação.

## Documentos

| Documento | Conteúdo |
|---|---|
| [Cores e tokens](CORES_E_TOKENS.md) | Paleta vigente, significado, uso e evolução semântica proposta |
| [Decisões visuais](DECISOES_VISUAIS.md) | Histórico das decisões, limites e pontos ainda pendentes |
| [Padrões de interação](PADROES_DE_INTERACAO.md) | Regras acordadas nos FORMs 1 e 2, origem, implementação e capturas locais restritas |
| [Relatório dos padrões](RELATORIO_PADROES_DE_INTERACAO.md) | Componentes compartilhados, duplicações, propostas de unificação e equivalentes no dashboard |

O levantamento dos padrões de interação documenta os componentes existentes em 18/11/2026 e suas diferenças. Não implementa a unificação proposta nem novas telas. As regras mínimas de acessibilidade permanecem também no resumo de contexto.

## Guardrails

- Clareza antes de decoração.
- Uma ação principal evidente por etapa.
- Estado nunca comunicado somente por cor.
- Ajuda e erro próximos do campo correspondente.
- HTML semântico e CSS pequeno são a opção preferencial.
- Movimento deve explicar continuidade, mudança ou confirmação.
- `prefers-reduced-motion` deve ser respeitado.
- Nenhuma regra de domínio pode migrar para CSS ou JavaScript.
- Referências visuais orientam características; não autorizam copiar terceiros.
- Toda mudança visual deve possuir comparação antes/depois e testes proporcionais.

## Fontes relacionadas

- Cartilha LGPD e identidade institucional de Hortolândia.
- ADR 000 — Princípios e Guardrails do Projeto.
- `README.md`, seção “Evolução visual planejada para a PoC ampliada”.
- `docs/contexto/design-system.md`.
- `app/estaticos/estilo.css`.

