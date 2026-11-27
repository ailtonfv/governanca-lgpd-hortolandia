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


FORM2_BLOCOS = {
    1: ("CART-03",),
    2: ("CART-05",),
    3: ("CART-05", "CART-06", "CART-07", "CART-29", "CART-30"),
    4: ("CART-07",),
    5: ("CART-08", "CART-18", "CART-36"),
    6: ("CART-24",),
    7: ("CART-23", "CART-36"),
    8: ("CART-14",),
    9: ("CART-28", "CART-11", "CART-27", "CART-53"),
    10: ("CART-09", "CART-11"),
    11: ("CART-37", "CART-40"),
    12: ("CART-32", "CART-41"),
    13: ("CART-17",),
    14: ("CART-21",),
}
FORM2_PERGUNTAS = {
    "F2-5.8": ("CART-18",),
    "F2-10.1": ("CART-09", "CART-10"),
    "F2-10.5": ("CART-09",),
    "F2-11S.1": ("CART-25",),
    "F2-13.1": ("CART-35",),
}
FORM2_CLAUSULAS = ("CART-52",)

FORM3_BLOCOS = {
    1: ("CART-21",),
    2: ("CART-21",),
    3: ("CART-47", "CART-50"),
    4: ("CART-21",),
    5: ("CART-47",),
    6: ("CART-15", "CART-38"),
    7: ("CART-15", "CART-32"),
    8: ("CART-53", "CART-11"),
    9: ("CART-21",),
    10: ("CART-16",),
    11: ("CART-15",),
    12: ("CART-43",),
    13: ("CART-15",),
    14: ("CART-47", "CART-49"),
    15: ("CART-48", "CART-50"),
    16: ("CART-21",),
}
FORM3_PERGUNTAS = {
    "F3-3.10": ("CART-24", "CART-33"),
    "F3-3.15": ("CART-26",),
    "F3-3.30": ("CART-46",),
    "F3-3.35": ("CART-45",),
    "F3-3.36": ("CART-46",),
    "F3-3.37": ("CART-46",),
}
FORM3_LACUNAS = ("CART-54", "CART-52")

FORM4_BLOCOS = {bloco: ("CART-49",) for bloco in range(1, 10)}
FORM4_BLOCOS[3] += ("CART-42",)
FORM4_PERGUNTAS = {"F4-4.4": ("CART-28",)}
FORM4_CLAUSULAS = ("CART-52", "CART-54", "CART-11")

GRADE_CARTILHA = ("CART-21",)
CARTILHA_CENTRAL = ("CART-02", "CART-04", "CART-09", "CART-42")
CARTILHA_GLOSSARIO = ("CART-12",)
CARTILHA_CENTRAL_DASHBOARD = ("CART-51",)
CARTILHA_PAINEL = ("CART-02",)
CARTILHA_FILAS = ("CART-44",)
CARTILHA_ABERTURA = {"como-funciona": ("CART-01", "CART-22"), "fluxograma": GRADE_CARTILHA}
CARTILHA_DASHBOARD = {
    "abertura": ("CART-51", "CART-02"),
    "risco": ("CART-51", "CART-47", "CART-48"),
    "correcao": ("CART-51", "CART-49"),
    "operacao": ("CART-51",),
    "cobertura": ("CART-51",),
    "circulacao": ("CART-51", "CART-14"),
    "aprendizados": ("CART-51", "CART-49"),
}

TOPICOS_APOIO = {
    "central": frozenset(CARTILHA_CENTRAL + CARTILHA_GLOSSARIO + CARTILHA_PAINEL
                         + CARTILHA_FILAS + tuple(chave for chaves in CARTILHA_ABERTURA.values() for chave in chaves)),
    "dashboard": frozenset(chave for chaves in CARTILHA_DASHBOARD.values() for chave in chaves),
    "aprendizados": frozenset(CARTILHA_DASHBOARD["aprendizados"]),
}
