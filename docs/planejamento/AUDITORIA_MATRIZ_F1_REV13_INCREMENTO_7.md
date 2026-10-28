# Auditoria da matriz de obrigatoriedade do FORM 1 — Incremento 7

**Data:** 28/10/2026  
**Catálogo:** `REV13-2026-09-20`  
**Matriz:** `MATRIZ-F1-REV13-OBR-v1`  
**Escopo:** Checkpoint A; nenhuma submissão implementada ou liberada.

## Resultado executivo

O catálogo canônico e a matriz possuem os mesmos **128 identificadores**, sem faltas, duplicidades ou identificadores excedentes. A implementação disponibiliza os 125 identificadores dos Blocos 1 a 14 no rascunho e trata `0.1` a `0.3` como cabeçalho institucional somente leitura.

A matriz classifica os campos assim:

| Classificação | Quantidade |
|---|---:|
| Essencial, somente leitura | 3 |
| Obrigatória essencial | 25 |
| Obrigatória condicional | 69 |
| Facultativa (REV13) | 4 |
| Facultativa nesta proposta | 27 |
| **Total** | **128** |

Os seis identificadores prefixados — `OUV.1` a `OUV.4` e `ESIC.1` a `ESIC.2` — integram os 69 obrigatórios condicionais. Sua apresentação já é controlada pelo retrato histórico de canais confirmado pelo APA, sem equiparar portal, telefone ou 156 a Ouvidoria ou e-SIC.

## Cobertura da implementação

- Os 14 blocos podem ser salvos e retomados incompletos no mesmo rascunho versionado.
- Catálogo, tipo da resposta, autorização do ARP, idempotência, controle otimista, auditoria, eventos e rollback permanecem aplicados no salvamento.
- As condicionais documentadas estão projetadas na interface e verificadas no domínio; respostas que perdem aplicabilidade deixam o conjunto ativo e permanecem no histórico inativo.
- `1.2` e `1.3` são obtidos da abertura do Registro, sem nova digitação.
- `2.1` é obtido do retrato histórico de canais quando ele existe; Registros legados preservam a resposta anterior.
- `0.1` possui nome fictício proveniente da identidade simulada. `0.2` e `0.3` não são inventados quando cargo/função e e-mail institucional não constam da fonte disponível.
- A submissão integral do contrato 3 não existe e nenhuma rota ou transição do contrato nuclear 2 foi alterada.

## Inconsistências e lacunas comprovadas

1. **Cabeçalho institucional incompleto.** A matriz classifica `0.1`, `0.2` e `0.3` como essenciais somente leitura. A PoC dispõe do nome fictício para `0.1`, mas não possui fonte institucional confiável para cargo/função (`0.2`) e e-mail institucional (`0.3`). Uma submissão que ignorasse esses campos contrariaria a matriz; preenchê-los livremente contrariaria a REV13 e os guardrails de identidade.
2. **Condição de WhatsApp.** A matriz ativa `8.7`, `8.8`, `8.8.1` e `8.9` para WhatsApp corporativo ou pessoal, mas `8.3` oferece somente `WhatsApp corporativo`. A implementação usa apenas a alternativa existente e não cria `WhatsApp pessoal` por inferência.
3. **Complemento de “Outro”.** O comportamento completo está decidido apenas para `5.1`. A matriz marca F1-D05 em outros campos, mas ainda não define de modo uniforme conteúdo, limite, armazenamento e obrigatoriedade do complemento na submissão.
4. **Exclusividades adicionais.** Estão implementadas somente as decisões expressas para `5.1` e `13.1`. A matriz ainda registra F1-D06 em outras seleções múltiplas, sem combinações aprovadas campo a campo.
5. **Condições não explicitadas.** `2.8.1`, `2.9.1` e `2.10.1` permanecem facultativos e sempre visíveis; `6.1.1` também permanece facultativo e sempre visível. Não foi criada condição por analogia. A condição de `10.2.1` segue o ramo ativo de `10.1` registrado na própria matriz, mas sua observação continua indicando necessidade de confirmação da condição exata.
6. **Marco de liberação.** O contrato candidato e a matriz ainda registram a necessidade de aprovação do marco que autorizará a submissão pelo contrato 3.

## Decisões humanas necessárias

Antes de habilitar ou implementar uma submissão integral capaz de concluir com sucesso, é necessário:

1. definir a fonte institucional confiável para `0.2` e `0.3`;
2. resolver F1-D04 sobre WhatsApp pessoal e corporativo;
3. aprovar F1-D05 para cada campo com “Outro”, sem generalização automática;
4. aprovar F1-D06 para as seleções múltiplas ainda pendentes;
5. confirmar a condição exata de `10.2.1` e decidir se as condições hoje não explicitadas continuarão sempre visíveis e facultativas;
6. aprovar formalmente a matriz e o marco de ativação da submissão do contrato 3.

## Decisão deste incremento

O Checkpoint B não foi iniciado. Os bloqueios acima impedem uma submissão integral tecnicamente fiel à política, especialmente pela ausência de fonte confiável para dois campos essenciais somente leitura. O rascunho dos 14 blocos permanece íntegro, e a PoC nuclear continua inalterada.
