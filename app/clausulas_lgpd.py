"""A12: conteúdo orientativo versionado e validação das listas, sem gerar minuta."""
import json
from pathlib import Path
from copy import deepcopy
ARQUIVO=Path(__file__).parent/'catalogos/clausulas_lgpd.json'

def catalogo():return json.loads(ARQUIVO.read_text(encoding='utf8'))

def perguntas_fornecedor():
    d=catalogo();itens=[]
    for t in d['fornecedor_guarda_dados']['temas']:
        itens.append(dict(id=t['pergunta_form2'],enunciado=t['tema'],ajudas_usuario=[t['texto']]))
    itens.append(dict(id='F2-9F.2a',enunciado='O Município consegue acessar e extrair seus dados a qualquer tempo, sem custo adicional e sem depender do fornecedor, com dicionário de dados?',ajudas_usuario=[]))
    return itens

def perguntas2():
    d=catalogo();itens=[dict(id='F2-9C.1',enunciado=d['pergunta_que_decide']['pergunta_form2'],ajudas_usuario=[d['pergunta_que_decide']['orientacao']])]+perguntas_fornecedor()
    for q in itens:
        opcoes=[('SIM','Sim'),('NAO','Não'),('A_CONFIRMAR','A confirmar')]
        if q['id'].startswith('F2-9F.'):opcoes.insert(2,('PARCIALMENTE','Parcialmente'))
        q.update(controle='Seleção única',edicao='rascunho',repetivel=False,condicoes=[],fontes_publicas=[],opcoes_outro=[],complementos_necessarios=[],alternativas=[dict(codigo=c,rotulo=r,complemento='') for c,r in opcoes])
    return itens

def guarda_fornecedor(respostas):
    v=respostas.get('11.2',[]);v=v if isinstance(v,list) else [v]
    return respostas.get('8.2.2')=='Sim' or any('fornecedor' in str(x).lower() for x in v)

def itens4(guarda=False):
    d=catalogo();itens=deepcopy(d['parte_b']['temas'])
    if guarda:
        itens+=deepcopy(d['fornecedor_guarda_dados']['temas'])
        itens.append(dict(codigo='F2a',tema='Acesso e extração pelo Município',texto=perguntas_fornecedor()[-1]['enunciado']))
    return itens

def aplica4(respostas):return bool(set(respostas.get('F4-4.4',[])) & {'Criar/alterar cláusula contratual','Aditar contrato'})

def validar4(respostas,lista,guarda):
    if not isinstance(lista,dict):raise ValueError('Lista de cláusulas inválida.')
    if lista and not aplica4(respostas):raise ValueError('Lista de cláusulas exige ação contratual.')
    permitidos={i['codigo'] for i in itens4(guarda)}
    if set(lista)-permitidos or any(v not in ('','Sim','Não','A confirmar') for v in lista.values()):raise ValueError('Resposta de cláusulas inválida.')
    return dict(lista)

def pendencias4(estado):
    if not aplica4(estado.get('respostas',{})):return []
    r=estado.get('clausulas_contrato',{})
    return [t['tema'] for t in itens4(estado.get('fornecedor_guarda_dados',False)) if r.get(t['codigo']) in ('Não','A confirmar')]
