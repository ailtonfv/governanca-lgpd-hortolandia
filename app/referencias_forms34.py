"""Referências imutáveis; não executa ingresso ou decisão institucional."""
import json
from sqlalchemy import select
from app.modelos import (ReferenciaParticipacaoForms34 as Referencia,
    IdentidadeForms34 as Identidade, VersaoForm1Integral, ParticipacaoForm2, Evento)
from app.comandos import fechar_comando
from app.eventos import (agora_utc, lacre, texto_canonico,
    CAMPOS_LACRADOS_DOMINIO, verificar_cadeia)
from app.infra_forms34 import _atomica, _uuid, _abrir, _registro, _gravar


def _snapshot(sessao, snapshot_id, registro_id):
    s = sessao.get(VersaoForm1Integral, snapshot_id)
    if not s or s.registro_id != registro_id:
        raise ValueError("Versão do FORM 1 incompatível com o Registro.")
    if lacre(s.conteudo_canonico) != s.lacre or json.loads(s.conteudo_canonico) != s.conteudo:
        raise ValueError("Integridade da versão do FORM 1 divergente.")
    return s


def _evento_fonte(sessao, fonte_id, registro_id):
    if not str(fonte_id).isdigit():
        raise ValueError("Referência de evento inválida.")
    ev = sessao.get(Evento, int(fonte_id))
    if not ev or ev.registro_id != registro_id:
        raise ValueError("Evento de origem incompatível com o Registro.")
    if (texto_canonico(ev, CAMPOS_LACRADOS_DOMINIO) != ev.payload_canonico
            or lacre(ev.payload_canonico) != ev.hash):
        raise ValueError("Integridade da origem divergente.")
    ok, _ = verificar_cadeia(sessao, ev.cadeia_id)
    if not ok:
        raise ValueError("Cadeia de origem divergente.")
    return ev


def _fonte(sessao, registro_id, form, fonte_form, fonte_id):
    if type(form) is not int or type(fonte_form) is not int or (
            form, fonte_form) not in {(3, 1), (3, 2), (4, 2), (4, 3)}:
        raise ValueError("Combinação de instrumentos não suportada.")
    if fonte_form == 1:
        s = _snapshot(sessao, fonte_id, registro_id)
        return dict(fonte_versao=s.numero, fonte_lacre=s.lacre,
                    fonte_canonica=s.conteudo_canonico, fonte_participacao_id=None,
                    snapshot_form1_id=s.id)
    ev = _evento_fonte(sessao, fonte_id, registro_id)
    if fonte_form == 2:
        p = sessao.get(ParticipacaoForm2, ev.cadeia_id)
        if ev.cadeia_tipo != 'participacao_form2' or not p or p.registro_id != registro_id:
            raise ValueError("Evento não pertence a uma participação do FORM 2.")
        numero = ev.conteudo.get('versao')
        if type(numero) is not int or numero < 1:
            raise ValueError("Evento não identifica a versão do FORM 2.")
        s = _snapshot(sessao, ev.conteudo.get('snapshot_id'), registro_id)
        participacao_id = p.id
    else:
        if ev.cadeia_tipo == 'forms34_objeto':
            obj = sessao.get(Identidade, ev.cadeia_id)
            ref = sessao.get(Referencia, obj.participacao_id) if obj else None
        elif ev.cadeia_tipo == 'forms34_contexto':
            ref = sessao.get(Referencia, ev.cadeia_id)
        else:
            ref = None
        if not ref or ref.form != 3 or ref.registro_id != registro_id:
            raise ValueError("Evento não pertence à base do FORM 3.")
        s = _snapshot(sessao, ref.snapshot_form1_id, registro_id)
        numero = ev.sequencia_cadeia
        participacao_id = ref.id
    return dict(fonte_versao=numero, fonte_lacre=ev.hash,
                fonte_canonica=ev.payload_canonico, fonte_participacao_id=participacao_id,
                snapshot_form1_id=s.id)


@_atomica
def fixar_referencia(sessao, *, comando_id, conta_id, participacao_id,
                     registro_id, form, fonte_form, fonte_id):
    """Persiste contexto técnico imutável, sem efetuar ingresso institucional.

    Não cria fila, unidade, responsável, aviso ou autorização. A futura função
    de ingresso deverá usar esta estrutura após sua própria autorização.
    """
    _uuid(participacao_id)
    fonte_id = str(fonte_id)
    dados = dict(participacao_id=participacao_id, registro_id=registro_id,
                 form=form, fonte_form=fonte_form, fonte_id=fonte_id)
    comando, resposta = _abrir(sessao, comando_id, conta_id, 'base34_fixar_referencia', dados)
    if resposta is not None:
        return resposta
    _registro(sessao, registro_id)
    fonte = _fonte(sessao, registro_id, form, fonte_form, fonte_id)
    ref = sessao.get(Referencia, participacao_id)
    if ref:
        esperado = dict(dados, **fonte)
        for campo, valor in esperado.items():
            if campo != 'participacao_id' and getattr(ref, campo) != valor:
                raise ValueError("A referência examinada está congelada; não pode ser substituída.")
        return fechar_comando(comando, {'permitido': True, 'participacao_id': ref.id,
                                      'referencia_existente': True})
    if sessao.scalar(select(Evento.id).where(Evento.cadeia_id == participacao_id).limit(1)):
        raise ValueError("Identificador já vinculado a outra cadeia de histórico.")
    ref = Referencia(id=participacao_id, criado_em=agora_utc(),
                     **{k: v for k, v in dados.items() if k != 'participacao_id'}, **fonte)
    sessao.add(ref)
    sessao.flush()
    ev = _gravar(sessao, comando, 'forms34_contexto', ref.id, registro_id,
                 'base34_referencia_fixada', dict(dados, fonte_lacre=ref.fonte_lacre))
    return fechar_comando(comando, {'permitido': True, 'participacao_id': ref.id,
                                  'evento_id': ev.id, 'referencia_existente': False})


