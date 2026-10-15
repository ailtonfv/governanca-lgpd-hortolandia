# Arquitetura da PoC nuclear — visão em camadas

Guia de orientação para quem lê ou mantém o código da PoC do Sistema de Governança Municipal LGPD
(Prefeitura Municipal de Hortolândia). Referências: SAD 09 (escopo) e SAD 10, DA-28 (stack). Volta ao [README](../../README.md) · percurso de um Registro: [Mapa do M1a](MAPA_M1a.md).

## 1. O caminho de uma requisição

```mermaid
flowchart LR
    U["👤 SERVIDOR<br/>(no navegador)"] -->|"1. IDA — formulário HTML<br/>preenche e clica Submeter, Analisar ou Validar"| A
    subgraph S["Aplicação (Python 3.14)"]
        A["Camada de entrada<br/>FastAPI — balcão"] -->|"2. comando"| D
        D["Camada de domínio<br/>workflow · permissões · eventos/hash"] -->|"3. leitura e gravação"| P
        P["Camada de persistência<br/>SQLAlchemy"]
        A -->|"5. pede a página de resposta"| T["Camada de apresentação<br/>Jinja2 — monta o HTML<br/>(modelo com lacunas)"]
    end
    P -->|"4. SQL (transação única)"| B[("PostgreSQL 18")]
    T -->|"6. VOLTA — página de resposta HTML<br/>ex.: Validado ✔ ou Negado: segregação"| U

    classDef servidor fill:#1e3a5f,stroke:#5b9bd5,color:#fff,stroke-width:3px
    classDef html fill:#4d3d1e,stroke:#d4a017,color:#fff
    class U servidor
    class T html
    linkStyle 0 stroke:#5b9bd5,stroke-width:3px
    linkStyle 5 stroke:#d4a017,stroke-width:3px
```

**Legenda:** azul = o SERVIDOR e o formulário HTML que ele preenche (ida) · amarelo = a página de resposta HTML montada pelo Jinja2 (volta).

O caminho é o mesmo para qualquer pedido e para qualquer Instrumento (FORM 1 a 4). Na PoC nuclear existe apenas o FORM 1 simplificado; os demais chegam na PoC ampliada sem mudar as camadas.

## 1A. Onde entra o FastAPI — hoje e depois

**Analogia:** o FastAPI é o **balcão de protocolo** da Prefeitura. Ele recebe o pedido de quem chega, confere quem é a pessoa e encaminha ao setor que decide. O balcão não decide nada: quem decide é o domínio (`permissoes.py`, `eventos.py`).

**Hoje (sem FastAPI):** quem "chega ao balcão" são os testes automatizados e as demonstrações, que rodamos no terminal.

```mermaid
flowchart LR
    T["Terminal<br/>python -m pytest<br/>(testes/)"] --> D["Domínio<br/>criar_registro()<br/>executar_acao()"]
    D --> P["SQLAlchemy"] --> B[("PostgreSQL")]
    classDef hoje fill:#1e4d2b,stroke:#5cb85c,color:#fff
    class T hoje
```

**Depois (com FastAPI):** quem chega é o servidor, pelo navegador. O domínio é **o mesmo**, sem mudar uma linha.

```mermaid
flowchart LR
    N["👤 SERVIDOR<br/>clica em Validar no navegador"] -->|"pedido HTTP"| F["FastAPI — balcão<br/>app/main.py"]
    F --> D["Domínio<br/>executar_acao()<br/>verificar_acao()"]
    D --> P["SQLAlchemy"] --> B[("PostgreSQL")]
    F -->|"monta a resposta"| J["Jinja2<br/>página HTML"] --> N
    classDef novo fill:#4d3d1e,stroke:#d4a017,color:#fff
    class N,F,J novo
```

**Legenda:** verde = o que existe hoje · amarelo = o que o FastAPI e o Jinja2 acrescentam.

O que muda é **só a porta de entrada**. É por isso que estamos construindo e testando o domínio primeiro: quando o balcão chegar, as regras já estarão provadas.

Quando: etapa de telas mínimas da PoC nuclear (depois do ciclo de vida e dos testes). O FastAPI ainda não está instalado nem no `requirements.txt`.

## 2. Responsabilidade de cada camada

| Camada | Tecnologia | O que faz | O que NÃO faz | SAD de referência | Arquivo(s) previsto(s) |
|---|---|---|---|---|---|
| Interface | Navegador | Exibe formulários e resultados | Não decide regras | SAD 02 | — |
| Entrada | FastAPI | Recebe a requisição, identifica o usuário, chama o domínio, devolve a resposta | Não contém regra de negócio | SAD 06 | `app/main.py` |
| Domínio | Python puro | Aplica as regras: transições de estado, segregação de funções (por pessoa), pedido idempotente, cadeia de eventos com hash | Não sabe nada de HTTP nem de SQL | SAD 03, SAD 04, SAD 08, DA-26, DA-27, DA-39 | `app/workflow.py`, `app/permissoes.py`, `app/comandos.py`, `app/eventos.py` |
| Persistência | SQLAlchemy | Traduz objetos em tabelas e grava tudo na mesma transação | Não decide regras | SAD 05 | `app/modelos.py`, `app/banco.py` |
| Banco | PostgreSQL | Guarda os dados e garante a consistência (índices únicos, transações) | — | SAD 05, DA-28 | — |
| Apresentação | Jinja2 | Monta as páginas HTML | Não acessa o banco diretamente | SAD 02 | `app/paginas/` |
| Testes | pytest | Executa os cenários de aceite (POC-TS) pela interface HTTP e pelas regras | — | SAD 09 | `testes/` |

## 3. Princípios que a divisão garante

1. **As regras ficam num só lugar (domínio).** Trocar a tela ou o banco não muda as regras.
2. **Portabilidade.** Os testes de aceite falam com o sistema pela interface HTTP; uma reimplementação em outra linguagem pode ser conferida com os mesmos testes (SAD 09, seção 37).
3. **Transação única.** Um comando grava o evento de domínio, a auditoria e a projeção juntos, ou nada (DA-26).
4. **Integridade verificável.** Cada evento guarda o hash do anterior; qualquer alteração quebra a cadeia (DA-27). Demonstração: `scripts/primeiro_hash.py` e `python -m demonstracoes.demo_eventos`.

## 4. Mapa das pastas

Regra: **pasta na raiz = código; `docs/` = texto.**

```mermaid
flowchart TB
    subgraph COD["🐍 Código — vai para o GitHub"]
        direction LR
        B1["app/<br/>o sistema: modelos, regras,<br/>pedidos, eventos"]
        B2["instalacao/<br/>criar tabelas,<br/>conferir conexão"]
        B3["migracoes/<br/>evolução versionada<br/>do banco"]
        B4["carga_ficticia/<br/>pessoas, papéis<br/>e catálogos fictícios"]
        B5["demonstracoes/<br/>ver funcionando"]
        B6["testes/<br/>testes automatizados<br/>(pytest)"]
        B7["scripts/<br/>exercícios de<br/>aprendizado"]
    end
    subgraph DOC["📘 docs/ — vai para o GitHub"]
        direction LR
        A1["arquitetura/<br/>este guia e<br/>o Mapa do M1a"]
        A2["operacao/<br/>instalação<br/>e execução"]
        A3["diario/<br/>registro datado"]
        A4["revisoes/<br/>revisões técnicas"]
    end
    subgraph CFG["⚙️ Configuração — vai para o GitHub"]
        C1[".gitignore · .env.exemplo<br/>requirements.txt · pytest.ini"]
    end
    subgraph LOCAL["🔒 Só no computador — NUNCA vai para o GitHub"]
        D1[".env (senha do banco) · cópias *.dump<br/>cola de comandos · trilha de aprendizagem"]
    end
    CFG -. o .gitignore bloqueia .-> LOCAL

    classDef doc fill:#1e3a5f,stroke:#5b9bd5,color:#fff
    classDef cod fill:#1e4d2b,stroke:#5cb85c,color:#fff
    classDef cfg fill:#4d3d1e,stroke:#d4a017,color:#fff
    classDef loc fill:#5c1e1e,stroke:#d9534f,color:#fff
    class A1,A2,A3,A4 doc
    class B1,B2,B3,B4,B5,B6,B7 cod
    class C1 cfg
    class D1 loc
```

**Legenda:** verde = código · azul = documentação · amarelo = configuração pública · vermelho = segredo ou material pessoal, só no computador.

## 5. Status

- 2026-10-09: ambiente preparado; demonstração da cadeia de hash (`primeiro_hash.py`). Camadas ainda não implementadas.
- 2026-10-11: cofre de configuração (`.env`, `.gitignore`, `.env.exemplo`) e conexão Python → PostgreSQL validada com o usuário `lgpd_poc_app`.
- 2026-10-14: Etapa 2d — pedido idempotente estrito (`app/comandos.py`), base `lgpd_poc_v2`, migrações versionadas, 40 testes automatizados.
- 2026-10-15: repositório reorganizado (código na raiz, texto em `docs/`).
