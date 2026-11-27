"""R17: salvamento parcial, atos futuros e histórico, somente massa fictícia."""
from copy import deepcopy
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app.main import app
from app.modelos import Evento
from app.obrigatoriedade_forms import (conferencia2, conferencia34, perguntas2,
    perguntas34, exigir, FormularioIncompleto, marca, excecoes)
from app.questionario_forms34 import salvar
from app.respostas_form2 import aplicar_revisao
from testes.test_lote12 import protecoes, entrada, entrar, ato, estado, fonte, avaliar, SECRETARIO, VERIFICADOR
from testes.apoio_r17 import completo2, preencher34


@pytest.mark.parametrize('form',[3,4])
def test_salvar_obrigatoria_vazia_e_marca(form):
    item='F3-3.13' if form==3 else 'F4-4.3'
    from app.questionario_forms34 import perguntas
    q=next(q for q in perguntas(form) if q['id']==item)
    e={'respostas':{},'situacao_form2':'concluida'}
    r=salvar(form,{},dict(bloco=q['bloco'],campos={item:''}),e)
    assert r[item]==''
    assert item in [q['item'] for q in conferencia34(form,{**e,'respostas':r})['faltantes']]
    assert marca(item)['marcador']=='*'


def test_condicional_inativa_nao_cobrada_ativa_cobrada():
    e={'respostas':{'F3-3.4':'Não'},'situacao_form2':'concluida'}
    assert 'F3-3.4.1' not in [q['item'] for q in conferencia34(3,e)['faltantes']]
    e['respostas']['F3-3.4']='Sim'
    assert 'F3-3.4.1' in [q['item'] for q in conferencia34(3,e)['faltantes']]
    m=marca('F3-3.4.1',True)
    assert (m['marcador'],m['marcador_ativo'],m['rotulo_ativo'])==('**','*','Obrigatório neste caso')


def test_informativa_recusada_e_excecao_configurada():
    with pytest.raises(ValueError,match='ato próprio'):
        salvar(3,{},dict(bloco=14,campos={'F3-3.52':'Sim'}),{})
    assert marca('F3-3.52',informativa=True)['marcador']=='****'
    assert set(excecoes())=={'F2-14.9','F4-4.27'}
    assert 'F2-14.9' not in [q['item'] for q in conferencia2({})['faltantes']]
    assert 'F4-4.27' not in [q['item'] for q in conferencia34(4,{'respostas':{}})['faltantes']]


def test_f2_salvamento_parcial_nao_conclui():
    from app.respostas_form2 import aplicar_bloco
    c,_=aplicar_bloco({},bloco=1,alteracoes={'F2-1.2':None},proxima_versao=1)
    assert not conferencia2(c)['pronto']
    assert any(q['item']=='F2-1.2' for q in conferencia2(c)['faltantes'])


def test_f2_encaminhamento_recusado_com_links_e_sem_evento(sessao,entrada):
    entrada.conteudo={'rascunho_form2_rev21_2':{'14':{'opcao:F2-14.5':['SIM']}}};sessao.commit()
    antes=sessao.scalars(select(Evento.id)).all()
    r=TestClient(app).post(f'/form2/participacoes/{entrada.id}?conta_id=CONTA-B1',data={
        'acao':'concluir','conta_id':'CONTA-B1','versao':entrada.versao,'comando_id':str(uuid4())})
    assert r.status_code==409
    assert f'/form2/participacoes/{entrada.id}/blocos/1?conta_id=CONTA-B1' in r.text
    assert 'perguntas sem resposta' in r.text
    assert sessao.scalars(select(Evento.id)).all()==antes
    sessao.refresh(entrada)
    assert entrada.conteudo['rascunho_form2_rev21_2']['14']['opcao:F2-14.5']==['SIM']


def test_a_confirmar_encaminha_registra_e_repeticao_anterior_preservada(sessao,entrada):
    from app.fluxo_forms34 import ingressar
    c=conferencia2(entrada.conteudo)
    assert c['pronto'] and c['quantidade_a_confirmar']>0
    cmd=str(uuid4()); versao=entrada.versao
    obj=entrar(sessao,entrada,comando_id=cmd)
    ev=sessao.scalar(select(Evento).where(Evento.comando_id==cmd,Evento.tipo_evento=='form2_encaminhamento34'))
    assert ev.conteudo['conteudo']['conferencia_r17']['quantidade_a_confirmar']==c['quantidade_a_confirmar']
    # New rule never invalidates an already recorded command after later edits.
    entrada.conteudo={};sessao.commit()
    repetido=ingressar(sessao,conta_id='CONTA-B1',comando_id=cmd,participacao_id=entrada.id,versao=versao,form=3)
    assert repetido['identidade_id']==obj
    assert estado(sessao,obj)['situacao']=='Em preenchimento'


def test_conclusao_f3_recusa_depois_aceita_e_preserva_respostas(sessao,entrada):
    obj=entrar(sessao,entrada)
    preencher34(sessao,obj,blocos={15})
    avaliar(sessao,obj)
    ato(sessao,obj,'aceitar_residual',conta=SECRETARIO,justificativa='Justificativa fictícia')
    ato(sessao,obj,'propor_triagem',resultado='analise_adicional',justificativa='Triagem fictícia')
    ato(sessao,obj,'confirmar_triagem',conta='CONTA-E1')
    antes=deepcopy(estado(sessao,obj))
    with pytest.raises(FormularioIncompleto):ato(sessao,obj,'concluir_avaliacao')
    assert estado(sessao,obj)==antes
    preencher34(sessao,obj)
    ato(sessao,obj,'concluir_avaliacao')
    e=estado(sessao,obj)
    assert e['situacao']=='Avaliação concluída' and e['conferencia_r17']['quantidade_a_confirmar']>0
    assert e['respostas']['F3-3.4']=='A confirmar'


def test_condicional_f2_por_ocorrencia_e_inativa():
    c=completo2()
    c['rascunho_form2_rev21_2']['10']['opcao:F2-10.2']=['NAO']
    c['rascunho_form2_rev21_2']['10'].pop('opcao:F2-10.3',None)
    assert 'F2-10.3' not in [q['item'] for q in conferencia2(c)['faltantes']]
    c['rascunho_form2_rev21_2']['10']['opcao:F2-10.2']=['SIM']
    assert 'F2-10.3' in [q['item'] for q in conferencia2(c)['faltantes']]


def test_a_confirmar_inativa_continua_visivel():
    e={'respostas':{'F3-3.4':'Não','F3-3.4.1':'A confirmar'},'situacao_form2':'concluida'}
    r=conferencia34(3,e)
    assert r['quantidade_a_confirmar']==1 and not r['a_confirmar'][0]['ativa']
    assert 'F3-3.4.1' not in [q['item'] for q in r['faltantes']]


def test_get_exibe_marcas_sem_html_required_para_salvar(sessao,entrada):
    obj=entrar(sessao,entrada)
    r=TestClient(app).get(f'/forms34/{obj}/blocos/2?conta_id=CONTA-B1')
    assert r.status_code==200 and 'data-r17' in r.text
    assert "0 respostas marcadas 'A confirmar'" not in r.text
    form=r.text.split('id="perguntas34"',1)[1].split('</form>',1)[0]
    assert ' required' not in form


def test_outro_parcial_salva_mas_exige_complemento_na_conclusao():
    from app.questionario_forms34 import perguntas
    q=next(q for q in perguntas(3) if q['id']=='F3-3.14')
    v=next(v for v in q['opcoes'] if v.startswith('Outro'))
    v=[v] if q['tipo']=='multi' else v
    r=salvar(3,{},dict(bloco=q['bloco'],campos={q['id']:v}),{})
    assert q['id'] in [i['item'] for i in conferencia34(3,{'respostas':r})['faltantes']]


def test_form1_metadados_sem_mudanca():
    from app.pre_validacao_form1_integral import metadado_visual_obrigatoriedade
    assert metadado_visual_obrigatoriedade('1.1')['marcador'] in ('*','**','****')


def test_f4_verificacao_cobra_somente_campos_do_verificador(sessao,entrada):
    from testes.test_lote12 import preparar_acao
    from app.etapas_forms34 import VERIFICACAO
    obj=preparar_acao(sessao,entrada)
    ato(sessao,obj,'executar_medida',resumo='Execução fictícia: acessos revisados e documentados.',evidencia='Evidência fictícia')
    antes=deepcopy(estado(sessao,obj))
    with pytest.raises(ValueError):
        ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Verificação fictícia')
    assert estado(sessao,obj)==antes
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Verificação fictícia',
        **{k:('Sim' if k=='F4-4.22' else 'A confirmar') for k in VERIFICACAO})
    e=estado(sessao,obj)
    assert e['encerrada'] and e['conferencia_r17']['quantidade_a_confirmar']>0
    ev=sessao.scalars(select(Evento).where(Evento.cadeia_id==obj,Evento.tipo_evento=='f34_encerramento_automatico')).one()
    assert ev.conteudo['estado']['conferencia_r17']==e['conferencia_r17']


def test_conclusao_historica_sem_r17_nao_recalculada(sessao,entrada):
    from app.fluxo_forms34 import _gravar_estado
    from app.infra_forms34 import _abrir
    from app.comandos import fechar_comando
    from app.modelos import IdentidadeForms34
    obj=entrar(sessao,entrada,4)
    # Arrange: evento anterior à regra, com questionário vazio; nunca reescrever o evento.
    cmd,_=_abrir(sessao,str(uuid4()),'CONTA-B1','fixture_historica_ficticia',{})
    e=estado(sessao,obj);e.pop('versao');e.update(encerrada=True,situacao='Concluída com verificação')
    ev=_gravar_estado(sessao,cmd,sessao.get(IdentidadeForms34,obj),'encerramento_automatico',e)
    fechar_comando(cmd,{'permitido':True});sessao.commit()
    antes=deepcopy(ev.conteudo)
    assert not conferencia34(4,e)['pronto']
    r=TestClient(app).get(f'/forms34/{obj}/blocos/1?conta_id=CONTA-B1')
    assert r.status_code==200 and 'Ação concluída automaticamente em ' in r.text
    assert 'após a verificação aprovada' in r.text and 'Sistema' in r.text
    sessao.refresh(ev)
    assert ev.conteudo==antes and estado(sessao,obj)['encerrada']



def test_salvar_parcial_nao_aciona_encerramento(sessao,entrada):
    from app.fluxo_forms34 import _gravar_estado
    from app.infra_forms34 import _abrir
    from app.comandos import fechar_comando
    from app.modelos import IdentidadeForms34
    obj=entrar(sessao,entrada,4)
    cmd,_=_abrir(sessao,str(uuid4()),'CONTA-B1','fixture_verificacao_ficticia',{})
    e=estado(sessao,obj);e.pop('versao');e.update(verificada=True)
    _gravar_estado(sessao,cmd,sessao.get(IdentidadeForms34,obj),'verificar',e)
    fechar_comando(cmd,{'permitido':True});sessao.commit()
    from app.questionario_forms34 import perguntas
    bloco=next(q['bloco'] for q in perguntas(4) if q['id']=='F4-4.3')
    ato(sessao,obj,'salvar_bloco',bloco=bloco,campos={'F4-4.3':''})
    e=estado(sessao,obj)
    assert e['respostas']['F4-4.3']=='' and not e.get('encerrada')


def test_conjunto_adicional_e_comentario_nao_substitui_resposta():
    c=completo2()
    c['rascunho_form2_rev21_2']['8']['texto:F2-8.2#2']=''
    c['rascunho_form2_rev21_2']['8']['comentario:F2-8.2']='Comentário fictício'
    c['rascunho_form2_rev21_2']['8']['opcao:F2-8.1']=['SIM']
    r=conferencia2(c)
    assert any(q['item']=='F2-8.2#2' for q in r['faltantes'])


def test_a_confirmar_arquivado_no_form2_permanece_na_lista():
    c={'respostas_inativas_rev212':{'10':{'opcao:F2-10.3':['A_CONFIRMAR']}}}
    r=conferencia2(c)
    assert any(q['item']=='F2-10.3' for q in r['a_confirmar'])
    assert 'F2-10.3' not in [q['item'] for q in r['faltantes']]
