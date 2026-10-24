# Relatório da rodada formal da PoC nuclear M1a

## Identificação

| Campo | Valor |
|---|---|
| Execução | `M1A-20261022-001` |
| Data | 22/10/2026 |
| Código executado | commit `df2db0f5b49579844eacd6107a633da14176f427` |
| Massa | exclusivamente sintética |
| Banco | `lgpd_poc_teste`, exclusivo para testes |
| Ambiente | Python 3.14.8; PostgreSQL 18.6; pytest 9.1.1; SQLAlchemy 2.1.4; FastAPI 0.147.0; psycopg 3.3.6 |
| Executor | Operador da PoC |
| Responsável pela validação técnica | Encarregado de Dados |

Esta rodada transformou a cobertura automatizada da PoC nuclear em uma execução identificada e reproduzível. Os artefatos operacionais permanecem no diretório local ignorado pelo Git `evidencias/M1A-20261022-001/`. Este relatório contém apenas resultados sintéticos e metadados necessários ao aceite.

## Resultado geral

| Verificação | Resultado observado |
|---|---:|
| Suíte automatizada | **189 de 189 testes aprovados** |
| Falhas | **0** |
| Erros | **0** |
| Testes ignorados | **0** |
| Tempo da suíte | 146,532 segundos |
| Ensaio de volume | **Aprovado** |
| Volume | 1.000 Registros e 50.000 eventos sintéticos |
| Cadeias verificadas | 1.000 de 1.000 |
| Reconstruções coincidentes | 25 de 25 |
| Tempo do ensaio de volume | 21,092 segundos |
| Dados pessoais reais | **Nenhum** |

## Cenários formais POC-TS

| Cenário | Resultado esperado | Resultado observado | Situação técnica |
|---|---|---|---|
| `POC-TS-001` | Repetição do mesmo `comando_id` devolve o resultado original sem novo evento. | Testes de idempotência dos atos e da chave concorrente aprovados. | **Aprovado** |
| `POC-TS-002` | Comandos simultâneos mantêm a sequência sem lacuna nem repetição. | Ensaios concorrentes de rascunho, submissão, conclusão e pendências aprovados. | **Aprovado** |
| `POC-TS-003` | Somente uma pessoa assume a análise ou pendência; a tentativa perdedora é negada e auditada. | Assunção única e auditoria da tentativa concorrente confirmadas. | **Aprovado** |
| `POC-TS-004` | Uma versão desatualizada não sobrescreve o rascunho atual. | Recusa confirmada no domínio e pela interface; conteúdo vigente preservado. | **Aprovado** |
| `POC-TS-005` | Falha entre evento e projeção não deixa gravação parcial. | Testes de atomicidade desfizeram evento, snapshot e projeção juntos. | **Aprovado** |
| `POC-TS-006` | Rollback de comando com vários eventos remove todo o comando. | Rollbacks dos percursos I3/G2, I4/G3, I5/G4 e I6/P1/G3 aprovados. | **Aprovado** |
| `POC-TS-007` | Acesso direto a Registro de outra Secretaria é negado e auditado. | Resposta negada, estado preservado e evento de auditoria confirmados. | **Aprovado** |
| `POC-TS-008` | A carga rejeita dado pessoal real antes de gravar. | Barreiras de identidade, CPF, e-mail e telefone recusaram a entrada sem gravação parcial nem reprodução do conteúdo suspeito. | **Aprovado** |
| `POC-TS-009` | 1.000 cadeias permanecem íntegras e a amostra reconstruída coincide com as projeções. | 50.000 eventos conferidos; 1.000 cadeias íntegras; 25 reconstruções coincidentes. | **Aprovado** |

## Pacotes POC-EV aplicáveis ao M1a

| Evidência | Critério | Resultado desta rodada |
|---|---|---|
| `POC-EV-001` | Requisitos obrigatórios implementados | Matriz do M1a coberta e suíte integral aprovada. |
| `POC-EV-002` | Todo teste obrigatório possui método | Os nove `POC-TS` possuem cobertura, resultado esperado e método identificados. |
| `POC-EV-003` | Cenários críticos de workflow executados | Cenários nucleares e seus testes de regressão aprovados. |
| `POC-EV-004` | Segregação de funções bloqueada | Tentativas incompatíveis foram negadas, auditadas e não alteraram o estado. |
| `POC-EV-005` | Histórico sem perda silenciosa | Versões, devoluções, reenvios, eventos e evidências anteriores permaneceram recuperáveis. |
| `POC-EV-006` | Versões anteriores recuperáveis | A Versão 1 permaneceu íntegra após a criação e validação da Versão 2. |
| `POC-EV-009` | Adulteração da cadeia detectada | Alteração, remoção e reordenação foram detectadas nos testes de integridade. |
| `POC-EV-011` | Estado reconstruível | As 25 reconstruções do ensaio de volume coincidiram com as projeções. |
| `POC-EV-014` | Ausência de dados reais | Massa e resultados usam marcadores sintéticos; tentativas em formatos pessoais foram recusadas. |
| `POC-EV-015` | Nenhum defeito crítico ou alto aberto | A rodada terminou sem falhas; não há defeito crítico ou alto registrado no escopo entregue. |

## Integridade dos artefatos operacionais

| Artefato local | SHA-256 |
|---|---|
| `pytest.xml` | `754B0E00E66C8B91FF42775CE939C696827C12A04E997B38C9B02773234489AA` |
| `poc-ts-009.json` | `B3EB53E3E4C1B192E3DC7B9401738625B9ABEE80CC178E1D24B3118E5AE29F5C` |

Os hashes permitem conferir que os arquivos apresentados à T.I. são os mesmos produzidos nesta rodada. A política do repositório mantém esses artefatos fora do Git.

## Limitações conhecidas

- O checkpoint externo da cadeia e a custódia institucional correspondente permanecem no backlog. A PoC nuclear demonstra a cadeia interna e a detecção de três classes de adulteração.
- Temporalidade e descarte dependem da tabela oficial e do grupo municipal responsável. A PoC nuclear não elimina automaticamente dados, além de usar somente massa fictícia.
- O Encarregado de Dados confirmou a validação técnica do M1a em 22/10/2026 com estas limitações conhecidas. A apresentação do repositório e da solução à T.I. permanece pendente e não equivale a aceite institucional.

## Conclusão técnica

Os nove cenários formais da PoC nuclear estão tecnicamente aprovados. A execução identificada, os resultados consolidados e os hashes dos artefatos sustentaram a validação técnica do M1a pelo Encarregado de Dados em 22/10/2026. Permanece pendente a apresentação do repositório e da solução à T.I. A validação técnica não inicia automaticamente a PoC ampliada nem substitui eventual formalização institucional.
