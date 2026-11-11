# FORM 1 · Composição REV18-v1

GOV_FORMS_REV18_03, 09/11/2026. A referência editorial é o Documento-Mestre REV18.0 e o [mapa documental v1](../planejamento/GOV_FORMS_REV18_02/correspondencia_v1.csv). O recorte acrescenta um campo e atualiza a apresentação do Bloco 14.

| Estrutura declarada no rascunho ou snapshot | IDs |
|---|---:|
| REV13 base | 128 |
| REV13 com MEDIDAS-v1 | 129 |
| REV13 com GUARDA-v1 | 139 |
| REV13 com ambas as extensões | 140 |
| `F1-C3-REV18-v1`, incluindo ambas as extensões | 141 |

## Adoção e leitura histórica

O ARP vigente inicia o rascunho pelo fluxo existente e encontra **Adotar a REV18 neste rascunho** no Bloco 11. A confirmação menciona as duas extensões. Consultar a página, navegar e salvar um bloco conservam a versão vigente. A proteção de saída solicita o salvamento de alterações locais antes da adoção.

A adoção verifica o ator e a versão lida, preserva ou reutiliza o snapshot anterior e grava uma nova versão de trabalho, o evento e a auditoria na mesma transação. Uma extensão já adotada conserva tanto as respostas como os metadados de adoção. Para cada extensão incorporada nesse ato, aplica-se o tratamento original de legado: o enunciado e a resposta agregada ficam consultáveis e os novos itens independentes começam sem resposta. A auditoria identifica a pessoa, o papel de ARP, a estrutura anterior, a nova estrutura e o snapshot de origem.

O contrato candidato 3 mantém sua identificação de base. A estrutura efetiva é lida de `versao_estrutura` no snapshot e nos eventos e dos marcadores do próprio conteúdo no rascunho. O marcador `revisao_18` registra também a política efetiva. A composição é aplicada somente a conteúdo que declare a adoção. Os catálogos históricos são consultados pela própria versão.

## Política consultiva e Blocos 11 e 14

- A política da composição é `MATRIZ-F1-REV18-v1`. Deriva da matriz REV13, do recorte 8V e das matrizes GUARDA/MEDIDAS. O único ID adicional é **11.2.5**, entre 11.2.4 e 11.3. Está sempre visível. Admite Sim, Não, Em alguns casos e A confirmar. A obrigatoriedade não foi definida pelo Mestre; usa-se a classe facultativa provisória já utilizada na PoC. A confirmar gera aviso consultivo. A identificação de um fato no exterior não produz uma conclusão jurídica.
- O Bloco 14 passa a **Pendências e situações observadas**. Em 14.2.1, a pergunta passa a **Em que momento do fluxo ocorre?** e mantém as alternativas. Em 14.1, o rótulo histórico é preservado pois as respostas anteriores não distinguem quais pendências já foram listadas. A orientação atrelada ao campo esclarece onde registrar uma pendência adicional. Os rótulos de 14.2 e 14.2.2 já correspondem à REV18. A lista consultiva e os condicionais continuam a usar as regras existentes.
- O Mestre qualifica **0.2 (cargo/função)** e **0.3 (e-mail institucional)** como obrigatórios. Prevalece nesta PoC a política operacional 8V: metadados somente de leitura, não bloqueantes, quando disponíveis em fonte institucional. As permissões APA/SAA e o bloqueio da submissão institucional permanecem vigentes.

A aceitação funcional em navegador pode ser feita com um Registro fictício: conferir o enunciado anterior de 14.2.1, adotar a REV18 como ARP no Bloco 11, marcar infraestrutura municipal, salvar 11.2.5 e recarregar. Conferir depois o Bloco 14, a leitura da versão anterior e a ausência de edição para o APA que não exerce o papel de ARP.
