# Diário da PoC — Sistema de Governança Municipal LGPD (Prefeitura Municipal de Hortolândia)

Registro técnico da construção da PoC nuclear (SAD 09 REV10; IMPLEMENTAR_POC_2026-10-08, minuta).
Regras deste diário: sem senhas, tokens ou dados pessoais; cada entrada com data; acessos diretos ao banco anotados aqui.

## 2026-10-09 — Preparação do ambiente

- Python: ambiente conda `lgpd-poc`, Python 3.14.8 (D:\Vendramini\anaconda3\envs\lgpd-poc).
- Banco: PostgreSQL 18.6 (64 bits), serviço `postgresql-x64-18` em execução; pasta de dados em C:\Program Files\PostgreSQL\18\data. Acesso de teste com o usuário `postgres` (SELECT version; SHOW data_directory) — nenhuma base da PoC criada ainda.
- Git 2.45.2; repositório privado https://github.com/ailtonfv/governanca-lgpd-hortolandia clonado em D:\Ailton\PMH\Cidades_Inteligentes\LGPD\poc (repositório ainda vazio).
- Documentação da série SAD movida para D:\Ailton\PMH\Cidades_Inteligentes\LGPD\Solution_Architecture_Document_(SAD)_Documento_de_Arquitetura_da_Solução (fora da pasta do curso).
- Operador da PoC: Encarregado de Dados (operador único; dados exclusivamente fictícios).

## 2026-10-10 — Base de dados e primeiros commits

- Git: pasta registrada como safe.directory (clone feito em terminal de administrador); primeiro commit (182d239) e segundo commit (abd8c0c) enviados ao GitHub.
- PostgreSQL: criado o usuário `lgpd_poc_app` (sem privilégios de administrador) e a base `lgpd_poc` (UTF8), de propriedade desse usuário — princípio do menor privilégio. Operação feita pelo Encarregado com o usuário `postgres`. Senhas fora do código e do repositório.

## 2026-10-11 — Conexão Python → PostgreSQL

- Bibliotecas instaladas no ambiente `lgpd-poc`: SQLAlchemy 2.1.4, psycopg 3.3.6, python-dotenv 1.2.4.
- Criados `.gitignore` (bloqueia `.env`, `.vscode/`, temporários e evidências) e `.env.exemplo` (modelo sem senha). O `.env` real fica só no computador.
- Teste de conexão (`teste_conexao.py`): falhou por autenticação. Causa: senha do `.env` diferente da do banco (mesmo tamanho, conteúdo diferente). Diagnóstico feito com `diagnostico_senha.py`, comparando impressões digitais (hash) sem exibir senhas. Corrigido o `.env`; conexão validada (usuário `lgpd_poc_app`, base `lgpd_poc`).
- Código de conexão usa `URL.create`, seguro para senhas com caracteres especiais.
- Primeira tabela criada (`evento`, livro de atos) via `criar_tabelas.py` e `app/modelos.py`.
- `app/eventos.py`: registro de eventos com cadeia de hash por objeto (SHA-256 sobre JSON canônico) e verificação relendo do banco. `demo_eventos.py` gravou 4 eventos fictícios (REG-0001 com 3, REG-0002 com 1); as duas correntes verificadas íntegras.
- Simulação de fraude (UPDATE direto no banco, desfeito por rollback): adulteração detectada no evento 2 do REG-0001. Nenhum dado real; livro de atos não modificado.
- Acesso direto ao banco: consulta somente leitura pelo pgAdmin (usuário `postgres`) para conferir a tabela `evento`.
- Observação: os 4 eventos têm o mesmo `registrado_em` porque foram gravados na mesma transação (o PostgreSQL usa o horário de início da transação).
- Tabelas `pessoa` e `conta` criadas (base da segregação de funções, O-66). Cada conta pertence a uma pessoa (chave estrangeira). Semeadas 3 pessoas fictícias e 4 contas (PESSOA-A com CONTA-A1 e CONTA-A2), sem CPF, matrícula ou dado real (`semear_pessoas.py`).
- Pendência registrada: alinhar a tabela `evento` ao SAD 05 REV11 e à DA-26 — trocar `pessoa_id` por `ator_tipo` + `ator_id` (eventos de pessoa, sistema ou integração), junto com os demais campos da DA-26.
- Tabelas `unidade` e `designacao` criadas; semeadas 2 unidades fictícias e 5 designações (`semear_designacoes.py`). PESSOA-A acumula elaborador e validador na Unidade Norte (cenário do O-66); o papel é dado à pessoa, não à conta.

## 2026-10-12 — README e dependências

- Criado `README.md` (versão 1): o que é o projeto, camadas de validação, situação, como montar o ambiente e rodar a PoC, autoria.
- Criado `requirements.txt` com as versões travadas das bibliotecas (reprodutibilidade).
- `COLA_COMANDOS.md`: seção sobre `git init` × `git clone`.
