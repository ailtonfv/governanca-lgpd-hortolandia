"""A1: decisão posterior à verificação; não reinterpreta atos antigos."""


def nota_confirmada(e):
    return (e.get('residual_acao') if set(e.get('residual_acao_confirmacoes', {})) == {'secretaria', 'dpo'} else None)


def reducao_total(e):
    return e.get('verificacao', {}).get('respostas', e.get('respostas', {})).get('F4-4.22') == 'Sim'


def pode_encerrar(e):
    if not e.get('verificada') or e.get('cancelada') or e.get('decisoes_pendentes'):
        return False
    tipos=e.get('respostas',{}).get('F4-4.4',[])
    if 'Elaborar/revisar RIPD' in tipos and not e.get('ripd_confirmado'):return False
    if reducao_total(e):
        return True
    nota = nota_confirmada(e)
    if not nota or not e.get('decisao_residual_acao'):
        return False
    if nota['faixa'] in ('Alto', 'Crítico'):
        return bool(e.get('aceitacao_residual_acao'))
    return True


def aviso_anterior(e):
    if e.get('encerrada') and not reducao_total(e) and not e.get('decisao_residual_acao'):
        return 'Esta providência foi encerrada por uma regra anterior. O risco residual depois da providência ainda não tem decisão.'
    return ''
