"""Histórico técnico por acréscimo; não autoriza atos institucionais."""
from app.modelos import IdentidadeForms34 as Identidade
from app.comandos import fechar_comando
from app.eventos import verificar_cadeia
from app.infra_forms34 import _atomica, _abrir, _registro, _gravar, historico


@_atomica
def acrescentar_historico(sessao, *, comando_id, conta_id, identidade_id,
                         versao_esperada, tipo, nota, corrigir_evento_id=None):
    """Anotação/correção/retirada técnica, sem atos de decisão do FORM 4."""
    if tipo not in ('anotacao', 'correcao', 'retirada_tecnica'):
        raise ValueError("Este tipo de ato não está disponível na base técnica.")
    if not isinstance(nota, str) or not nota.strip() or len(nota) > 1000:
        raise ValueError("Informe uma anotação de até 1000 caracteres.")
    if type(versao_esperada) is not int or versao_esperada < 1:
        raise ValueError("Versão esperada inválida.")
    dados = dict(identidade_id=identidade_id, versao_esperada=versao_esperada,
                 tipo=tipo, nota=nota, corrigir_evento_id=corrigir_evento_id)
    comando, resposta = _abrir(sessao, comando_id, conta_id, 'base34_historico', dados)
    if resposta is not None:
        return resposta
    obj = sessao.get(Identidade, identidade_id)
    if not obj:
        raise ValueError("Identidade inexistente.")
    _registro(sessao, obj.registro_id)
    eventos = historico(sessao, obj.id)
    if not verificar_cadeia(sessao, obj.id)[0]:
        raise ValueError("Histórico divergente.")
    if eventos[-1].sequencia_cadeia != versao_esperada:
        raise ValueError("O histórico mudou; releia a versão antes de acrescentar.")
    if any(e.tipo_evento == 'base34_retirada_tecnica' for e in eventos):
        raise ValueError("Identidade retirada; o número permanece reservado.")
    alvo = next((e for e in eventos if e.id == corrigir_evento_id), None)
    if tipo == 'correcao':
        if not alvo or alvo.tipo_evento not in ('base34_anotacao', 'base34_correcao'):
            raise ValueError("A correção exige anotação anterior da mesma identidade.")
    elif corrigir_evento_id is not None:
        raise ValueError("Referência de correção fora do tipo de evento correspondente.")
    ev = _gravar(sessao, comando, 'forms34_objeto', obj.id, obj.registro_id,
                 'base34_' + tipo, dados)
    return fechar_comando(comando, {'permitido': True, 'identidade_id': obj.id,
                                  'evento_id': ev.id, 'versao': ev.sequencia_cadeia})
