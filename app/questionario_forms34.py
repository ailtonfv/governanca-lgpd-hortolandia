"""Contrato de perguntas; editorial privado, condições decididas no 11-B."""
from copy import deepcopy
import re
from app.catalogo_forms34 import carregar_catalogo, estrutura

DETALHES4 = {'F4-' + i for i in ('4.9.1','4.10.1','4.10.2','4.10.3','4.11','4.11.1',
    '4.12','4.15.2','4.17','4.17.1','4.23','4.24','4.26','4.26.1','4.27')}
ATOS3 = {'F3-' + i for i in ('3.49','3.50','3.51','3.52','3.52.1','3.52.2','3.52.3','3.52.4',
    '3.52.5','3.52.6','3.55','3.56','3.57','3.43.1','3.43.4')}
ATOS4 = {'F4-' + i for i in ('4.2.1','4.6','4.7','4.10','4.10.1','4.10.2','4.10.3',
    '4.15','4.15.1','4.15.2','4.16','4.18','4.18.1','4.19','4.20','4.21','4.22',
    '4.23','4.24','4.25')}
DEPENDENCIAS = {
    'F3-3.4.1': 'F3-3.4', 'F3-3.11.1': 'F3-3.11', 'F3-3.25.1': 'F3-3.25',
    'F3-3.40': 'F3-3.39', 'F3-3.58.1': 'F3-3.58',
    **{'F3-3.43.' + str(n): 'F3-3.43' for n in range(1,5)},
    'F4-4.11.1': 'F4-4.11', 'F4-4.17.1': 'F4-4.17', 'F4-4.26.1': 'F4-4.26'}


def opcoes(controle, todos):
    fonte = controle['fonte_controle']
    if controle['id'] in ('F3-3.52.1', 'F3-3.52.2'):
        return ['1', '2', '3', '4', '5', 'A confirmar']
    parte = re.search(r'(?:Alternativas:|[úu]nica(?: por risco)?:)\s*(.*?)(?: Exibição|$)', fonte)
    if not parte:
        return []
    # Separador editorial é espaço/barra/espaço; barras internas são preservadas.
    texto = parte[1].split('. ')[0].rstrip('.')
    return [v.strip() for v in texto.split(' / ')]


def perguntas(form):
    d = carregar_catalogo(form)
    controles = {c['id']: c for c in d['controles']['itens']}
    saida = []
    for bloco in d['editorial']['blocos']:
        for item in bloco['itens']:
            c = controles[item['id']]
            tipo = c['controle']
            alternativas = opcoes(c, controles)
            if tipo == 'readonly' and alternativas:
                tipo = 'single'  # consulta assistida exige confirmação humana, sem pré-marcação
            ato = item['id'] in (ATOS3 if form == 3 else ATOS4)
            if ato:
                tipo = 'ato'
            saida.append(dict(id=item['id'], bloco=bloco['numero'], titulo=bloco['titulo'],
                enunciado=item['enunciado'], tipo=tipo, opcoes=alternativas,
                detalhe=item['id'] in DETALHES4, depende=DEPENDENCIAS.get(item['id']),
                ajuda='Confirme os fatos da origem; esta resposta não é preenchida automaticamente.'
                      if c['controle'] == 'readonly' and alternativas else ''))
    return saida


def ativa(item, respostas, estado):
    if item['id'] == 'F4-4.9.1':
        return bool(estado.get('prioridade_origem') and respostas.get('F4-4.9')) and respostas['F4-4.9'] != estado['prioridade_origem']
    dep = DEPENDENCIAS.get(item['id'])
    if dep:
        return respostas.get(dep) == 'Sim'
    if item['id'] == 'F3-3.3.1':
        return estado.get('situacao_form2') != 'concluida'
    return True


def recolhida(item, respostas, estado):
    # Recolhimento visual nunca apaga nem marca como não aplicável.
    if estado.get('aberturas', {}).get(str(item['bloco'])):
        return False
    if respostas.get(item['id']) not in (None, '', []):
        return False
    if item['bloco'] == 8 and item['id'] != 'F3-3.25' and item['id'].startswith('F3-'):
        return respostas.get('F3-3.25') == 'Não' and not estado.get('contradicoes', {}).get('8')
    if item['id'] == 'F3-3.33':
        return (respostas.get('F3-3.31') == 'Sim' and respostas.get('F3-3.32') == 'Não'
                and respostas.get('F3-3.34') == 'Não' and not estado.get('contradicoes', {}).get('9'))
    if item['id'] in ('F3-3.40', 'F3-3.41', 'F3-3.42'):
        return respostas.get('F3-3.39') == 'Não' and not estado.get('contradicoes', {}).get('11')
    if item['id'].startswith('F3-3.43.'):
        return (respostas.get('F3-3.43') == 'Não' and respostas.get('F3-3.44') == 'Não'
                and respostas.get('F3-3.45') == 'Sim' and respostas.get('F3-3.46') == 'Sim')
    return item['detalhe'] and not respostas.get(item['id'])


def salvar(form, anteriores, dados, estado):
    campos = dados.get('campos', {})
    bloco = dados.get('bloco')
    itens = {i['id']: i for i in perguntas(form) if i['bloco'] == bloco}
    if not itens or not isinstance(campos, dict) or set(campos) - set(itens):
        raise ValueError('Bloco ou pergunta inválida.')
    novo = deepcopy(anteriores)
    novo.update(campos)
    for chave, valor in campos.items():
        i = itens[chave]
        if i['tipo'] in ('readonly', 'computed', 'ato'):
            raise ValueError('Este campo é registrado pelo ato próprio, não por edição livre.')
        if not ativa(i, novo, estado):
            if valor != anteriores.get(chave) and valor not in ('', [], None):
                raise ValueError('Pergunta bloqueada pela condição de origem.')
            novo[chave] = anteriores.get(chave)
            continue
        if i['tipo'] in ('single', 'multi'):
            valores = valor if i['tipo'] == 'multi' else [valor]
            if not isinstance(valores, list) or any(not isinstance(v, str) for v in valores):
                raise ValueError('Seleção inválida.')
            if len(set(valores)) != len(valores) or any(v and v not in i['opcoes'] for v in valores):
                raise ValueError('Alternativa fora do catálogo.')
            if 'A confirmar' in valores and len(valores) > 1:
                raise ValueError('A confirmar deve ficar sozinha.')
        elif not isinstance(valor, str) or len(valor) > (1000 if i['tipo'] == 'text_long' else 200):
            raise ValueError('Texto fora do limite permitido.')
    from app.opcao_outro import validar_outro
    complementos={**estado.get('complementos',{}),**dados.get('complementos',{})}
    for chave,valor in campos.items():
        if ativa(itens[chave],novo,estado) and str(complementos.get(chave,'')).strip():
            validar_outro(valor,complementos.get(chave,''),chave)
    return novo


def grade(form, respostas, estado):
    itens = perguntas(form)
    resultado = []
    for n in range(1, 17 if form == 3 else 10):
        grupo = [i for i in itens if i['bloco'] == n]
        ativos = [i for i in grupo if i['tipo'] not in ('readonly', 'computed', 'ato')
                  and ativa(i, respostas, estado) and not recolhida(i, respostas, estado)]
        preenchidos = sum(respostas.get(i['id']) not in (None, '', []) for i in ativos)
        total = len(ativos)
        texto = ('Ainda não preenchido' if not preenchidos else
                 'Todas as perguntas ativas respondidas' if preenchidos == total else
                 f'Em preenchimento · {preenchidos} de {total} perguntas ativas')
        resultado.append(dict(numero=n, titulo=grupo[0]['titulo'], n=preenchidos, m=total,
                              texto=texto, percentual=round(100*preenchidos/total) if total else 0))
    return resultado
