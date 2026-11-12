# Pendências e retorno do FORM 1 — implementação demonstrativa

Data: 12/11/2026. Base: Mestre REV22.0 candidata v9, SHA-256 e5da7092bb98d24bff8c2d6679ea1e94f716500b2d3ea6e8fafe9211f424fbc9.
As decisões de segregação e complemento de manifestações foram aprovadas pelo usuário nesta sessão em 12/11/2026 para implementação demonstrativa. Isso não constitui ato municipal, ata do Comitê ou homologação D11.

## Persistência e comandos

A projeção `governanca_v9` integra o conteúdo da participação principal. Os eventos preservam as revisões. Não há alteração destrutiva dos snapshots históricos ou migração de catálogo. A leitura de complemento legado o apresenta como uma entrada única, sem dividir o texto; sua persistência acontece em comando explícito.

Os comandos bloqueiam o Registro e a participação, verificam versão lida, identidade funcional, papel vigente e estado. A chave por formulário é um SHA-256 de um identificador aleatório da página e da ação, limitado aos 64 caracteres suportados pelo banco. Repetir o mesmo envio não duplica o efeito. A chave não substitui as verificações de autorização.

## Percurso

1. A insuficiência ou divergência registrada no Bloco 1 origina solicitação individual. Necessidades adicionais são explícitas. Respostas “A confirmar” geram pendências próprias; vínculos são explícitos, sem comparação automática de textos.
2. Unidade destinatária e prazo são registrados separadamente. Indicar unidade não concede acesso. Sem unidade, a interface mostra que falta definir o destinatário. Sem prazo, não inventa vencimento. Escalonamento automático permanece não configurado.
3. A origem complementa o FORM 1. A confirmação pelo APA disponibiliza uma nova versão, sem substituir a versão em análise e sem repetir a ciência de ingresso ao DPO.
4. A origem devolve a versão confirmada por solicitação. Cada participação solicitante aceita ou pede novo complemento. O AAL decide separadamente usar a nova versão ou manter a anterior com motivo.
5. Manifestações anteriores permanecem concluídas e vinculadas à versão analisada. Quando afetadas, nasce nova solicitação na mesma unidade, ligada à anterior e à nova versão. Aviso do DPO é “Manifestação solicitada”, apenas na caixa local de testes nesta demonstração.

## Segregação

Quem apresentou ou confirmou a versão não pode validá-la como AAL, mesmo em outra conta da mesma identidade funcional. O AAL em exercício não pode apresentar nem confirmar nova versão do mesmo processo. A indicação de função na interface depende da participação assumida e da autorização vigente. Colaboradores que apenas preencheram partes não recebem bloqueio automático; a cobertura de seu alerta deve ser conferida separadamente.

## Interface

Um cartão por Registro reúne as participações visíveis e o acesso às pendências. A Central abre a fila atual. Na tela de pendências, responsável/prazo, vínculos e retirada são seções distintas. Os comandos ficam à direita, com largura adaptada em telas estreitas. A interface usa “nova versão do FORM 1”; identificadores de rastreabilidade ficam no histórico.

## Evidências e limites

Os testes ficam em `testes/test_governanca_form2_v9.py`, incluindo requisições geradas pelos formulários reais e repetição de comandos. A bateria geral e o resultado da rodada são registrados separadamente no relatório de vistoria; a existência deste contrato não significa que todos os testes passaram.

A inspeção visual desta rodada utiliza uma página renderizada pelo template real com dados sintéticos, em 1366 e 600 pixels. Não equivale à aceitação funcional de todos os blocos. Não há SMTP, publicação de catálogos, homologação jurídica ou liberação de conclusão institucional nesta entrega.
