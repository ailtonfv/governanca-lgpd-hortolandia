"""Referência jurídica por necessidade e participação; nunca em projeção geral."""
from uuid import uuid4
from sqlalchemy import select, func
from app.modelos import ReferenciaRestritaForms34 as Restrita, IdentidadeForms34, ReferenciaParticipacaoForms34
from app.permissoes_forms34 import contexto
from app.fila_form2 import pessoa_ativa, unidades
from app.eventos import registrar_auditoria, agora_utc


def pode_ler(sessao, conta_id, identidade_id, estado):
    pessoa = pessoa_ativa(sessao, conta_id)
    obj = sessao.get(IdentidadeForms34, identidade_id)
    if not obj:
        return False
    ref = sessao.get(ReferenciaParticipacaoForms34, obj.participacao_id)
    _, papeis, uid = contexto(sessao, conta_id, ref)
    if 'dpo' in papeis:
        return True
    escopos = estado.get('escopos_restritos', [])
    return pessoa.id in escopos and (bool(papeis.intersection(('aal','secretario','gabinete')))
        or bool(unidades(sessao, pessoa.id, 'juridico_form2')))


def ler(sessao, conta_id, identidade_id):
    from app.fluxo_forms34 import estado
    pessoa = pessoa_ativa(sessao, conta_id)
    permitido = pode_ler(sessao, conta_id, identidade_id, estado(sessao, identidade_id))
    registrar_auditoria(sessao, 'referencia34_consulta' if permitido else 'referencia34_negada',
        'pessoa', pessoa.id, {'identidade_id': identidade_id})
    if not permitido:
        raise PermissionError('Referência restrita: participação e necessidade não autorizadas.')
    return sessao.scalar(select(Restrita).where(Restrita.identidade_id == identidade_id)
        .order_by(Restrita.versao.desc()))


def acrescentar(sessao, identidade_id, pessoa_id, dados):
    campos = ('referencia', 'questao', 'conclusao', 'localizacao')
    if set(dados) - set(campos) or any(not isinstance(v,str) or len(v)>1000 for v in dados.values()):
        raise ValueError('Referência restrita inválida; não inclua anexos ou dados pessoais.')
    if not dados.get('referencia', '').strip():
        raise ValueError('Informe a referência institucional.')
    numero = (sessao.scalar(select(func.max(Restrita.versao)).where(Restrita.identidade_id == identidade_id)) or 0) + 1
    item = Restrita(id=str(uuid4()), identidade_id=identidade_id, versao=numero,
                   conteudo=dict(dados), autor_id=pessoa_id, criado_em=agora_utc())
    sessao.add(item)
    sessao.flush()
    return item.id
