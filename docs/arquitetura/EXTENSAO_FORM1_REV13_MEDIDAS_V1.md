# Extensão do contrato candidato 3 — medidas do item 13.2

**Identificação:** `F1-C3-REV13-EXT-MEDIDAS-v1`. **Matriz:** `MATRIZ-F1-REV13-EXT-MEDIDAS-v1`.
**Autorização:** INSTRUÇÃO_FORMS01_03, 05/11/2026. Implementação de rascunho; submissão institucional bloqueada.

## Catálogo e matriz centralizados

A fonte declarativa da extensão é [`form1_rev13_ext_medidas_v1.json`](../../app/catalogos/form1_rev13_ext_medidas_v1.json): enunciados, alternativas, classificação facultativa, independência, identificadores de versão e contagem efetiva. `catalogo_efetivo()` e `matriz_efetiva()` aplicam esse recorte somente ao conteúdo que identifica a adoção. Não há segunda cópia independente das regras.

O [contrato candidato original](CONTRATO_FORM1_INTEGRAL_REV13_CANDIDATO.md), o CSV original, seu hash e a matriz base permanecem inalterados, com **128 identificadores**. A extensão produz **129 identificadores efetivos**: mantém os outros 127, substitui a semântica de `13.2` exclusivamente na versão ampliada e acrescenta `13.2.1`. O Bloco 13 passa de quatro para cinco perguntas. O par **versão da estrutura + identificador** determina o significado; o número do rascunho, sozinho, não determina a semântica.

| Identificador na extensão | Objeto avaliado | Obrigatoriedade e condição |
|---|---|---|
| 13.2 | Guarda de documentos físicos contendo dados pessoais | Facultativa; sempre visível, independente de 13.2.1 |
| 13.2.1 | Bloqueio das estações de trabalho durante ausências | Facultativa; sempre visível, independente de 13.2 |

As opções permanecem as da pergunta original. Respostas diferentes são permitidas. Vazio não impede salvar; “A confirmar” gera aviso consultivo não bloqueante; “Não se aplica” refere-se apenas à medida respondida. Esta autorização funcional não equivale à aprovação institucional da matriz ou da submissão. As regras de `13.1` e sua ajuda permanecem intactas.

## Representação e adoção explícita

Sem `extensao_medidas.versao`, o conteúdo continua sendo `F1-C3-REV13`, com o enunciado e a resposta agregados originais. Novos rascunhos também começam na base; não existe adoção automática ou migração em lote.

O ARP vigente e autorizado pode adotar a extensão no Bloco 13, mediante confirmação expressa. O comando `adotar_extensao_medidas_form1_integral` exige `comando_id` e versão lida, usa os mesmos bloqueios e permissões do salvamento e realiza na mesma transação:

1. Preservação de um snapshot técnico completo do rascunho salvo anterior, ou reutilização do snapshot já existente daquela versão, sem reescrita.
2. Registro em `extensao_medidas` da versão, matriz, ARP, papel e data da adoção.
3. Arquivo em `extensao_medidas.legado` do enunciado original de `13.2`, resposta agregada (inclusive ausência), referência/número/lacre do snapshot e metadados do rascunho anterior. `rascunho_salvo_por` identifica quem salvou o rascunho, não presume autoria individual de cada resposta.
4. Remoção somente da resposta corrente agregada de `respostas["13.2"]`; nenhuma resposta é copiada para as duas perguntas da extensão. Ausência das chaves novas representa resposta vazia.
5. Avanço da versão de trabalho, novo lacre, evento encadeado e auditoria da adoção como ARP. O Registro, as apresentações e o fluxo de conferência não mudam de estado por esse ato.

As demais propriedades do envelope JSON são preservadas. O contrato numérico continua sendo `3`, com a identificação adicional da extensão; o contrato nuclear `2` não participa desse mecanismo. Não há novas tabelas nem migração. O banco de demonstração não recebe alterações nesta implementação.

## Compatibilidade e leitura histórica

- Rascunhos e snapshots carregam o marcador no próprio conteúdo. Novos envelopes de snapshot também explicitam `contrato.versao_estrutura`; snapshots antigos sem esse metadado continuam legados e não são regravados.
- A consulta de conferência seleciona o catálogo pelo conteúdo do snapshot, nunca pela versão atual do rascunho. A interface do Bloco 13 e a consulta ampliada disponibilizam a resposta agregada arquivada com seu enunciado original.
- Eventos de salvamento e preparação técnica registram a estrutura utilizada. A auditoria de adoção relaciona versão, papel e snapshot anterior.
- O salvamento do Bloco 13 envia `estrutura_lida`. Divergência entre a estrutura exibida e a armazenada é recusada, além do controle de versão existente. Chamadas antigas sem esse parâmetro continuam válidas somente em rascunhos legados; o formato de idempotência dessas chamadas é preservado.
- A interface impede adotar com edições locais não salvas. A recuperação de tentativa do navegador não restaura respostas de outra estrutura. Os novos controles usam a navegação, os rótulos, a consulta e a pré-validação existentes.
- Não há comando de retorno à versão base nem conversão automática. Uma evolução futura deve receber nova identificação, conservar esta definição e preservar os leitores históricos.

## Verificação e aceitação

Testes em `testes/test_extensao_medidas_form1.py` e `testes/apoio_extensao_medidas_form1.cjs` verificam catálogo/matriz base, adoção explícita, permissões, snapshot anterior, recuperação das respostas independentes, avisos facultativos, dados inválidos, aba antiga, idempotência, concorrência, rollback, consulta por versão, navegação e recuperação local. Os resultados efetivamente executados estão registrados no README e na AJ-004.

**Aceitação visual: NÃO VERIFICADA.** Roteiro manual, somente com dados fictícios:

1. No Bloco 13 de um Registro legado, conferir o enunciado agregado e sua resposta. Tentar adotar com edição não salva: deve orientar a salvar, sem descartar nada.
2. Salvar e adotar como ARP; conferir as duas perguntas vazias e a resposta anterior na consulta de legado. Como APA com outro ARP, conferir que não existe comando de adoção ou edição.
3. Responder “Sempre” e “Não”, salvar, recarregar e consultar como APA. Conferir facultatividade, tabulação, rótulos e legibilidade em telas larga e estreita.
4. Navegar 12 → 13 → 14; apresentar uma versão ampliada para conferência e comparar seu conteúdo com o snapshot anterior. Nenhum desses atos habilita submissão institucional.

## Arquivos do incremento

- Catálogo/matriz: `app/catalogos/form1_rev13_ext_medidas_v1.json`.
- Domínio e leitores versionados: `app/extensao_medidas_form1.py`, `app/rascunho_form1_integral.py`, `app/pre_validacao_form1_integral.py`, `app/submissao_form1_integral.py`.
- Projeções e rotas: `app/consultas_interface.py`, `app/main.py`.
- Interface: `app/paginas/_bloco_catalogado_form1.html`, `app/paginas/_extensao_medidas_form1.html`, `app/paginas/_legado_medidas_form1.html`, `app/paginas/conferencia_form1_integral.html`, `app/paginas/registro.html`, `app/estaticos/extensao_medidas_form1.js`.
- Testes: `testes/test_extensao_medidas_form1.py`, `testes/apoio_extensao_medidas_form1.cjs`.
- Documentação: `README.md`, `docs/planejamento/BACKLOG_AJUSTES_POC_AMPLIADA.md` e esta especificação. O diagnóstico documental preexistente da INSTRUÇÃO_FORMS01_02 foi preservado.
