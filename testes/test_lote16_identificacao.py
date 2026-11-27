"""A11.1: identificação compartilhada sem mudar as contagens."""
from html import unescape
import re
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.identificacao_registro import identificar
from app.modelos import Registro
from testes.test_lote12 import entrada, fonte, protecoes, entrar


def test_identificacao_nas_paginas(sessao,entrada):
    r=sessao.get(Registro,entrada.registro_id)
    obj=entrar(sessao,entrada)
    esperado=identificar(r)
    assert esperado == f'{r.codigo_lgpd} · Registro de teste (fictício) (Atividade)'
    c=TestClient(app)
    for caminho in ('/central','/painel','/form2/filas',f'/registros/{r.id}',f'/forms34/{obj}/blocos/1','/forms34','/dashboard?lista=ativos'):
        separador='&' if '?' in caminho else '?'
        resposta=c.get(caminho+separador+'conta_id=CONTA-B1')
        assert resposta.status_code==200, caminho
        texto = unescape(re.sub(r'<[^>]+>', '', resposta.text))
        assert esperado in texto, caminho
    assert identificar({'codigo_lgpd':'LGPD-2026-99999','titulo':'Objeto fictício','tipo':'Servico'})=='LGPD-2026-99999 · Objeto fictício (Serviço)'
