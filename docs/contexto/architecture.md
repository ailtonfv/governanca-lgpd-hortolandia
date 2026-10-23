# Arquitetura resumida

## Stack vigente

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 |
| HTTP | FastAPI 0.147.0 |
| Servidor | Uvicorn 0.54.0 |
| Apresentação | Jinja2 3.1.6, HTML e CSS |
| Persistência | SQLAlchemy 2.1.4 |
| Driver | psycopg 3.3.6 |
| Banco | PostgreSQL 18 |
| Testes | pytest 9.1.1 e httpx 0.28.1 |

As versões executáveis estão travadas em `requirements.txt`. Não atualize dependência sem registrar motivo, impacto e nova rodada de testes.

## Camadas

| Camada | Responsabilidade | Não deve fazer |
|---|---|---|
| HTTP, `app/main.py` | Validar entrada web, obter identidade simulada, chamar caso de uso e responder | Decidir regra de negócio |
| Consulta, `app/consultas_interface.py` | Montar modelos de leitura para as páginas | Executar comando ou alterar estado |
| Domínio, `workflow.py`, `instrumentos.py`, `pendencias.py`, `acoes.py` | Aplicar estados, autorizações, invariantes e efeitos | Conhecer HTML ou depender da tela |
| Comandos e eventos | Garantir idempotência, auditoria, cadeia e reconstrução | Aceitar escrita parcial |
| Persistência, `modelos.py`, `banco.py` | Mapear tabelas, constraints e transações | Inventar regra funcional |
| Apresentação, `paginas/`, `estaticos/` | Tornar o estado compreensível e acessível | Acessar banco diretamente |

## Padrões vigentes

- domínio separado da interface;
- event sourcing pragmático com projeções consultáveis;
- livro de atos encadeado por SHA-256;
- comando idempotente obrigatório;
- transação única por ato;
- controle otimista por versão lida;
- catálogos fechados com identificadores canônicos;
- segregação pela identidade da pessoa;
- POST, redirecionamento e GET nas ações web;
- testes no domínio e na fronteira HTTP;
- migrações versionadas e dados fictícios reproduzíveis.

## Organização

```text
app/              aplicação e domínio
carga_ficticia/   massa exclusivamente sintética
demonstracoes/    executores controlados
instalacao/       preparação do banco
migracoes/        evolução do esquema
testes/           suíte pytest
docs/             arquitetura, operação, aceite e contexto
evidencias/       saídas operacionais locais, fora do Git
```

## Guardrails técnicos

- Credenciais ficam somente em `.env` local.
- Banco de testes deve terminar em `_teste`.
- Código não conhece senha institucional nem consulta diretamente cadastro real de pessoal.
- Nenhum evento existente é alterado ou apagado.
- Mudança de contrato cria nova versão; não reinterpreta snapshot antigo.
- Constraints de banco reforçam invariantes, mas a regra também deve produzir recusa compreensível no domínio.
- Novo adaptador ou interface não pode mudar o resultado dos testes de aceite.

## Documentos completos

- `docs/arquitetura/ARQUITETURA_POC.md`.
- `docs/arquitetura/MAPA_M1a.md`.
- SAD 02 para requisitos, SAD 03 para papéis, SAD 04 para workflow, SAD 05 para dados, SAD 06 para integrações, SAD 08 para segurança, SAD 09 para validação e SAD 10 para decisões.

