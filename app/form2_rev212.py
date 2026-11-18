"""Contrato do rascunho REV21.2. O catálogo integral fica na instalação privada."""
from hashlib import sha256
from pathlib import Path
import json
import re


def orientacoes_ao_usuario(instrucao):
    """Extrai frases de orientação; controles, opções e condições seguem estruturados."""
    frases = re.split(r'(?<=\.)\s+(?=[A-ZÁÉÍÓÚ])', instrucao or '')
    prefixos = ('Se Sim,', 'Indique ', 'Informe ', 'Referência institucional (',
                'Sem dados pessoais.', 'Unidade, cargo ou função (')
    return [frase.strip() for frase in frases if frase.startswith(prefixos)]

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


def condicoes_d7():
    """DPO, 17/11/2026: divergência aprovada; incorporar na próxima revisão do Mestre."""
    return {**{q: condicao('F2-10.2', 'SIM') for q in ('F2-10.3', 'F2-10.4')},
            **{f'F2-10.9.{n}': condicao('F2-10.9.6', 'SIM') for n in range(7, 11)}}


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
        q['ajudas_usuario'] = orientacoes_ao_usuario(q.get('instrucao', ''))
        if chave == 'F2-7.10.1':
            rotulos = {'SIM':'Exclusivamente institucional', 'NAO':'Pode ter uso diverso', 'A_CONFIRMAR':'A confirmar'}
            for alternativa in q['alternativas']:
                alternativa['rotulo'] = rotulos[alternativa['codigo']]
        if chave == 'F2-7.1.1':
            q['ajudas_usuario'].append('Há dúvida = a situação existe e a análise é incerta; A confirmar = falta informação.')
        if chave in condicoes_d7():
            q['condicoes'] = condicoes_d7()[chave]
        q["repetivel"] = por_conjunto(chave)
        if chave in CONSULTAS:
            q.update(edicao="consulta", alternativas=[], controle="Consulta automática")
        if chave in D11:
            q["edicao"] = "bloqueada_d11"
        from app.complementos_form2 import codigos_com_complemento
        q["complementos_necessarios"] = codigos_com_complemento(q)
        from app.classificacao_analise_form2 import classificar
        classificar(q)
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


def condicoes_de_tela(itens, regras, valores, ramos):
    """Expõe os gatilhos locais e resolve na origem as condições externas ao bloco."""
    from app.contrato_form2_respostas import carregar_contrato
    rotulos = {(a['id'], a['codigo']): a['rotulo'] for a in carregar_contrato()['alternativas']}
    for chave, (_, alternativas, _) in novos_controles().items():
        rotulos.update({(chave, codigo): rotulo for codigo, rotulo in alternativas})
    locais = {q["id"]: q for q in itens}
    for q in itens:
        condicoes = []
        for regra in regras.get(q["id"], []):
            op, origem, codigo = (regra[k] for k in ("operador", "origem", "codigo_valor"))
            if op == "SEMPRE":
                continue
            c = {"operador": op, "origem": origem, "codigo": codigo}
            if origem in locais and op != "RAMO_PREENCHIDO":
                c["local"] = True
                c["repetivel"] = por_conjunto(origem)
            else:
                isoladas = {**regras, q["id"]: [regra]}
                c["fixa"] = aplicavel(q["id"], "", valores, ramos, isoladas)
            alternativas = locais.get(origem, {}).get("alternativas", [])
            rotulo = next((a["rotulo"] for a in alternativas if a["codigo"] == codigo),
                          rotulos.get((origem, codigo), "a opção indicada na pergunta de origem"))
            c["rotulo"] = rotulo
            if op == "RAMO_PREENCHIDO":
                c["descricao"] = "o FORM 1 indicar fluxo de " + {"OUV": "Ouvidoria", "ESIC": "e-SIC"}.get(codigo, "atendimento correspondente")
            elif op == "POR_OCORRENCIA":
                c["descricao"] = f"{origem} estiver preenchida neste conjunto"
            else:
                c["descricao"] = f"{origem} estiver respondida com “{rotulo}”"
            condicoes.append(c)
        conector = " ou " if any(r["combinar"] == "OU" for r in regras.get(q["id"], [])) else " e "
        frases = []
        grupos = {}
        for c in condicoes:
            if c["operador"] in ("IGUAL", "CONTEM"):
                grupos.setdefault(c["origem"], []).append(c["rotulo"])
            else:
                frases.append(c["descricao"])
        for origem, opcoes in grupos.items():
            valores_rotulados = conector.join(f"“{opcao}”" for opcao in opcoes)
            inclusao = any(c['origem'] == origem and c['operador'] == 'CONTEM' for c in condicoes)
            frases.append(f"a {origem} incluir {valores_rotulados}" if inclusao
                          else f"a resposta a {origem} for {valores_rotulados}")
        q["ajuda_condicao"] = conector.join(frases)
        q["gatilhos"] = condicoes
        q["qualquer"] = any(r["combinar"] == "OU" for r in regras.get(q["id"], []))


def mapa_regras(contrato):
    regras = {}
    for c in contrato["condicoes"]:
        regras.setdefault(c["alvo"], []).append(c)
    for k, (_, _, condicoes) in novos_controles().items():
        regras[k] = condicoes
    regras.update(condicoes_d7())
    return regras


def conjunto_da_chave(campo):
    return "#" + campo.rsplit("#", 1)[1] if "#" in campo else ""
