"""Migração e demonstração exclusivamente com massa fictícia."""
from copy import deepcopy
from sqlalchemy import select
from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.rev22_form1 import adotar,salvar,definicoes,NOVOS
from app.modelos import RascunhoForm1Integral,VersaoForm1Integral,ParticipacaoForm2,Designacao
from testes.test_conferencia_interna_form1_integral_8ac import _preparar
from testes.test_filas_form2_rev22 import origem
from app.fila_form2 import executar,salvar_bloco
from app.respostas_form2 import definicao_revisao,aplicar_revisao
from app.form2_rev212 import RASCUNHO

def test_equivalencia_nao_reinterpreta_respostas_antigas():
    from app.rev22_form1 import migrar,EQUIVALENCIA
    from app.extensao_medidas_form1 import catalogo_efetivo
    old={'respostas':{'9.2.1':'Histórico fictício','4.1':['A confirmar'],'8.7':'A confirmar','10.4':['Dado fictício']},'participantes':[{'respostas':{'3.3':'Unidade fictícia'}}]}
    before=deepcopy(old);new=migrar(old,catalogo_efetivo())
    assert old==before
    assert '9.2.1' not in new['respostas'] and new['revisao_22']['legado']['9.2.1']=='Histórico fictício'
    assert new['revisao_22']['participantes_anteriores']==old['participantes']
    assert '4.1' not in new['respostas'] and '10.4' not in new['respostas']
    for a,b in EQUIVALENCIA.items():assert a not in new['respostas']
    assert not set(NOVOS)&set(new['respostas'])

def test_adocao_preserva_snapshot_e_controla_versao(sessao):
    r=_preparar(sessao,'REV22');rid=r['registro_id'];draft=sessao.get(RascunhoForm1Integral,rid)
    old=deepcopy(draft.conteudo)
    args=dict(conta_id='CONTA-G1',comando_id='ADOTA22',registro_id=rid,versao_lida=draft.versao_rascunho,confirmar=True)
    assert adotar(sessao,**args)['permitido']
    assert adotar(sessao,**args)['reexecutado']
    assert len(definicoes())==145
    assert not set(NOVOS)&set(draft.conteudo['respostas'])
    snap=sessao.get(VersaoForm1Integral,draft.conteudo['revisao_22']['snapshot_anterior_id'])
    assert snap is not None
    assert old==snap.conteudo['form1_integral']
    versao=draft.versao_rascunho
    assert not salvar(sessao,conta_id='CONTA-A1',comando_id='NEGADO22',registro_id=rid,versao_lida=versao,bloco=4,respostas={})['permitido']
    assert not salvar(sessao,conta_id='CONTA-G1',comando_id='VELHO22',registro_id=rid,versao_lida=versao-1,bloco=4,respostas={})['permitido']
    q=definicoes()['4.1.1'];valor=q['options'][0]
    assert salvar(sessao,conta_id='CONTA-G1',comando_id='IDADE22',registro_id=rid,versao_lida=versao,bloco=4,respostas={'4.1.1':[valor]})['permitido']
    assert draft.conteudo['respostas']['4.1.1']==[valor]
    sessao.commit()
    c=TestClient(app)
    for b in range(1,15):
        response=c.get(f'/registros/{rid}/form1-rev22?conta_id=CONTA-G1&bloco={b}')
        assert response.status_code==200,response.text
    assert c.get(f'/registros/{rid}?conta_id=CONTA-G1').status_code==200
    from app.conferencia_interna_form1_integral import solicitar_conferencia_interna_form1_integral,confirmar_conferencia_interna_form1_integral
    sessao.refresh(draft)
    v=draft.versao_rascunho
    assert solicitar_conferencia_interna_form1_integral(sessao,conta_id='CONTA-G1',comando_id='PRESENT22',registro_id=rid,versao_lida=v)['permitido']
    sessao.commit()
    assert c.get(f'/registros/{rid}/form1-integral/conferencia-interna?conta_id=CONTA-A1').status_code==200
    assert confirmar_conferencia_interna_form1_integral(sessao,conta_id='CONTA-A1',comando_id='CONF22',registro_id=rid,versao_lida=1)['permitido']
    sessao.commit()
    participation=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id==rid))
    from app.origem_form2 import ler_origem
    leitura=ler_origem(sessao,rid,participation.snapshot_id)
    assert leitura['conteudo']['respostas']['4.1.1']==[valor]
    assert leitura['estrutura']=='F1-C3-REV22-CANDIDATA-v1'
    assert ler_origem(sessao,rid,snap.id)['conteudo']==old

def test_canais_adicionais_e_conjuntos_independentes(sessao):
    from app.rev22_form1 import ativa
    assert ativa('OUV.1',{'2.1':'Telefone','2.1.1':['Ouvidoria']})
    assert ativa('WPP.3',{'2.1':'Telefone','2.1.1':['WhatsApp pessoal'],'WPP.2':'Sempre'})
    r=_preparar(sessao,'CONJ22');rid=r['registro_id'];d=sessao.get(RascunhoForm1Integral,rid)
    adotar(sessao,conta_id='CONTA-G1',comando_id='AD-C22',registro_id=rid,versao_lida=d.versao_rascunho,confirmar=True)
    def save(id,bloco,valores,conjunto=None):
        return salvar(sessao,conta_id='CONTA-G1',comando_id=id,registro_id=rid,versao_lida=d.versao_rascunho,bloco=bloco,respostas=valores,conjunto=conjunto)
    assert save('OPEN3',3,{'3.1':'Sim'})['permitido']
    q=definicoes()['3.3'];assert q['kind']=='text'
    assert save('C1',3,{'3.3':'Unidade fictícia um'},1)['permitido']
    assert save('C2',3,{'3.3':'Unidade fictícia dois'},2)['permitido']
    rows=d.conteudo['conjuntos_rev22']['3']
    assert rows[0]['id']!=rows[1]['id']
    assert rows[0]['respostas']['3.3']!=rows[1]['respostas']['3.3']

def test_migracao_invalida_nao_grava_parcial(sessao):
    r=_preparar(sessao,'ROLL22');rid=r['registro_id'];d=sessao.get(RascunhoForm1Integral,rid)
    adotar(sessao,conta_id='CONTA-G1',comando_id='A22',registro_id=rid,versao_lida=d.versao_rascunho,confirmar=True);sessao.commit()
    before=deepcopy(d.conteudo);v=d.versao_rascunho
    with pytest.raises(ValueError):salvar(sessao,conta_id='CONTA-G1',comando_id='BAD22',registro_id=rid,versao_lida=v,bloco=4,respostas={'4.1.1':['INEXISTENTE']})
    sessao.rollback();assert sessao.get(RascunhoForm1Integral,rid).conteudo==before

def test_controles_candidatos_sem_homologacao(sessao):
    r=origem(sessao);p=sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id==r['registro_id']))
    sessao.add(Designacao(pessoa_id='PESSOA-B',unidade_id='UNID-NORTE',papel='aal_form2',ativa=True));sessao.commit()
    executar(sessao,conta_id='CONTA-B1',comando_id='ASS22',participacao_id=p.id,acao='assumir',versao=1);sessao.commit()
    c=TestClient(app)
    for b,id in [(2,'F2-2.1'),(3,'F2-3.1'),(14,'F2-14.1')]:
        q=next(q for q in definicao_revisao(b)['itens'] if q['id']==id)
        name='opcao:'+id;value=q['alternativas'][0]['codigo']
        assert name in c.get(f'/form2/participacoes/{p.id}/blocos/{b}?conta_id=CONTA-B1').text
        sessao.refresh(p)
        args=dict(conta_id='CONTA-B1',comando_id='SAVE22-'+str(b),participacao_id=p.id,versao=p.versao,bloco=b,campos={name:[value]})
        assert salvar_bloco(sessao,**args)['permitido'];assert salvar_bloco(sessao,**args)['reexecutado'];sessao.commit()
        assert p.conteudo[RASCUNHO][str(b)][name]==[value]
    assert p.conteudo['regime_respostas']['homologado'] is False
    with pytest.raises((ValueError,PermissionError)):
        executar(sessao,conta_id='CONTA-B1',comando_id='CLOSE22',participacao_id=p.id,acao='concluir',versao=p.versao,texto='Ensaio fictício')
    with pytest.raises(ValueError):aplicar_revisao({},3,{'opcao:F2-3.1':['ALT_01']})
