# Extensão versionada do Bloco 12 — guarda e destinação

## Fase A — diagnóstico e desenho (05/11/2026)

Autorização: INSTRUÇÃO_FORMS01_04. Base: `4d886aa64e8f5f269da48e321ef302b66eddc23c`, árvore limpa, seis commits locais não publicados. O catálogo REV13, sua matriz e a extensão `F1-C3-REV13-EXT-MEDIDAS-v1` foram examinados.

12.3 agrega quatro procedimentos; 12.4 agrega evidências e tem uma única localização (12.4.1); 12.5 pergunta por sistema/arquivo e tem um destino textual (12.5.1). As três perguntas principais são facultativas; localização e destino são condicionais. Reinterpretar esses valores em lugar de versioná-los perderia seu significado histórico.

**Compatibilidade confirmada no desenho:** o envelope JSON, os snapshots técnicos e o comando de adoção existentes comportam a evolução sem tabelas, migrações ou alteração de contratos externos. O contrato nuclear 2 fica intocado. Cada adoção é explícita, autorizada, idempotente, concorrente por versão lida e atômica com snapshot/evento/auditoria.

### Identificação e composição

Nova extensão: `F1-C3-REV13-EXT-GUARDA-v1`, matriz `MATRIZ-F1-REV13-EXT-GUARDA-v1`. As extensões de Blocos 12 e 13 são independentes: adotar uma não adota a outra. O perfil combinado identifica ambas como `F1-C3-REV13-EXT-MEDIDAS-GUARDA-v1`. A versão original continua com 128 IDs; somente MEDIDAS conserva 129; somente GUARDA tem 139; a composição tem 140. Não há campos de grupo fictícios incluídos nessa contagem.

### Numeração e regras da extensão

| Operação | Procedimento | Evidência | Localização da evidência |
|---|---|---|---|
| Guarda e arquivamento | 12.3 | 12.4 | 12.4.1 |
| Eliminação | 12.3.1 | 12.4.2 | 12.4.2.1 |
| Devolução | 12.3.2 | 12.4.3 | 12.4.3.1 |
| Transferência | 12.3.3 | 12.4.4 | 12.4.4.1 |

Procedimentos: Sim, Não, Não se aplica, A confirmar. Evidências: preservam Sim, Não, Em alguns casos, A confirmar e Não se aplica, individualizadas por operação. As oito respostas são facultativas e independentes: não se deduz evidência de procedimento, nem procedimento de evidência. Não/Não se aplica/A confirmar de uma operação não afetam as outras. Cada localização é condicional somente à evidência daquela operação = Sim ou Em alguns casos, preservando a natureza da regra anterior. Não é obrigatório informar localização quando a evidência não existe ou não se aplica.

12.5 pergunta se há transferência atualmente (Sim/Não/A confirmar, facultativa). Em caso de Sim, 12.5.1 identifica modalidades múltiplas: sistemas, arquivo físico/digital, unidades administrativas, custódia e Outra situação. 12.5.1.1 descreve Outra situação (até 200 caracteres), somente quando selecionada; 12.5.2 identifica destino/referência factual. Modalidades e destino são condicionais a Sim; o complemento é condicional a Sim + Outra situação. O rascunho aceita incompletude; a pré-validação sinaliza somente as condições ativas. Não se impõem exclusividades entre modalidades.

12.1–12.2 permanecem inalteradas, inclusive a alternativa Guarda permanente. Uma orientação distingue guarda permanente formalmente definida de permanência indefinida sem destinação. Ausência de eliminação não gera achado de irregularidade. As operações podem coexistir. O Bloco 12 não volta a cadastrar sistemas, destinatários ou repositórios dos Blocos 8, 10 e 11: admite referência factual ao que já foi identificado.

### Legado e adoção

Arquivar exatamente os enunciados, respostas e respostas condicionais inativas de 12.3, 12.4, 12.4.1, 12.5 e 12.5.1, além do snapshot completo, sua versão, autoria do rascunho, data e lacre. As respostas novas começam vazias. Os outros campos e qualquer extensão MEDIDAS existente permanecem intactos. Sem alteração em lote ou conversão automática.

Consultas escolhem catálogo e matriz pelo conteúdo preservado. Salvamentos dos Blocos 12/13 conferem a versão exibida; uma aba antiga não altera silenciosamente a semântica de perguntas. Recuperação local também respeita o perfil. A interface deve impedir adoção com alterações locais não salvas.

### Impacto mínimo previsto

Novo catálogo/matriz declarativo e módulo da extensão GUARDA; composição no leitor já existente de MEDIDAS; salvamento/validação dos blocos catalogados; pré-validação; projeções e rotas; componentes específicos do Bloco 12, consulta histórica e proteção de recuperação local; CSS compacto; testes e documentação. Modelos, permissões, contratos externos, banco demonstrativo, Cartilha e apresentação não mudam.

## Fase B — execução e evidências

Implementada. A fonte declarativa de enunciados, opções, regras, limites técnicos e agrupamento é [`form1_rev13_ext_guarda_v1.json`](../../app/catalogos/form1_rev13_ext_guarda_v1.json). Catálogo e matriz efetivos derivam dessa fonte, sem segunda cópia independente de regras.

`extensao_guarda` no JSON identifica versão, matriz, papel/autor/data de adoção e legado. O legado contém o snapshot exato e os cinco pares enunciado/resposta originais; respostas condicionais anteriormente inativas também são arquivadas ali, para não serem reinterpretadas como localizações específicas ou modalidades. Ausência desse marcador mantém o Bloco 12 original. `extensao_medidas` continua independente. A composição é explícita em rascunhos, snapshots, leitura, eventos e auditoria.

Salvamentos conferem o perfil efetivamente exibido. Chamadas legadas do Bloco 12 sem discriminador permanecem compatíveis somente enquanto a extensão GUARDA não foi adotada, inclusive em registros que já utilizam MEDIDAS. A interface compartilha a proteção contra adoção com edições locais não salvas. Regras continuam no domínio; interface e pré-validação reutilizam as mesmas condições declarativas.

A matriz compacta tem quatro linhas por operação, com procedimento, evidência e localização. Em telas estreitas, os controles são empilhados; não há abas ou salvamentos separados por operação. A numeração canônica mantém os grupos 12.3 e 12.4; a organização visual coloca as dimensões lado a lado por operação. Pendências usam a ordem do catálogo, preservando as localizações logo após a respectiva evidência. A consulta histórica e a leitura do APA não expõem controles editáveis.

**Resultados:** 38 testes de compatibilidade aprovados; 27 testes específicos aprovados e ensaio JavaScript aprovado separadamente; após incorporar esse ensaio à suíte, **652/652 testes aprovados** na regressão integral em 599,18 s, sendo 28 novos. Um aviso preexistente de descontinuação Starlette/AnyIO, sem falhas. Execuções exclusivamente em `lgpd_poc_teste`; comandos registrados no backlog. A cobertura inclui adoção nas duas ordens, permissões, chave idempotente, concorrência, rollback, leitura histórica, salvamento HTTP, condicionais independentes e navegação dos Blocos 11–14. Catálogo/matriz original e definição MEDIDAS permanecem sem alterações. A submissão institucional permanece bloqueada.

## Arquivos do incremento

- Fonte declarativa: `app/catalogos/form1_rev13_ext_guarda_v1.json`.
- Domínio e composição: `app/extensao_guarda_form1.py`, `app/extensao_medidas_form1.py`, `app/rascunho_form1_integral.py`, `app/pre_validacao_form1_integral.py`.
- Projeções e rotas: `app/consultas_interface.py`, `app/main.py`.
- Interface: `app/paginas/_bloco_catalogado_form1.html`, `app/paginas/_extensao_guarda_form1.html`, `app/paginas/_legado_guarda_form1.html`, `app/paginas/_operacoes_guarda_form1.html`, `app/paginas/conferencia_form1_integral.html`, `app/estaticos/extensao_medidas_form1.js`, `app/estaticos/estilo.css`.
- Testes: `testes/test_extensao_guarda_form1.py`, `testes/apoio_extensao_guarda_form1.cjs`.
- Documentação: esta especificação, `README.md` e `docs/planejamento/BACKLOG_AJUSTES_POC_AMPLIADA.md`.

## Aceitação manual pendente

**ACEITAÇÃO VISUAL NÃO VERIFICADA.** Os testes HTTP, DOM simulado e regras de CSS não substituem a inspeção real.

1. Como ARP, consultar o Bloco 12 legado. Salvar uma edição antes de adotar; verificar que a adoção com edição local pendente é impedida e que o legado permanece consultável.
2. Adotar e conferir quatro linhas por operação e novas respostas vazias, sem apagar 12.1–12.2 ou a extensão do Bloco 13.
3. Responder procedimento de eliminação = Não e evidência de eliminação = Sim; informar somente sua localização. Alternar outra evidência entre Sim, Não se aplica e A confirmar e conferir que as demais operações não mudam.
4. Marcar duas modalidades de transferência e Outra situação; salvar, recarregar e confirmar persistência. Alterar 12.5 para Não e conferir a retirada dos campos de transferência do preenchimento ativo.
5. Usar teclado em telas larga e estreita, conferir rótulos, foco e localizador das novas perguntas. Navegar 11 → 12 → 13 → 14.
6. Como APA com outro ARP, consultar as respostas sem editar; comparar uma apresentação antiga com uma nova, verificando seus enunciados e versões. Nenhum ato habilita submissão institucional.
