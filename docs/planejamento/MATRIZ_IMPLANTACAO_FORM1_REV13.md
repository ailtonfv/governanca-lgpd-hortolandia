# Matriz de implantação do FORM 1 integral — REV13

**Situação:** F1-0, F1-1 e F1-2 concluídos; F1-3 iniciado pelo Bloco 4, sem submissão integral
**Regra de preservação:** cada fatia deve manter aprovados os testes da PoC nuclear e acrescentar testes próprios

## Sequência de incrementos

| Incremento | Campos da REV13 | Entrega executável | Testes mínimos | Dependências |
|---|---|---|---|---|
| F1-0 — contrato e catálogo | metadados dos 128 identificadores | catálogo versionado de perguntas; nenhuma submissão v3 | IDs únicos; tipos conhecidos; fonte íntegra; contrato 2 inalterado | decisões de códigos e etapas podem permanecer pendentes |
| F1-1 — abertura, identificação e Bloco 1 | 0.1–0.3 e 1.1–1.4 | identificação de APA/ARP, cabeçalho, quatro etapas e rascunho editável do Bloco 1 | reuso de Registro; indicação elegível; catálogo fechado; idempotência; versão; concorrência; rollback; contrato 2 intacto | função e e-mail continuam indisponíveis na identidade simulada e não são inventados |
| F1-2 — fluxo e participantes — concluído | 2.1–3.5 e ramos Ouvidoria/e-SIC | entrada, execução e participantes repetíveis | condicionais; ocorrência por participante; salvamento parcial; autoria | regra WhatsApp não participa desta fatia |
| F1-3 — titulares, dados, origem e operações — iniciado | 4.1–7.1 | Bloco 4 executável; Blocos 5–7 pendentes | códigos válidos/desconhecidos/repetidos; excludentes; correspondência v2 | tabelas de correspondência aprovadas antes de qualquer conversão automática |
| F1-4 — sistemas, acesso e saídas | 8.1–10.9 | canais, sistemas, acesso e disponibilização | ramos Ouvidoria/e-SIC/WhatsApp; reuso de 5.1; tentativas forjadas | decisão WhatsApp e códigos de destinatários |
| F1-5 — armazenamento, guarda e achados | 11.1–14.2.4 | últimos quatro blocos e pendências factuais | condicionais; exclusividade 13.1; textos limitados; referências sem dados pessoais | regra oficial de temporalidade permanece informativa, não automatizada |
| F1-6 — submissão integral | todos os campos aplicáveis | snapshot imutável do contrato 3 e percurso I3 em diante | obrigatoriedade aprovada; rollback; idempotência; concorrência; regressão completa | todas as decisões bloqueantes fechadas |

## Matriz resumida por natureza

| Natureza | Regra candidata | Validação | Situação |
|---|---|---|---|
| Identidade 0.1–0.3 | somente leitura; derivada da pessoa autorizada | não aceitar nome, matrícula ou e-mail digitado no payload do FORM | depende da fonte institucional futura; na PoC, usar apenas identidade fictícia disponível |
| Seleção única | um código do catálogo da pergunta | recusar lista, código desconhecido e valor repetido | especificável |
| Seleção múltipla | lista sem repetição | recusar código desconhecido; aplicar excludentes aprovadas | parcialmente especificável |
| Texto curto | texto factual limitado | normalizar espaços; limite por contrato; barreira contra dados reais | limites ainda precisam ser aprovados |
| Texto longo | parágrafo factual limitado | limite, orientação e barreira contra dados reais | limites ainda precisam ser aprovados |
| Número/faixa | faixa fechada ou inteiro conforme pergunta | recusar formato incompatível | campos 2.8, 2.9 e 2.10 são opcionais |
| Catálogo de Secretaria | identificador institucional vigente | recusar Secretaria fora do catálogo e do alcance aplicável | reutiliza as 18 Secretarias já disponíveis |
| Participante | coleção de ocorrências independentes | cada ocorrência mantém identificador, tipo, atuação e instrumento próprios | estrutura executável no rascunho F1-2; obrigatoriedade somente na submissão futura |
| Condicional | visibilidade derivada de resposta anterior | envio forjado de ramo inaplicável deve ser recusado ou preservado como histórico inativo, conforme decisão | política de preservação a aprovar |

## Decisões funcionais registradas em 24/10/2026

| Código local | Decisão | Efeito |
|---|---|---|
| F1-D01 | Etapa 1 = blocos 1–3; etapa 2 = 4–8; etapa 3 = 9–11; etapa 4 = 12–14 | estrutura visual aprovada para a proposta |
| F1-D02 | três categorias: essencial, condicional e facultativa; rascunho não bloqueia; submissão futura valida campos ativos | matriz campo a campo passa a ser a referência declarativa candidata |

## Bloqueios de decisão remanescentes

| Código local | Questão | Impacto | Autoridade necessária |
|---|---|---|---|
| F1-D03 | Correspondência dos catálogos v2 ↔ REV13 | compatibilidade e alertas de sobreposição | governança LGPD |
| F1-D04 | WhatsApp pessoal/corporativo no item 8.3 | ramo 8.7–8.9 | responsável funcional do produto |
| F1-D05 | Alternativa “Outro” e complemento textual | catálogos fechados e minimização | governança LGPD |
| F1-D06 | Excludentes além do item 13.1 | validação de seleções múltiplas | responsável funcional do produto |
| F1-D07 | Fonte de função e e-mail institucional | identificação 0.2–0.3 | T.I. e governança de identidade |
| F1-D08 | Marco que autoriza submissão pelo contrato 3 | ativação da funcionalidade integral | autoridade do cronograma SAD 09 |

## Critério para iniciar código

O incremento F1-0 pode ser implementado sem habilitar submissão integral. Cada incremento seguinte somente começa quando suas dependências materiais estiverem decididas. Nenhum incremento reescreve o contrato 2 ou reduz a cobertura dos testes nucleares existentes.
