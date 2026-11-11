"""Preparação demonstrativa: política restrita aprovada na FORM02_05.

Não importa comandos/validadores nucleares, não submete e não decide.
O chamador controla a transação; nenhum serviço confirma gravação parcialmente.
"""
from datetime import datetime, timezone
from copy import deepcopy
import uuid

from sqlalchemy import func, inspect, select, text

from app.comandos import abrir_comando, fechar_comando
from app.continuidade_apa import pessoa_e_apa_em_exercicio
from app.eventos import registrar_evento, registrar_auditoria, lacre, verificar_cadeia
from app.modelos import (Conta, Pessoa, Registro, Ciclo, Evento, VersaoForm1Integral,
                        HabilitacaoForm2Preparacao, PreparacaoForm2)
from app.origem_form2 import canonico, ler_origem
from app.form2_rev212 import ramos_origem
from app.respostas_form2 import ENVELOPE_V2, aplicar_bloco, aplicar_revisao

POLITICA = "F2-DEMO-05-v1"
ENVELOPE = "F2-DEMO-PREP-v1"
ENVELOPES_LEGIVEIS = {ENVELOPE, ENVELOPE_V2}
LIMITE_ANOTACAO = 2000


def agora():
    return datetime.now(timezone.utc)


def _travar(sessao, registro_id):
    # Mesma ordem para habilitar/revogar/designar/salvar; sem tocar nas projeções F1.
    sessao.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:chave, 0))"),
                   {"chave": "form2-preparacao:" + registro_id})


def _auditar(sessao, tipo, ator_tipo, ator_id, dados, comando_id=None):
    sessao.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('form2-auditoria', 0))"))
    registrar_auditoria(sessao, tipo, ator_tipo, ator_id, dados, comando_id=comando_id)


def _negar(sessao, conta_id, registro_id, motivo, comando=None):
    conta = sessao.get(Conta, conta_id)
    _auditar(sessao, "form2_tentativa_negada", "pessoa" if conta else "desconhecido",
             conta.pessoa_id if conta else conta_id,
             {"registro_id": registro_id, "motivo": motivo},
             None if comando is None else comando.id)
    resposta = {"permitido": False, "motivo": motivo}
    return fechar_comando(comando, resposta) if comando else dict(resposta, reexecutado=False)


def _acesso(sessao, conta_id, registro_id, momento):
    conta = sessao.get(Conta, conta_id)
    pessoa = sessao.get(Pessoa, conta.pessoa_id) if conta and conta.ativa else None
    registro = sessao.get(Registro, registro_id)
    if not pessoa or not pessoa.ativa or not registro:
        raise PermissionError("Conta, pessoa ou Registro indisponível.")
    hab = sessao.scalar(select(HabilitacaoForm2Preparacao).where(
        HabilitacaoForm2Preparacao.registro_id == registro_id,
        HabilitacaoForm2Preparacao.pessoa_id == pessoa.id,
    ).execution_options(populate_existing=True))
    if (not hab or not hab.ativa or hab.versao_politica != POLITICA
            or not hab.vigente_de <= momento < hab.vigente_ate):
        raise PermissionError("Sem habilitação demonstrativa vigente para este Registro.")
    if hab.finalidade == "acompanhar" and not pessoa_e_apa_em_exercicio(
            sessao, pessoa.id, registro.unidade_principal_atual_id, momento):
        raise PermissionError("A consulta administrativa exige APA em exercício.")
    return pessoa, registro, hab


def registrar_habilitacao_controlada(sessao, *, comando_id, registro_id, pessoa_id,
                                    finalidade, vigente_de, vigente_ate,
                                    aprovacao_referencia, fundamento, ativa=True, momento=None):
    """Somente executor local: decisão individual documentada, nunca rota HTTP.

    O operador deve conferir aprovação do responsável funcional antes de executar.
    A aplicação não infere aprovação de um nome de arquivo ou do papel do agente.
    """
    momento = momento or agora()
    if (finalidade not in {"preparar", "acompanhar"} or type(ativa) is not bool
            or not all(isinstance(x, str) and 1 <= len(x.strip()) <= 250
                       for x in (aprovacao_referencia, fundamento))
            or vigente_de.tzinfo is None or vigente_ate.tzinfo is None
            or vigente_ate <= vigente_de):
        raise ValueError("Habilitação, vigência ou referência da aprovação inválida.")
    _travar(sessao, registro_id)
    registro, pessoa = sessao.get(Registro, registro_id), sessao.get(Pessoa, pessoa_id)
    if not registro or not pessoa or not pessoa.ativa:
        raise ValueError("Registro ou pessoa indisponível.")
    parametros = dict(registro_id=registro_id, pessoa_id=pessoa_id, finalidade=finalidade,
                      vigente_de=vigente_de.isoformat(), vigente_ate=vigente_ate.isoformat(),
                      aprovacao_referencia=aprovacao_referencia, fundamento=fundamento,
                      ativa=ativa, politica=POLITICA)
    comando, repeticao = abrir_comando(sessao, comando_id, "habilitar_form2_demo", parametros,
                                       "conta_servico", "executor_controlado_form2")
    if repeticao is not None:
        return repeticao
    hab = sessao.scalar(select(HabilitacaoForm2Preparacao).where(
        HabilitacaoForm2Preparacao.registro_id == registro_id,
        HabilitacaoForm2Preparacao.pessoa_id == pessoa_id))
    if hab is None:
        hab = HabilitacaoForm2Preparacao(id=str(uuid.uuid4()), registro_id=registro_id,
                                        pessoa_id=pessoa_id)
        sessao.add(hab)
    hab.finalidade, hab.ativa = finalidade, ativa
    hab.vigente_de, hab.vigente_ate = vigente_de, vigente_ate
    hab.fundamento, hab.versao_politica = fundamento, POLITICA
    hab.aprovacao_referencia, hab.registrado_em = aprovacao_referencia, momento
    sessao.flush()
    registrar_evento(sessao, comando, "form2_habilitacao", hab.id,
                      "habilitacao_form2_registrada", parametros,
                      registro_id=registro_id, versao_regra=POLITICA)
    _auditar(sessao, "form2_habilitacao_registrada", "conta_servico", "executor_controlado_form2",
             parametros, comando.id)
    return fechar_comando(comando, {"permitido": True, "habilitacao_id": hab.id,
                                    "motivo": "Habilitação demonstrativa registrada."})


def _evento_preparacao(sessao, comando, prep, tipo):
    dados = {"preparacao_id": prep.id, "registro_id": prep.registro_id,
             "snapshot_id": prep.snapshot_id, "lacre_origem": prep.lacre_origem,
             "estrutura_origem": prep.estrutura_origem, "preparador_id": prep.preparador_id,
             "designado_por": prep.designado_por, "designado_em": prep.designado_em.isoformat(),
             "habilitacao_id": prep.habilitacao_id, "versao_envelope": prep.versao_envelope,
             "versao_rascunho": prep.versao_rascunho, "conteudo": deepcopy(prep.conteudo),
             "lacre_conteudo": prep.lacre_conteudo, "salvo_por": prep.salvo_por,
             "salvo_em": prep.salvo_em.isoformat(),
             "papel_exercido": "APA_designante" if tipo == "form2_preparacao_iniciada" else "preparador_demonstrativo",
             "submissao_habilitada": False}
    registrar_evento(sessao, comando, "form2_preparacao", prep.id, tipo, dados,
                      registro_id=prep.registro_id, ciclo_id=prep.ciclo_id, versao_regra=POLITICA)
    _auditar(sessao, tipo, comando.ator_tipo, comando.ator_id,
             {k: v for k, v in dados.items() if k != "conteudo"}, comando.id)


def _historico_integro(sessao, prep):
    if (prep.versao_envelope not in ENVELOPES_LEGIVEIS or prep.versao_politica != POLITICA
            or prep.lacre_conteudo != lacre(canonico(prep.conteudo))
            or not verificar_cadeia(sessao, prep.id)[0]):
        raise ValueError("Integridade ou versão da preparação não confere.")
    eventos = sessao.scalars(select(Evento).where(Evento.cadeia_id == prep.id)
                            .order_by(Evento.sequencia_cadeia)).all()
    if not eventos:
        raise ValueError("Histórico da preparação ausente.")
    ultimo = eventos[-1].conteudo
    if (ultimo.get("conteudo") != prep.conteudo
            or ultimo.get("versao_rascunho") != prep.versao_rascunho
            or ultimo.get("snapshot_id") != prep.snapshot_id
            or ultimo.get("lacre_origem") != prep.lacre_origem
            or ultimo.get("preparador_id") != prep.preparador_id):
        raise ValueError("Projeção da preparação diverge do histórico.")
    return eventos


def iniciar_preparacao(sessao, *, comando_id, conta_id, registro_id, snapshot_id,
                      preparador_id, momento=None):
    """APA designa pessoa previamente habilitada e cria preparação vazia."""
    momento = momento or agora()
    _travar(sessao, registro_id)
    try:
        pessoa, registro, _ = _acesso(sessao, conta_id, registro_id, momento)
        if not pessoa_e_apa_em_exercicio(sessao, pessoa.id, registro.unidade_principal_atual_id, momento):
            raise PermissionError("Somente o APA em exercício pode designar o preparador.")
        hab = sessao.scalar(select(HabilitacaoForm2Preparacao).where(
            HabilitacaoForm2Preparacao.registro_id == registro_id,
            HabilitacaoForm2Preparacao.pessoa_id == preparador_id,
            HabilitacaoForm2Preparacao.finalidade == "preparar",
            HabilitacaoForm2Preparacao.ativa.is_(True),
            HabilitacaoForm2Preparacao.versao_politica == POLITICA,
            HabilitacaoForm2Preparacao.vigente_de <= momento,
            HabilitacaoForm2Preparacao.vigente_ate > momento))
        alvo = sessao.get(Pessoa, preparador_id)
        if not hab or not alvo or not alvo.ativa or not sessao.scalar(select(Conta.id).where(
                Conta.pessoa_id == preparador_id, Conta.ativa.is_(True))):
            raise PermissionError("Preparador sem habilitação específica vigente ou conta ativa.")
        origem = ler_origem(sessao, registro_id, snapshot_id)
    except (PermissionError, ValueError) as erro:
        return _negar(sessao, conta_id, registro_id, str(erro))
    parametros = dict(conta_id=conta_id, registro_id=registro_id, snapshot_id=snapshot_id,
                      preparador_id=preparador_id)
    comando, repeticao = abrir_comando(sessao, comando_id, "iniciar_form2_preparacao", parametros,
                                       "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    existente = sessao.scalar(select(PreparacaoForm2).where(
        PreparacaoForm2.registro_id == registro_id, PreparacaoForm2.snapshot_id == snapshot_id))
    if existente:
        if existente.preparador_id != preparador_id:
            return _negar(sessao, conta_id, registro_id, "Origem já atribuída a outro preparador; substituição fora deste recorte.", comando)
        return fechar_comando(comando, {"permitido": True, "preparacao_id": existente.id,
                                        "alterado": False, "motivo": "Preparação já existente."})
    ciclo = sessao.scalar(select(Ciclo).where(Ciclo.registro_id == registro_id,
                                            Ciclo.numero == registro.ciclo_atual))
    if not ciclo or ciclo.situacao != "ativo" or registro.estado_atual != "em_andamento":
        return _negar(sessao, conta_id, registro_id, "Preparação exige Registro em andamento e ciclo ativo.", comando)
    conteudo = {"anotacao_preparatoria": ""}
    prep = PreparacaoForm2(id=str(uuid.uuid4()), registro_id=registro_id, ciclo_id=ciclo.id,
        snapshot_id=snapshot_id, lacre_origem=origem["snapshot"].lacre,
        estrutura_origem=origem["estrutura"], preparador_id=preparador_id, habilitacao_id=hab.id,
        designado_por=pessoa.id, designado_em=momento, versao_politica=POLITICA,
        versao_envelope=ENVELOPE, conteudo=conteudo, versao_rascunho=1,
        salvo_por=pessoa.id, salvo_em=momento, lacre_conteudo=lacre(canonico(conteudo)))
    sessao.add(prep)
    sessao.flush()
    _evento_preparacao(sessao, comando, prep, "form2_preparacao_iniciada")
    return fechar_comando(comando, {"permitido": True, "preparacao_id": prep.id,
                                    "versao": 1, "motivo": "Preparador designado; rascunho demonstrativo iniciado."})


def salvar_preparacao(sessao, *, comando_id, conta_id, registro_id, preparacao_id,
                     versao_lida, conteudo, momento=None):
    momento = momento or agora()
    _travar(sessao, registro_id)
    try:
        pessoa, registro, hab = _acesso(sessao, conta_id, registro_id, momento)
        prep = sessao.get(PreparacaoForm2, preparacao_id, populate_existing=True)
        if (not prep or prep.registro_id != registro_id or prep.preparador_id != pessoa.id
                or hab.finalidade != "preparar" or hab.id != prep.habilitacao_id):
            raise PermissionError("Somente o preparador designado e habilitado pode editar.")
        ciclo = sessao.get(Ciclo, prep.ciclo_id)
        if (registro.estado_atual != "em_andamento" or not ciclo or ciclo.situacao != "ativo"
                or ciclo.numero != registro.ciclo_atual):
            raise PermissionError("Preparação fora do ciclo ativo do Registro.")
        origem = ler_origem(sessao, registro_id, prep.snapshot_id)
        if origem["snapshot"].lacre != prep.lacre_origem or origem["estrutura"] != prep.estrutura_origem:
            raise ValueError("Referência histórica da preparação não confere.")
        _historico_integro(sessao, prep)
    except (PermissionError, ValueError) as erro:
        return _negar(sessao, conta_id, registro_id, str(erro))
    parametros = dict(conta_id=conta_id, registro_id=registro_id, preparacao_id=preparacao_id,
                      versao_lida=versao_lida, conteudo=conteudo)
    comando, repeticao = abrir_comando(sessao, comando_id, "salvar_form2_preparacao", parametros,
                                       "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if type(versao_lida) is not int or versao_lida != prep.versao_rascunho:
        return _negar(sessao, conta_id, registro_id, "Rascunho desatualizado; recarregue antes de salvar.", comando)
    if (not isinstance(conteudo, dict) or set(conteudo) != {"anotacao_preparatoria"}
            or not isinstance(conteudo["anotacao_preparatoria"], str)
            or len(conteudo["anotacao_preparatoria"]) > LIMITE_ANOTACAO
            or "\x00" in conteudo["anotacao_preparatoria"]):
        return _negar(sessao, conta_id, registro_id, "Anotação inválida: texto simples de até 2.000 caracteres, sem campos extras.", comando)
    if prep.lacre_conteudo != lacre(canonico(prep.conteudo)):
        return _negar(sessao, conta_id, registro_id, "Integridade do rascunho não confere.", comando)
    novo_conteudo = deepcopy(prep.conteudo)
    novo_conteudo["anotacao_preparatoria"] = conteudo["anotacao_preparatoria"]
    prep.conteudo = novo_conteudo
    prep.versao_rascunho += 1
    prep.salvo_por, prep.salvo_em = pessoa.id, momento
    prep.lacre_conteudo = lacre(canonico(novo_conteudo))
    _evento_preparacao(sessao, comando, prep, "form2_preparacao_salva")
    sessao.flush()
    return fechar_comando(comando, {"permitido": True, "preparacao_id": prep.id,
        "versao": prep.versao_rascunho, "motivo": "Anotação salva no rascunho demonstrativo, sem submissão."})


def salvar_respostas_bloco(sessao, *, comando_id, conta_id, registro_id, preparacao_id,
                           bloco, versao_lida, alteracoes, complementos=None,
                           reativar=None, momento=None, revisao=False):
    """Salva respostas homologadas do bloco sem concluir ou submeter o FORM 2."""
    momento = momento or agora()
    _travar(sessao, registro_id)
    try:
        pessoa, registro, hab = _acesso(sessao, conta_id, registro_id, momento)
        prep = sessao.get(PreparacaoForm2, preparacao_id, populate_existing=True)
        if (not prep or prep.registro_id != registro_id or prep.preparador_id != pessoa.id
                or hab.finalidade != "preparar" or hab.id != prep.habilitacao_id):
            raise PermissionError("Somente o preparador designado e habilitado pode editar.")
        ciclo = sessao.get(Ciclo, prep.ciclo_id)
        if (registro.estado_atual != "em_andamento" or not ciclo or ciclo.situacao != "ativo"
                or ciclo.numero != registro.ciclo_atual):
            raise PermissionError("Preparação fora do ciclo ativo do Registro.")
        origem = ler_origem(sessao, registro_id, prep.snapshot_id)
        if origem["snapshot"].lacre != prep.lacre_origem or origem["estrutura"] != prep.estrutura_origem:
            raise ValueError("Referência histórica da preparação não confere.")
        _historico_integro(sessao, prep)
    except (PermissionError, ValueError) as erro:
        return _negar(sessao, conta_id, registro_id, str(erro))
    parametros = dict(conta_id=conta_id, registro_id=registro_id, preparacao_id=preparacao_id,
                      bloco=bloco, versao_lida=versao_lida, alteracoes=alteracoes,
                      complementos=complementos or {}, reativar=sorted(reativar or []))
    operacao = "salvar_form2_rascunho_rev212" if revisao else "salvar_form2_respostas_bloco"
    comando, repeticao = abrir_comando(sessao, comando_id, operacao,
                                       parametros, "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if type(versao_lida) is not int or versao_lida != prep.versao_rascunho:
        return _negar(sessao, conta_id, registro_id,
                      "Rascunho desatualizado; recarregue antes de salvar.", comando)
    if prep.lacre_conteudo != lacre(canonico(prep.conteudo)):
        return _negar(sessao, conta_id, registro_id, "Integridade do rascunho não confere.", comando)
    try:
        if revisao:
            novo_conteudo, resumo = aplicar_revisao(prep.conteudo, bloco, alteracoes, ramos_origem(origem))
        else:
            novo_conteudo, resumo = aplicar_bloco(
                prep.conteudo, bloco=bloco, alteracoes=alteracoes,
                complementos=complementos, reativar=reativar,
                proxima_versao=prep.versao_rascunho + 1,
            )
    except (PermissionError, ValueError, FileNotFoundError, OSError, KeyError, TypeError) as erro:
        return _negar(sessao, conta_id, registro_id, str(erro), comando)
    prep.conteudo = novo_conteudo
    prep.versao_envelope = ENVELOPE_V2
    prep.versao_rascunho += 1
    prep.salvo_por, prep.salvo_em = pessoa.id, momento
    prep.lacre_conteudo = lacre(canonico(novo_conteudo))
    _evento_preparacao(sessao, comando, prep, "form2_rascunho_rev212_salvo" if revisao else "form2_respostas_bloco_salvas")
    sessao.flush()
    return fechar_comando(comando, {"permitido": True, "preparacao_id": prep.id,
        "versao": prep.versao_rascunho, "bloco": bloco, "resumo": resumo,
        "motivo": "Respostas salvas no rascunho, sem conclusão, parecer ou submissão."})


def _preparacoes_visiveis(sessao, hab, e_apa):
    consulta = select(PreparacaoForm2).where(PreparacaoForm2.registro_id == hab.registro_id)
    if not e_apa:
        consulta = consulta.where(PreparacaoForm2.preparador_id == hab.pessoa_id,
                                  PreparacaoForm2.habilitacao_id == hab.id)
    preparacoes = sessao.scalars(consulta.order_by(PreparacaoForm2.designado_em)).all()
    if not e_apa and not preparacoes:
        raise PermissionError("A consulta à origem exige designação pelo APA neste Registro.")
    return preparacoes


def _pode_editar_preparacao(sessao, prep, pessoa, hab, registro):
    ciclo = sessao.get(Ciclo, prep.ciclo_id) if prep else None
    return bool(prep and prep.preparador_id == pessoa.id and hab.finalidade == "preparar"
                and ciclo and ciclo.situacao == "ativo" and ciclo.numero == registro.ciclo_atual
                and registro.estado_atual == "em_andamento")


def _candidatos_habilitados(registro_id, momento):
    return (select(Pessoa).join(HabilitacaoForm2Preparacao,
            Pessoa.id == HabilitacaoForm2Preparacao.pessoa_id).where(
                HabilitacaoForm2Preparacao.registro_id == registro_id,
                HabilitacaoForm2Preparacao.finalidade == "preparar",
                HabilitacaoForm2Preparacao.ativa.is_(True),
                HabilitacaoForm2Preparacao.versao_politica == POLITICA,
                HabilitacaoForm2Preparacao.vigente_de <= momento,
                HabilitacaoForm2Preparacao.vigente_ate > momento, Pessoa.ativa.is_(True),
                select(Conta.id).where(Conta.pessoa_id == Pessoa.id, Conta.ativa.is_(True)).exists()))


def _ciclo_em_andamento(sessao, registro):
    return registro.estado_atual == "em_andamento" and bool(sessao.scalar(
        select(Ciclo.id).where(Ciclo.registro_id == registro.id,
                               Ciclo.numero == registro.ciclo_atual, Ciclo.situacao == "ativo")
    ))


def projetar_trabalho_aal(sessao, preparacoes):
    """Distingue designação, salvamento vazio e observação já registrada, inclusive apagada depois."""
    if not preparacoes:
        return {}
    anotacao = Evento.conteudo["conteudo"]["anotacao_preparatoria"].as_string()
    tipos_estruturados = ("form2_respostas_bloco_salvas", "form2_rascunho_rev212_salvo")
    estruturado = Evento.tipo_evento.in_(tipos_estruturados)
    consulta = select(Evento.cadeia_id, func.bool_or(estruturado | anotacao.regexp_match(r"\S"))).where(
        Evento.cadeia_tipo == "form2_preparacao",
        Evento.cadeia_id.in_([p.id for p in preparacoes]),
        Evento.tipo_evento.in_(("form2_preparacao_salva", *tipos_estruturados)),
        Evento.conteudo["papel_exercido"].as_string() == "preparador_demonstrativo",
    ).group_by(Evento.cadeia_id)
    return dict(sessao.execute(consulta).all())


def projetar_navegacao_preparacao(sessao, *, conta_id, registro_id, momento=None):
    """Somente links autorizados; não consulta conteúdo nem produz ato/auditoria."""
    if not all(inspect(sessao.connection()).has_table(t) for t in
               ("preparacao_form2", "habilitacao_form2_preparacao")):
        return None
    momento = momento or agora()
    try:
        pessoa, registro, hab = _acesso(sessao, conta_id, registro_id, momento)
        e_apa = bool(pessoa_e_apa_em_exercicio(sessao, pessoa.id, registro.unidade_principal_atual_id, momento))
        visiveis = _preparacoes_visiveis(sessao, hab, e_apa)
    except PermissionError:
        return None
    editaveis = [p for p in visiveis if _pode_editar_preparacao(sessao, p, pessoa, hab, registro)]
    prep = editaveis[-1] if editaveis else visiveis[-1] if visiveis else None
    resumo = None
    if prep:
        versao, registrada_em = sessao.execute(select(
            VersaoForm1Integral.numero, VersaoForm1Integral.preparado_em).where(
            VersaoForm1Integral.id == prep.snapshot_id, VersaoForm1Integral.registro_id == registro.id)).one()
        trabalho = projetar_trabalho_aal(sessao, [prep])
        autor = sessao.get(Pessoa, prep.salvo_por)
        resumo = {"origem": versao, "origem_em": registrada_em, "salva": prep.id in trabalho,
                  "trabalhada": trabalho.get(prep.id, False), "rascunho": prep.versao_rascunho, "salvo_em": prep.salvo_em,
                  "autor": f"{autor.matricula} — {autor.nome}" if autor else None}
    pode_iniciar = bool(not prep and e_apa and _ciclo_em_andamento(sessao, registro)
                        and sessao.scalar(select(VersaoForm1Integral.id).where(
                            VersaoForm1Integral.registro_id == registro.id).limit(1))
                        and sessao.scalar(_candidatos_habilitados(registro.id, momento).limit(1)))
    return {"preparacao_id": prep.id if prep else None, "resumo": resumo, "pode_iniciar": pode_iniciar,
            "pode_editar": bool(editaveis), "e_apa": e_apa}


def consultar_preparacao(sessao, *, conta_id, registro_id, preparacao_id=None,
                        snapshot_id=None, momento=None):
    momento = momento or agora()
    try:
        pessoa, registro, hab = _acesso(sessao, conta_id, registro_id, momento)
        e_apa = bool(pessoa_e_apa_em_exercicio(sessao, pessoa.id, registro.unidade_principal_atual_id, momento))
        visiveis = _preparacoes_visiveis(sessao, hab, e_apa)
        prep = next((p for p in visiveis if p.id == preparacao_id), None)
        if preparacao_id and not prep:
            raise PermissionError("Preparação indisponível para consulta.")
        consulta_snapshots = select(VersaoForm1Integral).where(VersaoForm1Integral.registro_id == registro_id)
        referencia = prep
        if not e_apa:
            origens_atribuidas = {p.snapshot_id: p for p in visiveis}
            consulta_snapshots = consulta_snapshots.where(VersaoForm1Integral.id.in_(origens_atribuidas))
            if snapshot_id and snapshot_id not in origens_atribuidas:
                raise PermissionError("Origem indisponível para consulta.")
            referencia = prep or origens_atribuidas.get(snapshot_id)
        if prep and snapshot_id and prep.snapshot_id != snapshot_id:
            raise PermissionError("Origem incompatível com a preparação selecionada.")
        sid = prep.snapshot_id if prep else snapshot_id
        origem = ler_origem(sessao, registro_id, sid) if sid else None
        historico = []
        if referencia:
            if origem["snapshot"].lacre != referencia.lacre_origem or origem["estrutura"] != referencia.estrutura_origem:
                raise ValueError("Integridade da preparação não confere.")
            historico = _historico_integro(sessao, referencia)
        snapshots = sessao.scalars(consulta_snapshots.order_by(VersaoForm1Integral.numero)).all()
        candidatos = sessao.scalars(_candidatos_habilitados(registro_id, momento)).all() if e_apa else []
        _auditar(sessao, "form2_consulta", "pessoa", pessoa.id,
                 {"registro_id": registro_id, "preparacao_id": referencia.id if referencia else None,
                  "snapshot_id": sid, "politica": POLITICA})
        editaveis = [item.id for item in visiveis
                     if _pode_editar_preparacao(sessao, item, pessoa, hab, registro)]
        pode_editar = bool(prep and prep.id in editaveis)
        return {"permitido": True, "registro": registro, "pessoa": pessoa,
                "preparacao": prep, "preparacoes": visiveis, "origem": origem,
                "snapshots": snapshots, "candidatos": candidatos, "e_apa": e_apa,
                "ciclo_em_andamento": _ciclo_em_andamento(sessao, registro) if e_apa else False,
                "pode_editar": pode_editar, "preparacoes_editaveis": editaveis,
                "trabalho_aal": projetar_trabalho_aal(sessao, visiveis),
                "historico": historico, "politica": POLITICA}
    except (PermissionError, ValueError) as erro:
        return _negar(sessao, conta_id, registro_id, str(erro))
