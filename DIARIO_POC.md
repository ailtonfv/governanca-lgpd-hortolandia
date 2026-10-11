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
