"""Mapa editorial versionado: ID REV13 → seção estável → edição local.

Somente orientações de leitura; não altera contratos nem obrigatoriedade.
O documento interno e sua representação HTML não são publicados no Git.
"""

VERSAO_CARTILHA_AJUDAS_FORM1 = "REV30.13"
ARQUIVO_CARTILHA = "CARTILHA_LGPD_HORTOLANDIA_REV30_13_MARCO_03-11-2026.docx"
SHA256_CARTILHA = "479599007a3cd9a7b79797bc0f2e948a40ec9ed2b916fa7687aa404694855848"

# Orientação funcional aprovada, sem atribuir seção ou vínculo editorial à Cartilha.
AJUDAS_ALTERNATIVAS_FORM1 = {
    "13.1": (
        ("Nenhuma das situações acima", "O fluxo foi examinado e nenhuma das situações de exposição apresentadas foi identificada."),
        ("Não se aplica", "As situações investigadas não são pertinentes às características do fluxo analisado."),
        ("A confirmar", "Ainda não existem informações suficientes para concluir se alguma das situações apresentadas ocorre."),
    ),
}

# Identidade de tópico independente de paginação; não reutilizar para outro tema.
SECOES_CARTILHA = {
    "fatos-analises-decisoes": "1.3 Fatos, análises e decisões",
    "competencia-finalidade": "2.1 Competência, finalidade e hipótese legal",
    "dados-sensiveis": "2.4 Hipóteses legais e dados sensíveis",
    "participantes": "3.3 Operador, terceiros, OSCs e entidades parceiras",
    "conceitos": "4.1 Conceitos centrais da LGPD",
    "levantamento": "5.1 Levantamento da realidade",
    "canais-ambientes": "5.2 Operações, canais e ambientes",
    "imagem-voz": "6.1 Fotografias, vídeos, voz e comunicação institucional",
    "whatsapp": "6.10 WhatsApp e dispositivos pessoais",
    "ciencia-consentimento": "7.2 Transparência, ciência, consentimento e publicidade",
    "acesso-minimo": "8.1 Necessidade de conhecer e acesso mínimo",
    "retencao": "9.1 Retenção e temporalidade documental",
}

LIMITE_GERAL_FORM1 = (
    "O FORM 1 registra a realidade do fluxo; análises de legitimidade ou decisões "
    "corretivas pertencem aos FORMs posteriores."
)

LIMITE_FATO_FORM2 = (
    "O FORM 1 registra o fato observado; o FORM 2 valida competência, papel "
    "jurídico, finalidade e hipótese legal."
)

AJUDAS_CARTILHA_FORM1 = {
    "2.1": {
        "texto": (
            "Consulte os canais habituais confirmados pelo APA para este Registro. "
            "A confirmação pode indicar vários canais ou ausência de canais. Em "
            "Registros antigos sem confirmação histórica, preserve a informação "
            "existente; essa ausência não significa que nenhum canal se aplica. "
            "O ARP não altera aqui a confirmação do APA. WhatsApp é canal "
            "de entrada, não repositório oficial."
        ),
        "secao": "5.2 Operações, canais e ambientes",
        "limite": LIMITE_GERAL_FORM1,
    },
    "2.11": {
        "texto": (
            "Descreva para que os dados são usados na rotina. Registre a finalidade "
            "operacional no FORM 1; a validação da hipótese legal pertence ao FORM 2."
        ),
        "secao": "2.1 Competência, finalidade e hipótese legal",
        "limite": LIMITE_FATO_FORM2,
    },
    "2.12": {
        "texto": (
            "Informe se existe norma, ato, programa, processo ou documento que "
            "sustente ou evidencie o fluxo. Não conclua aqui que ele define a base legal."
        ),
        "secao": "1.3 Fatos, análises e decisões",
        "limite": LIMITE_FATO_FORM2,
    },
    "4.1": {
        "texto": (
            "Marque os grupos de pessoas a quem os dados se referem. Crianças, "
            "pacientes e pessoas vulneráveis podem exigir cautelas reforçadas."
        ),
        "secao": "4.1 Conceitos centrais da LGPD",
        "limite": LIMITE_GERAL_FORM1,
    },
    "5.1": {
        "texto": (
            "Marque as categorias realmente usadas no fluxo. Dados de saúde, "
            "biometria, religião e outras categorias do art. 5º, II, são sensíveis."
        ),
        "secao": "2.4 Hipóteses legais e dados sensíveis",
        "limite": LIMITE_GERAL_FORM1,
    },
    "6.1": {
        "texto": (
            "Registre de onde os dados chegam de fato, distinguindo titular, unidade, "
            "sistema, órgão e terceiro."
        ),
        "secao": "5.1 Levantamento da realidade",
        "limite": LIMITE_GERAL_FORM1,
    },
    "7.1": {
        "texto": (
            "Marque as operações realizadas, como coletar, consultar, alterar, "
            "compartilhar, guardar ou eliminar. O FORM 1 registra o fato; a "
            "legitimidade será avaliada no FORM 2."
        ),
        "secao": "4.1 Conceitos centrais da LGPD",
        "limite": LIMITE_FATO_FORM2,
    },
    "9.1": {
        "texto": (
            "Marque as funções e entidades que realmente acessam os dados. Acesso "
            "técnico não equivale a necessidade de conhecer."
        ),
        "secao": "8.1 Necessidade de conhecer e acesso mínimo",
        "limite": LIMITE_GERAL_FORM1,
    },
}


def _ajuda(texto, topico, limite=LIMITE_GERAL_FORM1):
    return {"texto": texto, "secao": SECOES_CARTILHA[topico], "limite": limite}


AJUDAS_CARTILHA_FORM1.update({
    "2.13": _ajuda(
        "Informe o que é solicitado na prática. Consentimento, ciência, aceite e "
        "autorização não são sinônimos; o nome ou a assinatura do documento não "
        "determina por si só a hipótese legal.", "ciencia-consentimento", LIMITE_FATO_FORM2),
    "2.13.1": _ajuda(
        "Descreva como essa manifestação é obtida e registrada, sem inserir dados "
        "de pessoas atendidas. Relatar o procedimento não significa validar "
        "juridicamente o consentimento.", "ciencia-consentimento", LIMITE_FATO_FORM2),
    "8.7": _ajuda(
        "Identifique o uso efetivo de WhatsApp institucional, pessoal ou ambos. "
        "Diferencie o canal utilizado, o dispositivo e o ambiente em que a "
        "informação administrativa é guardada.", "whatsapp"),
    "8.8": _ajuda(
        "Informe se a informação relevante recebida pelo aplicativo é registrada "
        "no ambiente institucional apropriado. A conversa no aplicativo não "
        "substitui o repositório oficial.", "whatsapp"),
    "8.8.1": _ajuda(
        "Identifique onde a informação é registrada institucionalmente. Descreva "
        "o ambiente, sem copiar mensagens, arquivos ou dados de cidadãos.", "whatsapp"),
    "8.9": _ajuda(
        "Informe se documentos ou cópias permanecem no aplicativo ou em backups "
        "fora do ambiente institucional, mesmo após o registro oficial.", "whatsapp"),
    "10.8": _ajuda(
        "Informe a divulgação pública que ocorre de fato. Captar, registrar e "
        "publicar imagem, voz ou outros dados são operações diferentes; relatar "
        "a publicação não significa aprovar sua legitimidade.", "imagem-voz", LIMITE_FATO_FORM2),
    "10.8.1": _ajuda(
        "Identifique onde ocorre a divulgação, distinguindo canais institucionais "
        "e pessoais. Transparência não significa exposição irrestrita nem "
        "autorização automática para reutilização.", "ciencia-consentimento", LIMITE_FATO_FORM2),
    "12.1": _ajuda(
        "Informe se existe prazo de guarda definido. Não invente prazos: consulte "
        "os instrumentos de temporalidade aplicáveis. Retenção de dados e "
        "temporalidade documental são relacionadas, mas distintas.", "retencao"),
    "3.2": _ajuda(
        "Identifique os tipos de participantes do fluxo. A participação de uma "
        "empresa, OSC ou entidade parceira não a torna automaticamente Operadora.", "participantes", LIMITE_FATO_FORM2),
    "3.3": _ajuda(
        "Identifique a unidade, órgão ou entidade participante, sem cadastrar "
        "cidadãos. Diferencie sua identidade institucional do papel jurídico "
        "que será analisado posteriormente.", "participantes", LIMITE_FATO_FORM2),
    "3.4": _ajuda(
        "Marque o que este participante realmente faz com os dados. As funções "
        "operacionais descritas não determinam automaticamente seu papel "
        "jurídico de Controlador ou Operador.", "participantes", LIMITE_FATO_FORM2),
    "3.4.1": _ajuda(
        "Descreva o acesso ou a retenção dos dados pelo participante conforme a "
        "realidade. Participar do fluxo não implica acesso irrestrito.", "acesso-minimo"),
    "3.5": _ajuda(
        "Informe se existe instrumento formal relacionado à participação. "
        "Contrato, convênio ou parceria não define sozinho o papel de Operador.", "participantes", LIMITE_FATO_FORM2),
})

# Mesmo mapa usado pelo componente e pela rota; nenhuma URL externa ou página presumida.
for _item in AJUDAS_CARTILHA_FORM1.values():
    _item["secao_id"] = next(
        chave for chave, titulo in SECOES_CARTILHA.items() if titulo == _item["secao"]
    )
