"""Lote 9: cenários fictícios; nunca usa bancos da vistoria."""
from copy import deepcopy
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from fastapi.testclient import TestClient
from app.main import app
from app.modelos import Designacao, Evento, Pessoa, ParticipacaoForm2
from app.form2_rev212 import RASCUNHO
from app.respostas_form2 import aplicar_revisao, definicao_revisao, contagem_perguntas_ativas
from testes.test_governanca_form2_v9 import principal


def test_u1_caixas_compartilhadas_preservam_contratos(sessao, principal):
    principal.estado = "aguardando"; principal.responsavel_id = None
    sessao.commit()
    from app.rotas_fila_form2 import paginas
    for nome in ('filas_form2.html', 'participacao_form2.html', 'conferencia_form1_integral.html',
                 'form1_rev22.html', 'registro.html'):
        fonte = paginas.env.loader.get_source(paginas.env, nome)[0]
        assert "_confirmacao_ato.html" in fonte
    tela = TestClient(app).get(f'/form2/participacoes/{principal.id}?conta_id=CONTA-B1')
    assert tela.status_code == 200
    assert 'data-fechar-dialogo' in tela.text and '<dialog' in tela.text


def test_u2_autoria_vem_do_ato_e_nao_da_url(sessao, principal):
    from app.fila_form2 import salvar_bloco
    from app.atos_interface import ato_registrado
    salvar_bloco(sessao, conta_id='CONTA-B1', comando_id='L9-ATO', participacao_id=principal.id,
                 versao=principal.versao, bloco=2, campos={'F2-2.9': 'A_CONFIRMAR'})
    sessao.commit()
    ato = ato_registrado(sessao, 'L9-ATO', 'CONTA-B1', participacao_id=principal.id)
    assert ato and 'Beta' in ato['autor'] and ' às ' in ato['quando']
    assert ato_registrado(sessao, 'L9-ATO', 'CONTA-A1') is None
    assert ato_registrado(sessao, 'L9-ATO', 'CONTA-B1', registro_id='REG-INEXISTENTE') is None
    tela = TestClient(app).get(f'/form2/participacoes/{principal.id}/blocos/2?conta_id=CONTA-B1&salvo=L9-ATO')
    assert 'Operação registrada em ' in tela.text and 'Servidor Beta (fictício)' in tela.text


def test_u3_identidade_idempotente_sem_mudar_pessoa(sessao, principal):
    from app.identidade_demonstrativa import identidade_demonstrativa
    p = sessao.get(Pessoa, 'PESSOA-B'); antes = p.nome
    assert identidade_demonstrativa('Servidor de teste') == 'Servidor de teste (fictício)'
    assert identidade_demonstrativa('Servidor de teste (fictício)') == 'Servidor de teste (fictício)'
    tela = TestClient(app).get(f'/form2/participacoes/{principal.id}?conta_id=CONTA-B1')
    assert 'Servidor Beta (fictício)' in tela.text and '(fictício) (fictício)' not in tela.text
    sessao.refresh(p)
    assert p.nome == antes


def test_da51_alfa_habilitado_fora_da_lista_e_post_recusado(sessao, principal):
    from app.fila_form2 import candidatos_atribuicao
    for papel in ('gestor_fila', 'aal_form2'):
        sessao.add(Designacao(pessoa_id='PESSOA-A', unidade_id=principal.unidade_id, papel=papel))
    sessao.commit()
    assert 'PESSOA-A' not in {p.id for p in candidatos_atribuicao(sessao, principal, 'PESSOA-A')}
    antes = sessao.scalar(select(func.count()).select_from(Evento))
    resp = TestClient(app).post(f'/form2/participacoes/{principal.id}/reatribuir', data={
        'conta_id':'CONTA-A1', 'comando_id':'L9-AUTO', 'versao':principal.versao,
        'responsavel_id':'PESSOA-A', 'motivo':'Tentativa fictícia'})
    assert resp.status_code == 409
    assert sessao.scalar(select(func.count()).select_from(Evento)) == antes
    sessao.refresh(principal)
    assert principal.responsavel_id == 'PESSOA-B'


def test_da51_sem_habilitado_estado_na_fila_e_dpo(sessao, principal):
    from app.fila_form2 import aguardando_definicao_analise
    principal.responsavel_id = None; principal.estado = 'aguardando'
    for d in sessao.scalars(select(Designacao).where(Designacao.papel == 'aal_form2')):
        d.ativa = False
    sessao.add(Designacao(pessoa_id='PESSOA-A', unidade_id=principal.unidade_id, papel='gestor_fila'))
    sessao.commit()
    assert aguardando_definicao_analise(sessao, principal)
    cliente = TestClient(app)
    for url in ('/form2/filas?conta_id=CONTA-A1', '/form2/painel-dpo?conta_id=CONTA-E1'):
        resposta = cliente.get(url)
        assert resposta.status_code == 200
        assert 'Aguardando definição de quem fará a análise' in resposta.text


def test_d1_dezoito_complementos_contam_so_depois_do_texto():
    from app.complementos_form2 import ITENS, codigos_com_complemento, falta_complemento
    itens = {q['id']:q for n in range(4,15) for q in definicao_revisao(n)['itens']}
    assert len(ITENS) == 18
    for chave in ITENS:
        q = itens[chave]; codigos = codigos_com_complemento(q)
        assert codigos, chave
        assert falta_complemento(q, [codigos[0]], '')
        assert not falta_complemento(q, [codigos[0]], 'Complemento fictício')
    base = {RASCUNHO:{'9':{'opcao:F2-9.1':['SIM']}}}
    salvo, _ = aplicar_revisao(base, 9, {'opcao:F2-9.6.1#1':['SIM']}, demonstrativo=True)
    n, m = contagem_perguntas_ativas(salvo, [9])[9]
    completo, _ = aplicar_revisao(salvo, 9, {'texto:F2-9.6.1#1':['Complemento fictício']}, demonstrativo=True)
    assert contagem_perguntas_ativas(completo, [9])[9] == (n + 1, m)


def test_d1_salva_sem_complemento_mas_nao_consolida(sessao, principal):
    from app.fila_form2 import salvar_bloco
    from app.consolidacao_form2 import consultar
    salvar_bloco(sessao, conta_id='CONTA-B1', comando_id='L9-D1-SALVA', participacao_id=principal.id,
                 versao=principal.versao, bloco=9, campos={'opcao:F2-9.1':['SIM'], 'opcao:F2-9.6.1#1':['SIM']})
    sessao.commit()
    resumo = consultar(sessao, conta_id='CONTA-B1', participacao_id=principal.id)
    assert any(i['item']=='F2-9.6.1#1' for i in resumo['resumo']['complementos_pendentes'])
    antes = sessao.scalar(select(func.count()).select_from(Evento))
    resposta = TestClient(app).post(f'/form2/participacoes/{principal.id}/consolidacao', data={
        'conta_id':'CONTA-B1','comando_id':'L9-D1-CONSOLIDA','versao':principal.versao,
        'hash_fontes':resumo['hash_fontes'],'sintese':'Síntese fictícia'})
    assert resposta.status_code == 409 and 'perguntas obrigatórias' in resposta.text
    assert f'/form2/participacoes/{principal.id}/blocos/9?' in resposta.text
    assert sessao.scalar(select(func.count()).select_from(Evento)) == antes
    assert not resumo['resumo']['conclusao_institucional_habilitada']


def test_d3_exclusivas_form1_e_form2():
    from app.rev22_form1 import validar
    from app.alternativas_exclusivas import exclusiva
    for rotulo in ('Nenhum', 'Nenhuma dessas opções', 'Não se aplica', 'A confirmar'):
        assert exclusiva(rotulo)
        q={'id':'SINTETICO','kind':'multi','options':[rotulo,'Alternativa fictícia']}
        assert validar(q,[rotulo]) == [rotulo]
        with pytest.raises(ValueError): validar(q,[rotulo,'Alternativa fictícia'])
    from app.respostas_form2 import _validar_valor
    q={'id':'F2-SINTETICO','controle':'Seleção múltipla','modo':'multipla','alternativas':[
        {'codigo':'NENHUM','rotulo':'Nenhum'},{'codigo':'OUTRO','rotulo':'Alternativa fictícia'}]}
    with pytest.raises(ValueError): _validar_valor(q,['NENHUM','OUTRO'])


def test_d9_classificacao_e_duvida_preservada():
    from app.classificacao_analise_form2 import classificar
    for chave,esperado in [('F2-3.1','jurídica'),('F2-13.6','técnica')]:
        q={'id':chave,'alternativas':[{'codigo':'ANALISE','rotulo':'Requer análise'}]}
        assert classificar(q)['alternativas'][0]['rotulo'] == 'Requer análise ' + esperado
    q={'id':'F2-TESTE-NAO-DELIBERADO','alternativas':[{'codigo':'ANALISE','rotulo':'Requer análise jurídica/técnica'}]}
    assert classificar(q)['analise_especializada']['classificacao'] == 'a_deliberar'
    assert q['alternativas'][0]['rotulo'] == 'Requer análise jurídica/técnica'


def test_d2_atalho_abre_consulta_sem_enviar(sessao, principal):
    cliente=TestClient(app)
    antes=sessao.scalar(select(func.count()).select_from(ParticipacaoForm2))
    tela=cliente.get(f'/form2/participacoes/{principal.id}/blocos/3?conta_id=CONTA-B1')
    assert tela.status_code == 200 and 'data-atalho-consulta' in tela.text
    for tipo in ('dpo','juridico','tematica'):
        tela=cliente.get(f'/form2/participacoes/{principal.id}?conta_id=CONTA-B1&consulta_item=F2-3.1&consulta_tipo={tipo}')
        assert tela.status_code == 200 and 'Consulta sobre F2-3.1: ' in tela.text
        assert tela.context['consulta_tipo'] == tipo
    assert sessao.scalar(select(func.count()).select_from(ParticipacaoForm2)) == antes


def test_d8_d10_d11_metadados_e_controles(principal):
    itens={q['id']:q for n in (7,8,9,10,11) for q in definicao_revisao(n)['itens']}
    assert [a['rotulo'] for a in itens['F2-7.10.1']['alternativas']] == [
        'Exclusivamente institucional','Pode ter uso diverso','A confirmar']
    assert 'falta informação' in ' '.join(itens['F2-7.1.1']['ajudas_usuario'])
    assert itens['F2-11.8.1']['enunciado'].endswith('no e-SIC?')
    assert 'Descreva categorias, não pessoas.' in itens['F2-10.8.1']['ajudas_usuario']
    for chave in ('F2-7.5','F2-7.11.4','F2-8.6','F2-9.7.2'):
        assert itens[chave]['selo_d11']
    tela=TestClient(app).get(f'/form2/participacoes/{principal.id}/blocos/7?conta_id=CONTA-B1')
    for chave in ('F2-7.5','F2-7.11.4'):
        trecho=tela.text.split('id="'+chave+'"',1)[1].split('</fieldset>',1)[0]
        assert '[D11] Aguarda homologação jurídica' in trecho


def test_c8_secretaria_validada_funcoes_curto(sessao, principal):
    from app.unidades_interface_form2 import secretarias_ativas
    unidades=secretarias_ativas(sessao); assert unidades
    chave='unidade:F2-14.3#1'
    novo,_=aplicar_revisao({},14,{'texto:F2-14.2#1':['Necessidade fictícia'],chave:[unidades[0].id], 'texto:F2-14.3#1':['Função fictícia']},
        demonstrativo=True, unidades_permitidas={u.id for u in unidades})
    assert novo[RASCUNHO]['14'][chave] == unidades[0].id
    for campos in ({chave:['UNID-INEXISTENTE']},{'texto:F2-14.3#1':['x'*201]}):
        with pytest.raises(ValueError): aplicar_revisao({},14,campos,demonstrativo=True,unidades_permitidas={u.id for u in unidades})
    tela=TestClient(app).get(f'/form2/participacoes/{principal.id}/blocos/14?conta_id=CONTA-B1')
    assert tela.status_code == 200 and 'name="unidade:F2-14.3#1"' in tela.text


def test_n3_n4_n5_textos_na_tela(sessao, principal, monkeypatch):
    import app.origem_form2 as rotas
    original = rotas.ler_origem
    def origem_temática(*args, **kwargs):
        from copy import deepcopy
        origem = dict(original(*args, **kwargs))
        origem['conteudo'] = deepcopy(origem['conteudo'])
        origem['conteudo'].setdefault('respostas', {}).update({'8.10':'Sim', '5.1':['Dados de saúde']})
        return origem
    monkeypatch.setattr(rotas, 'ler_origem', origem_temática)

    principal.conteudo={**principal.conteudo,'respostas_etapa1':{'F2-2.9':'A_CONFIRMAR'}}
    sessao.commit(); cliente=TestClient(app)
    tela=cliente.get(f'/form2/participacoes/{principal.id}/blocos/14?conta_id=CONTA-B1')
    assert tela.text.count('1 pergunta ativa com resposta') == 2
    assert 'pergunta(s)' not in tela.text and 'Com pendências' not in tela.text
    for n,titulo in ((9,'Wi-Fi oferecido pela Prefeitura'),(11,'Informações de saúde'),(12,'Informações de alta sensibilidade')):
        tela=cliente.get(f'/form2/participacoes/{principal.id}/blocos/{n}?conta_id=CONTA-B1')
        assert titulo in tela.text and 'Ramificação' not in tela.text
