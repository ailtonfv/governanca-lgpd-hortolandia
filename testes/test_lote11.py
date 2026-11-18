"""Base técnica isolada; fatos sintéticos, nenhum papel novo ou decisão."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier
from uuid import uuid4
import json

import pytest
from sqlalchemy import select, func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import (ReferenciaParticipacaoForms34 as Referencia,
    IdentidadeForms34 as Identidade, Evento, Comando, ParticipacaoForm2,
    AvisoDpo, Designacao, Registro, VersaoForm1Integral)
from app.base_forms34 import fixar_referencia, reservar_identidade, acrescentar_historico, historico
from app.projecoes_forms34 import fatos_existentes
from app.eventos import verificar_cadeia
from app import catalogo_forms34 as catalogo
from testes.test_filas_form2_rev22 import origem


@pytest.fixture(scope='module', autouse=True)
def protecoes_por_migracao_explicita(esquema):
    from migracoes.base_forms34 import aplicar
    aplicar(motor)


@pytest.fixture
def fonte(sessao):
    # Arrange: origem válida criada exclusivamente pelos fluxos já existentes.
    r = origem(sessao)
    p = sessao.scalar(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id == r['registro_id']))
    ev = sessao.scalar(select(Evento).where(Evento.cadeia_id == p.id).order_by(Evento.id.desc()))
    sessao.commit()
    return dict(registro_id=r['registro_id'], fonte_form=2, fonte_id=str(ev.id),
                snapshot_id=p.snapshot_id, form2_id=p.id)


def referencia(s, fonte, form=3, **extra):
    args = {k: fonte[k] for k in ('registro_id','fonte_form','fonte_id')}
    args.update(comando_id=str(uuid4()), conta_id='CONTA-A1',
                participacao_id=str(uuid4()), form=form)
    args.update(extra)
    result = fixar_referencia(s, **args)
    assert result['permitido']
    s.commit()
    return result['participacao_id']


def identidade(s, ref, tipo='R', chave=None):
    out = reservar_identidade(s, comando_id=str(uuid4()), conta_id='CONTA-A1',
                             participacao_id=ref, tipo=tipo, chave_origem=chave or str(uuid4()))
    s.commit()
    return out


def acrescentar(s, obj, **extra):
    args = dict(comando_id=str(uuid4()), conta_id='CONTA-A1', identidade_id=obj,
                versao_esperada=1, tipo='anotacao', nota='Anotação fictícia.')
    args.update(extra)
    out = acrescentar_historico(s, **args)
    s.commit()
    return out


@pytest.mark.parametrize('form,quantidade,blocos', [(3,77,16),(4,39,9)])
def test_catalogo_estrutura_sem_enunciados(form, quantidade, blocos):
    # Arrange / Act: somente a estrutura versionável.
    e = catalogo.estrutura(form)
    # Assert: cobertura, unicidade e metadados sem conteúdo editorial.
    assert len(e['itens']) == quantidade
    assert len({i['id'] for i in e['itens']}) == quantidade
    assert {i['bloco'] for i in e['itens']} == set(range(1,blocos+1))
    assert all(set(i) == {'id','bloco','tipo','condicao'} for i in e['itens'])
    assert all(i['id'].startswith(f'F{form}-{form}.') for i in e['itens'])


def test_catalogo_ausente_e_instrumento_invalido(monkeypatch):
    monkeypatch.delenv('LGPD_CATALOGO_FORM3', raising=False)
    with pytest.raises(FileNotFoundError): catalogo.carregar_catalogo(3)
    for form in (1, 2, True, '3'):
        with pytest.raises(ValueError): catalogo.estrutura(form)


def test_catalogo_lacre_ordem_e_copia_independente(tmp_path, monkeypatch):
    # Arrange: pacote sintético, sem enunciado do Mestre.
    d={'versao':'SINTETICA','editorial':{'blocos':[{'itens':[{'id':'F3-3.1','enunciado':'Campo fictício'}]}]},
       'controles':{'itens':[{'id':'F3-3.1'}]}}
    e={'versao':'SINTETICA','itens':[{'id':'F3-3.1'}],'sha256_privado':catalogo._hash(d)}
    monkeypatch.setattr(catalogo,'estrutura',lambda f:deepcopy(e))
    p=tmp_path/'catalogo.json';p.write_text(json.dumps(d),encoding='utf8')
    # Act / Assert: alteração da cópia em memória não afeta próxima leitura.
    lido=catalogo.carregar_catalogo(3,p);lido['versao']='ALTERADA'
    assert catalogo.carregar_catalogo(3,p)['versao']=='SINTETICA'
    p.write_text(json.dumps(dict(d,versao='TAMPER')),encoding='utf8')
    with pytest.raises(ValueError,match='divergente'):catalogo.carregar_catalogo(3,p)
    e['sha256_privado']=catalogo._hash(d);e['itens']=[{'id':'F3-3.2'}]
    p.write_text(json.dumps(d),encoding='utf8')
    with pytest.raises(ValueError,match='Identificadores'):catalogo.carregar_catalogo(3,p)


def test_contexto_nao_ingressa_nem_atribui_papeis(sessao, fonte):
    antes=[sessao.scalar(select(func.count()).select_from(m)) for m in (ParticipacaoForm2,AvisoDpo,Designacao)]
    estado=sessao.get(Registro,fonte['registro_id']).estado_atual
    # Act: contexto puramente técnico.
    pid=referencia(sessao,fonte)
    # Assert: nenhuma fila, aviso, papel ou estado institucional criado/alterado.
    assert antes==[sessao.scalar(select(func.count()).select_from(m)) for m in (ParticipacaoForm2,AvisoDpo,Designacao)]
    assert sessao.get(Registro,fonte['registro_id']).estado_atual==estado
    assert sessao.get(Referencia,pid).fonte_id==fonte['fonte_id']


def test_referencia_form1_e_acoes_form2_form3(sessao, fonte):
    # Arrange / Act: fontes permitidas e identidade reservada de cada instrumento.
    p3=referencia(sessao,fonte,fonte_form=1,fonte_id=fonte['snapshot_id'])
    r=identidade(sessao,p3)
    p4=referencia(sessao,fonte,form=4,fonte_form=3,fonte_id=str(r['evento_id']))
    a=identidade(sessao,p4,tipo='A')
    p4direto=referencia(sessao,fonte,form=4)
    b=identidade(sessao,p4direto,tipo='A')
    # Assert: origens exatas e sequência por Registro, não por participação.
    assert r['codigo'].endswith('-R01')
    assert a['codigo'].endswith('-A01') and b['codigo'].endswith('-A02')
    ref=sessao.get(Referencia,p4)
    assert ref.fonte_participacao_id==p3 and ref.snapshot_form1_id==fonte['snapshot_id']


@pytest.mark.parametrize('form,fonte_form',[(4,1),(3,3),(3,4),(2,1),(True,1)])
def test_origem_incompativel_sem_gravacao(sessao,fonte,form,fonte_form):
    # Arrange: combinação proibida, sem inferência de ingresso.
    with pytest.raises(ValueError):
        referencia(sessao,fonte,form=form,fonte_form=fonte_form)
    assert sessao.scalar(select(func.count()).select_from(Referencia))==0


def test_origem_outro_registro_inexistente_e_evento_inadequado(sessao,fonte):
    # Act / Assert: referências forjadas não produzem contexto nem comando parcial.
    for dados in [dict(registro_id=str(uuid4())),dict(fonte_id='99999999'),
                  dict(fonte_form=1,fonte_id=fonte['fonte_id'])]:
        with pytest.raises(ValueError):referencia(sessao,fonte,**dados)
    assert sessao.scalar(select(func.count()).select_from(Referencia))==0


def test_contexto_nao_reutiliza_cadeia_de_outro_instrumento(sessao,fonte):
    with pytest.raises(ValueError,match='outra cadeia'):
        referencia(sessao,fonte,participacao_id=fonte['form2_id'])
    assert sessao.scalar(select(func.count()).select_from(Referencia))==0


def test_origem_existente_de_outro_registro_recusada(sessao,fonte):
    # Arrange: outro Registro sintético com identidade própria.
    original=sessao.get(Registro,fonte['registro_id'])
    outro=Registro(id=str(uuid4()),codigo_lgpd='LGPD-2026-99999',tipo_objeto='servico',
        titulo_objeto='Serviço fictício',unidade_principal_atual_id=original.unidade_principal_atual_id,
        contexto_atuacao_id=original.contexto_atuacao_id,ano_codigo=2026,numero_codigo=99999,
        criado_por='PESSOA-A',ciclo_atual=1,estado_atual='em_andamento',sequencia_atual=1)
    sessao.add(outro);sessao.commit()
    # Act / Assert: evento e snapshot válidos, mas pertencentes a outro Registro.
    with pytest.raises(ValueError,match='incompatível'):
        referencia(sessao,fonte,registro_id=outro.id)
    with pytest.raises(ValueError,match='incompatível'):
        referencia(sessao,fonte,registro_id=outro.id,fonte_form=1,fonte_id=fonte['snapshot_id'])


@pytest.mark.parametrize('form',[1,2])
def test_origem_corrompida_nao_e_congelada(sessao,fonte,form):
    # Arrange: corrupção sintética deliberada só na cópia _teste.
    if form==1:
        s=sessao.get(VersaoForm1Integral,fonte['snapshot_id']);s.lacre='0'*64
        args=dict(fonte_form=1,fonte_id=s.id)
    else:
        e=sessao.get(Evento,int(fonte['fonte_id']));e.conteudo=dict(e.conteudo,falso=True)
        args={}
    sessao.commit()
    # Act / Assert: não criar referência a uma fonte cujo conteúdo/lacre diverge.
    with pytest.raises(ValueError,match='[Ii]ntegridade'):referencia(sessao,fonte,**args)
    assert sessao.scalar(select(func.count()).select_from(Referencia))==0


def test_referencia_congelada_com_nova_versao_e_idempotencia(sessao,fonte):
    from app.fila_form2 import evento
    from app.comandos import abrir_comando,fechar_comando
    # Arrange: contexto aponta para evento histórico, antes de outra versão.
    pid=referencia(sessao,fonte);ref=sessao.get(Referencia,pid);antes=ref.fonte_canonica
    p=sessao.get(ParticipacaoForm2,fonte['form2_id']);p.versao+=1
    cmd,_=abrir_comando(sessao,'FONTE-NOVA','sintetico',{},'pessoa','PESSOA-A','CONTA-A1')
    evento(sessao,cmd,p,'form2_teste_ficticio');fechar_comando(cmd,{'permitido':True});sessao.commit()
    nova=sessao.scalar(select(Evento).where(Evento.cadeia_id==p.id).order_by(Evento.id.desc()))
    # Act / Assert: mesma origem é estável; nova é recusada, não muda o lacre.
    referencia(sessao,fonte,participacao_id=pid)
    with pytest.raises(ValueError,match='congelada'):
        referencia(sessao,fonte,participacao_id=pid,fonte_id=str(nova.id))
    sessao.refresh(ref)
    assert ref.fonte_canonica==antes and ref.fonte_id==fonte['fonte_id']


def test_reenvio_identidade_mesmo_comando_e_mesma_origem(sessao,fonte):
    pid=referencia(sessao,fonte)
    args=dict(comando_id='IDEM',conta_id='CONTA-A1',participacao_id=pid,tipo='R',chave_origem='FICT-1')
    a=reservar_identidade(sessao,**args);sessao.commit()
    # Act: reenvios com a mesma chave de comando e outra chave/mesma origem.
    b=reservar_identidade(sessao,**args);sessao.commit()
    c=reservar_identidade(sessao,**dict(args,comando_id='OUTRA'));sessao.commit()
    # Assert: uma única identidade/evento.
    assert a['identidade_id']==b['identidade_id']==c['identidade_id']
    assert b['reexecutado'] and c['existente']
    assert len(historico(sessao,a['identidade_id']))==1
    negado=reservar_identidade(sessao,**dict(args,chave_origem='DIFERENTE'))
    assert not negado['permitido']


def test_retirada_nao_reutiliza_numero_nem_origem(sessao,fonte):
    pid=referencia(sessao,fonte);a=identidade(sessao,pid,chave='FICT-1')
    # Act: retirada técnica não é cancelamento institucional.
    acrescentar(sessao,a['identidade_id'],tipo='retirada_tecnica')
    b=identidade(sessao,pid,chave='FICT-2');c=identidade(sessao,pid,chave='FICT-1')
    # Assert: número consumido e origem preservada, sem reativação silenciosa.
    assert b['codigo'].endswith('-R02') and c['identidade_id']==a['identidade_id']
    with pytest.raises(ValueError,match='retirada'):acrescentar(sessao,a['identidade_id'],versao_esperada=2)


def test_identidade_tipo_participacao_e_autor_invalidos(sessao,fonte):
    pid=referencia(sessao,fonte)
    for args in [dict(tipo='A'),dict(tipo='X'),dict(conta_id='INEXISTENTE'),dict(participacao_id=str(uuid4()))]:
        parametros=dict(comando_id=str(uuid4()),conta_id='CONTA-A1',participacao_id=pid,tipo='R',chave_origem='FICT')
        with pytest.raises((ValueError,PermissionError)):reservar_identidade(sessao,**dict(parametros,**args))
    assert sessao.scalar(select(func.count()).select_from(Identidade))==0


def test_historico_autoria_correcao_e_reenvio(sessao,fonte):
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)['identidade_id']
    a=acrescentar(sessao,obj);original=sessao.get(Evento,a['evento_id']).payload_canonico
    args=dict(comando_id='CORRIGIR',conta_id='CONTA-A1',identidade_id=obj,
              versao_esperada=2,tipo='correcao',nota='Correção fictícia.',corrigir_evento_id=a['evento_id'])
    # Act: correção é um novo evento e reenvio não duplica.
    c=acrescentar_historico(sessao,**args);sessao.commit()
    d=acrescentar_historico(sessao,**args);sessao.commit()
    # Assert: autor pessoa, data, lacre e evento original preservados.
    eventos=historico(sessao,obj)
    assert len(eventos)==3 and c['evento_id']==d['evento_id'] and d['reexecutado']
    assert all(e.ator_id=='PESSOA-A' and e.ocorrido_em is not None for e in eventos)
    assert sessao.get(Evento,a['evento_id']).payload_canonico==original
    assert verificar_cadeia(sessao,obj)[0]


@pytest.mark.parametrize('tipo',['avaliar','aceitar','aprovar','verificar','prorrogar','cancelar','ingressar'])
def test_ato_institucional_nao_disponivel(sessao,fonte,tipo):
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)['identidade_id']
    with pytest.raises(ValueError,match='não está disponível'):acrescentar(sessao,obj,tipo=tipo)
    assert len(historico(sessao,obj))==1


def test_correcao_alvo_invalido_versao_antiga_sem_efeito(sessao,fonte):
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)['identidade_id']
    outro=identidade(sessao,pid)['identidade_id'];externo=acrescentar(sessao,outro)
    with pytest.raises(ValueError):acrescentar(sessao,obj,tipo='correcao',corrigir_evento_id=externo['evento_id'])
    acrescentar(sessao,obj)
    with pytest.raises(ValueError,match='mudou'):acrescentar(sessao,obj)
    assert len(historico(sessao,obj))==2


@pytest.mark.parametrize('alvo',['referencia','identidade','evento'])
@pytest.mark.parametrize('operacao',['UPDATE','DELETE'])
def test_banco_recusa_sobrescrita_e_exclusao(sessao,fonte,alvo,operacao):
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)
    tabela,chave,coluna = {'referencia':('referencia_participacao_forms34',pid,'fonte_id'),
        'identidade':('identidade_forms34',obj['identidade_id'],'codigo'),
        'evento':('evento',obj['evento_id'],'tipo_evento')}[alvo]
    sql=(f'UPDATE {tabela} SET {coluna}={coluna} WHERE id=:id' if operacao=='UPDATE'
         else f'DELETE FROM {tabela} WHERE id=:id')
    # Act / Assert: proteção mesmo quando o domínio é contornado por SQL.
    with pytest.raises(IntegrityError):
        with sessao.begin_nested():sessao.execute(text(sql),{'id':chave})
    assert verificar_cadeia(sessao,obj['identidade_id'])[0]


def test_rollback_atomico_evento_e_identidade(sessao,fonte,monkeypatch):
    import app.infra_forms34 as infra
    pid=referencia(sessao,fonte)
    def falhar(*args,**kwargs):raise RuntimeError('Falha fictícia após evento')
    monkeypatch.setattr(infra,'registrar_auditoria',falhar)
    # Act: falha depois da reserva e evento, antes de completar a auditoria.
    with pytest.raises(RuntimeError):identidade(sessao,pid)
    sessao.commit()
    # Assert: transação do comando desfeita, inclusive identidade e evento.
    assert sessao.scalar(select(func.count()).select_from(Identidade))==0
    assert sessao.scalar(select(func.count()).select_from(Evento).where(Evento.cadeia_tipo=='forms34_objeto'))==0


@pytest.mark.parametrize('modo',['distintas','mesmo_comando','mesma_origem'])
def test_concorrencia_reserva_serializada(sessao,fonte,modo):
    pid=referencia(sessao,fonte);barreira=Barrier(2)
    mesma_chave=modo!='distintas'
    def tarefa(n):
        with Session(motor) as s:
            barreira.wait(timeout=10)
            out=reservar_identidade(s,comando_id='IGUAL' if modo=='mesmo_comando' else f'C-{n}',
                conta_id='CONTA-A1',participacao_id=pid,tipo='R',chave_origem='IGUAL' if mesma_chave else f'O-{n}')
            s.commit();return out
    # Act: duas conexões independentes, sincronizadas antes da disputa.
    with ThreadPoolExecutor(max_workers=2) as pool:resultados=list(pool.map(tarefa,[1,2]))
    # Assert: sem número/evento duplicado; reenvio retorna a mesma identidade.
    assert len({r['identidade_id'] for r in resultados})==(1 if mesma_chave else 2)
    assert sessao.scalar(select(func.count()).select_from(Identidade))==(1 if mesma_chave else 2)
    if modo=='mesmo_comando':assert sum(r['reexecutado'] for r in resultados)==1
    if modo=='distintas':assert {r['codigo'].split('-')[-1] for r in resultados}=={'R01','R02'}


def test_concorrencia_historico_versao_otimista(sessao,fonte):
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)['identidade_id'];barreira=Barrier(2)
    def tarefa(n):
        with Session(motor) as s:
            barreira.wait(timeout=10)
            try:
                r=acrescentar_historico(s,comando_id=f'H-{n}',conta_id='CONTA-A1',
                    identidade_id=obj,versao_esperada=1,tipo='anotacao',nota=f'Fictício {n}')
                s.commit();return r['permitido']
            except ValueError:
                s.rollback();return False
    with ThreadPoolExecutor(max_workers=2) as pool:resultados=list(pool.map(tarefa,[1,2]))
    assert sorted(resultados)==[False,True]
    assert len(historico(sessao,obj))==2 and verificar_cadeia(sessao,obj)[0]


def test_projecao_somente_fatos_e_escopo(sessao,fonte):
    # Arrange / Act: ausência não vira avaliação, nível, porcentagem ou zero.
    vazio=fatos_existentes(sessao,registro_ids=[fonte['registro_id']])
    assert vazio['quantidade_identidades'] is None and vazio['nivel_risco'] is None
    pid=referencia(sessao,fonte);obj=identidade(sessao,pid)
    lido=fatos_existentes(sessao,registro_ids=[fonte['registro_id']])
    # Assert: só identidade, autoria e versão observadas; nenhum indicador inventado.
    assert lido['quantidade_identidades']==1 and lido['fatos'][0]['codigo']==obj['codigo']
    assert lido['fatos'][0]['origem']['id']==fonte['fonte_id']
    for k in ['nivel_risco','percentual','prazo','estado_institucional']:assert lido['fatos'][0][k] is None
    assert fatos_existentes(sessao,registro_ids=[])['fatos']==[]
    assert fatos_existentes(sessao,registro_ids=[str(uuid4())])['fatos']==[]
    with pytest.raises(ValueError):fatos_existentes(sessao,registro_ids=None)


def test_migracao_aditiva_repetivel_e_banco_nao_teste_recusado():
    from migracoes.base_forms34 import aplicar
    from types import SimpleNamespace
    # Act / Assert: execução repetida não remove história; banco real recusado antes de conexão.
    aplicar(motor);aplicar(motor)
    with pytest.raises(RuntimeError):aplicar(SimpleNamespace(url=SimpleNamespace(database='demonstracao')))
