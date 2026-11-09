# Etapa 1 do FORM 2 · contrato candidato de respostas v1

**Para decisão funcional · 09/11/2026.** A aplicação continua usando F2-DEMO-PREP-v1 para a anotação geral. A proposta abaixo exige aprovação específica antes da implementação. A [matriz de fatos](MATRIZ-F2-ETAPA1-FATOS-F1-v1.md) identifica os subsídios dos 47 itens.

## Percurso proposto

Identificar Registro, AAL, preparação e origem histórica antes dos blocos. Exibir “ETAPA 1 DE 4 / SEÇÃO Y DE 14”, com Y de 1 a 4. Mostrar as etapas 2 a 4 como “Ainda não disponível na PoC”, sem controles de edição. Em cada seção, usar três áreas:

| Área | Fonte | Ação |
|---|---|---|
| A · Fatos | Registro e snapshot autorizado, com enunciado da respectiva edição | Consultar, inclusive quando houver lacunas ou itens ausentes na origem |
| B · Perguntas e orientações | Versão identificada do catálogo local | Ler. Informar indisponibilidade se a edição não estiver instalada |
| C · Respostas | Versão própria da preparação | AAL designado e habilitado salva o bloco. Demais agentes consultam exclusivamente quando autorizados |

O código do Registro é um vínculo. A confirmação de contexto e as análises são atos próprios. Competência para manifestação jurídica, decisão e aceitação de pendências continua dependente de definição institucional.

## Contrato proposto · F2-ETAPA1-RESPOSTAS-v1

- **Identidade.** Uma preparação pertence a um Registro e aponta permanentemente para o identificador, versão e lacre de sua origem. Guardar a edição do catálogo, da matriz factual e do contrato utilizados. Revisão factual posterior permite nova preparação com origem explícita. A anterior permanece consultável como foi apresentada.
- **Escrita.** Comando por bloco com preparação, bloco, versão lida, identificador idempotente e alterações por ID. Validar identidade e autorização no servidor, vínculo ao Registro, ciclo, vigência, edição e pertinência dos IDs ao bloco. Proposta de atualização parcial: omissão preserva o valor, remoção explícita registra ato distinto; bloco incompleto pode ser salvo. A chave do Registro e fatos históricos não são entradas editáveis.
- **Controles.** O catálogo identifica escolha única para F2-2.9, F2-2.9.2 e F2-2.9.3, e múltipla para F2-2.9.1. Ler os valores da edição local. Para os demais itens, o catálogo v1 não especifica listas de escolha estruturadas. Confrontar com o Mestre e validar tipo, cardinalidade, obrigatoriedade e eventuais complementos antes de abrir edição. Não deduzir controle apenas do enunciado.
- **Condições documentadas.** F2-2.9.1 fica ativa com “Sim” em F2-2.9. F2-2.9.3 fica ativa com “Sim” em F2-2.9.2. Alterar a resposta principal preserva a filha e seu histórico como inativos. Proposta conservadora para reativação: mostrar o valor anterior e solicitar confirmação explícita antes de fazê-lo valer novamente. Pontos de obrigatoriedade e reativação aguardam decisão.
- **Pendências.** Registrar “A CONFIRMAR” apenas onde a edição oferece essa alternativa. Distinguir dúvida da análise no FORM 2 de insuficiência factual na origem. Na segunda, referenciar versão, pergunta e ocorrência pertinentes para esclarecimento, sem editar o FORM 1. Reservar referência à futura destinação de F2-14.3.1. Nesta etapa não há encaminhamento automático, prazo ou instância decisória definidos.
- **Versões.** Usar a revisão da preparação como controle otimista inicial, inclusive entre blocos. Repetir o mesmo comando com a mesma carga deve devolver o resultado original; reutilizar o identificador com outra carga deve ser recusado. Concorrência deve informar conflito e preservar a edição local para revisão. Em transação única, registrar conteúdo, versão, autor, papel, instante, origem, comando, evento e auditoria. Falha deve deixar a versão anterior íntegra.
- **Compatibilidade.** A anotação geral continua autônoma. Nenhuma frase será promovida a resposta. Leitura da versão histórica deve resolver tipos e rótulos da edição identificada. Preparações v1 e origens REV13, GUARDA, MEDIDAS, combinadas e REV18 devem continuar legíveis. A mesma pessoa em diferentes papéis continua sujeita à autorização específica de cada ato.

## Opções de persistência

| Alternativa | Impacto no banco | Condição para escolher |
|---|---|---|
| Evolução explícita do envelope JSON de preparação e eventos | Pode dispensar migração física caso coluna, limites e validações existentes comportem o novo contrato. Exige leitor/escritor versionados, atualização da verificação de integridade e concorrência compartilhada com anotação. | Fazer prova isolada de leitura v1, salvamento v2 e rollback. Primeira alternativa a avaliar. |
| Estrutura própria de versões por preparação e bloco | Exige migração aditiva, chaves referenciais, restrições de unicidade e ligação transacional à auditoria. | Justificar por consultas, concorrência entre blocos ou requisitos de histórico que a primeira opção não atenda. |

Decidir forma de adoção para preparações antigas, política de reativação, atribuição das pendências e controle dos itens sem definição estruturada. Disponibilizar editorialmente as respostas admitidas só em instalação autorizada.

## Incrementos de verificação e esforço

| Incremento candidato | Prova de aceite com dados fictícios | Esforço indicativo |
|---|---|---|
| Aprovar matriz, controles e origem | 47 IDs distintos em ordem, quatro blocos, fatos resolvidos por versão, separação Registro/FORM 1/FORM 2 e exemplos de ausência de informação | 3–5 h |
| Comando de um bloco e compatibilidade | AAL válido pode salvar, APA acompanhante apenas consulta, negação cruzada por Registro/origem, expiração, revogação, repetição e alteração concorrente, rollback e leitura de v1 | 6–10 h |
| Unidade de guarda e navegação | Duas condições, valores inativos preservados, “A CONFIRMAR”, voltar/retomar sem perda, origem imutável, catálogo ausente e navegação por teclado em 400 px | 4–7 h |
| Demais blocos da Etapa 1 e regressão | Instrumentar somente os controles aprovados. Verificar demais 43 itens, anotação independente, integridade da cadeia, histórico por edição, bloqueios institucionais e aceite humano APA/AAL | 7–12 h |

Faixa preliminar de 20–34 horas de trabalho para a Etapa 1, assumindo catálogo disponível, decisões de tipos resolvidas e suficiência do envelope atual. Exclui espera de aprovação, migração eventual e etapas seguintes. Principais riscos são atribuir valor jurídico automático a um fato, misturar origens históricas e perder respostas quando muda um gatilho.
