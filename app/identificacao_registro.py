"""Identificação pública única; contexto é apresentado em linha separada."""
def identificar(registro, nome=None):
    def valor(*chaves):
        for chave in chaves:
            v=registro.get(chave) if isinstance(registro,dict) else getattr(registro,chave,None)
            if v:return str(v)
        return ''
    codigo=valor('codigo_lgpd','codigo')
    nome=nome or valor('titulo_objeto','titulo')
    tipo=valor('tipo_objeto','tipo')
    tipo={'servico':'Serviço','serviço':'Serviço','processo':'Processo','atividade':'Atividade'}.get(tipo.lower(),tipo)
    return f'{codigo} · {nome} ({tipo})'
