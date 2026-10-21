# Plano de encerramento das provas de conceito em 2026

## 1. Objetivo

Concluir, até 30 de dezembro de 2026, a PoC nuclear e uma PoC ampliada essencial do Sistema de Governança Municipal LGPD, produzir evidências reproduzíveis e preparar a transferência técnica para a equipe designada pela Prefeitura. A partir de janeiro de 2027, o foco principal do Encarregado de Dados retorna ao encerramento do ATLAS.

Este plano organiza o trabalho e limita o crescimento do escopo. Ele não altera, por si só, os requisitos ou as decisões registrados na série SAD. Qualquer mudança formal de escopo deve ser registrada nos documentos de autoridade correspondentes.

## 2. Premissas

- Todos os dados utilizados nas PoCs serão fictícios.
- A PoC não será convertida informalmente em Piloto ou sistema de produção.
- A PoC nuclear permanece orientada pelo SAD 04 REV12, pelo SAD 09 REV12 e pelo SAD 10 REV16, especialmente a DA-39.
- As regras de domínio ficam separadas das interfaces e da persistência.
- Cada ato mutável é idempotente, transacional, auditável e reconstruível pela cadeia de eventos.
- Defeitos críticos ou altos impedem o aceite do marco.
- Ideias e requisitos novos serão registrados no backlog, sem entrada automática no escopo de 2026.
- A participação da TI deve começar antes da transferência definitiva, preferencialmente após o fechamento do M1a.

## 3. PoC nuclear M1a

### 3.1 Escopo restante

- rascunho e salvamento do FORM 1 sintético;
- criação de versões imutáveis;
- submissão e verificação material de possível sobreposição;
- retirada da submissão antes da análise;
- início e reatribuição da análise, com segregação de funções e controle de concorrência;
- devolução com pendência, correção, resposta, congelamento por hash e P5/P6 no percurso restrito da devolução;
- validação e recálculo do estado do Registro;
- conclusão sem medidas e após medidas;
- ação obrigatória sintética mínima;
- pendência intersecretarial;
- telas mínimas necessárias à demonstração;
- testes POC-TS-001 a POC-TS-009 e respectivas evidências;
- verificação das cadeias e registro do aceite do M1a.

### 3.2 Estimativa

Previsão de 60 a 80 horas de trabalho efetivo, sujeita à estabilidade das decisões vigentes e do ambiente técnico.

## 4. PoC ampliada essencial

### 4.1 Pergunta que deve responder

O núcleo arquitetural continua funcionando com o FORM 1 integral diante de suspensão, cancelamento, reabertura, continuidade institucional, concorrência e restauração?

### 4.2 Escopo incluído

- FORM 1 integral de ponta a ponta, conforme a Cartilha;
- autorizações mínimas necessárias aos atos demonstrados;
- regras de prazo indispensáveis ao percurso selecionado;
- suspensão e retomada;
- cancelamento e seu efeito mínimo sobre pendências;
- reabertura e criação de novo ciclo, com preservação do histórico;
- continuidade institucional em cenários essenciais;
- pendências adicionais estritamente necessárias aos cenários selecionados;
- backup e restauração demonstráveis em ambiente limpo;
- reexecução dos testes nucleares como regressão;
- evidências, registro das limitações e transferência técnica.

### 4.3 Limite de esforço

A PoC ampliada essencial terá como referência 85 horas, com faixa de planejamento entre 65 e 100 horas. Ao atingir o limite, qualquer ampliação dependerá de decisão expressa, com avaliação do impacto sobre o retorno ao ATLAS.

### 4.4 Fora do escopo de 2026

- implementação dos FORMs 2, 3 e 4 completos;
- integrações reais com sistemas municipais;
- ingestão e reprocessamento completos;
- interfaces sofisticadas;
- infraestrutura de produção;
- autenticação corporativa definitiva;
- operação institucional com dados pessoais reais;
- treinamento geral dos servidores;
- Pilotagem ou entrada em produção;
- requisitos que não sejam indispensáveis à resposta da pergunta da seção 4.1.

Os itens excluídos serão encaminhados à TI, ao futuro Piloto ou a etapa posterior formalmente autorizada.

## 5. Calendário de referência

| Período | Resultado esperado |
|---|---|
| 15/10/2026 a 13/11/2026 | Núcleo funcional do M1a concluído |
| 16/11/2026 a 20/11/2026 | Testes, evidências, aceite do M1a e revisão conjunta com a TI |
| 23/11/2026 a 18/12/2026 | PoC ampliada essencial implementada e testada |
| 21/12/2026 a 23/12/2026 | Regressão final e correção de defeitos críticos ou altos |
| 28/12/2026 a 30/12/2026 | Relatório de encerramento e transferência técnica |
| Janeiro de 2027 | Retorno do foco principal ao ATLAS |

As datas são metas de planejamento. O escopo deve ser reduzido antes de se deslocar a data final.

## 6. Ponto de decisão do M1a

Em 20 de novembro de 2026 será realizada uma verificação objetiva:

- se o M1a estiver aceito, inicia-se a PoC ampliada essencial;
- se o M1a ainda tiver defeito crítico ou alto, prioriza-se o seu encerramento e a transferência do que estiver validado;
- o atraso do M1a não autoriza automaticamente a invasão do calendário de 2027 nem a postergação do ATLAS.

## 7. Participação e transferência para a TI

Após o M1a, a TI deve receber uma apresentação técnica contendo arquitetura, código, instalação, testes, evidências, decisões vigentes, limitações e backlog. A participação deve crescer durante a PoC ampliada essencial, sem retirar do Encarregado a direção funcional e os critérios de aceite das PoCs.

A transferência definitiva deve incluir, no mínimo:

- código-fonte e histórico de versões;
- instruções reproduzíveis de instalação e teste;
- banco e cargas exclusivamente fictícios;
- suíte automatizada e evidências dos cenários;
- mapa das decisões arquiteturais aplicadas;
- limitações conhecidas e itens fora do escopo;
- recomendações para o Piloto;
- indicação das decisões institucionais ainda pendentes.

## 8. Controle de escopo

Uma demanda nova só entra no trabalho de 2026 quando for necessária para:

1. corrigir defeito crítico ou alto;
2. satisfazer critério de aceite já vigente;
3. preservar integridade, segregação, idempotência ou rastreabilidade;
4. demonstrar um dos cenários essenciais definidos neste plano.

Nos demais casos, a demanda será registrada para avaliação posterior. Não será incluída apenas porque é tecnicamente interessante ou útil a uma futura produção.

## 9. Condição de encerramento

O trabalho de 2026 será considerado encerrado quando:

- o M1a estiver aceito ou, diante de impedimento documentado, transferido com suas limitações explícitas;
- os cenários selecionados da PoC ampliada essencial estiverem demonstrados com dados fictícios;
- as cadeias e evidências aplicáveis tiverem sido verificadas;
- não houver defeito crítico ou alto aberto no escopo entregue;
- a documentação de transferência estiver disponível à TI;
- o backlog posterior estiver separado do escopo concluído;
- estiver formalmente registrado que Piloto e produção exigem autorização, equipe e controles próprios.

## 10. Diretriz final

O objetivo deste trabalho é reduzir a incerteza técnica e entregar uma base verificável à Prefeitura, sem transformar o Encarregado de Dados no responsável permanente pela construção e operação do sistema. O limite temporal de 2026 protege o encerramento do ATLAS e orienta a transição responsável para a TI.
