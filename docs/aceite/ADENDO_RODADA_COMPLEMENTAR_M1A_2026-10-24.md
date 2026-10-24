# Adendo da rodada complementar do M1a — 24/10/2026

Este adendo registra uma verificação técnica complementar executada depois do refinamento que separou a autorização de abertura do Registro da autorização de preenchimento do FORM 1. Ele preserva a rodada formal anterior e **não altera a minuta de ata já documentada nem declara novo aceite institucional**.

## Identificação

| Campo | Valor |
|---|---|
| Execução | `M1A-20261024-002` |
| Data | 24/10/2026 |
| Checkpoint testado | `cada2fc5201225bd25c1a5e5163d0e421d85bd52` |
| Banco | `lgpd_poc_teste`, exclusivo para testes |
| Ambiente | Python 3.14.8; PostgreSQL local; pytest |
| Dados | exclusivamente fictícios |

## Escopo verificado

- `responsavel_registro` abre e coordena o Registro em nome da Secretaria;
- `preenchedor` inicia, salva, ajusta e submete o FORM 1 quando autorizado;
- uma mesma pessoa pode acumular as duas autorizações;
- um servidor apenas preenchedor pode colaborar, mas não abrir novo Registro;
- cada ação mantém autoria individual, versão e auditoria;
- as consultas e a interface respeitam a responsabilidade institucional da Secretaria.

## Resultado

| Medida | Resultado |
|---|---|
| Testes coletados | 193 |
| Aprovados | 193 |
| Falhas | 0 |
| Erros | 0 |
| Ignorados | 0 |
| Duração | 170,717 segundos |

O relatório JUnit local foi produzido em `.codex-build/M1A-20261024-002-pytest.xml`, diretório ignorado pelo Git. Seu SHA-256 é:

```text
b5d841b475b9649a53a026c10143bfcc29c0b6b7e2578889c2184821f5348c3a
```

## Limites desta execução

O ensaio pesado do `POC-TS-009` não foi repetido nesta rodada complementar. A evidência de volume permanece vinculada à rodada formal `M1A-20261022-001`, que executou 1.000 Registros, 50.000 eventos, verificou 1.000 cadeias e reconstruiu 25 projeções sem divergência.

Esta execução demonstra a regressão do refinamento de papéis no checkpoint indicado. Ela não inicia a PoC ampliada, não altera a ata existente e não substitui qualquer decisão institucional.
