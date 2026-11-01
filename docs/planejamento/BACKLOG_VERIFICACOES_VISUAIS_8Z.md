# Backlog de verificações visuais — Incremento 8Z

**Situação:** pendências aceitas expressamente como ressalvas para a publicação do 8Z em 01/11/2026. O aceite da ressalva não equivale à aprovação das verificações.

## Evidências disponíveis

- regressão integral: 483 de 483 testes aprovados;
- diff integral revisado;
- painel inicial conferido pelo responsável funcional em tela larga, sem cortes aparentes;
- nenhuma migração criada;
- submissão do FORM 1 Integral preservada como bloqueada.

## Verificações manuais pendentes

| ID | Verificação | Critério de aceite manual |
|---|---|---|
| 8Z-VIS-01 | Empilhamento abaixo de 950 px | Em largura inferior a 950 px, o painel **O que precisa da sua atenção** aparece antes de **Mapeamentos disponíveis para você**; os cartões não produzem corte horizontal, e textos e ações continuam legíveis e acessíveis por teclado. |
| 8Z-VIS-02 | Limpeza de contexto incompatível | Na abertura, após trocar Secretaria, tipo ou objeto de modo que o contexto anterior deixe de ser permitido, o contexto é desmarcado, a interface informa a remoção e nenhum valor incompatível permanece selecionado ou é enviado como válido. |
| 8Z-VIS-03 | Duplicidade consultável | Ao repetir uma combinação fictícia já registrada, uma identidade autorizada visualiza código, objeto, Secretaria, contexto, situação e a ação **Consultar este Registro**, que conduz ao Registro correto. Uma identidade sem acesso não recebe identificadores nem conteúdo do conflito. |

## Limitação da evidência visual

A automação de navegador não conseguiu confirmar a URL no Windows com segurança. A proteção não foi contornada e nenhuma das três verificações acima deve ser declarada aprovada sem execução manual e registro da evidência correspondente.
