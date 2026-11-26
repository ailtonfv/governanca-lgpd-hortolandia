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
    return dict(iniciado=bool(salvos), primeiro=salvos[0] if salvos else None,
                ultimo=salvos[-1] if salvos else None,
                antes_atualizacao=bool(salvos and atualizacoes and
                    salvos[0].sequencia_cadeia < atualizacoes[-1].sequencia_cadeia))
