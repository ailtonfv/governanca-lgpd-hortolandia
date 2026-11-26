"""Distingue trabalho do servidor de inicialização e atualização técnica."""
from sqlalchemy import select
from app.modelos import Evento


def e_salvamento(tipo):
    return tipo == 'salvar_bloco_rev22_form1' or (
        tipo.startswith(('salvar_', 'adicionar_', 'remover_', 'atualizar_'))
        and ('form1' in tipo or tipo in ('salvar_cabecalho_bloco_3', 'salvar_cabecalho_bloco_10'))
    )


def atividade_form1(sessao, registro_id):
    eventos = list(sessao.scalars(select(Evento).where(
        Evento.registro_id == registro_id, Evento.cadeia_tipo == 'registro'
    ).order_by(Evento.sequencia_cadeia)))
    salvos = [e for e in eventos if e_salvamento(e.tipo_evento)]
    atualizacoes = [e for e in eventos if e.tipo_evento == 'adotar_rev22_form1']
    return dict(iniciado=bool(salvos), salvamentos=len(salvos), primeiro=salvos[0] if salvos else None,
                ultimo=salvos[-1] if salvos else None,
                antes_atualizacao=bool(salvos and atualizacoes and
                    salvos[0].sequencia_cadeia < atualizacoes[-1].sequencia_cadeia))


def aviso_apresentacao(conteudo):
    from app.rev22_form1 import blocos_com_respostas
    from app.consultas_interface import _blocos_sem_respostas
    vazios = [n for n in range(1,15) if n not in blocos_com_respostas(conteudo)] if 'revisao_22' in conteudo else _blocos_sem_respostas(conteudo)
    numeros = [str(n if isinstance(n,int) else n.get('numero',n.get('bloco'))) for n in vazios]
    lista = ', '.join(numeros[:-1]) + ' e ' + numeros[-1] if len(numeros)>1 else ''.join(numeros)
    return (('O bloco '+lista+' está sem resposta. ' if len(numeros)==1 else 'Os blocos '+lista+' estão sem resposta. ')+ 'O APA verá isso na conferência. Apresentar mesmo assim?') if numeros else 'O APA receberá as respostas salvas para conferência. Apresentar?'
