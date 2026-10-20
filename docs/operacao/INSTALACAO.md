# Instalação e execução da PoC

*Guia de operação do repositório. Volta ao [README](../../README.md).*

Todos os comandos são rodados na pasta do projeto, com o ambiente Python ativado. Somente dados fictícios.

## Como montar o ambiente

1. **Python** — criar e ativar o ambiente:
   ```
   conda create -n lgpd-poc python=3.14
   conda activate lgpd-poc
   python -m pip install -r requirements.txt
   ```
2. **Banco** — no `psql`, como administrador, criar o usuário da aplicação (sem privilégios de administrador) e a base:
   ```sql
   CREATE ROLE lgpd_poc_app LOGIN PASSWORD 'escolha_uma_senha';
   CREATE DATABASE lgpd_poc_v2 OWNER lgpd_poc_app;
   CREATE DATABASE lgpd_poc_teste OWNER lgpd_poc_app;
   ```
   A base `lgpd_poc_v2` é a da PoC; a `lgpd_poc_teste`, só dos testes automatizados. A base anterior (`lgpd_poc`, até a Etapa 2c) foi preservada, com cópia de segurança, apenas para consulta.
3. **Configuração** — copiar o modelo e preencher a senha (o `.env` nunca vai para o GitHub):
   ```
   copy .env.exemplo .env
   ```
4. **Conferir** — `python -m instalacao.teste_conexao` deve responder "Conexão estabelecida!".

## Como rodar a PoC (até aqui)

Os comandos estão separados pelo que fazem. Todos são rodados na pasta do projeto, com `python -m pasta.arquivo` (ponto, não barra).

**1. Instalação** — uma vez, num banco vazio:
```
python -m instalacao.criar_tabelas      (cria as tabelas e registra a versão 1 do esquema)
```

**2. Migrações** — evolução do esquema; roda só as que faltam, e rodar de novo não faz nada:
```
python -m migracoes.aplicar
```

**3. Carga fictícia** — pessoas, unidades, papéis e catálogos; pode ser repetida:
```
python -m carga_ficticia
```

**4. Demonstrações** — para ver funcionando; gravam uma vez só:
```
python -m demonstracoes.demo_eventos    (livro de atos, cadeia de hash e três fraudes simuladas)
python -m demonstracoes.demo_registro   (ato G1: criação, repetição, bloqueio e advertência)
```

**5. Testes automatizados** — num banco de teste próprio (`lgpd_poc_teste`), esvaziado a cada teste; nunca no banco da PoC:
```
python -m pytest
```

**6. Tela da PoC** — liga o servidor local; mantenha este terminal aberto:
```
python -m uvicorn app.main:app --reload
```
Depois, abra `http://127.0.0.1:8000` no navegador. O seletor de agente usa apenas contas fictícias para demonstrar o alcance institucional; ele ainda não representa a autenticação definitiva.
