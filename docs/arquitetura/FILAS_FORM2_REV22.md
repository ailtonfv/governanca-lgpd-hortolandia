# Filas do FORM 2 na PoC demonstrativa REV22

## Escopo autorizado em 11 de novembro de 2026

O usuário autorizou a implementação das pendências da candidata v5. Este incremento
introduz fila institucional, assunção, consultas por unidade, manifestações,
complementação e preparação dos avisos do DPO na demonstração fictícia.
As decisões institucionais e a homologação jurídica D11 seguem pendentes.

## Percurso disponível

A confirmação interna do FORM 1 cria a participação principal e a ciência do DPO
na mesma transação, como ensaio do futuro ingresso institucional. As versões
confirmadas anteriores podem ser encaminhadas pelo APA na tela de filas.
O Identificador LGPD é preservado.

A Central oferece acesso a /form2/filas. Os papéis explícitos são aal_form2,
juridico_form2, gestor_fila e governanca_protecao_dados. A vigência, a pessoa
ativa e a unidade ativa são verificadas. A autoria da apresentação é segregada
da assunção da validação. A migração é aditiva.

O responsável principal acessa os 14 blocos com os contratos existentes.
Os controles sujeitos à D11 conservam seus bloqueios. Pode encaminhar questões
a unidades temáticas, Jurídico ou DPO. Cada destinatário assume, salva e conclui
a própria manifestação. O AAL principal consulta os resultados.

A resposta ativa em 1.3.1 cria complemento ligado a 14.2. APA ou ARP atual vincula
nova versão confirmada do FORM 1. O AAL confere e resolve a pendência.
As versões anteriores e os eventos ficam preservados.

## Instalação e teste local

Executar no ambiente habitual:

    python -m demonstracoes.instalar_filas_form2

O instalador cria os papéis exclusivamente para agentes com matrícula fictícia.
Beta assume AAL na unidade Norte, Alfa demonstra gestor da fila e Delta demonstra
Jurídico em Assuntos Jurídicos. O Encarregado fictício conserva a designação
governanca_protecao_dados na unidade de governança.

Reiniciar o servidor e abrir /form2/filas?conta_id=CONTA-B1 para o AAL,
ou /form2/filas?conta_id=CONTA-E1 para o DPO.

## Avisos

A caixa transacional distingue ciencia e manifestacao. A unicidade é garantida
por participação e tipo. A consulta do painel precede a assunção.

    python -m demonstracoes.avisos_dpo

Esse comando gera mensagens EML locais, sem marcar entrega. Para SMTP, configurar
LGPD_SMTP_HOST, LGPD_SMTP_PORTA, LGPD_SMTP_SEGURANCA (SSL ou STARTTLS),
LGPD_SMTP_REMETENTE, LGPD_BASE_URL e, quando necessário,
LGPD_SMTP_USUARIO e LGPD_SMTP_SENHA exclusivamente no ambiente local.
LGPD_EMAIL_DPO define a caixa institucional. LGPD_DPO_CIENCIA_INDIVIDUAL=0
suprime o envio individual de ciência e mantém o de manifestação.

    python -m demonstracoes.avisos_dpo --enviar
    python -m demonstracoes.avisos_dpo --resumo-inicio 2026-11-01

O resumo cobre quinze dias a partir da data informada. Adicionar --enviar para
entrega SMTP. O agendador institucional deve chamar o executor.
Uma falha SMTP de resultado incerto exige conferência antes de reenvio.
O Message-ID é estável. SMTP não garante entrega exatamente uma vez.

## Limites a resolver

- Configuração institucional de SMTP e agendamento ainda necessários.
- A demonstração usa identidade simulada por conta_id. O acesso autenticado de
  produção depende da integração institucional.
- Encerramento institucional do Bloco 14, perfis temáticos por bloco, classificação
  impeditiva e ações integradas dos FORMs 3 e 4 continuam pendentes. A conferência
  demonstrativa versionada está implementada conforme o contrato abaixo.
- Este incremento mantém as escolhas de controles da REV21.2, incluindo os
  bloqueios D11. Abrir todos os blocos não representa homologação jurídica.
- A Cartilha local recebe orientação de fluxo identificada como candidata REV22.
  O DOCX institucional e seus vínculos históricos seguem sujeitos à revisão editorial.

## Conferência da consolidação — 11/11/2026

O AAL responsável pela participação principal pode consultar o resumo pelo Bloco 14
ou pela página da participação. O resumo reúne respostas salvas, itens ativos com
A_CONFIRMAR, complementações 1.3.1/14.2, conjuntos declarados em 14.2 com área,
destinos e destino principal, manifestações concluídas e em aberto, e indicações
registradas para os FORMs 3 e 4. Não classifica automaticamente impedimentos.
Ausência de respostas é informação de preenchimento, não regra de obrigatoriedade.

Registrar conferência exige síntese, participação em atendimento, Registro em andamento,
versão atual e a mesma impressão digital das fontes apresentadas. A gravação bloqueia
as linhas da principal e das manifestações consultadas, usa comando idempotente e
transação única. Mantém o estado da participação em atendimento. Não envia e-mail,
não abre outros FORMs e não libera os controles D11.

Cada conferência preserva fontes, códigos e rótulos utilizados, síntese, autoria,
data, número e resumo no evento encadeado form2_consolidacao_registrada. O JSON da
participação mantém apenas a última conferência; as anteriores são consultadas pelo
livro de eventos, sem reescrita. Não exige alteração do esquema do banco.
A impressão digital exclui a própria conferência para não se invalidar ao registrar.
Inclui as respostas, manifestações, responsáveis, complementações, origem e regras.
Alterações posteriores exibem aviso de desatualização. Texto digitado é devolvido
na página de conflito para permitir cópia; navegação com síntese não salva pede confirmação.

Decisões ainda necessárias: matriz de obrigatoriedade para encerramento, autoridade
e classificação impeditiva, homologação D11 e integração aos FORMs 3 e 4.
O registro demonstrativo pode coexistir com lacunas: ele documenta a conferência,
não atesta que as lacunas foram resolvidas nem que a validação foi concluída.


## Reversão técnica de infraestrutura vazia — 11/11/2026

A migração `migracoes/fila_form2.py` oferece `reverter(sessao)`. A operação verifica as quatro tabelas da fila (participações, complementações, avisos e resumos), bloqueia inserções durante a verificação e recusa a reversão se qualquer delas contiver dados. Também recusa tabelas externas com chaves estrangeiras dependentes. Não utiliza CASCADE nem confirma a transação internamente.

A ordem de remoção, somente quando vazias, é complementações, avisos, resumos e participações. A reversão da origem `migracoes/versao_form1_integral.py` exige que suas dependências já tenham sido revertidas e que não existam snapshots. Isso inclui as dependências de preparação e conferência, além da fila do FORM 2; reverter apenas a fila não garante que a origem possa ser removida. Uma recusa mantém as tabelas; um rollback da transação restaura o DDL executado.

Esta é uma ferramenta de desenvolvimento, não uma função de apagar processos. Havendo dados, é necessária estratégia própria de preservação/restauração e decisão explícita; este incremento não converte nem elimina dados para permitir a reversão. Nenhuma reversão foi executada na base demonstrativa do usuário. Os testes nomeados estão em `testes/test_reversao_segura_form2.py`.
