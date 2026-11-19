"""R17, decisão de 19/11/2026. Conferência somente nos atos futuros.

Salvamento parcial não chama exigir(). Exceções são configuração proposta.
As condições continuam nas funções de domínio de cada instrumento.
"""
from pathlib import Path
import json
from functools import lru_cache
import re

CONFIGURACAO = Path(__file__).with_name('r17_excecoes.json')


@lru_cache(maxsize=1)
def excecoes():
    return json.loads(CONFIGURACAO.read_text(encoding='utf8'))['excecoes']


def marca(item, condicional=False, informativa=False):
    from app.pre_validacao_form1_integral import (
        metadado_visual_obrigatoriedade, CLASSE_ESSENCIAL, CLASSE_CONDICIONAL,
        CLASSE_METADADO_NAO_BLOQUEANTE, CLASSE_FACULTATIVA_PROPOSTA)
    classe = (CLASSE_METADADO_NAO_BLOQUEANTE if informativa else
              CLASSE_FACULTATIVA_PROPOSTA if item in excecoes() else
              CLASSE_CONDICIONAL if condicional else CLASSE_ESSENCIAL)
    return metadado_visual_obrigatoriedade(item, classe=classe)


def preenchida(valor):
    if isinstance(valor, str):
        return bool(valor.strip())
    if isinstance(valor, (list, tuple)):
        return any(preenchida(v) for v in valor)
    return valor is not None and valor != {}


def _linha(item, bloco, valor, ativa, condicional, informativa, sufixo='', confirmar=False):
    m = marca(item, condicional, informativa)
    return dict(item=item+sufixo, ancora=item, bloco=bloco, ativa=ativa,
                marca=m, respondida=preenchida(valor), a_confirmar=confirmar,
                obrigatoria=not informativa and item not in excecoes())


def perguntas2(conteudo, ramos=()):
    from app.respostas_form2 import definicao_revisao, _ativa
    from app.form2_rev212 import RASCUNHO, indice_valores, mapa_regras, aplicavel
    from app.contrato_form2_respostas import carregar_contrato
    valores = indice_valores(conteudo)
    regras = mapa_regras(carregar_contrato())
    linhas = []
    indice = {}
    for n in range(1, 15):
        bloco = definicao_revisao(n)
        indice.update({q['id']:q for q in bloco['itens']})
        campos = conteudo.get(RASCUNHO, {}).get(str(n), {})
        ocorrencias = sorted({1, *(int(k.rsplit('#', 1)[1]) for k in campos
                                   if re.search(r'#[1-9][0-9]?$', k))})
        for q in bloco['itens']:
            chave = q['id']
            leitura = q.get('guardar_concluir') == 'Automático em leitura' or q['edicao'] == 'consulta' or (n == 1 and q['edicao'] != 'habilitada')
            condicional = any(c['operador'] != 'SEMPRE' for c in regras.get(chave, q.get('condicoes', [])))
            for suf in ([f'#{i}' for i in range(1, max(ocorrencias)+1)] if q.get('repetivel') else ['']):
                if q['edicao'] == 'habilitada':
                    valor = conteudo.get('respostas_etapa1', {}).get(chave)
                    ativo = _ativa(q, conteudo.get('respostas_etapa1', {}))
                else:
                    valor = campos.get(('opcao:' if q['alternativas'] else 'texto:') + chave+suf)
                    if chave == 'F2-14.3':
                        valor = campos.get('unidade:'+chave+suf) or valor
                    ativo = aplicavel(chave, suf, valores, ramos, regras)
                escolhas = valor if isinstance(valor, list) else [valor]
                codigos = {a['codigo'] for a in q['alternativas'] if a['rotulo'].strip().casefold() == 'a confirmar'} | {'A_CONFIRMAR'}
                linhas.append(_linha(chave,n,valor,ativo,condicional,leitura,suf,
                                     any(v in codigos for v in escolhas if isinstance(v,str))))
    from app.opcao_outro import eh_outro
    from app.complementos_form2 import falta_complemento
    for linha in linhas:
        q=indice[linha['ancora']]; chave=linha['item']
        if q['edicao']=='habilitada':
            selecionadas=conteudo.get('respostas_etapa1',{}).get(chave,[])
            selecionadas=selecionadas if isinstance(selecionadas,list) else [selecionadas]
            comp=conteudo.get('complementos_etapa1',{}).get(chave,{})
            falta=any(a['codigo'] in selecionadas and a.get('complemento','').startswith('Texto condicionado') and not preenchida(comp.get(a['codigo'])) for a in q['alternativas'])
        else:
            campos=conteudo.get(RASCUNHO,{}).get(str(linha['bloco']),{})
            selecionadas=campos.get('opcao:'+chave,[])
            comp=campos.get('texto:'+chave)
            falta=falta_complemento(q,selecionadas,comp) or any(a['codigo'] in selecionadas and eh_outro(a['rotulo']) and not preenchida(comp) for a in q['alternativas'])
        if falta and not linha['a_confirmar']:linha['respondida']=False
    # Inativas arquivadas continuam visíveis. Não exigir nem reativar respostas antigas.
    arquivadas={**conteudo.get('respostas_inativas_etapa1',{})}
    for campos in conteudo.get('respostas_inativas_rev212',{}).values():
        arquivadas.update({k.removeprefix('opcao:'):v for k,v in campos.items() if k.startswith('opcao:')})
    for chave,valor in arquivadas.items():
        if isinstance(valor,dict):valor=valor.get('valor')
        q=indice.get(chave.partition('#')[0]); escolhas=valor if isinstance(valor,list) else [valor]
        if q and ('A_CONFIRMAR' in escolhas or any(a['codigo'] in escolhas and a['rotulo']=='A confirmar' for a in q['alternativas'])):
            atual=next((l for l in linhas if l['item']==chave),None)
            if atual and not atual['respondida']:atual['a_confirmar']=True
            elif not atual:
                linhas.append(_linha(q['id'],int(re.match(r'F2-(\d+)',q['id'])[1]),valor,False,True,False,chave[len(q['id']):],True))
    return linhas


def perguntas34(form, estado):
    from app.questionario_forms34 import perguntas, ativa
    linhas = []
    respostas = estado.get('respostas', {})
    for q in perguntas(form):
        valor = respostas.get(q['id'])
        escolhas = valor if isinstance(valor,list) else [valor]
        leitura = q['tipo'] in ('readonly','computed','ato') or (form == 3 and q['bloco'] == 14)
        condicional = bool(q.get('depende')) or q['id'] in ('F3-3.3.1','F4-4.9.1')
        ativo = ativa(q,respostas,estado)
        linha=_linha(q['id'],q['bloco'],valor,ativo,condicional,leitura,confirmar='A confirmar' in escolhas)
        from app.opcao_outro import eh_outro
        if any(eh_outro(v) for v in escolhas if isinstance(v,str)) and not preenchida(estado.get('complementos',{}).get(q['id'])):
            linha['respondida']=False
        linhas.append(linha)
    return linhas


def resumir(linhas):
    faltantes = [q for q in linhas if q['ativa'] and q['obrigatoria'] and not q['respondida']]
    # Resposta histórica inativa permanece sinalizada, sem passar a ser exigida.
    confirmar = [q for q in linhas if q['a_confirmar']]
    grupos = [{'bloco':n,'quantidade':sum(q['bloco']==n for q in faltantes)}
              for n in sorted({q['bloco'] for q in faltantes})]
    return dict(faltantes=faltantes, grupos=grupos, a_confirmar=confirmar,
                quantidade_a_confirmar=len(confirmar), pronto=not faltantes)


def conferencia2(conteudo, ramos=()):
    return resumir(perguntas2(conteudo or {},ramos))


def conferencia34(form, estado):
    return resumir(perguntas34(form,estado))


def conferencia_participacao(sessao,p):
    from app.form2_rev212 import ramos_origem
    from app.origem_form2 import ler_origem
    return conferencia2(p.conteudo or {},ramos_origem(ler_origem(sessao,p.registro_id,p.snapshot_id)))


class FormularioIncompleto(ValueError):
    def __init__(self, conferencia, base):
        self.conferencia = conferencia
        self.base = base
        super().__init__('Há perguntas obrigatórias sem resposta. O preenchimento salvo foi preservado.')


def exigir(conferencia, base):
    if not conferencia['pronto']:
        raise FormularioIncompleto(conferencia,base)
    return retrato(conferencia)


def retrato(conferencia):
    return dict(regra='R17-2026-11-19', quantidade_a_confirmar=conferencia['quantidade_a_confirmar'],
                itens_a_confirmar=[q['item'] for q in conferencia['a_confirmar']],
                excecoes_situacao='proposta', excecoes=sorted(excecoes()))


def metadado_pergunta(q, form):
    if form == 2:
        leitura = q.get('guardar_concluir') == 'Automático em leitura' or q.get('edicao') == 'consulta' or (q['id'].startswith('F2-1.') and q.get('edicao') != 'habilitada')
        cond = any(c['operador'] != 'SEMPRE' for c in q.get('condicoes', []))
    else:
        leitura = q['tipo'] in ('readonly','computed','ato') or (form == 3 and q['bloco'] == 14)
        cond = bool(q.get('depende')) or q['id'] in ('F3-3.3.1','F4-4.9.1')
    return marca(q['id'],cond,leitura)


def conferencia_para_tela(sessao,p):
    try:
        return conferencia_participacao(sessao,p)
    except (FileNotFoundError,ValueError):
        # A leitura da participação permanece disponível; atos nunca usam este fallback.
        return {'indisponivel':True,'pronto':False}
