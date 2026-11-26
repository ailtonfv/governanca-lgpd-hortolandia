"""Carregamento autorizado. Não chama comandos, auditoria nem projeções gravadas."""
from dataclasses import dataclass
from datetime import datetime, timezone
from sqlalchemy import select
from app.modelos import (Registro, ParticipacaoForm2, AtribuicaoForm1Integral,
    IdentidadeForms34, Evento, HistoricoConferenciaForm1Integral, ComplementoForm2,
    VersaoForm1Integral)
from app.fila_form2 import pessoa_ativa, unidades, autorizado
from app.unidades_interface_form2 import secretarias_ativas
from app.fluxo_forms34 import estado


@dataclass(frozen=True)
class Escopo:
    perfil: str
    unidades: frozenset | None
    registros: frozenset | None


def escopo_da_conta(sessao, conta):
    pessoa = pessoa_ativa(sessao, conta)
    for papel, perfil in [('demo34_gabinete','Gabinete'), ('governanca_protecao_dados','DPO'),
                          ('demo34_relator','Comitê'), ('demo34_verificador','Comitê')]:
        if unidades(sessao, pessoa.id, papel):
            return Escopo(perfil, None, None)
    secretaria = unidades(sessao, pessoa.id, 'demo34_secretario')
    if secretaria:
        return Escopo('Secretário', frozenset(secretaria), None)
    from app.continuidade_apa import unidades_em_que_e_apa_atual
    secretaria = unidades_em_que_e_apa_atual(sessao, pessoa.id)
    if secretaria:
        return Escopo('APA', frozenset(secretaria), None)
    proprios = set()
    for p in sessao.scalars(select(ParticipacaoForm2).where(
            ParticipacaoForm2.tipo == 'principal', ParticipacaoForm2.responsavel_id == pessoa.id)):
        if autorizado(sessao, pessoa, p): proprios.add(p.registro_id)
    if unidades(sessao,pessoa.id,'aal_form2'):
        return Escopo('AAL', None, frozenset(proprios))
    raise PermissionError('Seu perfil não está habilitado para este dashboard.')


def pendencias_do_aal(sessao, conta_id, dados, agora):
    """Fila pessoal: responsável da participação, sem alterar filas institucionais."""
    from app.dashboard.consultas import operacao
    pessoa = pessoa_ativa(sessao, conta_id)
    pessoais = {**dados, 'objetos': [], 'participacoes': [
        p for p in dados['participacoes'] if p.responsavel_id == pessoa.id]}
    fila = next(q for q in operacao(pessoais, agora) if q['chave'] == 'fila_AAL')
    return {**fila, 'chave': 'minha_fila_AAL'}


def carregar(sessao, escopo):
    consulta = select(Registro)
    if escopo.unidades is not None:
        consulta = consulta.where(Registro.unidade_principal_atual_id.in_(escopo.unidades))
    if escopo.registros is not None:
        consulta = consulta.where(Registro.id.in_(escopo.registros))
    registros = list(sessao.scalars(consulta.order_by(Registro.codigo_lgpd)))
    ids = [r.id for r in registros]
    secretarias = list(secretarias_ativas(sessao))
    if escopo.unidades is not None: secretarias = [u for u in secretarias if u.id in escopo.unidades]
    if escopo.registros is not None:
        secretarias = [u for u in secretarias if u.id in {r.unidade_principal_atual_id for r in registros}]
    dados = dict(registros=registros, secretarias=secretarias, participacoes=[], objetos=[],
                 apresentacoes=[], complementos=[], snapshots={}, escopo=escopo)
    if not ids: return dados
    dados['participacoes'] = list(sessao.scalars(select(ParticipacaoForm2).where(ParticipacaoForm2.registro_id.in_(ids))))
    dados['apresentacoes'] = list(sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.registro_id.in_(ids)).order_by(HistoricoConferenciaForm1Integral.numero_apresentacao)))
    pids = [p.id for p in dados['participacoes']]
    dados['complementos'] = list(sessao.scalars(select(ComplementoForm2).where(ComplementoForm2.participacao_id.in_(pids))))
    dados['snapshots'] = {s.id:s for s in sessao.scalars(select(VersaoForm1Integral).where(VersaoForm1Integral.registro_id.in_(ids)))}
    eventos = list(sessao.scalars(select(Evento).where(Evento.registro_id.in_(ids),
        Evento.cadeia_tipo == 'forms34_objeto').order_by(Evento.sequencia_cadeia)))
    por_objeto = {}
    for ev in eventos: por_objeto.setdefault(ev.cadeia_id, []).append(ev)
    for obj in sessao.scalars(select(IdentidadeForms34).where(IdentidadeForms34.registro_id.in_(ids))):
        historia = por_objeto.get(obj.id, [])
        if not any(e.tipo_evento == 'f34_ingresso' for e in historia): continue
        # Reconstrói pelo domínio, incluindo verificação da cadeia. Reserva não conta.
        dados['objetos'].append(dict(obj=obj, estado=estado(sessao,obj.id), eventos=historia))
    return dados


def categorias_circulacao(dados):
    """Somente alternativas estruturadas, nunca campos de destinatários em texto livre."""
    from app.form2_rev212 import indice_valores
    from app.respostas_form2 import definicao_revisao
    from app.extensao_medidas_form1 import catalogo_efetivo
    try:
        opcoes={q['id']:{a['codigo']:a['rotulo'] for a in q['alternativas']}
                for q in definicao_revisao(8)['itens'] if q['id'] in ('F2-8.1','F2-8.2','F2-8.7')}
        resultado={r.id:dict(categorias=set(),instrumentos=set()) for r in dados['registros']}
        for p in dados['participacoes']:
            if p.tipo!='principal':continue
            valores=indice_valores(p.conteudo or {})
            for chave,vs in valores.items():
                q=chave.removeprefix('opcao:').split('#')[0]
                if not chave.startswith('opcao:') or q not in opcoes:continue
                for v in vs if isinstance(vs,list) else [vs]:
                    rotulo=opcoes[q].get(v)
                    if not rotulo: continue
                    if q=='F2-8.7': resultado[p.registro_id]['instrumentos'].add(rotulo)
                    elif v not in ('SIM','NAO','A_CONFIRMAR'):
                        resultado[p.registro_id]['categorias'].add(rotulo)
        ultimas={a.registro_id:a for a in dados['apresentacoes'] if a.confirmada_em}
        for rid,a in ultimas.items():
            s=dados['snapshots'].get(a.snapshot_id)
            if not s:continue
            fonte=s.conteudo.get('form1_integral',{})
            campo=catalogo_efetivo(fonte).get('10.2')
            vs=fonte.get('respostas',{}).get('10.2',[])
            for v in vs if isinstance(vs,list) else [vs]:
                if campo and v in campo.alternativas:resultado[rid]['categorias'].add(v)
        return resultado
    except (FileNotFoundError,KeyError,ValueError):
        return None  # Sem catálogo íntegro não se apresenta zero como resultado.


def rotulo_perfil(sessao, conta_id, escopo):
    if escopo.perfil != 'AAL/ARP': return escopo.perfil
    pessoa=pessoa_ativa(sessao,conta_id)
    papeis=[]
    if unidades(sessao,pessoa.id,'aal_form2'):papeis.append('AAL')
    if unidades(sessao,pessoa.id,'preenchedor'):papeis.append('ARP')
    return ' e '.join(papeis) or 'Consulta'
