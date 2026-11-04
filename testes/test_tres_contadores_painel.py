"""Contadores independentes e edição depois da conferência; somente massa sintética."""
from copy import deepcopy
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.consultas_interface import carregar_painel, carregar_registro
from app.modelos import RascunhoForm1Integral, VersaoForm1Integral
from app.rascunho_form1_integral import iniciar_rascunho_form1_integral, salvar_bloco_5_form1_integral, salvar_bloco_2_form1_integral
from app.atribuicao_form1_integral import atribuir_arp_form1_integral
from testes.test_confirmacao_conferencia_form1_integral_8ag import _preparar_s2, _confirmar
from testes.test_conferencia_interna_form1_integral_8ac import _preparar, _solicitar
from testes.test_devolucao_reapresentacao_form1_integral_8af import _devolver
from testes.apoio import g1

cliente = TestClient(app)


def test_arp_edita_apos_s2_confirmada_sem_modificar_snapshots(sessao):
    # Arrange: duas apresentações e confirmação explícita da segunda.
    r, s1, s2 = _preparar_s2(sessao, 'CONTADORES-S2')
    assert _confirmar(sessao, r, comando='CONTADORES-CONF')['permitido']
    originais = {s['snapshot_id']: deepcopy(sessao.get(VersaoForm1Integral, s['snapshot_id']).conteudo) for s in (s1, s2)}
    rid = r['registro_id']
    # Act: mesma URL de Registro, contas distintas.
    apa = cliente.get(f'/registros/{rid}?conta_id=CONTA-A1')
    arp = cliente.get(f'/registros/{rid}?conta_id=CONTA-G1')
    painel = cliente.get('/?conta_id=CONTA-G1')
    # Assert: confirmação não retira a permissão vigente nem transforma pendências em tarefas.
    assert apa.status_code == arp.status_code == painel.status_code == 200
    assert 'name="campo__5.1"' not in apa.text
    assert 'name="campo__5.1"' in arp.text
    assert 'data-modo-consulta="false"' in arp.text
    assert f'/registros/{rid}?conta_id=CONTA-G1#titulo-bloco-' in painel.text
    assert 'Retomar rascunho do FORM 1' in painel.text
    p = carregar_painel(sessao, 'CONTA-G1')
    assert p['quantidade_providencias_conferencia'] == 0
    _, detalhe = carregar_registro(sessao, 'CONTA-G1', rid)
    assert p['quantidade_campos_obrigatorios_pendentes'] == detalhe['form1_integral']['pre_validacao']['quantidades']['incompletos'] > 0
    versao = sessao.get(RascunhoForm1Integral, rid).versao_rascunho
    assert salvar_bloco_5_form1_integral(sessao, comando_id='CONTADORES-EDIT', conta_id='CONTA-G1', registro_id=rid, versao_lida=versao, respostas={'5.1':['Nome']})['permitido']
    sessao.commit()
    for sid, conteudo in originais.items():
        assert sessao.get(VersaoForm1Integral, sid).conteudo == conteudo
    assert 'conclusão institucional do FORM 1 ainda não está habilitada' in arp.text


def test_soma_so_arp_autorizado_inclusive_nao_iniciado_sem_gravar(sessao):
    r = _preparar(sessao, 'CONTADORES-PRONTO')
    outro = g1('CONTADORES-OUTRO', 'OBJ-SRV-001', 'CTX-TRIB-03', titulo='Serviço fictício de outro ARP')
    inicial = g1('CONTADORES-INICIAL', 'OBJ-PRC-001', 'CTX-TRIB-02', titulo='Processo fictício ainda não iniciado')
    for item, pessoa in [(outro, 'PESSOA-A'), (inicial, 'PESSOA-G')]:
        assert atribuir_arp_form1_integral(sessao, comando_id='ATR-'+item['registro_id'], conta_id='CONTA-A1', registro_id=item['registro_id'], modo='proprio' if pessoa=='PESSOA-A' else 'outro', arp_pessoa_id=pessoa if pessoa!='PESSOA-A' else None, versao_lida=0)['permitido']
        sessao.commit()
    antes = carregar_painel(sessao, 'CONTA-G1')
    assert len(antes['registros']) == 3
    pertinentes = [x for x in antes['registros'] if x['preenchimento_arp']]
    assert {x['id'] for x in pertinentes} == {r['registro_id'], inicial['registro_id']}
    assert antes['quantidade_campos_obrigatorios_pendentes'] == sum(x['preenchimento_arp']['quantidade'] for x in pertinentes)
    assert antes['quantidade_providencias_conferencia'] == 0
    assert sessao.get(RascunhoForm1Integral, inicial['registro_id']) is None
    assert iniciar_rascunho_form1_integral(sessao, comando_id='CONTADORES-INICIO', conta_id='CONTA-G1', registro_id=inicial['registro_id'])['permitido']
    sessao.commit()
    depois = carregar_painel(sessao, 'CONTA-G1')
    assert depois['quantidade_campos_obrigatorios_pendentes'] == antes['quantidade_campos_obrigatorios_pendentes']
    assert carregar_painel(sessao, 'CONTA-B1')['quantidade_campos_obrigatorios_pendentes'] == 0


def test_conferencia_e_devolucao_contam_atos_nao_campos(sessao):
    r = _preparar(sessao, 'CONTADORES-ATOS')
    assert _solicitar(sessao, r, comando='CONTADORES-S1')['permitido']
    assert carregar_painel(sessao, 'CONTA-A1')['quantidade_providencias_conferencia'] == 1
    assert carregar_painel(sessao, 'CONTA-A1')['quantidade_campos_obrigatorios_pendentes'] == 0
    assert carregar_painel(sessao, 'CONTA-G1')['quantidade_providencias_conferencia'] == 0
    assert _devolver(sessao, r, comando='CONTADORES-DEV')['permitido']
    p = carregar_painel(sessao, 'CONTA-G1')
    assert p['quantidade_providencias_conferencia'] == 1
    assert p['quantidade_campos_obrigatorios_pendentes'] > 1
    assert carregar_painel(sessao, 'CONTA-A1')['quantidade_providencias_conferencia'] == 0


def test_contador_reutiliza_condicionais_e_exclui_avisos_facultativos(sessao):
    r = _preparar(sessao, 'CONTADORES-COND')
    for versao, escolha in [(1, 'Não'), (2, 'Sim')]:
        assert salvar_bloco_2_form1_integral(sessao, comando_id=f'CONTADORES-COND-{versao}', conta_id='CONTA-G1', registro_id=r['registro_id'], versao_lida=versao, respostas={'2.12': escolha, '2.13':'A confirmar'})['permitido']
        sessao.commit()
        _, d = carregar_registro(sessao, 'CONTA-G1', r['registro_id'])
        pv = d['form1_integral']['pre_validacao']
        p = carregar_painel(sessao, 'CONTA-G1')
        assert p['quantidade_campos_obrigatorios_pendentes'] == pv['quantidades']['incompletos']
        assert all(x['campo_id'] != '2.13' for x in pv['incompletos'])
        if escolha == 'Não':
            assert not any(x['campo_id'].startswith('2.12.') for x in pv['incompletos'])
        else:
            assert {'2.12.1', '2.12.2'} <= {x['campo_id'] for x in pv['incompletos']}
    html = cliente.get('/?conta_id=CONTA-G1').text
    for titulo in ('Registros disponíveis', 'Providências de conferência', 'Campos obrigatórios pendentes'):
        assert titulo in html
    assert 'Zero providências não significa FORM 1 completo' in html
    css = (Path(__file__).resolve().parents[1]/'app/estaticos/estilo.css').read_text(encoding='utf-8')
    assert 'repeat(3, minmax(0, 1fr))' in css
    assert '@media (max-width: 700px) { .resumo-contadores-painel { grid-template-columns: 1fr; } }' in css
