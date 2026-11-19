"""Atores demonstrativos aprovados; nenhuma competência institucional real."""
from sqlalchemy import select
from app.modelos import Pessoa, Conta, Designacao
from migracoes.atos_forms34 import BANCO_8013

ATORES = (
    ('SECULT', 'Secretário(a) de Cultura (fictício)', 'SEC-CULT', 'demo34_secretario'),
    ('PREF', 'Prefeito (fictício)', 'SEC-GOV', 'demo34_prefeito'),
    ('VERIF', 'Membro do Comitê — Secretaria de Esportes (fictício)', 'SEC-ESP', 'demo34_verificador'),
    ('RELAT', 'Relator do Comitê (fictício)', 'SEC-ADM-GP', 'demo34_relator'),
    ('GAB', 'Gabinete do Prefeito (fictício)', 'SEC-GOV', 'demo34_gabinete'),
)


def semear(sessao, somente=None):
    banco = sessao.get_bind().url.database or ''
    if not banco.endswith('_teste') and banco != BANCO_8013:
        raise RuntimeError('Carga permitida apenas em teste ou na cópia nominal 8013.')
    for indice, (sufixo, nome, unidade, papel) in enumerate(ATORES, 201):
        if somente is not None and sufixo!=somente:continue
        pid, cid = 'PESSOA-DEMO34-' + sufixo, 'CONTA-DEMO34-' + sufixo
        if not sessao.get(Pessoa, pid):
            sessao.add(Pessoa(id=pid, matricula=f'MAT-FICT-{indice:04}', nome=nome))
            sessao.flush()
        if not sessao.get(Conta, cid):
            sessao.add(Conta(id=cid, pessoa_id=pid))
        if not sessao.scalar(select(Designacao).where(Designacao.pessoa_id == pid,
                Designacao.unidade_id == unidade, Designacao.papel == papel)):
            sessao.add(Designacao(pessoa_id=pid, unidade_id=unidade, papel=papel,
                fundamento_administrativo='Competência demonstrativa — proposta em deliberação (D11)'))
    sessao.flush()
