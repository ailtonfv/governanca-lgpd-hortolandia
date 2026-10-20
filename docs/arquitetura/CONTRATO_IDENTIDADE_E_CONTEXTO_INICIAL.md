# Contrato de identidade do agente e contexto inicial do Registro

## Decisões institucionais incorporadas

- Em Hortolândia, cada servidor — concursado ou não — possui uma única matrícula.
- A matrícula será o nome de usuário apresentado na entrada da plataforma.
- Cada servidor utilizará senha individual, nunca compartilhada.
- A fonte oficial da Prefeitura deverá confirmar a identidade funcional depois da autenticação.
- A plataforma não cadastra pessoas titulares dos serviços: o FORM 1 guarda somente categorias.
- Os dados funcionais do agente têm outro propósito: autenticação, autorização, autoria e auditoria.
- Antes do FORM 1, o agente confirma primeiro a Secretaria/unidade responsável principal (“master”) dentro de seu alcance institucional.
- Em seguida, define se mapeará um serviço, processo ou atividade do catálogo e escolhe o contexto de atuação.
- A Prefeitura permanece a controladora; a Secretaria é a responsável interna pelo objeto.

## Percurso inicial

```mermaid
flowchart TD
    E["Matrícula + senha individual"] --> A["Autenticação institucional"]
    A --> I["Identidade funcional<br/>nome · situação · lotação"]
    I --> U["Secretaria/unidade<br/>responsável principal"]
    U --> T{"O que será<br/>mapeado?"}
    T --> S["Serviço"]
    T --> P["Processo"]
    T --> V["Atividade"]
    S --> C["Item do catálogo oficial"]
    P --> C
    V --> C
    C --> X["Contexto de atuação"]
    X --> G["G1 cria Registro + ciclo 1<br/>FORM 1 Não iniciado"]
```

## Dados mínimos do agente

| Dado | Finalidade na plataforma |
|---|---|
| Identificador técnico interno | Relacionar eventos sem espalhar a matrícula por todas as tabelas |
| Matrícula única | Nome de usuário e ligação com a identidade institucional |
| Nome | Identificação clara nas telas e atos autorizados |
| Situação funcional | Impedir acesso de vínculo inativo |
| Lotação atual | Apoiar a determinação do alcance institucional |
| Designações e vigência | Autorizar preenchimento, análise, validação e conclusão |
| Histórico de atuação | Autoria, segregação de funções e auditoria |

CPF, endereço, remuneração e demais dados do cadastro de pessoal não integram este contrato.

## Limite da PoC

Todas as matrículas, pessoas, unidades, objetos e contextos atuais são fictícios. O seletor inicial apenas simula uma entrada por matrícula; nenhuma senha existe na PoC. A autenticação real não será improvisada nem conectada diretamente ao banco de pessoal. Ana e Rafael deverão informar o mecanismo institucional para validar matrícula e senha e fornecer somente os atributos necessários.

O primeiro corte permite escolher a unidade principal entre aquelas nas quais o agente fictício é elaborador. O cadastro permanente de unidades participantes continua reservado à PoC ampliada; no M1a, a colaboração já é demonstrada pelo percurso de pendência intersecretarial sem transferência da unidade principal.
