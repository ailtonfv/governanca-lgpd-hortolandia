"""Leitura compartilhada da Central, listas e cabeçalho, sem novos atos."""
from app.atos_forms34_interface import disponiveis
from app.leitura_atos34 import NOMES, horario
from app.infra_forms34 import historico


def titulo(obj, e):
    codigo = obj.codigo.split('-')[-1]
    especie = 'Risco' if e['form'] == 3 else 'Ação'
    texto = e.get('evento') if e['form'] == 3 else e.get('respostas', {}).get('F4-4.3') or e.get('plano')
    if not isinstance(texto, str):texto = None
    if texto:
        texto = ' '.join(texto.split())
        if len(texto) > 120: texto = texto[:117].rstrip()+'…'
    return f"{especie} {int(codigo[1:])}: {texto or 'Título ainda não informado'} ({codigo})"


def resumo(sessao, obj, e, papeis, pessoa_id):
    atos = []
    for n in range(1, 17 if e['form'] == 3 else 10):
        for a in disponiveis(e['form'], n, papeis, e, pessoa_id):
            if a['acao'] in ('adicionar_risco', 'abrir_detalhes', 'manifestar_dpo', 'informar_ripd',
                             'confirmar_gatilho_juridico', 'enviar_juridico', 'autorizar_referencia',
                             'pedir_cancelamento', 'pedir_prorrogacao') or a.get('recolhido'):continue
            atos.append((n, a))
    prioritarios = {'manifestar_comite':0, 'aceitar_residual':0, 'aprovar_plano':0,
                   'verificar':0, 'conferir_aprendizagem':0, 'autorizar_aprendizagem':0}
    atos.sort(key=lambda x:prioritarios.get(x[1]['acao'], 1))
    bloco, ato = atos[0] if atos else (14 if e['form']==3 else 7, None)
    ultimo = next((ev for ev in reversed(historico(sessao,obj.id)) if ev.tipo_evento.startswith('f34_')
                   and ev.tipo_evento not in ('f34_salvar_bloco','f34_abrir_detalhes')), None)
    situacao = NOMES.get(ultimo.tipo_evento.removeprefix('f34_'), e['situacao'])+' em '+horario(ultimo.ocorrido_em) if ultimo else e['situacao']
    return dict(titulo=titulo(obj,e), situacao=situacao, bloco=bloco, pendente=bool(ato),
                botao=ato['titulo'] if ato else 'Acompanhar',
                pendencia=ato['titulo'] if ato else 'Nenhuma decisão aguardando o Gabinete' if 'gabinete' in papeis else 'Nenhum ato pendente para seu papel')
