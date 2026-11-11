"""Conferência interna preparatória entre ARP e APA."""

import uuid

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.continuidade_apa import apa_em_exercicio, pessoa_e_apa_em_exercicio
from app.eventos import registrar_auditoria, registrar_evento
from app.permissoes import tem_papel
from app.modelos import (
    AtribuicaoForm1Integral, ConferenciaInternaForm1Integral,
    HistoricoConferenciaForm1Integral, Pessoa, Registro, VersaoForm1Integral,
)
from app.rascunho_form1_integral import (
    _agora_utc, _ator, _ciclo, _contexto_autorizado, _lacre, _negar,
    _rascunho_bloqueado, _validar_versao,
)
from app.submissao_form1_integral import preparar_snapshot_na_transacao


TIPO_COMANDO = "solicitar_conferencia_interna_form1_integral"
SITUACAO = "aguardando_conferencia_interna_apa"
TIPO_COMANDO_DEVOLUCAO = "devolver_conferencia_interna_form1_integral"
SITUACAO_DEVOLVIDA = "devolvida_para_ajustes"
TIPO_COMANDO_CONFIRMACAO = "confirmar_conferencia_interna_form1_integral"
SITUACAO_CONFIRMADA = "conferencia_interna_confirmada"
LIMITE_JUSTIFICATIVA = 2000


def _ultimo_historico(sessao, registro_id, *, bloquear=False):
    consulta = (
        select(HistoricoConferenciaForm1Integral)
        .where(HistoricoConferenciaForm1Integral.registro_id == registro_id)
        .order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc())
        .limit(1)
    )
    if bloquear:
        consulta = consulta.with_for_update()
    return sessao.scalars(consulta).first()


def solicitar_conferencia_interna_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, momento=None,
):
    """Preserva a versão apresentada ao APA sem submeter ou concluir o FORM 1."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
    }
    _conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, TIPO_COMANDO, parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_versao(versao_lida)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, problema,
        )
    registro, pessoa_id, ator_tipo, ator_id, problema = _contexto_autorizado(
        sessao, conta_id, registro_id
    )
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, problema,
        )
    rascunho = _rascunho_bloqueado(sessao, registro_id)
    if rascunho is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, "inicie o rascunho integral antes de solicitar a conferência",
        )
    if rascunho.versao_rascunho != versao_lida:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO,
            "rascunho integral desatualizado: recarregue antes de solicitar a conferência",
            versao_lida=versao_lida, versao_atual=rascunho.versao_rascunho,
        )
    if _lacre(rascunho.conteudo) != rascunho.lacre_conteudo:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, "lacre do rascunho integral não confere",
        )
    existente = sessao.scalars(
        select(ConferenciaInternaForm1Integral)
        .where(ConferenciaInternaForm1Integral.registro_id == registro_id)
        .with_for_update()
    ).one_or_none()
    if existente is not None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO,
            "já existe solicitação de conferência interna aguardando o APA",
            versao_rascunho=existente.versao_rascunho,
        )
    exercicio = apa_em_exercicio(sessao, registro.unidade_principal_atual_id, momento)
    if exercicio is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO, "a Secretaria não possui APA em exercício",
        )

    ultimo = _ultimo_historico(sessao, registro_id, bloquear=True)
    if (
        ultimo is not None
        and ultimo.situacao == SITUACAO_DEVOLVIDA
        and rascunho.versao_rascunho <= ultimo.versao_rascunho
    ):
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO,
            "salve ao menos um ajuste no rascunho antes de solicitar nova conferência",
            versao_devolvida=ultimo.versao_rascunho,
            versao_atual=rascunho.versao_rascunho,
        )

    snapshot, evento_snapshot = preparar_snapshot_na_transacao(
        sessao, comando=comando, registro=registro, rascunho=rascunho,
        pessoa_id=pessoa_id, momento=momento, reusar_existente=True,
    )
    ordem = 2 if evento_snapshot is not None else 1
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd, TIPO_COMANDO,
        {
            "registro_id": registro.id,
            "snapshot_id": snapshot.id,
            "numero_snapshot": snapshot.numero,
            "versao_rascunho": rascunho.versao_rascunho,
            "lacre_snapshot": snapshot.lacre,
            "solicitada_por_id": pessoa_id,
            "apa_em_exercicio_no_momento_id": exercicio["pessoa_id"],
            "situacao": SITUACAO,
            "numero_apresentacao": (
                1 if ultimo is None else ultimo.numero_apresentacao + 1
            ),
            "papel_ator": "ARP",
            "ato_preparatorio": True,
            "submissao_habilitada": False,
            "conclusao_institucional": False,
        },
        ordem_no_comando=ordem,
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    sessao.add(ConferenciaInternaForm1Integral(
        registro_id=registro.id,
        situacao=SITUACAO,
        versao_projecao=1,
        snapshot_id=snapshot.id,
        versao_rascunho=rascunho.versao_rascunho,
        solicitada_por_id=pessoa_id,
        solicitada_em=momento,
        apa_em_exercicio_no_momento_id=exercicio["pessoa_id"],
        evento_solicitacao_id=evento.id,
    ))
    numero_apresentacao = 1 if ultimo is None else ultimo.numero_apresentacao + 1
    sessao.add(HistoricoConferenciaForm1Integral(
        id=str(uuid.uuid4()),
        registro_id=registro.id,
        numero_apresentacao=numero_apresentacao,
        situacao=SITUACAO,
        versao=1,
        snapshot_id=snapshot.id,
        versao_rascunho=rascunho.versao_rascunho,
        solicitada_por_id=pessoa_id,
        solicitada_em=momento,
        apa_em_exercicio_no_momento_id=exercicio["pessoa_id"],
        evento_solicitacao_id=evento.id,
    ))
    registrar_auditoria(
        sessao, "conferencia_interna_form1_solicitada", ator_tipo, ator_id,
        {
            "registro_id": registro.id,
            "snapshot_id": snapshot.id,
            "versao_rascunho": rascunho.versao_rascunho,
            "apa_em_exercicio_no_momento_id": exercicio["pessoa_id"],
            "numero_apresentacao": numero_apresentacao,
            "papel_ator": "ARP",
            "submissao_habilitada": False,
        },
        comando_id=comando.id,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "Conferência interna do FORM 1 solicitada ao APA",
        "registro_id": registro.id,
        "snapshot_id": snapshot.id,
        "numero_snapshot": snapshot.numero,
        "versao_rascunho": rascunho.versao_rascunho,
        "evento": evento.sequencia_cadeia,
        "situacao": SITUACAO,
        "numero_apresentacao": numero_apresentacao,
        "submissao_habilitada": False,
    })
    sessao.flush()
    return resultado


def devolver_conferencia_interna_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida,
    justificativa, momento=None,
):
    """Devolve ao ARP o snapshot apresentado, sem submeter o FORM 1."""

    momento = momento or _agora_utc()
    justificativa = (justificativa or "").strip()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
        "justificativa": justificativa,
    }
    _conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, TIPO_COMANDO_DEVOLUCAO, parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    if not justificativa:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO, "informe a justificativa da devolução",
        )
    if len(justificativa) > LIMITE_JUSTIFICATIVA:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO,
            f"a justificativa deve ter no máximo {LIMITE_JUSTIFICATIVA} caracteres",
        )

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None or not pessoa_e_apa_em_exercicio(
        sessao, pessoa_id, registro.unidade_principal_atual_id
    ):
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO,
            "somente o APA em exercício pode devolver a versão apresentada",
        )
    conferencia = sessao.scalars(
        select(ConferenciaInternaForm1Integral)
        .where(ConferenciaInternaForm1Integral.registro_id == registro_id)
        .with_for_update()
    ).one_or_none()
    if conferencia is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO,
            "não existe solicitação de conferência interna pendente",
        )
    if versao_lida != conferencia.versao_projecao:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO,
            "conferência interna desatualizada: recarregue antes de devolver",
            versao_lida=versao_lida,
            versao_atual=conferencia.versao_projecao,
        )
    historico = sessao.scalars(
        select(HistoricoConferenciaForm1Integral)
        .where(
            HistoricoConferenciaForm1Integral.registro_id == registro_id,
            HistoricoConferenciaForm1Integral.snapshot_id == conferencia.snapshot_id,
        )
        .with_for_update()
    ).one_or_none()
    if historico is None or historico.situacao != SITUACAO:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_DEVOLUCAO,
            "o histórico da apresentação pendente não está íntegro",
        )

    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd,
        TIPO_COMANDO_DEVOLUCAO,
        {
            "registro_id": registro.id,
            "snapshot_id": conferencia.snapshot_id,
            "numero_apresentacao": historico.numero_apresentacao,
            "versao_rascunho": conferencia.versao_rascunho,
            "justificativa": justificativa,
            "devolvida_por_id": pessoa_id,
            "papel_ator": "APA",
            "situacao": SITUACAO_DEVOLVIDA,
            "ato_preparatorio": True,
            "submissao_habilitada": False,
            "conclusao_institucional": False,
        },
        ordem_no_comando=1,
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    historico.situacao = SITUACAO_DEVOLVIDA
    historico.versao += 1
    historico.devolvida_por_id = pessoa_id
    historico.devolvida_em = momento
    historico.justificativa_devolucao = justificativa
    historico.evento_devolucao_id = evento.id
    sessao.delete(conferencia)
    registrar_auditoria(
        sessao, "conferencia_interna_form1_devolvida", ator_tipo, ator_id,
        {
            "registro_id": registro.id,
            "snapshot_id": historico.snapshot_id,
            "numero_apresentacao": historico.numero_apresentacao,
            "versao_rascunho": historico.versao_rascunho,
            "justificativa": justificativa,
            "papel_ator": "APA",
            "submissao_habilitada": False,
        },
        comando_id=comando.id,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "FORM 1 devolvido ao ARP para ajustes",
        "registro_id": registro.id,
        "snapshot_id": historico.snapshot_id,
        "numero_apresentacao": historico.numero_apresentacao,
        "versao_rascunho": historico.versao_rascunho,
        "evento": evento.sequencia_cadeia,
        "situacao": SITUACAO_DEVOLVIDA,
        "submissao_habilitada": False,
    })
    sessao.flush()
    return resultado


def confirmar_conferencia_interna_form1_integral(
    sessao, *, comando_id, conta_id, registro_id, versao_lida, momento=None,
):
    """Confirma o snapshot apresentado como ato preparatório e auditável do APA."""

    momento = momento or _agora_utc()
    parametros = {
        "conta_id": conta_id,
        "registro_id": registro_id,
        "versao_lida": versao_lida,
    }
    _conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    comando, resposta = abrir_comando(
        sessao, comando_id, TIPO_COMANDO_CONFIRMACAO, parametros,
        ator_tipo, ator_id, conta_id,
    )
    if resposta is not None:
        return resposta
    problema = _validar_versao(versao_lida)
    if problema:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_CONFIRMACAO, problema,
        )

    registro = sessao.scalars(
        select(Registro).where(Registro.id == registro_id).with_for_update()
    ).one_or_none()
    if registro is None or not pessoa_e_apa_em_exercicio(
        sessao, pessoa_id, registro.unidade_principal_atual_id
    ):
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_CONFIRMACAO,
            "somente o APA em exercício pode confirmar a conferência interna",
        )
    conferencia = sessao.scalars(
        select(ConferenciaInternaForm1Integral)
        .where(ConferenciaInternaForm1Integral.registro_id == registro_id)
        .with_for_update()
    ).one_or_none()
    if conferencia is None:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_CONFIRMACAO,
            "não existe solicitação de conferência interna pendente",
        )
    if versao_lida != conferencia.versao_projecao:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_CONFIRMACAO,
            "conferência interna desatualizada: recarregue antes de confirmar",
            versao_lida=versao_lida,
            versao_atual=conferencia.versao_projecao,
        )
    historico = sessao.scalars(
        select(HistoricoConferenciaForm1Integral)
        .where(
            HistoricoConferenciaForm1Integral.registro_id == registro_id,
            HistoricoConferenciaForm1Integral.snapshot_id == conferencia.snapshot_id,
        )
        .with_for_update()
    ).one_or_none()
    if historico is None or historico.situacao != SITUACAO:
        return _negar(
            sessao, comando, ator_tipo, ator_id, conta_id, registro_id,
            TIPO_COMANDO_CONFIRMACAO,
            "o histórico da apresentação pendente não está íntegro",
        )
    pessoa = sessao.get(Pessoa, pessoa_id)
    evento = registrar_evento(
        sessao, comando, "registro", registro.codigo_lgpd,
        TIPO_COMANDO_CONFIRMACAO,
        {
            "registro_id": registro.id,
            "snapshot_id": conferencia.snapshot_id,
            "numero_apresentacao": historico.numero_apresentacao,
            "versao_rascunho": conferencia.versao_rascunho,
            "confirmada_por_id": pessoa_id,
            "matricula_funcional_snapshot": pessoa.matricula,
            "papel_ator": "APA",
            "situacao": SITUACAO_CONFIRMADA,
            "ato_preparatorio": True,
            "submissao_habilitada": False,
            "conclusao_institucional": False,
        },
        ordem_no_comando=1,
        registro_id=registro.id,
        ciclo_id=_ciclo(sessao, registro).id,
        versao_esquema_evento=2,
    )
    from sqlalchemy import inspect
    if inspect(sessao.connection()).has_table("participacao_form2"):
        from app.fila_form2 import ingresso
        ingresso(sessao, registro, historico.snapshot_id, comando, momento)
    historico.situacao = SITUACAO_CONFIRMADA
    historico.versao += 1
    historico.confirmada_por_id = pessoa_id
    historico.confirmada_em = momento
    historico.evento_confirmacao_id = evento.id
    sessao.delete(conferencia)
    registrar_auditoria(
        sessao, "conferencia_interna_form1_confirmada", ator_tipo, ator_id,
        {
            "registro_id": registro.id,
            "snapshot_id": historico.snapshot_id,
            "numero_apresentacao": historico.numero_apresentacao,
            "versao_rascunho": historico.versao_rascunho,
            "matricula_funcional_snapshot": pessoa.matricula,
            "papel_ator": "APA",
            "submissao_habilitada": False,
            "conclusao_institucional": False,
        },
        comando_id=comando.id,
    )
    registro.sequencia_atual = evento.sequencia_cadeia
    resultado = fechar_comando(comando, {
        "permitido": True,
        "motivo": "Conferência interna do FORM 1 confirmada pelo APA",
        "registro_id": registro.id,
        "snapshot_id": historico.snapshot_id,
        "numero_apresentacao": historico.numero_apresentacao,
        "versao_rascunho": historico.versao_rascunho,
        "evento": evento.sequencia_cadeia,
        "situacao": SITUACAO_CONFIRMADA,
        "submissao_habilitada": False,
        "conclusao_institucional": False,
    })
    sessao.flush()
    return resultado


def carregar_versao_para_conferencia(sessao, *, conta_id, registro_id):
    """Entrega a versão pendente ao APA ou a confirmada aos perfis autorizados."""

    conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    registro = sessao.get(Registro, registro_id)
    e_apa = bool(
        registro is not None
        and pessoa_e_apa_em_exercicio(
            sessao, pessoa_id, registro.unidade_principal_atual_id
        )
    )
    conferencia = (
        None if registro is None
        else sessao.get(ConferenciaInternaForm1Integral, registro_id)
    )
    historico_confirmado = None
    if registro is not None and conferencia is None:
        historico_confirmado = sessao.scalars(
            select(HistoricoConferenciaForm1Integral)
            .where(
                HistoricoConferenciaForm1Integral.registro_id == registro_id,
                HistoricoConferenciaForm1Integral.situacao == SITUACAO_CONFIRMADA,
            )
            .order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc())
            .limit(1)
        ).first()
    atribuicao = (
        None if registro is None
        else sessao.get(AtribuicaoForm1Integral, registro_id)
    )
    e_arp_atual = bool(
        atribuicao is not None
        and atribuicao.arp_atual_id == pessoa_id
        and tem_papel(
            sessao, pessoa_id, registro.unidade_principal_atual_id,
            {"preenchedor"},
        )
    )
    autorizado = (
        e_apa if conferencia is not None
        else historico_confirmado is not None and (e_apa or e_arp_atual)
    )
    if not autorizado:
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {
                "acao_tentada": "consultar_conferencia_interna_form1_integral",
                "registro_id": registro_id,
                "conta_id": conta_id,
                "motivo": (
                    "somente o APA em exercício pode consultar a versão pendente; "
                    "a versão confirmada exige APA ou ARP atual autorizado"
                ),
            },
        )
        return None
    apresentacao = conferencia or historico_confirmado
    snapshot = sessao.get(VersaoForm1Integral, apresentacao.snapshot_id)
    solicitante = sessao.get(Pessoa, apresentacao.solicitada_por_id)
    registrar_auditoria(
        sessao, "conferencia_interna_form1_consultada", "pessoa", pessoa_id,
        {
            "registro_id": registro_id,
            "snapshot_id": snapshot.id,
            "situacao": apresentacao.situacao,
        },
    )
    return registro, apresentacao, snapshot, solicitante
