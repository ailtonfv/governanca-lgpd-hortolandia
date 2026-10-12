# Cola de comandos — PoC LGPD

## Ao abrir o Anaconda Prompt (sempre, nesta ordem)
```
conda activate lgpd-poc
cd /d D:\Ailton\PMH\Cidades_Inteligentes\LGPD\poc
```
Confira: a linha deve começar com `(lgpd-poc)` e terminar em `...\poc>`.

## Rodar um programa
```
python nome_do_arquivo.py
```

## Abrir a pasta no VS Code
```
code .
```

## Git — registrar e enviar alterações
```
git status                      (o que mudou?)
git add nome_do_arquivo         (separar UM arquivo para o registro)
git add .                       (separar TODOS os alterados; o .gitignore protege o .env)
git commit -m "descrição"       (fechar o registro)
git push                        (enviar ao GitHub)
git pull                        (trazer novidades do GitHub, se editou lá)
git log                         (ver o histórico)
```

## Git — começar um repositório: init ou clone?
| Caminho | Comandos | Quando usar |
|---|---|---|
| Do zero | `git init` → `git add` → `git commit` → `git remote add origin <endereço>` → `git push` | A pasta já tem arquivos e ainda não é repositório |
| Clonar (o nosso caso) | `git clone <endereço> <pasta>` → `git add` → `git commit` → `git push` | O repositório já existe no GitHub |

- O `git clone` já faz o `git init` sozinho e já liga a pasta ao GitHub. Na `poc`, **não é preciso** `git init`.
- Cuidado: nunca rodar `git init` na pasta errada (ex.: a pasta do usuário inteira).
- A pasta oculta `.git` é o "arquivo morto" do Git: pode olhar, nunca mexer.

## PostgreSQL
```
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```
Dentro do psql: `\l` lista as bases · `\q` sai · `\r` limpa um comando pela metade.
Lembre: todo comando SQL termina com `;`.

## FastAPI (ainda não usado — etapa de telas)

- O que é: o **balcão** que recebe os pedidos do navegador e chama as regras. Diagrama em `ARQUITETURA_POC.md`, seção 1A.
- Quando chegar a hora, será assim (não rodar agora):
  - instalar: `pip install fastapi uvicorn`
  - ligar o balcão: `uvicorn app.main:app --reload`
  - abrir no navegador: http://127.0.0.1:8000
  - desligar: Ctrl+C no terminal

## Lembretes
- `(base)` = Python errado para a PoC. Use `conda activate lgpd-poc`.
- Uma linha cinza = um comando = um Enter.
- Nunca colocar senhas em arquivos que vão para o Git. Senha só no `.env`.
