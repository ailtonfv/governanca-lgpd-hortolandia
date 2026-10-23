# Domínio do Sistema Municipal de Governança LGPD

## Pergunta central

O domínio registra como a Prefeitura trata dados pessoais em determinado serviço, processo ou atividade, quem responde internamente pelo mapeamento e como o histórico pode ser comprovado.

## Conceitos centrais

| Conceito | Definição operacional |
|---|---|
| Registro LGPD | Unidade de governança que reúne o tratamento, seu ciclo, instrumentos, participantes, pendências, medidas, eventos e evidências |
| Serviço | Entrega percebida pelo cidadão ou usuário |
| Processo | Sequência que produz um resultado |
| Atividade | Etapa concreta de execução dentro de um processo |
| Canal | Meio transversal de atendimento; é apoio, salvo quando realiza tratamento autônomo |
| Secretaria responsável | Secretaria que coordena e mantém o Registro |
| Secretaria participante | Secretaria que contribui sem assumir automaticamente a responsabilidade principal |
| Contexto de atuação | Classificação administrativa e funcional escolhida de catálogo |
| Finalidade | Propósito legítimo, específico e explícito para o qual os dados pessoais são utilizados |
| Instrumento | FORM ou outro instrumento com estado, autoria e versões próprias |
| Evento | Fato imutável do domínio, encadeado e auditável |
| Pendência | Solicitação formal com destino, responsável, resposta e decisão |
| Ação obrigatória | Medida que deve ser concluída e comprovada antes do encerramento |

## Distinções obrigatórias

- Secretaria responde **quem coordena**.
- Objeto responde **o que é mapeado**.
- Contexto responde **em qual frente funcional ocorre**.
- Finalidade responde **para que os dados pessoais são utilizados**.
- Canal responde **por onde o atendimento chega**.
- Hipótese legal responde **por que o tratamento é juridicamente permitido**.

Essas dimensões não devem ser fundidas num único campo.

## Identidade e autorização

- Na solução futura, a matrícula será o nome de usuário e a senha será individual.
- A identidade funcional deverá vir de mecanismo institucional informado pela T.I.
- A aplicação utiliza identificador técnico interno para evitar espalhar matrícula pelo banco.
- Nome, situação funcional, lotação e designações servem a autenticação, autorização, autoria e auditoria.
- CPF, endereço, remuneração e outros dados funcionais desnecessários não integram o contrato.
- Autorização depende da pessoa, do papel, da vigência e do alcance institucional.
- Segregação de funções compara a pessoa, não apenas a conta de acesso.

## Titulares e FORM 1

O FORM 1 descreve categorias pertinentes ao tratamento. Seleção múltipla não significa marcar todos os papéis sociais que uma pessoa possa exercer fora do objeto mapeado.

O FORM 1 sintético vigente contém:

- finalidade;
- categorias de titulares;
- categorias de dados;
- compartilhamentos.

Os valores categóricos vêm de listas fechadas. Código desconhecido, repetido ou campo não previsto é recusado. Uma versão submetida nunca é reescrita.

## Invariantes do fluxo

- Todo Registro possui uma Secretaria responsável e um ciclo atual.
- Cada comando possui `comando_id` idempotente.
- Evento, auditoria, snapshot e projeção relacionados ao comando são gravados juntos ou desfeitos juntos.
- Eventos são imutáveis e encadeados por hash.
- Concorrência não pode criar duas assunções, duas versões ou duas decisões válidas para o mesmo ponto lógico.
- Tela desatualizada não sobrescreve estado mais novo.
- Devolução preserva a versão submetida e cria pendência rastreável.
- Participação intersecretarial não autoriza a Secretaria de destino a editar o FORM 1.
- Conclusão exige versão validada, ausência de bloqueios e competência formal.
- Medida obrigatória exige responsável, estado, evidência e vínculo com Registro, ciclo e Instrumento.

## Catálogos e curadoria

O percurso de criação segue a cascata:

`Secretaria responsável → tipo → objeto vinculado → contexto permitido → G1`

Se não houver item adequado, o agente solicita revisão. Ele não cria nome ou contexto livremente. Carta de Serviços, portal, FORMs e inventários fornecem candidatos; somente a curadoria aprova o item canônico, sua fonte, vigência e vínculos.

## Fontes detalhadas

- `README.md`, especialmente “Como os Registros são organizados”.
- `docs/arquitetura/MAPA_M1a.md`.
- `docs/arquitetura/CONTRATO_FORM1_SINTETICO.md`.
- `docs/arquitetura/CONTRATO_IDENTIDADE_E_CONTEXTO_INICIAL.md`.
- SAD 03, SAD 04, SAD 05, SAD 08, SAD 09 e SAD 10.

