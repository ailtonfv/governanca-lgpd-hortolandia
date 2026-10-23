# Estratégia de testes

## Objetivo

Os testes demonstram que a regra funciona, que uma ação proibida não produz efeito e que falhas ou concorrência não deixam o sistema parcialmente atualizado.

Teste aprovado não equivale sozinho a aceite institucional. O caminho é:

`regra → cenário POC-TS → teste automatizado → evidência POC-EV → ata`

## AAA

Os testes devem seguir Arrange–Act–Assert:

1. **Arrange:** preparar massa fictícia, papéis, estados e versões.
2. **Act:** executar um comando ou uma tentativa controlada.
3. **Assert:** conferir resultado, estado, eventos, auditoria e ausência de efeito indevido.

Use comentários AAA apenas quando tornarem um teste complexo mais fácil de ler. A separação estrutural importa mais que os rótulos.

## Regras de segurança

- O banco deve terminar em `_teste`; o padrão é `lgpd_poc_teste`.
- A suíte recria o esquema e limpa as tabelas.
- Use apenas pessoas, matrículas, nomes, objetos e Registros com marcadores fictícios.
- Nunca copie dado pessoal real para testar rejeição. Use valores simulados nos formatos que a barreira deve detectar.
- Resultados operacionais ficam em `evidencias/`, fora do Git.

## Cobertura esperada por mudança

| Mudança | Teste mínimo |
|---|---|
| Regra simples | caminho permitido e principal recusa |
| Novo ato | autorização, estado inicial, efeito, evento, auditoria e idempotência |
| Ato com várias gravações | rollback integral |
| Escrita com versão | tela ou comando desatualizado |
| Assunção ou decisão única | concorrência com dois agentes |
| Novo campo categórico | código válido, desconhecido, repetido e campo extra |
| Interface | visibilidade, envio válido, envio forjado e resposta ao usuário |
| Migração | aplicação em base existente e preservação do histórico |
| Segurança | tentativa negada, auditoria e estado inalterado |

## Comandos

Com o ambiente `lgpd-poc` ativado:

```powershell
python -m pytest -q
```

Ensaio pesado do M1a:

```powershell
$env:BANCO_NOME='lgpd_poc_teste'
python -m demonstracoes.poc_ts_009 --executar
```

## Estado de referência do M1a

- 189 testes automatizados aprovados.
- 9 de 9 cenários `POC-TS` tecnicamente aprovados.
- Relatório: `docs/aceite/RELATORIO_RODADA_FORMAL_M1A_2026-10-22.md`.
- Matriz: `docs/aceite/MATRIZ_ACEITE_M1A.md`.
- Commit do código ensaiado: `df2db0f5b49579844eacd6107a633da14176f427`.

## Dois significados de AAA

Neste documento, AAA significa Arrange–Act–Assert. Em `design-system.md`, AAA pode significar o nível mais exigente das diretrizes WCAG de acessibilidade. Não confunda os dois usos.

