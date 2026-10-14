# Revisão da Etapa 2c (prevenção de duplicidade) — pontos do Encarregado, 14/10/2026

Situação: a Etapa 2c **não** é registrada como evidência aceita até que os itens abaixo estejam resolvidos e testados.
Nome de trabalho da correção: **Etapa 2d**.

## A. Correções de código

| # | Ponto | Correção |
|---|---|---|
| A1 | Idempotência (ponto 2) | `comando_id` obrigatório em todo ato mutável; `hash_parametros` (JSON canônico, mesmo método do lacre) gravado no comando; mesma chave + mesmo hash → **resultado original idêntico** + indicador separado `reexecutado = true`; mesma chave + hash diferente → negado como reutilização indevida, com auditoria; colisão simultânea na chave primária `comando_pkey` → relê o comando e responde como reexecução. Comandos antigos sem hash: reexecução permitida, sem conferência (legado). Vale também para `executar_acao` (permissoes.py). |
| A2 | IntegrityError amplo (ponto 3) | Examinar `erro.orig.diag.constraint_name`; tratar só `uq_objeto_contexto_assunto_ativo` (e `comando_pkey`, em A1); se o ocupante não for encontrado, relançar; qualquer outra restrição → relançar. |
| A3 | Papel não pode depender da ordem da lista | Parâmetros explícitos: `objeto_principal_id`, `objetos_abrangidos_ids`, `objetos_citados` (com papel APOIO ou RELACIONADO). |
| A4 | Conflitos múltiplos | A verificação de equivalência devolve **todos** os conflitos (objeto, Registro, contexto, estado), não só o primeiro. |
| A5 | Ações sugeridas estáticas | Resposta passa a trazer: ações possíveis **para aquele ator**; ações apenas solicitáveis; unidade principal atual e designações vigentes (não `criado_por`); competência especial exigida (ex.: cancelar Registro Concluído, DA-37 item 4). Estados ativos e Suspenso passam a mostrar "cancelar (G11)"; Concluído, "cancelar (G11, competência reforçada)". |
| A6 | Ano do código LGPD | Ano pelo fuso `America/Sao_Paulo`, não UTC. |
| A7 | Alertas repetidos | Chave de deduplicação `(objeto_relacionado, registro, contexto, tipo_do_sinal)`, agregando as bases que fundamentaram o alerta. |
| A8 | Consultas unitárias em laço (N+1) | Ocorrências e alertas por JOIN (objeto, Registro, contexto). Baixa prioridade para o volume da PoC. |
| A9 | Verificação em dois momentos (ponto 1) | G1 = triagem **estrutural** (objeto, contexto, família, relações catalogadas, bases comuns). Submissão do FORM 1 (I3) = verificação **material** (finalidade, titulares, categorias de dados, compartilhamentos), alerta à governança, examinada na análise, refeita a cada versão submetida, sem bloqueio automático. Implementada junto com o ato de submissão. |

## B. Organização e execução (ponto 6)

- Pastas: `instalacao/`, `migracoes/`, `carga_ficticia/`, `demonstracoes/`, `testes/`; execução por `python -m pasta.script`.
- Migrações versionadas: tabela `versao_esquema` (número, nome, aplicada_em, aplicada_por) e aplicador único `python -m migracoes.aplicar`, que roda só as pendentes. A migração 2c2 é registrada como já aplicada.
- Testes automatizados (pytest) em **banco de teste próprio**, recriado a cada execução; nunca no banco da PoC.
- README e COLA_COMANDOS com os cinco blocos separados.

## C. Testes a acrescentar

1. chave idempotente repetida com conteúdo diferente;
2. duas requisições simultâneas com o mesmo `comando_id`;
3. erro de integridade que não seja a trava de equivalência (deve subir);
4. vários objetos, cada um ocupado por Registro diferente (todos listados);
5. objeto citado também informado como assunto;
6. contexto desativado; objeto desativado;
7. conta inativa; falta de papel;
8. justificativa vazia ou só com espaços;
9. advertência registrada no evento G1;
10. alertas deduplicados;
11. Registro cancelado permitindo nova criação;
12. Suspenso e Concluído continuando a bloquear;
13. mudança de ano no fuso de São Paulo.

Observação: 11 e 12 dependem dos atos de suspender, concluir e cancelar (M1b.1). Até lá, podem ser testados como **regra do banco**, preparando o estado diretamente no banco de teste, com o rótulo "provisório até o M1b.1".

## D. Decisões do Encarregado necessárias

1. ~~Cardinalidade do contexto~~ — **DECIDIDO pelo Encarregado (14/10/2026), D1 — Um contexto por Registro:** cada Registro possui exatamente um contexto de atuação, aplicável a todos os seus objetos PRINCIPAL e ABRANGIDO. Consequências: `contexto_atuacao_id` é atributo do Registro; o G1 recebe um único contexto; APOIO e RELACIONADO não ganham contexto próprio naquele Registro; outro contexto exige outro Registro e análise de autonomia; mudança posterior de contexto só por comando governado, com nova verificação de duplicidade e evento (ato futuro). Implementação: `registro.contexto_atuacao_id` NOT NULL + UNIQUE (id, contexto_atuacao_id); em `registro_objeto`, FK composta (registro_id, contexto_atuacao_id) → registro (id, contexto_atuacao_id), com CHECK: assunto ⇒ contexto preenchido; citado ⇒ contexto vazio (a FK composta não se aplica a linhas com contexto vazio). Parâmetros do G1: `objeto_principal_id`, `objetos_abrangidos_ids`, `objetos_citados`.
2. **Semântica da advertência de família**: quais das quatro formas de resolução (DA-38, item 6) entram na PoC; repetição da advertência a partir do terceiro contexto; sinalização também do Registro já existente; se a justificativa do elaborador é examinada depois, na análise.
3. **AB-02** (saída não programada como quinta situação de continuidade): antes do M1b.2.
4. ~~Numeração do código LGPD~~ — **DECIDIDO pelo Encarregado (14/10/2026), D4 — Numeração anual dos Registros:** "O código humano do Registro terá o formato `LGPD-AAAA-NNNNN`, em que `AAAA` corresponde ao ano civil da criação, apurado no fuso oficial `America/Sao_Paulo`, e `NNNNN` corresponde a uma sequência reiniciada a cada ano. Reabertura e novos ciclos preservam o código original. Números atribuídos não são reutilizados após cancelamento. O UUID permanece como identificador técnico permanente." Regras complementares: lacunas por falha ou concorrência são aceitáveis; unicidade no banco para `codigo_lgpd` e para `(ano, numero)`. Implementação: tabela `contador_registro (ano, ultimo_numero)`, atualizada na mesma transação do G1 por `INSERT ... ON CONFLICT (ano) DO UPDATE ... RETURNING` (substitui a sequência global `seq_codigo_lgpd`). Aplicação: nova base da PoC (dados fictícios), sem alterar códigos já gravados em eventos encadeados.

## E. Documentos

- SAD 10: DA-39 (verificação material na submissão; remissão na DA-38, item 9(c)); detalhamento da idempotência estrita (DA-26, item 3); formas de resolução da advertência e cardinalidade, conforme D1 e D2.
- LISTA_OBSERVACOES: O-82 retitulado "Consolidação documental da decisão do G11 no SAD 04"; O-83 idem para a DA-38.
- README: tabela de pendências com a coluna "Natureza" (decisão pendente × consolidação documental); cenário 8 dependente da implementação dos atos, não do SAD 04; próximos passos reordenados (ponto 5); verificação em dois momentos; situação da Etapa 2c como "em revisão".

## F. Ordem adotada (do Encarregado)

1. corrigir a idempotência;
2. restringir o tratamento de IntegrityError;
3. dividir a análise de duplicidade entre G1 e submissão do FORM 1;
4. converter `teste_contexto.py` em pytest;
5. alinhar DA-38, README e código quanto às formas de resolver a advertência;
6. esclarecer AB-02 e a cardinalidade de contexto;
7. somente então registrar a etapa como evidência aceita.
