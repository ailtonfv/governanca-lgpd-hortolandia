"""12-F: atos futuros, versão preservada e responsabilidades separadas."""
from uuid import uuid4
import pytest
from app.fluxo_forms34 import estado
from app.obrigatoriedade_forms import FormularioIncompleto
from app.fila_form2 import executar as fila
from app.etapas_forms34 import VERIFICACAO
from app.atos_forms34_interface import disponiveis
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, avaliar, SECRETARIO, VERIFICADOR, RELATOR
from testes.apoio_r17 import preencher34


def concluir2(s, p, conta='CONTA-B1'):
    r = fila(s, conta_id=conta, comando_id=str(uuid4()), participacao_id=p.id,
             versao=p.versao, acao='concluir', texto='Resultado fictício, com pendências visíveis')
    s.commit()
    return r


def test_form2_conclusao_preserva_pendencias_e_encaminhamento(sessao, entrada):
    concluir2(sessao, entrada)
    c = entrada.conteudo['conclusao_analise']
    assert entrada.estado == 'concluida'
    assert c['snapshot_id'] == entrada.snapshot_id
    assert c['conferencia_r17']['quantidade_a_confirmar'] > 0
    obj = entrar(sessao, entrada)
    assert estado(sessao, obj)['situacao_form2'] == 'concluida'
    from app.fila_form2 import salvar_bloco
    with pytest.raises(PermissionError):
        salvar_bloco(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),participacao_id=entrada.id,
                     versao=entrada.versao,bloco=1,campos={})
    from fastapi.testclient import TestClient
    from app.main import app
    texto=TestClient(app).get(f'/form2/participacoes/{entrada.id}?conta_id=CONTA-B1').text
    assert 'Conclusão da etapa de análise; não equivale a homologação jurídica.' in texto


def test_form2_conclusao_recusa_vazio_e_pessoa_errada(sessao, entrada):
    with pytest.raises(PermissionError):concluir2(sessao, entrada, 'CONTA-A1')
    sessao.rollback()
    entrada.conteudo = {}
    sessao.commit()
    with pytest.raises(FormularioIncompleto):concluir2(sessao, entrada)


def test_risco_concluido_protegido_ripd_complementar_e_reavaliacao(sessao, entrada):
    obj = entrar(sessao, entrada)
    preencher34(sessao, obj)
    avaliar(sessao, obj, 1)
    ato(sessao,obj,'propor_triagem',resultado='nao_indicado',justificativa='Triagem fictícia')
    ato(sessao,obj,'confirmar_triagem',conta='CONTA-E1')
    with pytest.raises(ValueError, match='autoridade'):ato(sessao, obj, 'concluir_avaliacao')
    ato(sessao, obj, 'aceitar_residual', conta=SECRETARIO, justificativa='Decisão fictícia')
    ato(sessao, obj, 'concluir_avaliacao')
    anterior = estado(sessao, obj)['conclusao']
    with pytest.raises(ValueError, match='concluída'):
        ato(sessao, obj, 'salvar_bloco', bloco=16, campos={})
    ato(sessao, obj, 'informar_ripd', referencia='Processo fictício RIPD-01')
    assert estado(sessao, obj)['conclusao'] == anterior
    ato(sessao, obj, 'revisar_avaliacao', evento='Evento fictício revisto', causa='Causa fictícia',
        consequencia='Consequência fictícia', p=2, i=2, pr=2, ir=2, justificativa='Revisão fictícia', controles=[])
    e = estado(sessao, obj)
    assert not e['concluida'] and e['conclusoes_anteriores'][-1] == anterior
    assert e['avaliacao']['residual']['nota'] == 1


def test_comite_recusa_duplicidade_na_rodada(sessao, entrada):
    obj = entrar(sessao, entrada)
    avaliar(sessao, obj, 5)
    ato(sessao, obj, 'manifestar_comite', conta=RELATOR, finalidade='residual', ata='Ata fictícia', texto='Deliberação fictícia', favoravel=True)
    with pytest.raises(ValueError, match='Finalidade'):
        ato(sessao, obj, 'manifestar_comite', conta=RELATOR, finalidade='residual', ata='Outra ata fictícia', texto='Duplicada fictícia', favoravel=True)
    assert not any(a['acao']=='manifestar_comite' for a in disponiveis(3,14,{'relator'},estado(sessao,obj)))
    ato(sessao,obj,'revisar_avaliacao',evento='Evento fictício revisto',causa='Causa fictícia',
        consequencia='Consequência fictícia',p=5,i=5,pr=5,ir=5,justificativa='Revisão fictícia',controles=[])
    ato(sessao,obj,'confirmar_avaliacao',conta='CONTA-E1')
    from app.regras_atos34 import finalidades
    assert 'residual' in finalidades(estado(sessao,obj))


def test_verificacao_e_aprendizagem_separadas_do_plano(sessao, entrada):
    obj = entrar(sessao, entrada, 4)
    preencher34(sessao, obj)
    ato(sessao, obj, 'planejar', plano='Plano fictício para revisar e documentar os acessos.', cargo='Equipe da unidade executora', duracao_dias=30)
    ato(sessao, obj, 'aprovar_plano', conta=SECRETARIO, justificativa='Aprovação fictícia')
    with pytest.raises(ValueError, match='Plano aprovado'):
        ato(sessao, obj, 'salvar_bloco', bloco=1, campos={})
    ato(sessao, obj, 'executar_medida', resumo='Execução fictícia: acessos revisados e documentados.', evidencia='Processo fictício 01')
    with pytest.raises(ValueError):ato(sessao,obj,'aprender',contexto='Fictício',diretriz='Fictícia',escopo='Fictício')
    with pytest.raises(ValueError):ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Verificação fictícia')
    respostas={k:('Sim' if k=='F4-4.22' else 'A confirmar') for k in VERIFICACAO}
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Verificação fictícia',**respostas)
    e=estado(sessao,obj)
    assert e['execucao']['evidencia']=='Processo fictício 01'
    assert e['execucao']['cargo_responsavel']=='Equipe da unidade executora'
    assert e['execucao']['unidade_responsavel_id']
    assert e['verificacao']['quantidade_a_confirmar']==3
    assert e['verificacao']['pessoa_id'] != e['execucao']['pessoa_id']
    ato(sessao,obj,'aprender',contexto='Contexto fictício',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True,sem_falha_exposta=True)
    ato(sessao,obj,'autorizar_aprendizagem')
    ato(sessao,obj,'aprender',contexto='Contexto fictício revisto',diretriz='Diretriz fictícia',escopo='Limites fictícios')
    assert not estado(sessao,obj).get('aprendizagem_conferida')
    assert not estado(sessao,obj).get('aprendizagem_autorizada')


def test_interface_nao_oferece_aprendizagem_antes_da_verificacao():
    e={'form':4,'execucao':{'evidencia':'Fictícia'}}
    assert not disponiveis(4,9,{'secretaria'},e,'PESSOA-B')
    e['verificada']=True
    assert not disponiveis(4,9,{'secretaria'},e,'PESSOA-B')
    e['encerrada']=True
    e['verificacao']={'respostas':{'F4-4.22':'Sim'}}
    assert [a['acao'] for a in disponiveis(4,9,{'secretaria'},e,'PESSOA-B')]==['aprender']


def test_nova_origem_confirmada_reabre_preservando_conclusao(sessao, entrada):
    from testes.test_governanca_form2_v9 import segunda, ato as governar
    concluir2(sessao,entrada)
    anterior=entrada.conteudo['conclusao_analise'].copy()
    nova=segunda(sessao,entrada)
    sessao.commit()
    governar(sessao,entrada,'fonte',snapshot_id=nova)
    assert entrada.estado=='em_atendimento' and entrada.concluida_em is None
    assert entrada.snapshot_id==nova
    assert entrada.conteudo['conclusoes_anteriores'][-1]==anterior
    assert 'conclusao_analise' not in entrada.conteudo


def test_tela_verificacao_historico_e_aprendizagem(sessao, entrada):
    from fastapi.testclient import TestClient
    from app.main import app
    from html.parser import HTMLParser
    obj=entrar(sessao,entrada,4)
    preencher34(sessao,obj)
    ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Chefia da unidade',duracao_dias=30)
    ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    ato(sessao,obj,'executar_medida',resumo='Execução fictícia: acessos revisados e documentados.',evidencia='Referência fictícia 12F')
    client=TestClient(app)
    tela=client.get(f'/forms34/{obj}/blocos/7?conta_id=CONTA-B1')
    assert tela.status_code==200
    assert 'Referência fictícia 12F' in tela.text
    assert 'Salvar bloco 7' not in tela.text
    assert 'Responsável pela verificação' in tela.text
    assert 'As perguntas seguem a numeração do documento-mestre (F4 = FORM 4).' in tela.text
    assert 'Aguardando verificação por membro' in tela.text
    verificador=client.get(f'/forms34/{obj}/blocos/7?conta_id={VERIFICADOR}')
    assert verificador.status_code==200
    for k in VERIFICACAO:assert f'name="{k}"' in verificador.text
    aprendizagem=client.get(f'/forms34/{obj}/blocos/9?conta_id=CONTA-B1').text
    assert 'value="aprender"' not in aprendizagem
    assert 'A aprendizagem pode ser registrada depois da verificação da ação.' in aprendizagem
    todos=client.get(f'/forms34/{obj}/blocos/6?conta_id=CONTA-B1&filtrar=1&historico=todos').text
    class Historico(HTMLParser):
        def __init__(self):super().__init__();self.salvos=[];self.soltos=[]
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='li' and attrs.get('data-historico-ato')=='nao':self.salvos.append(attrs)
        def handle_data(self,d):
            if d.strip()=='*':self.soltos.append(d)
    parsed=Historico();parsed.feed(todos)
    assert parsed.salvos and all('hidden' not in h for h in parsed.salvos)
    # Marcadores em spans de campos não são asteriscos soltos no topo.
    topo=todos.split('<h1>',1)[1].split('<section',1)[0]
    assert '>*<' not in topo


def test_plano_incompleto_recusado_antes_aprovacao(sessao,entrada):
    obj=entrar(sessao,entrada,4)
    ato(sessao,obj,'planejar',plano='Plano fictício para revisar e documentar os acessos.',cargo='Chefia da unidade',duracao_dias=30)
    with pytest.raises(FormularioIncompleto):
        ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    assert not estado(sessao,obj).get('plano_aprovado')


def test_origem_da_acao_congelada_e_outro_encaminhamento_explicito(sessao,entrada):
    from app.modelos import IdentidadeForms34, ReferenciaParticipacaoForms34
    risco=entrar(sessao,entrada)
    preencher34(sessao,risco)
    avaliar(sessao,risco,1)
    acao=ato(sessao,risco,'encaminhar_acao',justificativa='Providência fictícia')['identidade_id']
    ref=sessao.get(ReferenciaParticipacaoForms34,sessao.get(IdentidadeForms34,acao).participacao_id)
    original=ref.fonte_canonica
    with pytest.raises(ValueError,match='Reavaliar'):
        ato(sessao,risco,'salvar_bloco',bloco=16,campos={})
    oferecidos=disponiveis(3,16,{'aal','secretaria'},estado(sessao,risco),'PESSOA-B')
    outro=next(a for a in oferecidos if a['acao']=='encaminhar_acao')
    assert outro['titulo']=='Encaminhar outra providência' and outro['recolhido']
    assert ato(sessao,risco,'encaminhar_acao',justificativa='Clique repetido fictício')['identidade_id']==acao
    nova=ato(sessao,risco,'encaminhar_acao',justificativa='Outra providência fictícia',outra=True)['identidade_id']
    assert nova!=acao
    ato(sessao,risco,'revisar_avaliacao',evento='Evento fictício revisto',causa='Causa fictícia',
        consequencia='Consequência fictícia',p=2,i=2,pr=2,ir=2,justificativa='Revisão fictícia',controles=[])
    ato(sessao,risco,'confirmar_avaliacao',conta='CONTA-E1')
    sessao.refresh(ref)
    assert ref.fonte_canonica==original


def test_legado_verificado_sem_cobrar_plano_da_secretaria(sessao,entrada):
    from app.fluxo_forms34 import _gravar_estado
    from app.infra_forms34 import _abrir
    from app.comandos import fechar_comando
    from app.modelos import IdentidadeForms34
    from copy import deepcopy
    obj=entrar(sessao,entrada,4)
    e=estado(sessao,obj);e.pop('versao')
    e.update(plano_aprovado={'pessoa_id':'PESSOA-DEMO34-SECULT','em':'2026-11-19T14:51:00-03:00'},
             execucao={'pessoa_id':'PESSOA-B','em':'2026-11-19T15:39:00-03:00','evidencia':'Referência fictícia legada'})
    cmd,_=_abrir(sessao,str(uuid4()),'CONTA-B1','fixture_legada_ficticia',{})
    ev=_gravar_estado(sessao,cmd,sessao.get(IdentidadeForms34,obj),'executar_medida',e)
    fechar_comando(cmd,{'permitido':True});sessao.commit()
    anterior=deepcopy(ev.conteudo)
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=False,evidencia='Ajustes fictícios',**{k:'Não' for k in VERIFICACAO})
    with pytest.raises(ValueError,match='verificação aprovada'):
        ato(sessao,obj,'aprender',contexto='Fictício',diretriz='Fictícia',escopo='Fictício')
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Conferência fictícia',**{k:'Sim' for k in VERIFICACAO})
    sessao.refresh(ev)
    assert ev.conteudo==anterior and estado(sessao,obj)['encerrada']
    assert not estado(sessao,obj)['respostas'].get('F4-4.3')
