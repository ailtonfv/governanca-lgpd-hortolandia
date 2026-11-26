"""Aceite do Lote 15 com dados fictícios; nenhuma consulta à base da vistoria."""
from copy import deepcopy
from datetime import datetime, timezone
from sqlalchemy import select, func
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from app.main import app
from app.modelos import Registro, RascunhoForm1Integral
from app.etapa_registro import decidir_etapa
from app.rev22_form1 import contagem_blocos, ativa
from testes.apoio import g1, CADASTRO
from testes.test_conferencia_interna_form1_integral_8ac import _preparar


def test_etapa_atual_cenarios_aprovados():
    data=datetime(2026,11,20,tzinfo=timezone.utc)
    f1=dict(estado='Em preenchimento',desde=data,responsavel='Alfa (ARP)')
    p=dict(estado='em_atendimento',entrada_em=data,assumida_em=data,concluida_em=None,responsavel='Beta (AAL)')
    assert decidir_etapa(f1,[],[])['responsavel']=='Alfa (ARP)'
    assert decidir_etapa(f1,[p],[])['responsavel']=='Beta (AAL)'
    sem={**p,'responsavel':None,'assumida_em':None}
    assert decidir_etapa(f1,[sem],[])['situacao']=='Aguardando atribuição de AAL pelo gestor da fila (APA)'
    acao=dict(form=4,estado=dict(verificada=True,aprendizagem_autorizada=dict(em=data.isoformat())))
    etapa=decidir_etapa(f1,[p],[acao])
    assert etapa['form']=='Ciclo completo' and etapa['responsavel'] is None
    assert etapa['desde'].startswith('2026-11-20')


def test_contagem_ativas_sem_r17():
    inicio=contagem_blocos({'respostas':{'1.2':'Tipo fictício','1.3':'Nome fictício'}})[1]
    assert inicio['respondidas']==1 and 'Em preenchimento' in inicio['texto']  # C173: nome editável conta.
    nao=contagem_blocos({'respostas':{'1.1':'Não'}})[1]
    sim=contagem_blocos({'respostas':{'1.1':'Sim'}})[1]
    assert sim['ativas']==nao['ativas']+1
    assert sim['respondidas']==1 and 'perguntas respondidas' in sim['texto']
    assert contagem_blocos({'respostas':{'1.1':'A confirmar'}})[1]['respondidas']==1
    assert contagem_blocos({'respostas':{'1.1':'Sem resposta'}})[1]['respondidas']==0
    assert not ativa('OUV.1',{})


def test_entrada_condicoes_e_ajudas(sessao):
    r=_preparar(sessao,'L15-F1');rid=r['registro_id'];sessao.commit()
    cliente=TestClient(app)
    url=f'/registros/{rid}/form1-rev22?conta_id=CONTA-G1'
    pagina=cliente.get(url)
    assert pagina.status_code==200
    assert 'Preparar o FORM 1 para preenchimento' not in pagina.text
    assert 'Escolha um bloco para preencher.' in pagina.text
    assert 'condicoes_rev22.js' in pagina.text and 'data-condicao-pergunta="1.1.1"' in pagina.text
    assert 'obrigatórias' not in pagina.text
    assert 'Entenda esta pergunta' in cliente.get(url+'&bloco=13').text
    for bloco,topico in [(8,'WhatsApp e dispositivos pessoais'),(10,'Fotografias, vídeos, voz e comunicação institucional')]:
        tela=cliente.get(url+f'&bloco={bloco}').text
        assert 'Na Cartilha:</strong> '+topico in tela
        assert 'seção 6.10' not in tela


def test_central_papel_dashboard_e_aviso_unico(sessao):
    from app.modelos import Designacao
    sessao.add(Designacao(pessoa_id='PESSOA-B', unidade_id='UNID-NORTE', papel='aal_form2', ativa=True))
    sessao.commit()
    tela=TestClient(app).get('/central?conta_id=CONTA-B1').text
    assert '· AAL</dd>' in tela
    assert 'Administração Central — TI' not in tela
    assert tela.count('Não equivale a homologação institucional.')==1
    assert 'href="/dashboard?conta_id=CONTA-B1">Acessar Dashboard</a>' in tela


def test_duplicidade_contexto_e_justificativa(sessao):
    primeiro=g1('L15-G1',CADASTRO,'CTX-TRIB-01')
    bloqueado=g1('L15-REPETIDO',CADASTRO,'CTX-TRIB-01',justificativa='Justificativa fictícia')
    assert not bloqueado['permitido'] and primeiro['codigo_lgpd'] in bloqueado['motivo']
    assert 'trava do banco' not in bloqueado['motivo']
    # Um contexto diferente já autorizado para o item na massa fictícia.
    from app.modelos import ObjetoContextoCatalogo, ContextoAtuacao
    contexto=sessao.scalar(select(ContextoAtuacao).join(ObjetoContextoCatalogo,ObjetoContextoCatalogo.contexto_id==ContextoAtuacao.id).where(
        ObjetoContextoCatalogo.objeto_id==CADASTRO, ContextoAtuacao.id!='CTX-TRIB-01'))
    assert contexto is not None
    recusado=g1('L15-OUTRO-SEM',CADASTRO,contexto.id)
    assert not recusado['permitido'] and 'justificativa' in recusado['motivo']
    aceito=g1('L15-OUTRO-COM',CADASTRO,contexto.id,resolucao_familia='tratamento_autonomo',justificativa='Tratamento autônomo fictício')
    assert aceito['permitido']


def test_criacao_incompleta_nao_grava(sessao):
    antes=sessao.scalar(select(func.count()).select_from(Registro))
    response=TestClient(app).post('/registros',data=dict(conta_id='CONTA-A1',comando_id='L15-INCOMPLETO',unidade_id='UNID-NORTE',tipo_objeto='servico'))
    assert response.status_code==200 and 'Revise os campos' in response.text
    assert sessao.scalar(select(func.count()).select_from(Registro))==antes
