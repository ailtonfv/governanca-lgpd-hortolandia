"""Associação editorial entre as telas e as chaves do catálogo local."""

FORM1_BLOCOS = {
    1: ("CART-19", "CART-03"),
    2: ("CART-05",),
    3: ("CART-11", "CART-53"),
    4: ("CART-26",),
    5: ("CART-07",),
    6: ("CART-13", "CART-31", "CART-34"),
    7: ("CART-13", "CART-20"),
    8: ("CART-20", "CART-13", "CART-39", "CART-32"),
    9: ("CART-14", "CART-38"),
    10: ("CART-14",),
    11: ("CART-16",),
    12: ("CART-16",),
    13: ("CART-41",),
    14: ("CART-19",),
}

FORM1_TOPICOS_ANTERIORES = {
    "fatos-analises-decisoes": "CART-03",
    "competencia-finalidade": "CART-05",
    "dados-sensiveis": "CART-07",
    "participantes": "CART-11",
    "conceitos": "CART-12",
    "levantamento": "CART-19",
    "canais-ambientes": "CART-20",
    "imagem-voz": "CART-23",
    "whatsapp": "CART-32",
    "ciencia-consentimento": "CART-36",
    "acesso-minimo": "CART-38",
    "retencao": "CART-45",
}

FORM1_PERGUNTAS = {
    "2.12": ("CART-05",),
    "2.13": ("CART-08",),
    "4.1.1": ("CART-24",),
    "5.1": ("CART-27",),
    "8.6": ("CART-41",),
    "12.3": ("CART-46",),
    "12.4": ("CART-46",),
}


def topicos_pergunta_form1(campo, secao_anterior=None):
    chaves = ("CART-37",) if campo.startswith(("OUV.", "ESIC.")) else FORM1_PERGUNTAS.get(campo, ())
    if secao_anterior:
        chaves += (FORM1_TOPICOS_ANTERIORES[secao_anterior],)
    return chaves
