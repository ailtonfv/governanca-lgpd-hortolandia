# Especificação técnica curta — futura submissão do FORM 1 integral

**Situação:** preparação do próximo incremento; funcionalidade não implementada nem liberada.
**Contrato:** candidato 3 / REV13. O contrato nuclear 2 permanece separado e inalterado.

## 1. Componentes técnicos independentes

A futura submissão deverá ser um comando próprio, idempotente e autorizado, recebido com `comando_id`, versão lida do rascunho e identidade autenticada do ARP autorizado. Antes de qualquer mudança de estado, o domínio deverá executar a validação integral baseada na matriz versionada, recusando pendências obrigatórias ativas sem alterar nem apagar o rascunho.

Quando válida e institucionalmente liberada, uma única transação deverá:

1. bloquear e conferir a versão vigente do rascunho para impedir concorrência perdida;
2. conferir autoria, designação vigente, Registro, canais históricos e integridade do lacre;
3. produzir um snapshot imutável do envelope REV13, incluindo respostas ativas, histórico necessário, complementos, participantes, destinatários estruturados e metadados de origem;
4. gravar versão, texto canônico, hash, autor, data, versão do contrato e evento de submissão;
5. atualizar somente as projeções e os estados aprovados para o contrato 3;
6. efetivar tudo atomicamente ou realizar rollback integral.

Repetição do mesmo comando deve devolver o resultado original; a mesma chave com conteúdo diferente deve ser recusada. Tentativas simultâneas sobre a mesma versão devem produzir no máximo uma submissão. Uma rejeição de validação, autorização, versão ou lacre deve preservar integralmente o rascunho.

A implementação deve reutilizar os mecanismos maduros de comando, evento, versão imutável e auditoria do projeto, mas não pode chamar diretamente a submissão do FORM 1 sintético: hoje `submeter_instrumento` valida e transiciona o **contrato nuclear 2**. O contrato 3 precisa de comando e adaptação próprios, sem conversão automática entre os dois conteúdos.

## 2. Ativação controlada

A rota e a ação visível de submissão permanecerão indisponíveis enquanto o marco institucional estiver fechado. O mecanismo técnico poderá ser preparado atrás de uma liberação explícita e testável, cujo valor padrão seja bloqueado. A pré-validação continuará consultiva e não criará versão, protocolo, aprovação ou declaração de adequação à LGPD.

## 3. Dependências institucionais bloqueadoras

- fonte funcional autenticada para cargo/função (`0.2`) e e-mail institucional (`0.3`), ambos somente leitura;
- aprovação institucional da matriz de obrigatoriedade e do marco de liberação;
- decisões ainda registradas no contrato candidato e na matriz, sem inferência automática;
- definição de quem possui competência para receber, analisar, devolver e validar o FORM 1 integral; estar lotado na T.I. não concede essa competência automaticamente;
- validação humana das justificativas e dos instrumentos associados aos destinatários do item `10.2.1`, quando aplicável.

Sem essas decisões, o sistema pode calcular e exibir pendências, mas não deve concluir a submissão.

## 4. Verificação mínima do próximo incremento

Os testes deverão cobrir: sucesso com massa totalmente fictícia; matriz e condicionais; pendências sem mutação; ARP não autorizado; versão desatualizada; lacre inválido; repetição idempotente; reutilização indevida da chave; concorrência; rollback; snapshot imutável; preservação de rascunho e histórico; ausência da ação quando a liberação estiver fechada; e regressão integral do contrato nuclear 2.

Não se prevê migração no Incremento 8B. Antes de uma implementação futura, deverá ser decidido se a versão integral reutilizará, com discriminação explícita de contrato, as tabelas genéricas de Instrumento e Versão ou se exigirá projeção própria não destrutiva.

## 5. Infraestrutura preparada no Incremento 8C

O contrato candidato 3 passou a possuir uma projeção própria de versões técnicas, separada de `VersaoInstrumento`, porque esta última atende à submissão do FORM 1 sintético do contrato 2. O comando interno congela o envelope REV13, a origem do rascunho e o retrato histórico dos canais, registra autoria, texto canônico, lacre, evento e auditoria na mesma transação e impede dois snapshots da mesma versão do rascunho.

Essa preparação **não é submissão**: não possui rota ou botão, não altera estado do Registro ou do Instrumento, não cria versão nuclear e declara `submissao_habilitada: false`. A migração 17 cria somente a tabela separada e a proteção de imutabilidade; no ambiente de desenvolvimento ela possui reversão explícita. As dependências institucionais da seção 3 permanecem bloqueadoras da liberação.
