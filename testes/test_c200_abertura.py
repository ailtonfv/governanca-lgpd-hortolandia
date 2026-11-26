"""C199/C200: estrutura visível do seletor; massa fictícia no banco _teste."""
from html.parser import HTMLParser
from pathlib import Path
import os
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app


class Elementos(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elementos=[]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elementos.append((tag, dict(attrs)))


def test_c200_seletor_visivel_desativado_antes_do_tipo_e_aviso_fora(sessao):
    pagina=TestClient(app).get('/registros/novo?conta_id=CONTA-A1')
    assert pagina.status_code==200
    elementos=Elementos(pagina.text).elementos
    select=next(attrs for tag,attrs in elementos if attrs.get('id')=='objeto_principal_id')
    assert 'disabled' in select and 'hidden' not in select
    assert select['name']=='objeto_principal_id'
    aviso=next((tag,attrs) for tag,attrs in elementos if attrs.get('id')=='aviso-duplicidade')
    assert aviso[0]=='section' and 'hidden' in aviso[1]
    fim=pagina.text.index('</select>',pagina.text.index('id="objeto_principal_id"'))
    assert fim < pagina.text.index('id="aviso-duplicidade"')
    opcoes=[a for tag,a in elementos if tag=='option' and a.get('data-tipo')=='servico']
    assert opcoes and any('UNID-NORTE' in a['data-unidades'].split(',') for a in opcoes)
    assert 'Escolha primeiro o tipo, acima' in pagina.text
    assert 'Falta informar: tipo, item, canais, contexto.' in pagina.text
    botao=next(a for _,a in elementos if a.get('id')=='confirmar-abertura')
    assert 'disabled' in botao
    # Evidência opcional para inspeção de tela com o JavaScript real, fora do Git.
    if os.environ.get('LGPD_EVIDENCIA_C200'):
        Path(os.environ['LGPD_EVIDENCIA_C200']).write_text(pagina.text,encoding='utf8')
