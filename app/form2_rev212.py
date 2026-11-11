"""Contrato do rascunho REV21.2. O catálogo integral fica na instalação privada."""
from hashlib import sha256
from pathlib import Path
import json

ARQUIVO = Path(__file__).with_name("catalogos") / "form2_rev21_2_privado.json"
LACRE = "f3c25cdb4531d66dc9785100034405bbae3096465dc1202fe7ab1ed93a227d52"
RASCUNHO = "rascunho_form2_rev21_2"
D11 = {"F2-9.7.2", "F2-14.1"}
CONSULTAS = {"F2-13.9", "F2-14.8.1", "F2-14.8.2"}


def catalogo():
    bruto = ARQUIVO.read_bytes()
    if sha256(bruto.replace(b"\r\n", b"\n")).hexdigest() != LACRE:
        raise ValueError("Catálogo REV21.2 divergente.")
    return json.loads(bruto)["itens"]


def por_conjunto(chave):
    raiz = chave.split(".")[0]
    return ((raiz == "F2-8" and chave != "F2-8.1")
            or (raiz == "F2-9" and chave != "F2-9.1")
            or chave in {"F2-14.2", "F2-14.3", "F2-14.3.1"})


def condicao(origem, *codigos):
    return [{"origem": origem, "operador": "IGUAL", "codigo_valor": c, "combinar": "OU"}
            for c in codigos]


def novos_controles():
    sim_nao = [("SIM", "Sim"), ("NAO", "Não"), ("A_CONFIRMAR", "A confirmar")]
    mecanismos = [("NAO_CARACTERIZADA", "Transferência não caracterizada"),
                  ("ADEQUACAO", "Decisão de adequação aplicável"), ("CLAUSULAS", "Cláusulas-padrão"),
                  ("NCG", "Normas corporativas globais"), ("OUTRA", "Outra hipótese do art. 33 (especificar)"),
                  ("JURIDICO", "Requer análise jurídica"), ("A_CONFIRMAR", "A confirmar")]
    return {
        "F2-9.6.1": ("Seleção única + texto", sim_nao, condicao("F2-9.1", "SIM")),
        "F2-9.6.2": ("Seleção única + texto", sim_nao, condicao("F2-9.1", "SIM")),
        "F2-9.7.2": ("Seleção única + texto", mecanismos, condicao("F2-9.7.1", "SIM", "ALT_03")),
        "F2-13.12": ("Seleção única", sim_nao, []),
        "F2-13.12.1": ("Texto curto", [], condicao("F2-13.12", "SIM")),
    }


def montar_bloco(base):
    antigos = {q["id"]: q for q in base["itens"]}
    novos = novos_controles()
    itens = []
    for chave, redacao in catalogo().items():
        if chave in antigos:
            q = antigos[chave]
        elif chave in novos and chave.startswith(f'F2-{base["numero"]}.'):
            tipo, opcoes, regras = novos[chave]
            q = {"id": chave, "controle": tipo, "edicao": "rascunho", "condicoes": regras,
                 "fontes_publicas": [], "alternativas": [
                     {"codigo": codigo, "rotulo": rotulo, "complemento": ""} for codigo, rotulo in opcoes]}
        else:
            continue
        q.update(redacao)
        q["repetivel"] = por_conjunto(chave)
        if chave in CONSULTAS:
            q.update(edicao="consulta", alternativas=[], controle="Consulta automática")
        if chave in D11:
            q["edicao"] = "bloqueada_d11"
        itens.append(q)
    return {**base, "itens": itens, "versao": "REV21.2"}


def ramos_origem(origem):
    respostas = origem.get("conteudo", {}).get("respostas", {})
    return {k.partition(".")[0] for k, v in respostas.items() if v and "." in k}


def indice_valores(conteudo):
    valores = {}
    for campos in conteudo.get(RASCUNHO, {}).values():
        valores.update(campos)
    for chave, valor in conteudo.get("respostas_etapa1", {}).items():
        valores["opcao:" + chave] = valor if isinstance(valor, list) else [valor]
    return valores


def aplicavel(q, conjunto, valores, ramos, regras):
    def avaliar(c):
        op, origem, codigo = c["operador"], c["origem"], c["codigo_valor"]
        if op == "SEMPRE":
            return True
        if op == "RAMO_PREENCHIDO":
            return codigo in ramos
        sufixo = conjunto if por_conjunto(origem) else ""
        if op == "POR_OCORRENCIA":
            return bool(valores.get("texto:" + origem + sufixo, "").strip())
        if op in ("CONTEM", "IGUAL"):
            return (codigo in valores.get("opcao:" + origem + sufixo, [])
                    and aplicavel(origem, sufixo, valores, ramos, regras))
        raise ValueError("Condição de exibição desconhecida.")
    condicoes = regras.get(q, [])
    return (any(map(avaliar, condicoes)) if any(c["combinar"] == "OU" for c in condicoes)
            else all(map(avaliar, condicoes)))


def mapa_regras(contrato):
    regras = {}
    for c in contrato["condicoes"]:
        regras.setdefault(c["alvo"], []).append(c)
    for k, (_, _, condicoes) in novos_controles().items():
        regras[k] = condicoes
    return regras


def conjunto_da_chave(campo):
    return "#" + campo.rsplit("#", 1)[1] if "#" in campo else ""
