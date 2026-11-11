from copy import deepcopy
from hashlib import sha256
import re

import pytest

from app.respostas_form2 import aplicar_revisao, definicao_revisao
from app.form2_rev212 import RASCUNHO, ramos_origem


def salvar(conteudo, bloco, **campos):
    return aplicar_revisao(conteudo, bloco, campos)[0]


def test_catalogo_e_controles():
    itens = [q for b in range(1, 15) for q in definicao_revisao(b)["itens"]]
    assert len(itens) == len({q["id"] for q in itens}) == 255
    por_id = {q["id"]: q for q in itens}
    assert sha256(por_id["F2-1.2"]["enunciado"].encode("utf-8")).hexdigest() == "9811f0889b165a54c5c69642ca0fd02fc7f0c87c109421514e49c0575be1b522"
    assert por_id["F2-14.1"]["edicao"] == "bloqueada_d11"
    assert por_id["F2-9.7.2"]["edicao"] == "bloqueada_d11"


def test_transparencia_e_historico():
    antigo = {"revisao_blocos_rev20": {"13": {"texto:F2-13.12": "Local anterior"}}}
    copia = deepcopy(antigo)
    with pytest.raises(ValueError):
        salvar(antigo, 13, **{"texto:F2-13.12.1": ["inativo"]})
    novo = salvar(antigo, 13, **{"opcao:F2-13.12": ["SIM"], "texto:F2-13.12.1": ["Portal fictício"]})
    fechado = salvar(novo, 13, **{"opcao:F2-13.12": ["NAO"]})
    assert "texto:F2-13.12.1" not in fechado[RASCUNHO]["13"]
    assert fechado["respostas_inativas_rev212"]["13"]["texto:F2-13.12.1"] == "Portal fictício"
    assert antigo == copia and fechado["revisao_blocos_rev20"] == copia["revisao_blocos_rev20"]


@pytest.mark.parametrize("bloco,item", [(3, "3.1"), (4, "4.1"), (5, "5.1"), (10, "10.1"),
                                         (9, "9.7.2#1"), (14, "14.1"), (13, "13.9"), (14, "14.8.1")])
def test_bloqueios(bloco, item):
    with pytest.raises(ValueError):
        salvar({}, bloco, **{"opcao:F2-" + item: ["SIM"]})


def test_instrumentos_distintos_e_pendencias():
    dados = salvar({}, 9, **{"opcao:F2-9.1": ["SIM"],
                             "opcao:F2-9.6.1#1": ["SIM"], "texto:F2-9.6.1#1": ["Cláusula A"],
                             "opcao:F2-9.6.2#2": ["NAO"]})
    assert dados[RASCUNHO]["9"]["texto:F2-9.6.1#1"] == "Cláusula A"
    with pytest.raises(ValueError):
        salvar(dados, 9, **{"opcao:F2-9.6.2": ["NAO"]})
    with pytest.raises(ValueError):
        salvar({}, 14, **{"texto:F2-14.3#2": ["Unidade fictícia"]})
    dados = salvar({}, 14, **{"texto:F2-14.2#2": ["Conferir"], "texto:F2-14.3#2": ["Unidade fictícia"]})
    assert dados[RASCUNHO]["14"]["texto:F2-14.3#2"] == "Unidade fictícia"


def test_ramo_da_origem():
    ramo = ramos_origem({"conteudo": {"respostas": {"OUV.1": ["Solicitação"], "ESIC.1": ""}}})
    assert ramo == {"OUV"}
    with pytest.raises(ValueError):
        aplicar_revisao({}, 11, {"opcao:F2-11.7": ["SIM"]}, ())
    assert aplicar_revisao({}, 11, {"opcao:F2-11.7": ["SIM"]}, ramo)[0][RASCUNHO]
