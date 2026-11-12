"""Percurso v9 e recusas. Massa fictícia; banco exclusivo _teste."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from fastapi.testclient import TestClient
from app.main import app
from app.modelos import (ParticipacaoForm2, AvisoDpo, Designacao, VersaoForm1Integral,
    ComplementoForm2, Comando, Evento, Conta, RascunhoForm1Integral)
from app.fila_form2 import executar, salvar_bloco, importar_confirmada
from app.governanca_form2_v9 import executar as agir, estado, resumo, CHAVE
from testes.test_filas_form2_rev22 import origem
from testes.test_conferencia_interna_form1_integral_8ac import _solicitar
from testes.test_confirmacao_conferencia_form1_integral_8ag import _confirmar
from testes.test_devolucao_reapresentacao_form1_integral_8af import _salvar_ajuste


@pytest.fixture
def principal(sessao):
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r['registro_id']))
    sessao.add(Designacao(pessoa_id='PESSOA-B', unidade_id='UNID-NORTE', papel='aal_form2', ativa=True))
    sessao.commit()
    executar(sessao, conta_id='CONTA-B1', comando_id='V9-ASSUME', participacao_id=p.id, acao='assumir', versao=p.versao)
    sessao.commit()
    return p


def salvar(sessao, p, bloco=1, campos=None):
    resultado = salvar_bloco(sessao, conta_id='CONTA-B1', comando_id=str(uuid4()),
        participacao_id=p.id, versao=p.versao, bloco=bloco,
        campos=campos or {'F2-1.2':'CONFIRMADA', 'F2-1.3':'PARCIAL', 'F2-1.3.1':'Complemento fictício do fluxo.'})
    sessao.commit()
    return resultado


def ato(sessao, p, acao, pend=None, conta='CONTA-B1', alvo=None, **dados):
    resultado = agir(sessao, conta_id=conta, comando_id=str(uuid4()), participacao_id=alvo or p.id,
        versao=p.versao, acao=acao, pendencia_id=pend, dados={'motivo':'Justificativa fictícia de teste.', **dados})
    assert resultado['permitido'], resultado
    sessao.commit()
    sessao.refresh(p)
    return resultado


def pendencia(sessao, p):
    salvar(sessao, p)
    return next(iter(estado(sessao,p)['pendencias']))


def segunda(sessao, p, confirmar=True):
    r={'registro_id':p.registro_id}
    ajuste=_salvar_ajuste(sessao,r,comando='V9-AJUSTE-'+str(uuid4()))
    assert ajuste['permitido'], ajuste
    s2=_solicitar(sessao,r,comando='V9-S2-'+str(uuid4()),versao=ajuste['versao_rascunho'])
    assert s2['permitido'], s2
    if confirmar:
        resultado=_confirmar(sessao,r,comando='V9-CONF-'+str(uuid4()))
        assert resultado['permitido'], resultado
    sessao.refresh(p)
    return s2['snapshot_id']


def consultar_dpo(sessao,p):
    c=executar(sessao,conta_id='CONTA-B1',comando_id=str(uuid4()),participacao_id=p.id,
        acao='consultar',versao=p.versao,tipo='dpo',unidade_id='UNID-GOV',texto='Questão fictícia sobre S1.')
    q=sessao.get(ParticipacaoForm2,c['participacao_id'])
    executar(sessao,conta_id='CONTA-E1',comando_id=str(uuid4()),participacao_id=q.id,acao='assumir',versao=q.versao)
    executar(sessao,conta_id='CONTA-E1',comando_id=str(uuid4()),participacao_id=q.id,acao='concluir',versao=q.versao,texto='Manifestação fictícia sobre S1.')
    sessao.commit()
    return q


def test_T05_lista_repetivel_e_idempotencia(sessao,principal):
    p=principal; ident=pendencia(sessao,p)
    args=dict(conta_id='CONTA-B1',comando_id='V9-IDEM',participacao_id=p.id,versao=p.versao,
        acao='adicionar',dados={'descricao':'Outra necessidade fictícia.','motivo':'Necessidade distinta.'})
    a=agir(sessao,**args);sessao.commit()
    b=agir(sessao,**args);sessao.commit()
    assert a['pendencia_id']==b['pendencia_id'] and b['reexecutado']
    assert len(estado(sessao,p)['pendencias'])==2
    assert ident in estado(sessao,p)['pendencias']


def test_T07_automatica_sem_area_e_vinculo_explicito(sessao,principal):
    p=principal; ident=pendencia(sessao,p)
    salvar(sessao,p,2,{'F2-2.9':'A_CONFIRMAR'})
    g=estado(sessao,p); auto=next(d for d in g['pendencias'].values() if d['id']!=ident)
    assert next(d for d in resumo(sessao,p)['pendencias'].values() if d['id']==auto['id'])['destinacao']=='Destinação pendente'
    ato(sessao,p,'vincular',ident,referencia=auto['id'])
    g=estado(sessao,p)
    assert g['pendencias'][auto['id']]['estado']=='vinculada'
    assert len(g['pendencias'][ident]['origens'])==2
    salvar(sessao,p,2,{'F2-2.9':'A_CONFIRMAR'})
    assert len([d for d in estado(sessao,p)['pendencias'].values() if d['estado']!='vinculada'])==1


def test_T08_T09_retorno_aceite_fonte_manifestacao_e_aviso(sessao,principal):
    p=principal; ident=pendencia(sessao,p); s1=p.snapshot_id
    anterior=consultar_dpo(sessao,p)
    conteudo=deepcopy(sessao.get(VersaoForm1Integral,s1).conteudo)
    s2=segunda(sessao,p)
    assert p.snapshot_id==s1
    assert sessao.scalar(select(func.count()).select_from(ParticipacaoForm2).where(ParticipacaoForm2.tipo=='principal'))==1
    assert sessao.scalar(select(func.count()).select_from(AvisoDpo).where(AvisoDpo.tipo=='ciencia'))==1
    ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    assert p.snapshot_id==s1
    ato(sessao,p,'aceitar',ident)
    assert p.snapshot_id==s1
    ato(sessao,p,'fonte',snapshot_id=s2)
    assert p.snapshot_id==s2
    chave=s2+':'+anterior.id
    ato(sessao,p,'impacto',impacto_id=chave,decisao='complemento_necessario')
    g=estado(sessao,p); nova=sessao.get(ParticipacaoForm2,g['impactos'][chave]['suplemento_id'])
    assert anterior.estado=='concluida' and anterior.snapshot_id==s1
    assert anterior.manifestacao=='Manifestação fictícia sobre S1.'
    assert nova.snapshot_id==s2 and nova.conteudo['reavalia_manifestacao_id']==anterior.id
    aviso=sessao.scalar(select(AvisoDpo).where(AvisoDpo.participacao_id==nova.id))
    assert aviso.metadados['complemento'] is True
    from app.avisos_dpo import entregar_pendentes
    caixa=[]
    entregar_pendentes(sessao,caixa.append,base_url='http://localhost:8001')
    entregar_pendentes(sessao,caixa.append,base_url='http://localhost:8001')
    assert len(caixa)==3
    assert sum('Complemento de manifestação' in m.get_content() for m in caixa)==1
    assert sessao.get(VersaoForm1Integral,s1).conteudo==conteudo
    executar(sessao,conta_id='CONTA-E1',comando_id=str(uuid4()),participacao_id=nova.id,acao='assumir',versao=nova.versao)
    executar(sessao,conta_id='CONTA-E1',comando_id=str(uuid4()),participacao_id=nova.id,acao='concluir',versao=nova.versao,texto='Complemento fictício sobre S2.')
    sessao.commit()
    assert estado(sessao,p)['impactos'][chave]['estado']=='complementada'


def test_E01_rejeicao_por_solicitacao(sessao,principal):
    p=principal; ident=pendencia(sessao,p); s2=segunda(sessao,p)
    ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    ato(sessao,p,'rejeitar',ident,motivo='Resposta fictícia insuficiente.')
    d=estado(sessao,p)['pendencias'][ident]
    assert d['estado']=='aberta' and d['snapshot_resposta_id']==s2
    assert d['historico'][-1]['motivo']=='Resposta fictícia insuficiente.'


def test_E03_E11_manter_S1_e_avaliar_nao_afetada(sessao,principal):
    p=principal; ident=pendencia(sessao,p); s1=p.snapshot_id; q=consultar_dpo(sessao,p)
    s2=segunda(sessao,p); ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    ato(sessao,p,'aceitar',ident); ato(sessao,p,'manter_fonte',snapshot_id=s2)
    ato(sessao,p,'impacto',impacto_id=s2+':'+q.id,decisao='nao_afetada')
    assert p.snapshot_id==s1 and q.snapshot_id==s1
    assert estado(sessao,p)['fontes'][-1]['decisao']=='manter_fonte'


def test_E04_consolidacao_expoe_reavaliacoes_sem_concluir(sessao,principal):
    from app.consolidacao_form2 import consultar, registrar
    p=principal; ident=pendencia(sessao,p); consultar_dpo(sessao,p);s2=segunda(sessao,p)
    ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    tela=consultar(sessao,conta_id='CONTA-B1',participacao_id=p.id)
    assert len(tela['resumo']['reavaliacoes_pendentes'])==2
    assert not tela['resumo']['conclusao_institucional_habilitada']
    assert registrar(sessao,conta_id='CONTA-B1',comando_id='V9-CONFERENCIA',participacao_id=p.id,
        versao=p.versao,hash_fontes=tela['hash_fontes'],sintese='Ensaio fictício com pontos abertos.')['permitido']


def test_E05_tela_desatualizada_e_rollback(sessao,principal,monkeypatch):
    p=principal; ident=pendencia(sessao,p); antes=p.versao
    ato(sessao,p,'destinar',ident,unidade_id='UNID-NORTE',prazo='2026-12-01')
    with pytest.raises(ValueError,match='Atualize'):
        agir(sessao,conta_id='CONTA-B1',comando_id='V9-VELHA',participacao_id=p.id,versao=antes,
            acao='retirar',pendencia_id=ident,dados={'motivo':'Fictício'})
    sessao.rollback()
    import app.fila_form2 as fluxo
    real=fluxo.evento
    def falhar(*args,**kwargs):
        real(*args,**kwargs); raise RuntimeError('falha fictícia')
    monkeypatch.setattr(fluxo,'evento',falhar)
    with pytest.raises(RuntimeError):
        agir(sessao,conta_id='CONTA-B1',comando_id='V9-ROLLBACK',participacao_id=p.id,versao=p.versao,
            acao='retirar',pendencia_id=ident,dados={'motivo':'Fictício'})
    sessao.rollback();sessao.refresh(p)
    assert estado(sessao,p)['pendencias'][ident]['estado']=='aberta'
    assert sessao.get(Comando,'V9-ROLLBACK') is None


def test_E06_confirmador_e_outra_conta_da_mesma_pessoa(sessao,principal):
    p=principal
    sessao.add(Designacao(pessoa_id='PESSOA-A',unidade_id='UNID-NORTE',papel='aal_form2',ativa=True))
    sessao.add(Conta(id='CONTA-A-ALIAS',pessoa_id='PESSOA-A',ativa=True))
    sessao.commit()
    for conta in ('CONTA-A1','CONTA-A-ALIAS'):
        with pytest.raises(PermissionError,match='segregação'):
            executar(sessao,conta_id=conta,comando_id=str(uuid4()),participacao_id=p.id,acao='assumir',versao=p.versao)
        sessao.rollback()


def test_E07_relogio_prazo_e_reatribuicao(sessao,principal,monkeypatch):
    import app.governanca_form2_v9 as gov
    p=principal; ident=pendencia(sessao,p)
    ato(sessao,p,'destinar',ident,unidade_id='UNID-NORTE',prazo='2026-12-01')
    monkeypatch.setattr(gov,'agora',lambda:datetime(2026,12,5,tzinfo=timezone.utc))
    d=resumo(sessao,p)['pendencias'][ident]
    assert d['atrasada'] and d['escalonamento']=='Escalonamento não configurado'
    assert d['estado']=='aberta'


def test_E08_unidade_nao_concede_acesso(sessao,principal):
    p=principal; ident=pendencia(sessao,p)
    ato(sessao,p,'destinar',ident,unidade_id='UNID-GOV')
    with TestClient(app) as client:
        assert client.get(f'/form2/participacoes/{p.id}/governanca?conta_id=CONTA-E1').status_code==403
        page=client.get(f'/form2/participacoes/{p.id}/governanca?conta_id=CONTA-G1')
        assert page.status_code==200 and 'Para responder, complemente o FORM 1' in page.text
        assert 'Enviar resposta ao solicitante' not in page.text
        assert 'Reavaliação das manifestações' not in page.text


def test_E09_ocultar_nao_retira_pendencia(sessao,principal):
    p=principal; ident=pendencia(sessao,p)
    salvar(sessao,p,1,{'F2-1.2':'CONFIRMADA','F2-1.3':'SIM'})
    assert estado(sessao,p)['pendencias'][ident]['estado']=='aberta'


def test_E10_legado_uma_entrada_sem_dividir(sessao,principal):
    p=principal
    from app.fila_form2 import agora
    legado=ComplementoForm2(id=str(uuid4()),participacao_id=p.id,snapshot_origem_id=p.snapshot_id,
        solicitacao='Primeira e segunda necessidade fictícias no texto legado.',estado='aberta',criada_em=agora())
    sessao.add(legado);sessao.commit()
    antes=deepcopy(p.conteudo)
    g=estado(sessao,p)
    assert len(g['pendencias'])==1 and p.conteudo==antes
    ato(sessao,p,'destinar',legado.id,unidade_id='UNID-NORTE')
    assert estado(sessao,p)['pendencias'][legado.id]['texto']==legado.solicitacao


def test_T08_nao_devolve_sem_confirmacao(sessao,principal):
    p=principal; ident=pendencia(sessao,p); s2=segunda(sessao,p,confirmar=False)
    with pytest.raises(ValueError,match='confirmada'):
        ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    sessao.rollback()


def test_HTTP_lista_retorno_e_negacao(sessao,principal):
    p=principal;pendencia(sessao,p)
    with TestClient(app) as c:
        url=f'/form2/participacoes/{p.id}/governanca'
        pagina=c.get(url+'?conta_id=CONTA-B1')
        assert pagina.status_code==200 and 'Acrescentar outra necessidade' in pagina.text
        for caminho in [url, f'/form2/participacoes/{p.id}', f'/form2/participacoes/{p.id}/blocos/1']:
            tela = c.get(caminho + '?conta_id=CONTA-B1')
            assert tela.status_code == 200
            assert 'AAL — Agente de Análise de Legitimidade' in tela.text
            assert 'Unidade de atuação:' in tela.text
            assert 'pode editar suas respostas' in tela.text
        origem = c.get(url + '?conta_id=CONTA-A1')
        assert origem.status_code == 200
        assert 'AAL — Agente de Análise de Legitimidade' not in origem.text
        assert 'Complementar FORM 1' in origem.text
        assert f'/registros/{p.registro_id}/form1-rev22?conta_id=CONTA-A1&amp;bloco=1' in origem.text
        assert '14 blocos do FORM 1 deste processo' in origem.text
        assert 'decida qual versão' not in origem.text
        assert 'Complementar FORM 1' not in pagina.text
        assert 'Retorno da S2' not in pagina.text
        assert 'Usar nova versão na análise' not in pagina.text
        assert 'Conferir unidade de retorno de Ouvidoria/e-SIC' not in pagina.text
        assert 'Próximo passo:' in pagina.text
        assert 'aguardando definição do destinatário' in pagina.text
        assert c.post(url,data={'conta_id':'CONTA-G1','comando_id':'V9-FORJA','versao':p.versao,
            'acao':'adicionar','descricao':'Forjado','motivo':'Forjado'}).status_code==403


def test_E06_AAL_nao_confirma_S2_nem_apresenta(sessao,principal):
    from app.conferencia_interna_form1_integral import confirmar_conferencia_interna_form1_integral
    from app.atribuicao_form1_integral import atribuir_arp_form1_integral
    from app.modelos import AtribuicaoForm1Integral
    p=principal;segunda(sessao,p,confirmar=False)
    # Fixture: Beta passa a ser APA; a aplicação deve negar mesmo com o papel correto.
    titular=sessao.scalar(select(Designacao).where(Designacao.pessoa_id=='PESSOA-A',
        Designacao.unidade_id=='UNID-NORTE',Designacao.papel=='responsavel_registro'))
    titular.ativa=False;sessao.flush()
    sessao.add(Designacao(pessoa_id='PESSOA-B',unidade_id='UNID-NORTE',papel='responsavel_registro',
        tipo_apa='titular',ativa=True))
    sessao.commit()
    result=confirmar_conferencia_interna_form1_integral(sessao,conta_id='CONTA-B1',
        comando_id='V9-BETA-CONFIRMA',registro_id=p.registro_id,versao_lida=1)
    assert not result['permitido'] and 'AAL em exercício' in result['motivo']
    sessao.commit()
    a=sessao.get(AtribuicaoForm1Integral,p.registro_id)
    result=atribuir_arp_form1_integral(sessao,comando_id='V9-BETA-ARP',conta_id='CONTA-B1',
        registro_id=p.registro_id,modo='proprio',arp_pessoa_id=None,versao_lida=a.versao)
    # Caso a conferência pendente já impeça reatribuição, a primeira barreira é suficiente.
    sessao.commit()
    if result['permitido']:
        r=sessao.get(RascunhoForm1Integral,p.registro_id)
        result=_solicitar(sessao,{'registro_id':p.registro_id},comando='V9-BETA-APRESENTA',conta='CONTA-B1',versao=r.versao_rascunho)
        assert not result['permitido'] and 'AAL em exercício' in result['motivo']


def test_E05_concorrencia_mesma_pendencia(sessao,principal):
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy.orm import Session
    from app.banco import motor
    p=principal;ident=pendencia(sessao,p);version=p.versao;pid=p.id
    sessao.commit()
    def concorrente(n):
        with Session(motor) as s:
            try:
                result=agir(s,conta_id='CONTA-B1',comando_id='V9-CONC-'+str(n),participacao_id=pid,
                    versao=version,acao='destinar',pendencia_id=ident,
                    dados={'motivo':'Ensaio concorrente fictício.','unidade_id':'UNID-NORTE','prazo':f'2026-12-0{n}'})
                s.commit();return result['permitido']
            except ValueError:
                s.rollback();return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(concorrente,(1,2)))==[False,True]


def test_E05_S3_impede_vinculo_de_tela_S2(sessao,principal):
    from app.rascunho_form1_integral import salvar_bloco_1_form1_integral
    p=principal;ident=pendencia(sessao,p);s2=segunda(sessao,p)
    ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2);ato(sessao,p,'aceitar',ident)
    r=sessao.get(RascunhoForm1Integral,p.registro_id)
    result=salvar_bloco_1_form1_integral(sessao,comando_id='V9-S3-AJUSTE',conta_id='CONTA-G1',
        registro_id=p.registro_id,versao_lida=r.versao_rascunho,respostas={'1.1':'Sim','1.1.1':'S3-FICT'})
    sessao.commit();assert result['permitido'], result
    s3=_solicitar(sessao,{'registro_id':p.registro_id},comando='V9-S3',versao=result['versao_rascunho'])
    assert s3['permitido']
    with pytest.raises(ValueError,match='versão mais recente'):
        ato(sessao,p,'fonte',snapshot_id=s2)
    sessao.rollback()


def test_E02_aceite_de_todos_solicitantes(sessao,principal):
    p=principal;ident=pendencia(sessao,p)
    c=executar(sessao,conta_id='CONTA-B1',comando_id='V9-OUTRA',participacao_id=p.id,
        acao='consultar',versao=p.versao,tipo='dpo',unidade_id='UNID-GOV',texto='Questão fictícia.');sessao.commit()
    q=sessao.get(ParticipacaoForm2,c['participacao_id'])
    executar(sessao,conta_id='CONTA-E1',comando_id='V9-OUTRA-ASSUME',participacao_id=q.id,acao='assumir',versao=q.versao);sessao.commit()
    ato(sessao,p,'solicitante',ident,solicitante_id=q.id)
    s2=segunda(sessao,p);ato(sessao,p,'responder',ident,conta='CONTA-G1',snapshot_id=s2)
    ato(sessao,p,'aceitar',ident)
    assert estado(sessao,p)['pendencias'][ident]['estado']=='respondida'
    ato(sessao,p,'aceitar',ident,conta='CONTA-E1',alvo=q.id)
    assert estado(sessao,p)['pendencias'][ident]['estado']=='resolvida'


def test_E07_reatribuicao_preserva_prazo(sessao,principal):
    from app.fila_form2 import reatribuir
    p=principal;ident=pendencia(sessao,p)
    ato(sessao,p,'destinar',ident,unidade_id='UNID-NORTE',prazo='2026-12-01')
    antes=deepcopy(estado(sessao,p)['pendencias'][ident])
    sessao.add(Designacao(pessoa_id='PESSOA-A',unidade_id='UNID-NORTE',papel='gestor_fila',ativa=True))
    sessao.add(Designacao(pessoa_id='PESSOA-F',unidade_id='UNID-NORTE',papel='aal_form2',ativa=True));sessao.commit()
    reatribuir(sessao,conta_id='CONTA-A1',comando_id='V9-REATRIBUIR',participacao_id=p.id,
        versao=p.versao,responsavel_id='PESSOA-F',motivo='Substituição fictícia.');sessao.commit()
    assert estado(sessao,p)['pendencias'][ident]==antes


def test_T10_avisos_apenas_metadados(sessao,principal):
    from app.avisos_dpo import montar_aviso
    p=principal;q=consultar_dpo(sessao,p)
    aviso=sessao.scalar(select(AvisoDpo).where(AvisoDpo.participacao_id==q.id))
    conteudo=montar_aviso(aviso,'http://localhost:8001').get_content()
    assert q.questao not in conteudo and q.manifestacao not in conteudo
    assert 'conta_id=' not in conteudo


def test_E08_unidade_retorno_APA_confirma_AAL(sessao,principal):
    from app.unidade_retorno_institucional import registrar,consultar
    p=principal
    args=dict(conta_id='CONTA-A1',comando_id='V9-RETORNO-APA',registro_id=p.registro_id,
        versao=0,acao='informar',unidade_id='UNID-NORTE',canal='ESIC',motivo='Destino fictício de retorno.')
    assert registrar(sessao,**args)['permitido'];sessao.commit()
    assert registrar(sessao,**args)['reexecutado'];sessao.commit()
    assert consultar(sessao,p.registro_id)['situacao']=='Aguardando confirmação do AAL'
    with pytest.raises(PermissionError):
        registrar(sessao,conta_id='CONTA-G1',comando_id='V9-RETORNO-FORJA',registro_id=p.registro_id,
            versao=1,acao='confirmar',motivo='Não autorizado.')
    sessao.rollback()
    assert registrar(sessao,conta_id='CONTA-B1',comando_id='V9-RETORNO-AAL',registro_id=p.registro_id,
        versao=1,acao='confirmar',motivo='Unidade conferida no ensaio.')['permitido'];sessao.commit()
    assert consultar(sessao,p.registro_id)['snapshot_id']==p.snapshot_id
    with TestClient(app) as c:
        assert c.get(f'/registros/{p.registro_id}/unidade-retorno?conta_id=CONTA-A1').status_code==200

def test_fila_cartao_unico_e_encaminhamento_so_APA(sessao, principal):
    salvar(sessao, principal)
    with TestClient(app) as client:
        beta = client.get('/form2/filas?conta_id=CONTA-B1')
        assert beta.status_code == 200
        assert beta.text.count('data-registro="' + principal.registro_id + '"') == 1
        assert 'Abrir FORM 2' in beta.text
        assert 'Ver pendências e respostas' in beta.text
        assert 'Complementação do FORM 1: definir unidade responsável pela resposta.' in beta.text
        assert 'Encaminhar versão do FORM 1 já confirmada' not in beta.text
        alfa = client.get('/form2/filas?conta_id=CONTA-A1')
        assert alfa.status_code == 200
        assert alfa.text.count('data-registro="' + principal.registro_id + '"') == 1
        assert 'Ver pendências e respostas' in alfa.text
        assert 'Encaminhar versão do FORM 1 já confirmada' in alfa.text


def test_HTTP_destinar_com_chave_real_da_tela_e_repeticao(sessao, principal):
    import re
    from html import unescape
    p = principal
    ident = pendencia(sessao, p)
    with TestClient(app) as client:
        url = f'/form2/participacoes/{p.id}/governanca'
        page = client.get(url + '?conta_id=CONTA-B1')
        forms = re.findall(r'<form method="post">(.*?)</form>', page.text, re.S)
        form = next(f for f in forms if 'value="destinar"' in f)
        dados = {k: unescape(v) for k, v in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', form)}
        assert len(dados['comando_id']) <= 64
        dados.update(acao='destinar', unidade_id='UNID-NORTE', prazo='', motivo='Complementação fictícia pela origem.')
        for _ in range(2):
            resposta = client.post(url, data=dados, follow_redirects=False)
            assert resposta.status_code == 303
        sessao.expire_all()
        salvo = estado(sessao, sessao.get(ParticipacaoForm2, p.id))['pendencias'][ident]
        assert salvo['unidade_id'] == 'UNID-NORTE'
        assert salvo['prazo'] is None
        assert sum(h['ato'] == 'destinar' for h in salvo['historico']) == 1


def _enviar_formulario_tela(client, url, conta, acao, **campos):
    import re
    from html import unescape
    pagina = client.get(url + '?conta_id=' + conta)
    assert pagina.status_code == 200
    formularios = re.findall(r'<form method="post">(.*?)</form>', pagina.text, re.S)
    formulario = next(f for f in formularios if f'value="{acao}"' in f)
    dados = {k: unescape(v) for k, v in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', formulario)}
    assert 0 < len(dados['comando_id']) <= 64
    dados.update(acao=acao, motivo='Motivo fictício da vistoria automatizada.', **campos)
    resposta = client.post(url, data=dados, follow_redirects=False)
    assert resposta.status_code == 303, resposta.text
    return dados


def test_HTTP_percurso_retorno_aceite_e_reavaliacao(sessao, principal):
    p = principal
    ident = pendencia(sessao, p)
    s1 = p.snapshot_id
    anterior = consultar_dpo(sessao, p)
    url = f'/form2/participacoes/{p.id}/governanca'
    with TestClient(app) as client:
        _enviar_formulario_tela(client, url, 'CONTA-B1', 'destinar', unidade_id='UNID-NORTE', prazo='')
        sessao.expire_all()
        s2 = segunda(sessao, p)
        retorno = client.get(url + '?conta_id=CONTA-G1')
        assert 'Apresentado por' in retorno.text and 'confirmado pelo APA' in retorno.text
        assert '>Versão 2</option>' not in retorno.text
        _enviar_formulario_tela(client, url, 'CONTA-G1', 'responder', snapshot_id=s2)
        conferencia = client.get(url + '?conta_id=CONTA-B1')
        assert conferencia.status_code == 200
        assert 'Resposta enviada pela origem' in conferencia.text
        assert 'Servidor Épsilon' in conferencia.text
        consulta = 'Consultar o FORM 1 confirmado enviado nesta resposta'
        assert consulta in conferencia.text
        assert conferencia.text.index(consulta) < conferencia.text.index('value="aceitar"')
        assert 'Sem resposta nesta apresentação.' in conferencia.text
        origem_page = client.get(url + '?conta_id=CONTA-G1')
        assert consulta not in origem_page.text
        _enviar_formulario_tela(client, url, 'CONTA-B1', 'aceitar')
        _enviar_formulario_tela(client, url, 'CONTA-B1', 'fonte', snapshot_id=s2)
        sessao.expire_all()
        chave = s2 + ':' + anterior.id
        # Escolhe o formulário da manifestação temática, não o das respostas próprias.
        pagina = client.get(url + '?conta_id=CONTA-B1')
        import re
        from html import unescape
        formulario = next(f for f in re.findall(r'<form method="post">(.*?)</form>', pagina.text, re.S) if chave in f)
        dados = {k: unescape(v) for k, v in re.findall(r'<input type="hidden" name="([^"]+)" value="([^"]*)"', formulario)}
        assert len(dados['comando_id']) <= 64
        dados.update(acao='impacto', decisao='complemento_necessario', motivo='Fatos fictícios alterados na nova versão.')
        for _ in range(2):
            assert client.post(url, data=dados, follow_redirects=False).status_code == 303
    sessao.expire_all()
    assert p.snapshot_id == s2
    assert anterior.estado == 'concluida' and anterior.snapshot_id == s1
    assert estado(sessao,p)['pendencias'][ident]['estado'] == 'resolvida'
    assert sessao.scalar(select(func.count()).select_from(AvisoDpo).where(AvisoDpo.tipo=='ciencia')) == 1
    assert estado(sessao,p)['impactos'][chave]['suplemento_id']


def test_vinculo_item_FORM1_na_versao_preservada(sessao, principal):
    p=principal; ident=pendencia(sessao,p)
    snap=sessao.get(VersaoForm1Integral,p.snapshot_id)
    antes=deepcopy(snap.conteudo)
    chave=next(iter(snap.conteudo['form1_integral']['respostas']))
    ato(sessao,p,'vincular',ident,referencia='F1-'+chave)
    assert any(o['item']=='F1-'+chave for o in estado(sessao,p)['pendencias'][ident]['origens'])
    assert snap.conteudo==antes


def test_HTTP_chave_reatribuicao_cabe_no_banco(sessao, principal):
    import re
    p=principal
    sessao.add(Designacao(pessoa_id='PESSOA-A',unidade_id='UNID-NORTE',papel='gestor_fila',ativa=True))
    sessao.commit()
    with TestClient(app) as c:
        pagina=c.get('/form2/filas?conta_id=CONTA-A1')
        assert pagina.status_code==200
        chaves=re.findall(r'name="comando_id" value="([^"]+)"',pagina.text)
        assert chaves and all(len(chave)<=64 for chave in chaves)


def test_HTTP_resposta_pendente_continua_disponivel_apos_adotar_versao(sessao, principal):
    p=principal; primeira=pendencia(sessao,p)
    r=ato(sessao,p,'adicionar',descricao='Segunda necessidade fictícia.')
    segunda_pendencia=r['pendencia_id']
    s2=segunda(sessao,p)
    ato(sessao,p,'responder',primeira,conta='CONTA-G1',snapshot_id=s2)
    ato(sessao,p,'aceitar',primeira)
    ato(sessao,p,'fonte',snapshot_id=s2)
    with TestClient(app) as client:
        _enviar_formulario_tela(client,f'/form2/participacoes/{p.id}/governanca',
            'CONTA-G1','responder',snapshot_id=s2)
    sessao.expire_all()
    assert estado(sessao,p)['pendencias'][segunda_pendencia]['estado']=='respondida'
