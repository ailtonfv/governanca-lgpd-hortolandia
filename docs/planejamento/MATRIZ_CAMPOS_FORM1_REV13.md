# Matriz das perguntas do FORM 1 integral — REV13

**Identificador da matriz:** `MATRIZ-F1-REV13-OBR-v1`
**Situação:** fonte declarativa central da obrigatoriedade; a submissão pelo contrato 3 ainda não está implementada.
**Fonte:** REV13, inventário de 128 identificadores e decisão funcional de 24/10/2026.
**Regra:** campo oculto não bloqueia; rascunho pode permanecer incompleto; a validação ocorrerá somente na futura submissão integral.

## Política de obrigatoriedade

Esta tabela é a fonte única das classificações e condições dos 128 identificadores. O README resume a política e aponta para esta matriz; não mantém uma segunda relação campo a campo. Alterações futuras devem modificar esta fonte, seu identificador de versão e os testes correspondentes antes de alcançar interface ou validação.

| Classificação | Regra declarativa |
|---|---|
| Essencial, somente leitura | Deve estar disponível por fonte institucional confiável; não é digitado livremente no FORM 1. |
| Obrigatória essencial | Deve estar respondida na submissão quando o campo estiver sempre visível. |
| Obrigatória condicional | Deve estar respondida na submissão somente quando a condição registrada nesta matriz estiver ativa. |
| Facultativa (REV13) | A própria REV13 a declara opcional; sua ausência não bloqueia a submissão. |
| Facultativa nesta proposta | A classificação é provisória e sua ausência não bloqueia enquanto não houver decisão posterior versionada. |

### Estados do preenchimento

- **Abertura do Registro:** exige apenas os dados necessários para criar e identificar o Registro e atribuir as responsabilidades. Não exige o preenchimento dos 128 identificadores. Os itens 0.1 a 0.3 são metadados institucionais do ARP e não autorizam digitação livre de identidade.
- **Rascunho:** pode ser iniciado, salvo e retomado incompleto. Campo essencial vazio, campo condicional ativo vazio e resposta `A confirmar` não impedem o salvamento. Cada valor informado continua sujeito a catálogo, tipo, autoria, idempotência e controle de versão.
- **Submissão integral:** antes de criar o snapshot imutável do contrato 3, a futura validação deverá calcular os campos ativos e exigir todos os essenciais e condicionais ativos. Campos ocultos ou condicionais inativos não bloqueiam. Campos facultativos não bloqueiam. Essa validação ainda não está implementada.

### Tratamento de respostas especiais

- **`A confirmar`:** somente pode ser utilizado quando constar expressamente no catálogo da pergunta. No rascunho representa informação ainda não confirmada. Na submissão, não satisfaz campo essencial nem condicional ativo; nesses casos deverá ser substituído por resposta conclusiva. Em campo facultativo poderá permanecer registrado, mas deverá ser apresentado como pendência para confirmação, sem ser convertido silenciosamente em ausência, `Não` ou `Não se aplica`.
- **`Não se aplica`:** somente pode ser utilizado quando constar expressamente no catálogo da pergunta. É uma resposta conclusiva e satisfaz a obrigatoriedade do campo. Em seleção múltipla, não deve coexistir com alternativa factual nem com `A confirmar`. Seus campos dependentes ficam inativos, salvo condição diferente expressamente registrada nesta matriz.
- **Campo sem resposta:** é diferente de `A confirmar` e de `Não se aplica`. É aceito no rascunho, mas bloqueia a submissão quando o campo for essencial ou condicional ativo.

### Complementos de “Outro” — decisão F1-D05

Os 38 contextos catalogados com `Outro`, `Outra` ou alternativa equivalente adotam uma única política: complemento descritivo de até **200 caracteres**, armazenado separadamente pelo identificador canônico. O complemento é independente entre perguntas comuns, ocorrências repetíveis de participantes e perguntas que reutilizam o catálogo 5.1. Ele pode faltar no rascunho, mas será exigido pela futura submissão quando a alternativa correspondente estiver ativa. Ao desmarcá-la, o valor deixa de ser ativo sem ser apagado do histórico versionado. A política não se aplica às justificativas de destinatários do item `10.2.1`.

O item `2.1` permanece sob responsabilidade do APA quando existe confirmação histórica de canais; nesse caso, a resposta e qualquer complemento são somente leitura para o ARP. As referências F1-D05 nas linhas abaixo identificam os campos alcançados por esta política já decidida, e não uma decisão ainda aberta.

As regras acima descrevem a validação futura da submissão. A interface e o domínio já implementados não devem ser apresentados como se aplicassem integralmente essa política antes dos testes específicos do incremento F1-6.

## Etapas visuais

| Etapa | Blocos | Denominação |
|---|---|---|
| Cabeçalho | 0.1–0.3 | Identificação institucional |
| Etapa 1 | 1–3 | Identificação e funcionamento do serviço |
| Etapa 2 | 4–8 | Dados pessoais e operações de tratamento |
| Etapa 3 | 9–11 | Acesso, compartilhamento e armazenamento |
| Etapa 4 | 12–14 | Guarda, situações observadas e pendências |

## Matriz campo a campo

| ID | Etapa | Obrigatoriedade | Condição de exibição | Pendência ou observação |
|---|---|---|---|---|
| 0.1 | Cabeçalho | Essencial, somente leitura | Sempre visível | F1-D07: fonte institucional |
| 0.2 | Cabeçalho | Essencial, somente leitura | Sempre visível | F1-D07: fonte institucional |
| 0.3 | Cabeçalho | Essencial, somente leitura | Sempre visível | F1-D07: fonte institucional |
| 1.1 | Etapa 1 | Facultativa nesta proposta | Sempre visível | — |
| 1.1.1 | Etapa 1 | Obrigatória condicional | 1.1 = Sim | — |
| 1.2 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 1.3 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 1.4 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.1 | Etapa 1 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro |
| 2.2 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.3 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.4 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.4.1 | Etapa 1 | Obrigatória condicional | 2.4 = Não | — |
| 2.4.2 | Etapa 1 | Obrigatória condicional | 2.4 = Não | — |
| 2.5 | Etapa 1 | Facultativa nesta proposta | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 2.6 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.7 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.8 | Etapa 1 | Facultativa (REV13) | Sempre visível | — |
| 2.8.1 | Etapa 1 | Facultativa nesta proposta | Sempre visível | condição exata não explicitada; F1-D05: complemento de Outro |
| 2.9 | Etapa 1 | Facultativa (REV13) | Sempre visível | — |
| 2.9.1 | Etapa 1 | Facultativa nesta proposta | Sempre visível | condição exata não explicitada; F1-D05: complemento de Outro |
| 2.10 | Etapa 1 | Facultativa (REV13) | Sempre visível | — |
| 2.10.1 | Etapa 1 | Facultativa nesta proposta | Sempre visível | condição exata não explicitada; F1-D05: complemento de Outro |
| 2.11 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 2.12 | Etapa 1 | Facultativa nesta proposta | Sempre visível | — |
| 2.12.1 | Etapa 1 | Obrigatória condicional | 2.12 = Sim | — |
| 2.12.2 | Etapa 1 | Obrigatória condicional | 2.12 = Sim | — |
| 2.13 | Etapa 1 | Facultativa nesta proposta | Sempre visível | — |
| 2.13.1 | Etapa 1 | Obrigatória condicional | 2.13 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| OUV.1 | Etapa 1 | Obrigatória condicional | 2.1 = Ouvidoria | F1-D06: excludentes |
| OUV.2 | Etapa 1 | Obrigatória condicional | 2.1 = Ouvidoria | F1-D06: excludentes |
| OUV.3 | Etapa 1 | Obrigatória condicional | 2.1 = Ouvidoria | — |
| OUV.4 | Etapa 1 | Obrigatória condicional | 2.1 = Ouvidoria | — |
| ESIC.1 | Etapa 1 | Obrigatória condicional | 2.1 = e-SIC | — |
| ESIC.2 | Etapa 1 | Obrigatória condicional | 2.1 = e-SIC | — |
| 3.1 | Etapa 1 | Obrigatória essencial | Sempre visível | — |
| 3.2 | Etapa 1 | Obrigatória condicional | 3.1 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes; uma ocorrência por participante |
| 3.3 | Etapa 1 | Obrigatória condicional | 3.1 = Sim | uma ocorrência por participante |
| 3.4 | Etapa 1 | Obrigatória condicional | 3.1 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes; uma ocorrência por participante |
| 3.4.1 | Etapa 1 | Obrigatória condicional | 3.1 = Sim | F1-D06: excludentes; uma ocorrência por participante |
| 3.5 | Etapa 1 | Obrigatória condicional | 3.1 = Sim | uma ocorrência por participante |
| 3.5.1 | Etapa 1 | Obrigatória condicional | 3.1 = Sim e 3.5 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes; uma ocorrência por participante |
| 4.1 | Etapa 2 | Obrigatória essencial | Sempre visível | F1-D03: correspondência v2/REV13; F1-D05: complemento de Outro; F1-D06: excludentes |
| 4.2 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 4.2.1 | Etapa 2 | Obrigatória condicional | 4.2 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 4.2.2 | Etapa 2 | Obrigatória condicional | 4.2 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 4.2.3 | Etapa 2 | Obrigatória condicional | 4.2 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 4.2.4 | Etapa 2 | Obrigatória condicional | 4.2 = Sim ou Em alguns casos | — |
| 4.2.4.1 | Etapa 2 | Obrigatória condicional | 4.2 ativo e 4.2.4 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 4.2.5 | Etapa 2 | Obrigatória condicional | 4.2 = Sim ou Em alguns casos | — |
| 4.2.5.1 | Etapa 2 | Obrigatória condicional | 4.2 ativo e 4.2.5 = Sim | — |
| 5.1 | Etapa 2 | Obrigatória essencial | Sempre visível | Sem conversão com contrato 2; `Outro` admite complemento de até 200 caracteres, obrigatório somente na futura submissão; `A confirmar` é exclusivo |
| 6.1 | Etapa 2 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 6.1.1 | Etapa 2 | Facultativa nesta proposta | Sempre visível | condição exata não explicitada |
| 6.2 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 6.2.1 | Etapa 2 | Obrigatória condicional | 6.2 = Sim | — |
| 6.2.2 | Etapa 2 | Obrigatória condicional | 6.2 = Sim | — |
| 7.1 | Etapa 2 | Obrigatória essencial | Sempre visível | F1-D06: excludentes |
| 8.1 | Etapa 2 | Obrigatória essencial | Sempre visível | — |
| 8.2 | Etapa 2 | Facultativa nesta proposta | Sempre visível | F1-D06: excludentes |
| 8.2.1 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 8.2.1.1 | Etapa 2 | Obrigatória condicional | 8.2.1 = Sim | — |
| 8.2.2 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 8.2.2.1 | Etapa 2 | Obrigatória condicional | 8.2.2 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.2.2.2 | Etapa 2 | Facultativa (REV13) | 8.2.2 = Sim ou Em alguns casos | — |
| 8.3 | Etapa 2 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.4 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 8.4.1 | Etapa 2 | Obrigatória condicional | 8.4 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.4.2 | Etapa 2 | Obrigatória condicional | 8.4 = Sim | — |
| 8.4.3 | Etapa 2 | Obrigatória condicional | 8.4 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.5 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 8.5.1 | Etapa 2 | Obrigatória condicional | 8.5 = Sim | — |
| 8.6 | Etapa 2 | Facultativa nesta proposta | Sempre visível | — |
| 8.6.1 | Etapa 2 | Obrigatória condicional | 8.6 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.6.2 | Etapa 2 | Obrigatória condicional | 8.6 = Sim ou Em alguns casos | — |
| 8.6.3 | Etapa 2 | Obrigatória condicional | 8.6 = Sim ou Em alguns casos | — |
| 8.6.4 | Etapa 2 | Obrigatória condicional | 8.6 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 8.7 | Etapa 2 | Obrigatória condicional | 8.3 inclui WhatsApp corporativo ou pessoal | F1-D04: WhatsApp |
| 8.8 | Etapa 2 | Obrigatória condicional | 8.3 inclui WhatsApp corporativo ou pessoal | F1-D04: WhatsApp |
| 8.8.1 | Etapa 2 | Obrigatória condicional | ramo WhatsApp ativo e 8.8 = Sempre ou Às vezes | F1-D04: WhatsApp |
| 8.9 | Etapa 2 | Obrigatória condicional | 8.3 inclui WhatsApp corporativo ou pessoal | F1-D04: WhatsApp |
| 9.1 | Etapa 3 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 9.2 | Etapa 3 | Facultativa nesta proposta | Sempre visível | — |
| 9.2.1 | Etapa 3 | Obrigatória condicional | 9.2 = Não | — |
| 9.2.2 | Etapa 3 | Obrigatória condicional | 9.2 = Não e 9.2.1 = Sim | — |
| 9.3 | Etapa 3 | Facultativa nesta proposta | Sempre visível | — |
| 10.1 | Etapa 3 | Obrigatória essencial | Sempre visível | — |
| 10.2 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | F1-D03: correspondência v2/REV13; F1-D05: complemento de Outro; F1-D06: excludentes |
| 10.2.1 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | condição exata não explicitada |
| 10.3 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 10.4 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | — |
| 10.5 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | — |
| 10.6 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | — |
| 10.7 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | — |
| 10.7.1 | Etapa 3 | Obrigatória condicional | 10.1 ativo e 10.7 = Sim ou Em alguns casos | — |
| 10.8 | Etapa 3 | Obrigatória condicional | 10.1 = Sim ou Em alguns casos | — |
| 10.8.1 | Etapa 3 | Obrigatória condicional | 10.1 ativo e 10.8 = Sim ou Em alguns casos | F1-D05: complemento de Outro; F1-D06: excludentes |
| 10.9 | Etapa 3 | Facultativa nesta proposta | Sempre visível | F1-D05: complemento de Outro |
| 11.1 | Etapa 3 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 11.2 | Etapa 3 | Facultativa nesta proposta | Sempre visível | — |
| 11.2.1 | Etapa 3 | Obrigatória condicional | 11.2 = infraestrutura de terceiro, mista ou A confirmar | — |
| 11.2.2 | Etapa 3 | Obrigatória condicional | 11.2 = infraestrutura de terceiro, mista ou A confirmar | — |
| 11.2.3 | Etapa 3 | Obrigatória condicional | 11.2 = infraestrutura de terceiro, mista ou A confirmar | — |
| 11.2.4 | Etapa 3 | Obrigatória condicional | 11.2 = infraestrutura de terceiro, mista ou A confirmar | — |
| 11.3 | Etapa 3 | Facultativa nesta proposta | Sempre visível | — |
| 11.3.1 | Etapa 3 | Obrigatória condicional | 11.3 = Sim ou Em alguns casos | — |
| 12.1 | Etapa 4 | Obrigatória essencial | Sempre visível | — |
| 12.1.1 | Etapa 4 | Obrigatória condicional | 12.1 = Sim | — |
| 12.1.2 | Etapa 4 | Obrigatória condicional | 12.1 = Sim | F1-D05: complemento de Outro |
| 12.1.3 | Etapa 4 | Obrigatória condicional | 12.1 = Sim | F1-D05: complemento de Outro; F1-D06: excludentes |
| 12.2 | Etapa 4 | Obrigatória essencial | Sempre visível | F1-D05: complemento de Outro |
| 12.3 | Etapa 4 | Facultativa nesta proposta | Sempre visível | — |
| 12.4 | Etapa 4 | Facultativa nesta proposta | Sempre visível | — |
| 12.4.1 | Etapa 4 | Obrigatória condicional | 12.4 = Sim ou Em alguns casos | — |
| 12.5 | Etapa 4 | Facultativa nesta proposta | Sempre visível | — |
| 12.5.1 | Etapa 4 | Obrigatória condicional | 12.5 = Sim | — |
| 13.1 | Etapa 4 | Obrigatória essencial | Sempre visível | excludentes definidas na REV13 |
| 13.2 | Etapa 4 | Facultativa nesta proposta | Sempre visível | — |
| 13.3 | Etapa 4 | Facultativa nesta proposta | Sempre visível | — |
| 13.4 | Etapa 4 | Facultativa nesta proposta | Sempre visível | F1-D05: complemento de Outro; F1-D06: excludentes |
| 14.1 | Etapa 4 | Obrigatória essencial | Sempre visível | — |
| 14.1.1 | Etapa 4 | Obrigatória condicional | 14.1 = Sim | — |
| 14.1.2 | Etapa 4 | Obrigatória condicional | 14.1 = Sim | — |
| 14.2 | Etapa 4 | Obrigatória essencial | Sempre visível | — |
| 14.2.1 | Etapa 4 | Obrigatória condicional | 14.2 = Sim | F1-D05: complemento de Outro |
| 14.2.2 | Etapa 4 | Obrigatória condicional | 14.2 = Sim | — |
| 14.2.3 | Etapa 4 | Obrigatória condicional | 14.2 = Sim | — |
| 14.2.4 | Etapa 4 | Obrigatória condicional | 14.2 = Sim e 14.2.3 = Sim | — |

## Limites

“Sempre visível” indica somente ausência de condição explícita registrada; não torna o campo obrigatório. A matriz não altera enunciados ou alternativas. Pontos pendentes não serão programados por analogia.
