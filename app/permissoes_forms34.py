"""Escopo por pessoa e unidade; competências exclusivamente demonstrativas."""
from sqlalchemy import select
from app.fila_form2 import pessoa_ativa, unidades, autorizado
from app.modelos import ParticipacaoForm2, AtribuicaoForm1Integral, Registro

PAPEIS_DEMO = {'secretario': 'demo34_secretario', 'prefeito': 'demo34_prefeito',
               'verificador': 'demo34_verificador', 'relator': 'demo34_relator'}


def contexto(sessao, conta_id, referencia):
    pessoa = pessoa_ativa(sessao, conta_id)
    registro = sessao.get(Registro, referencia.registro_id)
    uid = registro.unidade_principal_atual_id
    papeis = set()
    if unidades(sessao, pessoa.id, 'governanca_protecao_dados'):
        papeis.add('dpo')
    principal = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.registro_id == registro.id, ParticipacaoForm2.tipo == 'principal',
        ParticipacaoForm2.responsavel_id == pessoa.id))
    if principal and autorizado(sessao, pessoa, principal):
        papeis.update(('aal', 'secretaria'))
    atribuicao = sessao.get(AtribuicaoForm1Integral, registro.id)
    if atribuicao and atribuicao.arp_atual_id == pessoa.id and uid in unidades(sessao, pessoa.id, 'preenchedor'):
        papeis.add('secretaria')
    for papel, codigo in PAPEIS_DEMO.items():
        lotacoes = unidades(sessao, pessoa.id, codigo)
        if ((papel == 'secretario' and uid in lotacoes) or
                (papel == 'prefeito' and lotacoes) or
                (papel in ('verificador', 'relator') and lotacoes - {uid})):
            papeis.add(papel)
    return pessoa, papeis, uid


def exigir(papeis, *permitidos):
    if not papeis.intersection(permitidos):
        raise PermissionError('Este ato não está autorizado para sua participação.')
