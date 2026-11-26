"""Leitura dos atos; sem gravação nem inferência de recomendações."""
from datetime import date

def data_br(v):
    if not v:return 'Não definido'
    try:return date.fromisoformat(str(v)).strftime('%d/%m/%Y')
    except ValueError:return str(v)

def ripd(e):
    from app.leitura_atos34 import horario
    r=e.get('referencia_ripd')
    if not r:return 'RIPD: referência não informada. O RIPD é elaborado pela Secretaria e juntado ao processo como evidência.'
    return f"RIPD juntado em {r['referencia']}, informado em {horario(r['em'])} por {r['papel']}."

def conteudo_decisao(acao,e,autores,unidades):
    from app.leitura_atos34 import conteudo_ato
    fontes={'aprovar_plano':['planejar'],'executar_medida':['planejar','aprovar_plano'],
      'verificar':['planejar','executar_medida'], 'decidir_prorrogacao':['planejar','pedir_prorrogacao'],
      'cancelar':['planejar','pedir_cancelamento'],'conferir_aprendizagem':['aprender'],
      'autorizar_aprendizagem':['aprender','conferir_aprendizagem']}
    if acao in ('confirmar_residual_acao','decidir_residual_acao','aceitar_residual_acao'):
        return conteudo_ato('propor_residual_acao',e,autores,unidades)
    return [linha for fonte in fontes.get(acao,[]) for linha in conteudo_ato(fonte,e,autores,unidades)]

def mensagem_decisao(e):
    from app.leitura_atos34 import horario
    return [f"Decisão do Prefeito, registrada pelo Gabinete em {horario(d['em'])}, conforme {d['documento']}"
            for d in (e.get('aceitacao',{}),e.get('plano_aprovado',{})) if d.get('documento') and d.get('registrador')=='Gabinete']
