"""A5: achados categóricos, sem inferência a partir de texto livre."""
import hashlib
import json
from pathlib import Path

ARQUIVO = Path(__file__).parent / 'catalogos/lacunas_form3.json'
PENDENTES = {'F3-3.22', 'F3-3.29', 'F3-3.44'}
NENHUM = 'Nenhum controle identificado'
DESTINOS = ('Confirmar com a Secretaria', 'Complementação ou correção do FORM 1',
    'Revisão do FORM 2', 'Avaliação técnica', 'Manifestação jurídica',
    'Elaboração ou revisão de RIPD', 'Providência no FORM 4', 'Decisão da autoridade competente')


def validar_destino(dados):
    if dados.get('destino') not in DESTINOS or dados.get('prioridade') not in ('Imediata','Alta','Média','Baixa','A confirmar'):
        raise ValueError('Escolha o destino e a prioridade da lacuna.')


def configuracao():
    return json.loads(ARQUIVO.read_text(encoding='utf8'))


def codigo_controle(nome):
    return hashlib.sha256(nome.encode()).hexdigest()[:12]


def elegivel(item, respostas, estado):
    from app.questionario_forms34 import ativa
    if not ativa(item, respostas, estado):
        return False
    b, ident = item['bloco'], item['id']
    # Respostas históricas não reabrem condições fechadas.
    if b == 8 and ident != 'F3-3.25' and respostas.get('F3-3.25') != 'Sim':
        return False
    if ident == 'F3-3.33' and respostas.get('F3-3.32') != 'Sim':
        return False
    if b == 11 and ident != 'F3-3.39' and respostas.get('F3-3.39') != 'Sim':
        return False
    if b == 12 and respostas.get('F3-3.43') == 'Não' and respostas.get('F3-3.44') == 'Não':
        return False
    return True


def listar(estado):
    from app.questionario_forms34 import perguntas
    itens = {q['id']: q for q in perguntas(3)}
    respostas = estado.get('respostas', {})
    saida = []
    for regra in configuracao()['itens']:
        ident = regra['id']
        item = itens.get(ident)
        if not item or not regra.get('habilitada', False) or ident in PENDENTES:
            continue
        if regra['natureza'] in ('entrada', 'fora') or not elegivel(item, respostas, estado):
            continue
        valor = respostas.get(ident)
        valores = valor if isinstance(valor, list) else [valor]
        if not valor:
            continue
        if ident == 'F3-3.35' and any(str(v).startswith('Em definição pela Prefeitura') for v in valores):
            continue
        natureza = regra['natureza']
        if ident == 'F3-3.46' and not estado.get('revisao_texto_346'):
            natureza = 'a_confirmar'
        elif any(v in ('A confirmar', 'Requer análise') for v in valores):
            natureza = 'a_confirmar'
        elif not any(v in regra['desfavoravel'] for v in valores):
            continue
        if ident == 'F3-3.48' and estado.get('controles_bloco13'):
            continue
        saida.append(dict(id='LAC-'+ident, pergunta=ident, bloco=item['bloco'],
            natureza=natureza, rotulo=('Confirmar com a Secretaria: '+regra['assunto'])
                if natureza == 'a_confirmar' else regra.get('rotulo') or regra['assunto'],
            tema=regra.get('tema'), acao_sugerida=regra.get('acao_sugerida', ''),
            destino='Confirmar com a Secretaria' if natureza == 'a_confirmar' else ''))
    marcados = respostas.get('F3-3.47', [])
    for nome, controle in estado.get('controles_bloco13', {}).items():
        if nome not in marcados or controle.get('implementado') not in ('Não', 'Parcial'):
            continue
        saida.append(dict(id='LAC-F3-3.47-'+codigo_controle(nome), pergunta='F3-3.47', bloco=13,
            natureza='lacuna', rotulo=f"O controle {nome} foi indicado, mas sua implementação é {controle['implementado']}.",
            tema='T16', acao_sugerida='', destino=''))
    return saida


def salvar_controles(estado, dados):
    controles = dados.get('controles_bloco13', {})
    observacoes = dados.get('observacoes_controles', '')
    if not isinstance(controles, dict) or not isinstance(observacoes, str) or len(observacoes) > 1000:
        raise ValueError('Dados dos controles inválidos.')
    marcados = estado['respostas'].get('F3-3.47', [])
    for nome, detalhe in controles.items():
        if nome not in marcados or nome in (NENHUM, 'A confirmar'):
            raise ValueError('Informe detalhes somente dos controles selecionados.')
        if not isinstance(detalhe, dict) or detalhe.get('implementado', '') not in ('', 'Sim', 'Parcial', 'Não'):
            raise ValueError('Situação do controle inválida.')
        if not isinstance(detalhe.get('evidencia', ''), str) or len(detalhe.get('evidencia', '')) > 1000:
            raise ValueError('Referência da evidência inválida.')
    estado['controles_bloco13'] = controles
    estado['observacoes_controles'] = observacoes


def incoerencias(estado):
    import re
    respostas = estado.get('respostas', {})
    marcados = respostas.get('F3-3.47', [])
    avisos = []
    for par in configuracao()['incoerencias_bloco13']['pares']:
        if par['controle'] not in marcados:
            continue
        if any(respostas.get(i) == v.strip() for i, v in re.findall(r'(F3-[\d.]+) = (Sim|Não)', par['contradiz'])):
            avisos.append(par['aviso'])
    return avisos
