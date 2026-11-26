"""A8: classificação única das consultas, sem produzir atos ou alterar respostas."""


def situacao_consulta(p):
    if p.tipo != 'dpo':
        return None
    conteudo = p.conteudo or {}
    if conteudo.get('resposta'):
        return 'respondidas'
    if p.estado == 'concluida' and (p.manifestacao or '').strip():
        return 'aguardando_aal'
    if not conteudo.get('de_oficio') and (p.questao or '').strip() and p.estado != 'concluida':
        return 'aguardando_dpo'
    return None


def aguardando_dpo(p):
    return situacao_consulta(p) == 'aguardando_dpo'


def respostas_para_leitura(conteudo):
    """Usa o catálogo instalado; nenhuma redação privada é copiada no código."""
    from app.respostas_form2 import definicao_bloco, definicao_revisao, RASCUNHO
    saida = []
    for numero in range(1, 15):
        definicao = definicao_bloco(numero) if numero <= 2 else definicao_revisao(numero)
        linhas = []
        revisao = conteudo.get(RASCUNHO, {}).get(str(numero), {})
        for q in definicao['itens']:
            valores = []
            if numero <= 2 and q['id'] in conteudo.get('respostas_etapa1', {}):
                valores.append(conteudo['respostas_etapa1'][q['id']])
            for chave, valor in revisao.items():
                if chave.split(':')[-1].split('#')[0] == q['id'] and not chave.startswith('comentario:'):
                    valores.append(valor)
            alternativas = {a['codigo']: a['rotulo'] for a in q.get('alternativas', [])}
            for valor in valores:
                if valor in (None, '', []):
                    continue
                lista = valor if isinstance(valor, list) else [valor]
                textos = [alternativas.get(str(v), str(v)) for v in lista]
                linhas.append(dict(id=q['id'], pergunta=q['enunciado'], valor=', '.join(textos)))
        if linhas:
            saida.append(dict(numero=numero, titulo=definicao['titulo'], perguntas=linhas))
    return saida
