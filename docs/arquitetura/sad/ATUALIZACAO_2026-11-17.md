# Atualização documental — 17/11/2026

Base: main `0d247db`. Branch documental: `docs-sad-2026-11-17`, sem merge. Nenhum arquivo da aplicação alterado; nenhum servidor ou banco acessado para escrita.

## Registro das decisões

| Registrado | Conferido | Falta conferir |
|---|---|---|
| SAD 10 REV17, seção 3, DA-40 — P36 | Indicação/reatribuição pelo APA da unidade, com habilitação e segregação preservadas | Aceite institucional para produção, quando aplicável |
| Seção 3, DA-41 — P69 | Guarda institucional sem pendência para a origem; selo textual distinguido do ícone no main | Definição do grupo de trabalho; etiqueta textual do Lote 8 em tela |
| Seção 3, DA-42 — P74 | Manifestação de ofício do DPO permanece consultiva | Nenhuma decisão nova atribuída ao DPO |
| Seção 3, DA-43 — P79/P96 | Suplente habilitado confere; sem suplente, aguarda definição; dispensa descartada | Exceção com segundo ato pela mesma pessoa continua em deliberação |
| Seção 3, DA-44 — P83 | Exclusividade de A confirmar e combinação permitida para análise jurídica registradas | Homologação jurídica não é presumida |
| Seção 3, DA-45 — P86 | Contagem por perguntas ativas, centralizada e expressamente provisória | Decisão R17 |
| Seção 3, DA-46 — P91 | Designação formal, painel exclusivo e ausência de suplente/substituto na demonstração | Responsável pelo cadastro em produção; continuidade institucional da AB-10 não resolvida |
| Seção 3, DA-47 — P101 | Três escolhas de saída e descarte explícito | Nada novo nesta revisão documental |
| Seção 3, DA-48 — C1 | Lista/quantidade nas duas perguntas; resposta do AAL sem pré-marcação; sem classificação automática de impeditivos | Vistoria/merge do Lote 8 e deliberação da classificação de impeditivos |
| Seção 3, DA-49 — D6 | Sete perguntas de abertura consultam a apresentação em análise sem pré-marcar resposta | Vistoria/merge do Lote 8 |
| Seção 3, DA-50 — D7 | Divergência aprovada registrada com data, decisor e identificadores das perguntas | Incorporar à próxima revisão do Mestre; vistoria/merge do Lote 8 |
| Seção 3, reafirmação “Registro macro” | Remissão às DA-17 e DA-19; não criada ficha duplicada | Nada adicional |
| Seção 4, AB-11 — D-FORM3-DPO | Proposta registrada como em deliberação; nenhum efeito atribuído ao código | Decisão de Ailton |
| Seção 3.1, PROD-01 a PROD-03, ligada à DA-35 e à seção 37 do SAD 09 | Autenticação real; concorrência na auditoria; cadastro da designação do DPO | Verificação na transferência à TI; responsável pelo cadastro a definir. D5 não decidida |

A numeração sem lacunas de PROD-02 refere-se à cadeia de auditoria. Não altera a DA-39, item 3, que admite lacunas na numeração anual dos Registros. As decisões de outubro permanecem históricas. O SAD 10 foi lido antes das inclusões; SAD 01, SAD 04 e ADR 000 foram usados como referências vinculantes. Os outros SADs não foram modificados.

## Documentos orientativos

| Registrado | Conferido | Falta conferir |
|---|---|---|
| Cartilha REV30.21, seção 3.1 | Papéis APA/suplente, indicação do AAL, DPO consultivo e painel exclusivo | Leitura editorial de Ailton |
| Cartilha, seção 5.4 | P17; grade, perguntas ativas, selos, condicionais, saída sem salvar e consulta ao DPO | Recursos do Lote 8 identificados como em conferência |
| Cartilha, seção 8.7 e glossário do ciclo do FORM 1 | Corrigida autoconferência antiga; Registro macro e cinco verbetes acrescentados | Leitura editorial |
| Palestra v16.13, slide 6; slide 28 e notas 28–29 | Suplente; P17; “Quatro papéis, quatro atos” nas notas do slide 29, opção expressamente permitida nas instruções | Ensaio oral das notas |
| Palestra, slide 35 e suas notas | Frase de abertura e sequência demonstrativa; itens do Lote 8 condicionados à conferência/integração | Ensaio do percurso |
| Palestra, rodapés dos slides 9–11, 13–16, 27–30, 35–36 e 39 | Aviso de demonstração e autenticação real; mantidos 39 slides | Conferir projeção no equipamento da palestra |
| README, abertura, papéis, percurso e seção de atualização de 17/11 | Terminologia, autenticação real e ligação ao SAD 10 REV17 | Merge documental depende de autorização |
| Lista restrita PARA_REVISAO_DO_MESTRE.md | D7 e diferenças D13, com remissão ao relatório restrito completo do Lote 8 | Revisão do Mestre por Ailton; arquivo fora do GitHub |

A frase recebida sobre o AAL classificar impeditivos foi alinhada à decisão mais recente: a classificação permanece em deliberação; não foi apresentada como regra já definida. “A confirmar” não foi descrita como abertura automática universal de pendência: a orientação respeita a regra de cada item e a exceção da guarda institucional.

O arquivo complementar de textos de 14/11 não foi localizado nesta rodada. A atualização equivalente da P17 foi feita com base na decisão expressa de Ailton, no código do main e na evidência de teste; não se declara comparação literal com aquele arquivo.

## Verificações

- P17: `test_confirmacao_atualiza_fila_sem_assuncao` aprovado na última bateria registrada em `testes-final.xml` do Lote 8. Domínio, teste e reconciliação correspondentes não diferem entre main e Lote 8. Não havia marca “implementação pendente” da P17 no README a remover; havia texto antigo na Cartilha, atualizado.
- Documentação apenas: não foi repetida a bateria da aplicação nem usado banco de demonstração.
- Renderização completa pelo Word e PowerPoint instalados: Cartilha com 102 páginas, SAD 10 com 38 páginas e palestra com 39 slides. Inspeção das páginas alteradas e panoramas de paginação; preservado o desenho dos documentos de origem.
- O renderizador empacotado apresentou falha de codificação/limpeza no LibreOffice local. A conferência foi feita com os programas nativos; não se declarou sucesso daquele renderizador.
- Sumário e campos de página atualizados. Os 243 marcadores estáveis da Cartilha foram preservados. O Word havia retirado 83 marcadores; foram restaurados nos títulos correspondentes com IDs únicos e reconhecidos novamente pelo Word.
- Sem atualização de configuração da aplicação para outra revisão da Cartilha; a versão usada pelas referências históricas da PoC permanece preservada.
- As revisões anteriores foram mantidas. Novas revisões foram preparadas para as mesmas pastas documentais.
- Fontes jurídicas, históricos e capítulos fora deste pedido não passaram por nova auditoria normativa.

## Publicação

Publicar somente README e a edição textual integral do SAD 10 REV17, com este relatório. A edição textual contém as decisões e identificadores, sem enunciados do catálogo ou do Mestre. A autoria pública foi reduzida a “Ailton, DPO”, conforme a identificação solicitada.

Cartilha, palestra, cópias de segurança, PDFs de conferência, lista restrita e fontes não entram no GitHub. Revisão de segredos sem achados nos documentos a enviar. Nenhum .env, cópia de banco, senha ou dado de atendimento real incluído. Não alterar main nem apagar branches.

