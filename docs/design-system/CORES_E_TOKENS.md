# Cores e tokens

## Paleta aplicada na PoC nuclear

| Token vigente | Valor | Uso principal |
|---|---:|---|
| `--azul` | `#075985` | ação primária, links e seleção |
| `--azul-escuro` | `#0C3B5A` | cabeçalho e títulos |
| `--verde` | `#166534` | sucesso e próxima ação |
| `--fundo` | `#F4F7F9` | superfície geral |
| `--texto` | `#17212B` | conteúdo principal |
| `--borda` | `#D6E0E6` | separação de campos e blocos |
| `--branco` | `#FFFFFF` | superfícies de leitura |

Vermelho, âmbar, verde e azul claro complementam os estados operacionais. Texto e, quando pertinente, ícone ou estilo de borda devem acompanhar a cor.

## Evolução semântica proposta

Na PoC ampliada, os nomes poderão expressar finalidade em vez da aparência:

```css
:root {
  --cor-acao: #075985;
  --cor-titulo: #0c3b5a;
  --cor-sucesso: #166534;
  --cor-fundo: #f4f7f9;
  --cor-texto: #17212b;
  --cor-borda: #d6e0e6;
}
```

Assim, uma alteração institucional pode ser feita num ponto único e repercutir de modo coerente nos componentes que usam o token. Esse exemplo não altera o CSS vigente e não constitui autorização para iniciar a PoC ampliada.

## Regras de uso

- Não escolher uma cor isoladamente: conferir contraste no contexto real.
- WCAG AA é o mínimo; buscar AAA para textos essenciais quando compatível.
- Foco de teclado deve permanecer visível.
- Erro, bloqueio, atenção e sucesso devem possuir texto compreensível.
- O brasão deve manter proporção e área de respiro.
- Novos tokens exigem nome semântico, finalidade e registro da decisão.

