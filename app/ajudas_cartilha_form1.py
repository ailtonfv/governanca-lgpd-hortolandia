"""Ajudas contextuais do piloto Cartilha REV30.11 × FORM 1 REV13.

O conteúdo reproduz a seleção de oito campos da matriz de correspondência do
Incremento 8W. A Cartilha é documento interno e, enquanto não houver um meio
institucional de consulta autenticada, a interface informa a seção correta sem
publicar ou simular um link para o arquivo.
"""

VERSAO_CARTILHA_AJUDAS_FORM1 = "REV30.11"

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
            "Marque o primeiro canal pelo qual a demanda chega. WhatsApp é canal "
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
