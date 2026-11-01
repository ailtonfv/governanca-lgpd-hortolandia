# Decisões P0 da matriz do FORM 1 Integral REV13

**Incremento:** 8U

**Data:** 01/11/2026

**Situação:** especificação funcional e técnica para o próximo incremento; não substitui a matriz vigente, não altera contrato e não libera submissão

## 1. Resultado executivo

As seis exceções P0 identificadas no Incremento 8S e detalhadas no 8T foram consolidadas em regras executáveis para uma futura política `MATRIZ-F1-REV13-OBR-v2-candidata-8U`.

Quatro decisões estão funcionalmente definidas e aguardam versionamento e implementação: `0.2` não bloqueante, `0.3` não bloqueante, exclusividade de `A confirmar` e exclusividade de `Não se aplica`. A política geral dos 128 identificadores possui proposta candidata tecnicamente consistente, mas ainda depende de aprovação funcional no âmbito da PoC. A correção de WhatsApp possui proposta mínima recomendada, porém depende de autorização específica para versionar a alternativa de `8.3` e o contrato candidato 3.

A matriz vigente `MATRIZ-F1-REV13-OBR-v1` continua sendo a fonte declarativa utilizada pela aplicação. A pré-validação permanece consultiva e a submissão integral continua bloqueada.

## 2. Quadro consolidado das seis P0

| Exceção | Regra atual | Regra proposta ou decisão consolidada | Impacto técnico | Decisão ainda pendente | Testes necessários | Critério de aceite futuro |
|---|---|---|---|---|---|---|
| `8S-01` — `0.2` | Essencial, somente leitura; ausência aparece como dependência | Metadado institucional facultativo, somente leitura e não bloqueante; preencher automaticamente apenas com fonte confiável | Nova classe na matriz e ajuste da pré-validação/apresentação; sem migração estrutural | Aprovação funcional da política candidata e futura definição da fonte institucional | ausência sem bloqueio; fonte autenticada; escrita livre recusada; snapshot identifica a origem | declaração do ARP não é bloqueada pela ausência e nenhum valor é inventado ou digitado livremente |
| `8S-02` — `0.3` | Essencial, somente leitura; sem fonte integrada | Metadado institucional facultativo, somente leitura e não bloqueante; não solicitar preenchimento manual | Mesmo tratamento de `0.2`; eventual uso para comunicação depende de integração própria | Aprovação funcional da política candidata e eventual necessidade operacional do e-mail | ausência sem bloqueio; valor autenticado; escrita forjada recusada; autoria independente do e-mail | ausência não bloqueia e identidade/autoria continuam baseadas na matrícula e sessão autenticada |
| `8S-03` — política dos 128 IDs | Cobertura técnica completa, mas 25 essenciais e 69 condicionais ainda não têm aprovação funcional global | Adotar a v2 candidata por deltas explícitos sobre a v1, preservando os 128 IDs e todas as regras não excepcionadas | Versionar a política; vincular pré-validação e futura versão à matriz aprovada | Aprovação funcional para a PoC; aprovação institucional formal para operação continua separada | cobertura 128/128; classes e condições; vínculo da versão da matriz ao snapshot; regressão dos contratos 2 e 3 | autoridade competente aprova versão identificada; código e documentação carregam exatamente a mesma versão |
| `8S-04` — WhatsApp | `8.3` oferece apenas “WhatsApp corporativo”; `8.7` distingue institucional, pessoal ou ambos; matriz menciona corporativo ou pessoal | Recomenda-se que `8.3` passe a identificar genericamente o canal “WhatsApp”; `8.7` qualifica dispositivo/conta; `8.8` registra transferência ao repositório oficial; `8.9` registra cópias e backups residuais | Exige versão contratual para a alternativa de `8.3`, compatibilidade com o valor legado e ajuste das condições; não exige nova tabela | Autorização específica para versionar contrato/catálogo e aprovação do rótulo genérico | valor novo e legado ativam o ramo; `8.7` independente de `8.8/8.9`; códigos forjados recusados; legado preservado | realidade pessoal/corporativa/ambos pode ser mapeada sem chamar uso pessoal de corporativo e sem converter histórico |
| `8S-05` — `A confirmar` | Exclusividade expressa em `5.1` e `13.1`; 29 seleções múltiplas permanecem sem regra uniforme | Em toda seleção múltipla que contenha a alternativa, `A confirmar` é isolado e não pode coexistir com resposta substantiva ou `Não se aplica` | Validação declarativa comum; interface desmarca opções incompatíveis; pré-validação distingue bloqueio e aviso; legado não é reescrito | Aprovação funcional da v2 candidata; nenhuma decisão campo a campo adicional é necessária para a regra de exclusividade | 31 campos parametrizados; rascunho isolado; combinação recusada; essencial/condicional bloqueia; facultativo gera aviso | nenhuma nova combinação contraditória é salva; valor isolado conserva seu significado de pendência e nunca satisfaz obrigação ativa |
| `8S-06` — `Não se aplica` | Exclusividade parcial; divergência em `3.4.1` e `13.4`; `13.1` já possui regra | Em seleção múltipla com alternativa catalogada, `Não se aplica` é isolado, incompatível com substantivas e `A confirmar`, e só é conclusivo quando o campo está aplicável e a matriz permite a alternativa | Regra comum para `3.4.1`, `13.1` e `13.4`; interface e domínio; respostas legadas apenas sinalizadas | Aprovação funcional da v2 candidata | três campos parametrizados; opção isolada; misturas recusadas; ramo ativo/inativo; legado preservado | opção não contorna campo ativo, não é aplicada a campo sem alternativa e não apaga respostas históricas |

## 3. Política candidata de obrigatoriedade

### 3.1 Identificação e natureza

- **Identificador proposto:** `MATRIZ-F1-REV13-OBR-v2-candidata-8U`.
- **Base:** herda os 128 identificadores e todas as classificações e condições da `MATRIZ-F1-REV13-OBR-v1`, exceto os deltas expressos neste documento.
- **Situação:** candidata técnica pronta para revisão funcional; não aprovada institucionalmente e não carregada pela aplicação.
- **Princípio de versionamento:** a v1 não será editada silenciosamente. A futura versão aprovada terá identificador próprio e permanecerá associada às versões do FORM 1 que a utilizarem.

Não será criada uma segunda tabela integral de 128 linhas neste documento. A proposta é uma versão por herança controlada e deltas, evitando duas cópias independentes antes da aprovação.

### 3.2 Classificações candidatas

| Classificação candidata | Quantidade | Efeito futuro |
|---|---:|---|
| Essencial, somente leitura | 1 | `0.1`; deve existir na identidade autenticada |
| Metadado institucional não bloqueante, somente leitura | 2 | `0.2` e `0.3`; pode permanecer ausente |
| Obrigatória essencial | 25 | bloqueia somente a futura conclusão/submissão quando vazia |
| Obrigatória condicional | 69 | bloqueia somente quando sua condição estiver ativa |
| Facultativa segundo a REV13 | 4 | não bloqueia |
| Facultativa nesta política candidata | 27 | não bloqueia; depende da aprovação funcional da política |
| **Total** | **128** | cobertura integral preservada |

Os marcadores visuais deverão refletir a versão aprovada. Para `0.2` e `0.3`, propõe-se `****` com o rótulo **Facultativo · somente leitura**, sem transformar ausência em pendência bloqueante.

### 3.3 Deltas propostos sobre a v1

| Delta | Identificadores | Alteração candidata |
|---|---|---|
| `P0-D01` | `0.2` | de “Essencial, somente leitura” para “Metadado institucional não bloqueante, somente leitura” |
| `P0-D02` | `0.3` | mesma reclassificação de `0.2` |
| `P0-D03` | 31 seleções múltiplas com `A confirmar` | alternativa isolada; nunca conclusiva para campo obrigatório ativo; aviso não bloqueante em facultativo |
| `P0-D04` | `3.4.1`, `13.1`, `13.4` | `Não se aplica` isolado e conclusivo somente quando permitido pelo catálogo e aplicável pela matriz |
| `P0-D05` | `8.3`, `8.7`, `8.8`, `8.8.1`, `8.9` | ramo ativado por canal genérico WhatsApp, com qualificações separadas; depende de versão contratual autorizada |
| `P0-D06` | 128 IDs | a política só poderá governar conclusão após aprovação funcional identificada e vínculo explícito da versão |

### 3.4 Aprovação técnica, funcional e institucional

Três atos não devem ser confundidos:

1. **Validação técnica da candidata:** comprova cobertura, consistência, ausência de condições impossíveis e capacidade de implementação. Não aprova regra de negócio.
2. **Aprovação funcional no âmbito da PoC:** confirma que a política candidata representa o preenchimento esperado e autoriza sua implementação e ensaio com dados fictícios.
3. **Aprovação institucional formal:** ato da autoridade competente para operação municipal. Não é produzido por teste, commit, parecer técnico ou aceite da PoC e permanece fora deste incremento.

O próximo incremento técnico só poderá usar uma política com aprovação funcional expressa e identificador definitivo. A liberação institucional continuará exigindo ato próprio.

## 4. Regras consolidadas

### 4.1 Identidade funcional `0.2` e `0.3`

- matrícula/identidade autenticada continua sendo a referência principal da autoria e das permissões;
- cargo/função e e-mail não satisfazem nem substituem autenticação;
- ambos permanecem somente leitura;
- se a fonte institucional não entregar o atributo, o valor permanece ausente;
- a ausência não integra `incompletos`, não bloqueia a declaração do ARP e não autoriza digitação livre;
- quando presentes, o snapshot deverá registrar valor e origem institucional, sem transformar o e-mail em identificador principal;
- eventual comunicação por e-mail é funcionalidade separada e não altera a obrigatoriedade.

### 4.2 WhatsApp

Os campos descrevem dimensões diferentes:

| Campo | Dimensão |
|---|---|
| `8.3` | canal ou meio pelo qual a informação circula |
| `8.7` | natureza institucional, pessoal ou mista da conta/dispositivo utilizado |
| `8.8` | transferência das informações relevantes para ambiente institucional |
| `8.8.1` | sistema, protocolo, processo ou repositório oficial de destino |
| `8.9` | permanência residual de cópias, arquivos ou backups fora do ambiente institucional |

**Correção mínima recomendada para autorização futura:** em nova versão do contrato candidato 3, substituir a alternativa visível e canônica `WhatsApp corporativo` de `8.3` por `WhatsApp`. Novas respostas usam o valor genérico. Rascunhos e snapshots com o valor legado `WhatsApp corporativo` permanecem válidos e ativam o mesmo ramo, sem conversão automática. `8.7` passa a registrar se o uso concreto é institucional/corporativo, pessoal ou ambos.

Essa solução evita duplicar canais em `8.3`, mantém a qualificação em `8.7` e impede que a presença do canal seja interpretada como prova de registro oficial. `8.8`, `8.8.1` e `8.9` continuam respondendo sobre transferência, repositório e permanência.

Como a mudança alcança uma alternativa do catálogo, ela permanece **proposta pendente de autorização contratual específica**. Até lá, a regra executável atual não deve ser alterada.

### 4.3 Exclusividade de `A confirmar`

Escopo: todas as 31 seleções múltiplas cujo catálogo contém `A confirmar`. `5.1` e `13.1` já possuem regra; os 29 campos restantes estão relacionados no relatório 8S.

Regras candidatas:

1. `A confirmar` pode ser salvo isoladamente no rascunho.
2. A interface deverá desmarcar respostas substantivas e `Não se aplica` quando `A confirmar` for selecionado, e desmarcar `A confirmar` quando outra resposta for escolhida.
3. O domínio recusará novo salvamento que envie combinação incompatível, inclusive por requisição forjada.
4. Em campo essencial ou condicional ativo, `A confirmar` aparece como **informação pendente** e bloqueia a futura declaração de conclusão/submissão.
5. Em campo facultativo, não bloqueia, mas aparece em categoria própria de **aviso para confirmação**.
6. Em campo condicional inativo, a resposta histórica permanece armazenada, mas não é avaliada como obrigação ativa.
7. Rascunho legado com combinação incompatível não será convertido nem apagado. A pré-validação o sinaliza; ao editar o campo, o agente deverá escolher uma combinação válida antes de salvar.

### 4.4 Exclusividade de `Não se aplica`

Escopo atual: `3.4.1`, `13.1` e `13.4`, únicas seleções múltiplas da REV13 que contêm a alternativa.

Regras candidatas:

1. `Não se aplica` só existe onde estiver catalogado; não pode ser acrescentado por analogia.
2. Deve ser selecionado isoladamente.
3. Não pode coexistir com resposta substantiva nem com `A confirmar`.
4. Satisfaz um campo obrigatório ativo somente quando a própria matriz permitir a alternativa naquela pergunta.
5. Não pode ser utilizado para responder campo cuja condição de visibilidade esteja inativa; nesse caso o campo simplesmente não participa da validação.
6. Dependentes ficam inativos somente conforme condição expressa da matriz, nunca por inferência da interface.
7. Rascunhos legados incompatíveis são preservados e sinalizados, sem conversão automática.

## 5. Compatibilidade e impacto técnico

### 5.1 Rascunhos e snapshots existentes

- nenhum rascunho será migrado ou reescrito;
- `0.2` e `0.3` ausentes permanecem ausentes;
- combinações legadas de `A confirmar` ou `Não se aplica` serão detectadas pela pré-validação e deverão ser corrigidas antes da futura conclusão;
- o valor legado `WhatsApp corporativo` continuará compreendido pela versão que o produziu e, se a proposta for autorizada, também como gatilho compatível do novo ramo;
- snapshots imutáveis mantêm contrato, matriz e conteúdo originais;
- nenhuma regra nova será aplicada retroativamente para declarar inválida uma versão histórica.

### 5.2 Estrutura, código e migração

Não foi identificada necessidade obrigatória de nova tabela ou migração de banco para as seis P0. A implementação mínima tende a alcançar:

- nova versão declarativa da matriz;
- carregador e metadados visuais de obrigatoriedade;
- pré-validação consultiva;
- validação comum de seleções múltiplas no domínio;
- comportamento visual de opções excludentes;
- condição do ramo WhatsApp e compatibilidade de catálogo, se a alteração contratual for autorizada;
- testes parametrizados e documentação.

Qualquer mudança física deverá ser justificada separadamente. O contrato nuclear 2 e o FORM 1 sintético não participam dessas alterações.

## 6. Plano técnico mínimo para o próximo incremento

### Checkpoint A — Aprovação e fonte declarativa

1. obter aprovação funcional expressa da candidata, exceto do delta WhatsApp se ainda pendente;
2. atribuir identificador definitivo à nova matriz;
3. materializar a nova versão sem sobrescrever a v1;
4. registrar data, responsável funcional e relação de deltas;
5. manter submissão bloqueada.

### Checkpoint B — Identidade não bloqueante

1. ajustar leitura, metadados visuais e pré-validação de `0.2` e `0.3`;
2. preservar somente leitura e ausência de preenchimento livre;
3. testar origem institucional e ausência.

### Checkpoint C — Excludentes

1. centralizar regra declarativa para `A confirmar` nos 31 campos;
2. centralizar `Não se aplica` nos três campos catalogados;
3. ajustar interface, domínio e pré-validação;
4. preservar e sinalizar legado sem reescrita.

### Checkpoint D — WhatsApp

Executar somente após autorização contratual específica: versionar alternativa de `8.3`, aceitar o valor legado como compatibilidade de leitura e gatilho, ajustar condições e testar as quatro dimensões separadamente.

### Checkpoint E — Verificação

Executar testes focais, regressão integral dos contratos 2 e 3 e ensaio sintético. A aprovação dos testes não libera submissão; o ciclo ARP/APA do 8T deverá ser implementado e autorizado separadamente.

## 7. Conjunto mínimo de testes futuros

1. matriz nova com exatamente 128 IDs e contagens candidatas `1 + 2 + 25 + 69 + 4 + 27`;
2. v1 preservada e snapshots ligados à versão correta;
3. `0.2` e `0.3` ausentes sem bloqueio e sem edição livre;
4. valores institucionais presentes com origem e autoria corretas;
5. teste parametrizado dos 31 campos com `A confirmar` isolado, combinado e forjado;
6. `A confirmar` bloqueante em essencial/condicional ativo e apenas aviso em facultativo;
7. teste parametrizado de `Não se aplica` em `3.4.1`, `13.1` e `13.4`;
8. campo condicional inativo não avaliado e resposta histórica preservada;
9. WhatsApp novo e legado ativando o ramo, se autorizado;
10. `8.7`, `8.8`, `8.8.1` e `8.9` mantendo semânticas independentes;
11. rascunhos legados sem conversão automática;
12. tentativa inválida sem efeito, com auditoria quando aplicável;
13. idempotência, concorrência e rollback dos futuros atos de conclusão;
14. regressão integral do contrato nuclear 2 e do contrato candidato 3;
15. confirmação de que nenhum teste habilita submissão.

## 8. Decisões institucionais ainda reais

| Tema | Situação após o 8U | Responsabilidade da próxima decisão |
|---|---|---|
| Política candidata dos 128 IDs | pronta tecnicamente, não aprovada funcionalmente | instância funcional competente da PoC |
| `0.2` e `0.3` não bloqueantes | decisão funcional consolidada; implementação pendente | aprovação da versão da matriz; fonte real será definida com a T.I. |
| `A confirmar` exclusivo | decisão funcional consolidada; implementação pendente | aprovação da versão da matriz |
| `Não se aplica` exclusivo | decisão funcional consolidada; implementação pendente | aprovação da versão da matriz |
| WhatsApp genérico em `8.3` | proposta técnica recomendada | autorização funcional e contratual específica |
| Aprovação institucional para operação | não concedida pelo 8U | autoridade municipal competente em ato próprio |
| Liberação da submissão | continua bloqueada | depende da matriz aprovada, implementação/testes e ciclo ARP/APA autorizado |

## 9. Critério de encerramento das seis P0

As P0 somente serão consideradas tecnicamente encerradas quando:

1. uma matriz com identificador definitivo tiver aprovação funcional expressa;
2. os deltas de `0.2`, `0.3`, `A confirmar` e `Não se aplica` estiverem implementados e testados;
3. o WhatsApp tiver decisão contratual ou for formalmente excluído do marco com bloqueio documentado;
4. rascunhos e snapshots anteriores permanecerem íntegros;
5. pré-validação, interface e domínio utilizarem a mesma versão declarativa;
6. o contrato nuclear 2 permanecer intacto;
7. a regressão completa for aprovada;
8. a submissão continuar bloqueada até autorização própria.

## 10. Conclusão

O 8U transforma as exceções P0 em uma política candidata verificável, sem alterar a fonte vigente. Cargo/função e e-mail deixam de ser futuros bloqueios; `A confirmar` e `Não se aplica` recebem regras uniformes e compatíveis com rascunhos; e o conflito do WhatsApp recebe uma proposta que separa canal, dispositivo, repositório e permanência de arquivos.

O próximo incremento técnico recomendado é implementar os checkpoints B e C sobre uma nova matriz já aprovada funcionalmente. O checkpoint D deve aguardar autorização específica da mudança contratual de WhatsApp. Nenhuma dessas etapas, isoladamente, autoriza a submissão do FORM 1 Integral.
