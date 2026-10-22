# Relatório técnico preliminar do POC TS 009

Este relatório registra a execução técnica do cenário de volume da PoC nuclear. Ele demonstra o comportamento observado com massa totalmente sintética, mas ainda deverá ser associado ao commit do checkpoint e referenciado pelo pacote formal de evidências e pela ata de aceite do M1a.

## Cenário executado

| Item | Resultado |
|---|---:|
| Banco utilizado | `lgpd_poc_teste`, exclusivo para testes |
| Registros sintéticos | 1.000 |
| Eventos sintéticos | 50.000 |
| Eventos por cadeia | 50 |
| Cadeias verificadas integralmente | 1.000 |
| Amostra reconstruída | 25 Registros |
| Projeções coincidentes | 25 de 25 |
| Dados pessoais reais | nenhum |
| Resultado | **Aprovado** |

## Tempos observados

| Etapa | Duração |
|---|---:|
| Carga | 20,204 segundos |
| Verificação das cadeias e reconstrução | 5,503 segundos |
| Execução total | 27,298 segundos |

A execução terminou em **22/10/2026 às 07:49:51**, horário de Brasília, correspondente a `2026-10-22T10:49:51.495445+00:00` em UTC.

## Como o ensaio foi protegido

- o executor recusa bancos cujo nome não termine em `_teste`;
- a recriação das tabelas ocorre somente depois da confirmação explícita `--executar`;
- todos os Registros, comandos e eventos usam identificadores e conteúdos sintéticos;
- os eventos são lacrados com o mesmo texto canônico e o mesmo algoritmo SHA-256 usados pela aplicação;
- cada uma das 1.000 cadeias é relida do PostgreSQL e conferida quanto a sequência, elo anterior, conteúdo canônico e hash;
- a reconstrução usa o último estado e a última sequência do livro de atos e os compara com a projeção guardada no Registro.

## Resultado coloquial

O teste criou mil pastas fictícias. Cada pasta recebeu cinquenta atos, como se o Registro tivesse percorrido várias etapas. Depois, o sistema releu todos os cinquenta mil atos e conferiu se algum número pulou, se algum elo se perdeu ou se algum conteúdo deixou de combinar com o seu lacre. Nenhuma divergência foi encontrada. Em seguida, vinte e cinco pastas foram reconstruídas a partir do histórico e chegaram exatamente ao mesmo estado apresentado na consulta rápida.

## Reprodutibilidade

O executor está em `demonstracoes/poc_ts_009.py`. O teste rápido de regressão está em `testes/test_volume.py`. Com o ambiente `lgpd-poc` ativado, a execução formal usa:

```powershell
$env:BANCO_NOME='lgpd_poc_teste'
python -m demonstracoes.poc_ts_009 --executar
```

Antes do aceite institucional, o resultado deverá ser associado ao commit executado, referenciado pelo pacote `POC-EV` aplicável e conferido pelo responsável pelo aceite. Os artefatos operacionais de evidência permanecem fora do Git, conforme a política do `.gitignore`.
