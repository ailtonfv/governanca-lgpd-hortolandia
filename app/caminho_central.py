"""Projeção dos fluxos: agrupa a mesma lista autorizada, sem reclassificar itens."""
from urllib.parse import urlencode
from app.fila_form2 import pessoa_ativa, unidades
from app.continuidade_apa import unidades_em_que_e_apa_atual

ETAPAS = (
    ('f1-abre', 1, 'Abrir e indicar o preenchimento', 'APA abre e envia ao ARP, ou preenche ele mesmo'),
    ('f1-levanta', 1, 'Descrever os fatos', 'ARP descreve o tratamento'),
    ('f1-confere', 1, 'Conferir e confirmar', 'APA confere; quem apresentou não confere'),
    ('f2-analisa', 1, 'Analisar', 'AAL analisa o tratamento'),
    ('f2-conclui', 1, 'Análise concluída', 'Não equivale a homologação'),
    ('apoio', 0, 'Apoio à análise, quando necessário', 'DPO, Jurídico e consultas temáticas'),
    ('f3-avalia', 2, 'Risco avaliado', 'Secretaria e DPO confirmam conjuntamente'),
    ('f3-decide', 2, 'Decisão sobre o risco', 'Autoridade competente, com manifestações quando exigidas'),
    ('f4-plano', 2, 'Plano aprovado', 'Secretaria prepara; autoridade competente aprova'),
    ('f4-executa', 2, 'Ação executada', 'Unidade executora registra a execução'),
    ('f4-verifica', 2, 'Verificação independente', 'Comitê, de outra Secretaria'),
    ('f4-aprende', 2, 'Aprendizagem autorizada', 'Secretaria registra, DPO confere, Secretaria autoriza'),
)


def caminho(sessao, conta_id, listas):
    pessoa = pessoa_ativa(sessao, conta_id)
    atua = set()
    if unidades_em_que_e_apa_atual(sessao, pessoa.id):
        atua.update(('f1-abre', 'f1-confere'))
    if unidades(sessao, pessoa.id, 'preenchedor'):
        atua.update(('f1-levanta', 'f3-avalia', 'f4-plano', 'f4-executa', 'f4-aprende'))
    if unidades(sessao, pessoa.id, 'aal_form2'):
        atua.update(('f2-analisa', 'f2-conclui', 'apoio', 'f3-avalia', 'f3-decide', 'f4-plano', 'f4-executa', 'f4-aprende'))
    if unidades(sessao, pessoa.id, 'governanca_protecao_dados'):
        atua.update(('apoio', 'f3-avalia', 'f3-decide', 'f4-aprende'))
    if unidades(sessao, pessoa.id, 'juridico_form2'):
        atua.add('apoio')
    if unidades(sessao, pessoa.id, 'demo34_verificador'):
        atua.add('f4-verifica')
    if unidades(sessao, pessoa.id, 'demo34_relator'):
        atua.update(('f3-avalia', 'f3-decide', 'f4-executa'))
    if unidades(sessao, pessoa.id, 'demo34_secretario') or unidades(sessao, pessoa.id, 'demo34_gabinete'):
        atua.update(('f3-decide', 'f4-plano'))
    itens = [i for lista in listas.values() for i in lista]
    saida = []
    for chave, fluxo, titulo, explicacao in ETAPAS:
        grupo = filtrar(itens, chave)
        lista_url = '/central/providencias?' + urlencode(dict(conta_id=conta_id, etapa=chave))
        saida.append(dict(chave=chave, fluxo=fluxo, titulo=titulo, explicacao=explicacao,
                          sua_parte=chave in atua, quantidade=len(grupo), itens=grupo[:3],
                          lista=lista_url, href=grupo[0]['href'] if len(grupo) == 1 else lista_url))
    return saida


def filtrar(itens, etapa):
    return sorted((i for i in itens if i['pendente'] and i['etapa'] == etapa),
                  key=lambda i:(i['desde'], i['href']))
