"""Catálogos sintéticos: leitura usa a edição lacrada, nunca a atual."""
import json
from hashlib import sha256
import pytest
from app import rev22_form1 as rev
from app.extensao_medidas_form1 import catalogo_efetivo


def test_catalogo_historico_preserva_edicao_e_recusa_adulteracao(tmp_path, monkeypatch):
    item = dict(id='1.3', block=1, title='Fictício', question='Campo fictício antigo', kind='text', options=[], help='')
    raw = json.dumps({'items':[item]}).encode()
    digest = sha256(raw).hexdigest()
    monkeypatch.setattr(rev, 'PASTA_CATALOGOS', tmp_path)
    monkeypatch.setattr(rev, 'LACRES_HISTORICOS', frozenset([digest]))
    arquivo = tmp_path/f'form1_rev22_{digest}_privado.json'
    arquivo.write_bytes(raw)
    origem = {'revisao_22':{'versao':rev.VERSAO, 'catalogo_sha256':digest}}
    assert catalogo_efetivo(origem)['1.3'].pergunta == 'Campo fictício antigo'
    assert '8.10' not in catalogo_efetivo(origem)
    arquivo.write_bytes(raw+b' ')
    with pytest.raises(ValueError, match='divergente'):
        catalogo_efetivo(origem)
    with pytest.raises(ValueError, match='divergente'):
        rev.definicoes('desconhecido')
