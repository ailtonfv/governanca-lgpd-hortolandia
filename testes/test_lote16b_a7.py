"""Respostas de leitura não simulam campos editáveis."""
import pytest
from app.rotas_forms34 import paginas
from testes.test_lote16b_a3 import Tags

@pytest.mark.parametrize('form', [3,4])
@pytest.mark.parametrize('bloqueio,pode', [('Plano aprovado',True),('',False)])
def test_a7_leitura_texto_multiplas_e_pendencia(form,bloqueio,pode):
    itens=[dict(id='F4-4.4',tipo='multi',opcoes=['Opção fictícia A','Opção fictícia B','Opção fictícia C']),dict(id='F4-4.5',tipo='text_long'),dict(id='F4-4.6',tipo='single')]
    for q in itens:q.update(bloco=2,ativa=True,enunciado='Pergunta fictícia',depende=None,recolhida=False,ocultar_condicional=False,opcoes_outro=[])
    html=paginas.env.get_template('_perguntas_forms34.html').render(itens=itens,estado={'versao':1,'respostas':{'F4-4.4':['Opção fictícia A','Opção fictícia B'],'F4-4.5':'Descrição fictícia <segura>','F4-4.6':'A confirmar'}},ref={'form':form},bloco=2,valores={},bloqueio_edicao=bloqueio,pode_preencher=pode)
    tags=Tags(html)
    assert not any(t in ('textarea','select') or (t=='input' and a.get('type')=='checkbox') for t,a in tags.tags)
    assert 'Opção fictícia A · Opção fictícia B' in html and 'Opção fictícia C' not in html
    assert 'Descrição fictícia &lt;segura&gt;' in html
    assert tags.classe('pendencia-resposta34') and not tags.classe('barra-salvar-bloco')
