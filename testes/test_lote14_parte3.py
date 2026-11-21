"""Aprendizado público sem abrir a origem; leitura da unidade sem novos atos."""
import pytest
from sqlalchemy import select
from app.main import app
from app.modelos import Designacao
from app.dashboard.fontes import escopo_da_conta
from app.aprendizados_publicos import consultar
from app.fluxo_forms34 import consultar as consultar_objeto
from app.etapas_forms34 import VERIFICACAO
from testes.apoio_entrada import ClienteAposApresentacao as TestClient
from testes.test_lote12 import entrada, fonte, protecoes, entrar, ato, SECRETARIO, VERIFICADOR
from testes.apoio_r17 import preencher34


def test_apa_dashboard_unidade_travada(sessao, entrada):
    escopo = escopo_da_conta(sessao, 'CONTA-A1')
    assert escopo.perfil == 'APA' and escopo.unidades == {entrada.unidade_id}
    c = TestClient(app)
    pagina = c.get('/dashboard?conta_id=CONTA-A1')
    assert pagina.status_code == 200 and 'Pendências da sua Secretaria' in pagina.text
    assert c.get('/dashboard?conta_id=CONTA-A1&secretaria=UNID-SUL').status_code == 403


def test_leitor_unidade_nao_ganha_ato(sessao, entrada):
    obj = entrar(sessao, entrada)
    assert 'leitor_unidade' in consultar_objeto(sessao, 'CONTA-A1', obj)[4]
    with pytest.raises(PermissionError):
        ato(sessao, obj, 'salvar_bloco', conta='CONTA-A1', bloco=1, campos={})
    with pytest.raises(PermissionError):
        consultar_objeto(sessao, 'CONTA-C1', obj)


def test_aprendizado_outra_secretaria_sem_acesso_origem(sessao, entrada):
    risco = entrar(sessao, entrada)
    obj = entrar(sessao, entrada, 4)
    preencher34(sessao, obj)
    ato(sessao,obj,'planejar',plano='Plano fictício',cargo='Equipe da unidade executora',prazo='2027-01-15')
    ato(sessao,obj,'aprovar_plano',conta=SECRETARIO,justificativa='Aprovação fictícia')
    ato(sessao,obj,'executar_medida',resumo='Execução fictícia',evidencia='EVIDENCIA-NAO-PUBLICAVEL-FICTICIA')
    ato(sessao,obj,'verificar',conta=VERIFICADOR,aprovada=True,evidencia='Conferência fictícia',**{k:'Sim' for k in VERIFICACAO})
    ato(sessao,obj,'aprender',contexto='Contexto fictício autorizado',diretriz='Diretriz fictícia autorizada',escopo='Limites fictícios')
    assert consultar(sessao,'CONTA-C1')['total'] == 0
    ato(sessao,obj,'conferir_aprendizagem',conta='CONTA-E1',sem_dados_pessoais=True)
    assert consultar(sessao,'CONTA-C1')['total'] == 0
    ato(sessao,obj,'autorizar_aprendizagem')
    # Secretário passa a representar exclusivamente outra Secretaria fictícia.
    for d in sessao.scalars(select(Designacao).where(Designacao.pessoa_id=='PESSOA-DEMO34-SECULT')):
        d.ativa=False
    sessao.add(Designacao(pessoa_id='PESSOA-DEMO34-SECULT',unidade_id='UNID-SUL',papel='demo34_secretario',ativa=True))
    sessao.commit()
    c=TestClient(app)
    for conta in ('CONTA-C1',SECRETARIO,'CONTA-D1'):
        pagina=c.get('/dashboard/aprendizados',params={'conta_id':conta,'secretaria':entrada.unidade_id,'palavra':'Diretriz'})
        assert pagina.status_code==200 and 'Diretriz fictícia autorizada' in pagina.text
        assert 'EVIDENCIA-NAO-PUBLICAVEL-FICTICIA' not in pagina.text
        assert '/forms34/' not in pagina.text and '/registros/' not in pagina.text
    for caminho in (f'/forms34/{obj}/blocos/1',f'/forms34/{risco}/blocos/1',f'/registros/{entrada.registro_id}'):
        assert c.get(caminho,params={'conta_id':SECRETARIO}).status_code==403
    assert consultar(sessao,SECRETARIO,palavra='inexistente')['total']==0
    ato(sessao,obj,'aprender',contexto='Rascunho novo fictício',diretriz='NAO-PUBLICAR-NOVA',escopo='Limites fictícios')
    publicado=consultar(sessao,SECRETARIO)
    assert publicado['total']==1 and publicado['destaque']['diretriz']=='Diretriz fictícia autorizada'
