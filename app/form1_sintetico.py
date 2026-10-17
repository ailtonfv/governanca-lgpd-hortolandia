"""Contrato fechado do FORM 1 sintético usado na PoC nuclear.

Os catálogos são deliberadamente pequenos e fictícios. A interface deve
apresentá-los como seleção; o servidor nunca digita categorias livremente.
"""

VERSAO_CONTRATO_FORM1 = 2

CATEGORIAS_TITULARES = {
    "TIT-CONTRIBUINTE": "Contribuinte",
    "TIT-CIDADAO-USUARIO": "Cidadão usuário de serviço público",
    "TIT-SERVIDOR": "Servidor público",
    "TIT-ESTUDANTE": "Estudante",
    "TIT-RESPONSAVEL-LEGAL": "Responsável legal",
    "TIT-REPRESENTANTE-FORNECEDOR": "Representante de fornecedor",
}

CATEGORIAS_DADOS = {
    "DAD-IDENTIFICACAO": "Dados de identificação",
    "DAD-CONTATO": "Dados de contato",
    "DAD-ENDERECO": "Dados de endereço",
    "DAD-FINANCEIRO": "Dados financeiros",
    "DAD-FUNCIONAL": "Dados funcionais",
    "DAD-ACADEMICO": "Dados acadêmicos",
    "DAD-SAUDE": "Dados de saúde",
}

DESTINATARIOS_COMPARTILHAMENTO = {
    "DST-ORGAO-MUNICIPAL": "Outro órgão ou unidade municipal",
    "DST-ORGAO-PUBLICO-EXTERNO": "Órgão público externo",
    "DST-OPERADOR-CONTRATADO": "Operador contratado",
}

CAMPOS_DE_CATALOGO = {
    "categorias_titulares": CATEGORIAS_TITULARES,
    "categorias_dados": CATEGORIAS_DADOS,
    "compartilhamentos": DESTINATARIOS_COMPARTILHAMENTO,
}

CAMPOS_FORM1 = {"finalidade", *CAMPOS_DE_CATALOGO}


def validar_conteudo(conteudo):
    """Retorna os problemas bloqueantes do contrato sintético vigente."""
    if not isinstance(conteudo, dict):
        return ["o conteúdo do FORM 1 deve ser um objeto JSON"]

    problemas = []
    desconhecidos = sorted((chave for chave in conteudo if chave not in CAMPOS_FORM1), key=str)
    if desconhecidos:
        problemas.append("campos não reconhecidos pelo contrato: " +
                          ", ".join(map(str, desconhecidos)))

    finalidade = conteudo.get("finalidade")
    if not isinstance(finalidade, str) or not finalidade.strip():
        problemas.append("finalidade deve ser um texto não vazio")
    elif len(finalidade.strip()) > 500:
        problemas.append("finalidade deve ter no máximo 500 caracteres")

    for campo, catalogo in CAMPOS_DE_CATALOGO.items():
        valor = conteudo.get(campo)
        if not isinstance(valor, list):
            problemas.append(f"{campo} deve ser uma lista de códigos do catálogo")
            continue
        if campo != "compartilhamentos" and not valor:
            problemas.append(f"{campo} deve conter ao menos um código")
        textos = [item for item in valor if isinstance(item, str)]
        if len(textos) != len(set(textos)):
            problemas.append(f"{campo} não deve repetir códigos")
        invalidos = sorted({str(item) for item in valor
                            if not isinstance(item, str) or item not in catalogo})
        if invalidos:
            problemas.append(f"{campo} contém código(s) desconhecido(s): " +
                              ", ".join(map(str, invalidos)))
    return problemas
