"""Solicitação preparatória do ARP para conferência interna do APA."""

from sqlalchemy import select

from app.comandos import abrir_comando, fechar_comando
from app.continuidade_apa import apa_em_exercicio, pessoa_e_apa_em_exercicio
from app.eventos import registrar_auditoria, registrar_evento
from app.modelos import (
    ConferenciaInternaForm1Integral, Pessoa, Registro, VersaoForm1Integral,
)
from app.rascunho_form1_integral import (
    _agora_utc, _ator, _ciclo, _contexto_autorizado, _lacre, _negar,
    _rascunho_bloqueado, _validar_versao,
)
from app.submissao_form1_integral import preparar_snapshot_na_transacao


TIPO_COMANDO = "solicitar_conferencia_interna_form1_integral"
SITUACAO = "aguardando_conferencia_interna_apa"


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
    registrar_auditoria(
        sessao, "conferencia_interna_form1_solicitada", ator_tipo, ator_id,
        {
            "registro_id": registro.id,
            "snapshot_id": snapshot.id,
            "versao_rascunho": rascunho.versao_rascunho,
            "apa_em_exercicio_no_momento_id": exercicio["pessoa_id"],
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
        "submissao_habilitada": False,
    })
    sessao.flush()
    return resultado


def carregar_versao_para_conferencia(sessao, *, conta_id, registro_id):
    """Entrega ao APA atual somente o retrato imutável que lhe foi apresentado."""

    _conta, pessoa_id, ator_tipo, ator_id = _ator(sessao, conta_id)
    registro = sessao.get(Registro, registro_id)
    if registro is None or not pessoa_e_apa_em_exercicio(
        sessao, pessoa_id, registro.unidade_principal_atual_id
    ):
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {
                "acao_tentada": "consultar_conferencia_interna_form1_integral",
                "registro_id": registro_id,
                "conta_id": conta_id,
                "motivo": "somente o APA em exercício pode consultar a versão apresentada",
            },
        )
        return None
    conferencia = sessao.get(ConferenciaInternaForm1Integral, registro_id)
    if conferencia is None:
        registrar_auditoria(
            sessao, "tentativa_negada", ator_tipo, ator_id,
            {
                "acao_tentada": "consultar_conferencia_interna_form1_integral",
                "registro_id": registro_id,
                "conta_id": conta_id,
                "motivo": "não existe versão apresentada para conferência interna",
            },
        )
        return None
    snapshot = sessao.get(VersaoForm1Integral, conferencia.snapshot_id)
    solicitante = sessao.get(Pessoa, conferencia.solicitada_por_id)
    registrar_auditoria(
        sessao, "conferencia_interna_form1_consultada", "pessoa", pessoa_id,
        {"registro_id": registro_id, "snapshot_id": snapshot.id},
    )
    return registro, conferencia, snapshot, solicitante
