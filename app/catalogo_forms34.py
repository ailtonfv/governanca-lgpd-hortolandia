"""Contratos estruturais; conteúdo editorial somente no pacote privado local.

Condições são metadados candidatos. Este módulo não avalia respostas, escalas,
competências ou ingresso. Não fornece fallback editorial quando o pacote falta.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path


def _hash(dados):
    return sha256(json.dumps(dados, sort_keys=True, ensure_ascii=False,
                             separators=(",", ":")).encode("utf8")).hexdigest()


def estrutura(form):
    if type(form) is not int or form not in (3, 4):
        raise ValueError("Instrumento não suportado nesta base.")
    caminho = Path(__file__).parent / 'catalogos' / f'form{form}_estrutura_base_v1.json'
    return json.loads(caminho.read_text(encoding='utf8'))


def carregar_catalogo(form, caminho=None):
    """Valida edição privada contra a estrutura e o lacre conferidos."""
    contrato = estrutura(form)
    local = caminho or os.getenv(f'LGPD_CATALOGO_FORM{form}')
    if not local or not Path(local).is_file():
        raise FileNotFoundError(f"Catálogo privado do FORM {form} indisponível.")
    dados = json.loads(Path(local).read_text(encoding='utf8'))
    if _hash(dados) != contrato['sha256_privado']:
        raise ValueError("Catálogo privado divergente da edição conferida.")
    if dados['versao'] != contrato['versao']:
        raise ValueError("Versão do catálogo divergente.")
    itens = [i for b in dados['editorial']['blocos'] for i in b['itens']]
    ids = [i['id'] for i in itens]
    esperados = [i['id'] for i in contrato['itens']]
    if ids != esperados or len(set(ids)) != len(ids):
        raise ValueError("Identificadores ausentes, repetidos ou fora de ordem.")
    if [i['id'] for i in dados['controles']['itens']] != esperados:
        raise ValueError("Controles não correspondem ao catálogo.")
    return deepcopy(dados)
