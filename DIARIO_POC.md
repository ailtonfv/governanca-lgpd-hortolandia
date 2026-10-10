# Diário da PoC — Sistema de Governança Municipal LGPD (Prefeitura Municipal de Hortolândia)

Registro técnico da construção da PoC nuclear (SAD 09 REV10; IMPLEMENTAR_POC_2026-10-08, minuta).
Regras deste diário: sem senhas, tokens ou dados pessoais; cada entrada com data; acessos diretos ao banco anotados aqui.

## 2026-10-09 — Preparação do ambiente

- Python: ambiente conda `lgpd-poc`, Python 3.14.8 (D:\Vendramini\anaconda3\envs\lgpd-poc).
- Banco: PostgreSQL 18.6 (64 bits), serviço `postgresql-x64-18` em execução; pasta de dados em C:\Program Files\PostgreSQL\18\data. Acesso de teste com o usuário `postgres` (SELECT version; SHOW data_directory) — nenhuma base da PoC criada ainda.
- Git 2.45.2; repositório privado https://github.com/ailtonfv/governanca-lgpd-hortolandia clonado em D:\Ailton\PMH\Cidades_Inteligentes\LGPD\poc (repositório ainda vazio).
- Documentação da série SAD movida para D:\Ailton\PMH\Cidades_Inteligentes\LGPD\Solution_Architecture_Document_(SAD)_Documento_de_Arquitetura_da_Solução (fora da pasta do curso).
- Operador da PoC: Encarregado de Dados (operador único; dados exclusivamente fictícios).
