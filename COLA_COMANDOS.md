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
git add nome_do_arquivo         (separar para o registro)
git commit -m "descrição"       (fechar o registro)
git push                        (enviar ao GitHub)
git pull                        (trazer novidades do GitHub, se editou lá)
git log                         (ver o histórico)
```

## PostgreSQL
```
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```
Dentro do psql: `\l` lista as bases · `\q` sai · `\r` limpa um comando pela metade.
Lembre: todo comando SQL termina com `;`.

## Lembretes
- `(base)` = Python errado para a PoC. Use `conda activate lgpd-poc`.
- Uma linha cinza = um comando = um Enter.
- Nunca colocar senhas em arquivos que vão para o Git. Senha só no `.env`.
