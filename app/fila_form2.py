"""Fluxo institucional demonstrativo da candidata REV22, sem homologação de mérito."""
from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select, or_
from app.modelos import (ParticipacaoForm2, AvisoDpo, Pessoa, Conta, Designacao,
                        Unidade, Registro, HistoricoConferenciaForm1Integral)
from app.comandos import abrir_comando, fechar_comando
from app.eventos import registrar_evento, registrar_auditoria
from app.continuidade_apa import pessoa_e_apa_em_exercicio

PAPEIS = {"principal": "aal_form2", "tematica": "aal_form2",
          "juridico": "juridico_form2", "dpo": "governanca_protecao_dados"}


def agora():
    return datetime.now(timezone.utc)


def pessoa_ativa(sessao, conta_id):
    conta = sessao.get(Conta, conta_id)
    pessoa = sessao.get(Pessoa, conta.pessoa_id) if conta and conta.ativa else None
    if not pessoa or not pessoa.ativa:
        raise PermissionError("Conta ou pessoa indisponível.")
    return pessoa


def unidades(sessao, pessoa_id, papel):
    momento = agora()
    return set(sessao.scalars(select(Designacao.unidade_id).join(
        Unidade, Unidade.id == Designacao.unidade_id).where(
        Designacao.pessoa_id == pessoa_id, Designacao.papel == papel,
        Designacao.ativa.is_(True), Unidade.ativa.is_(True),
        or_(Designacao.vigente_de.is_(None), Designacao.vigente_de <= momento),
        or_(Designacao.vigente_ate.is_(None), Designacao.vigente_ate > momento))))


def autorizado(sessao, pessoa, participacao):
    return participacao.unidade_id in unidades(sessao, pessoa.id, PAPEIS[participacao.tipo])


def ingresso(sessao, registro, snapshot_id, comando, momento=None):
    """Chamado na mesma transação da confirmação interna, para ensaio da fila."""
    momento = momento or agora()
    existente = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.snapshot_id == snapshot_id, ParticipacaoForm2.tipo == "principal"))
    if existente:
        return existente
    p = ParticipacaoForm2(id=str(uuid4()), registro_id=registro.id,
        snapshot_id=snapshot_id, unidade_id=registro.unidade_principal_atual_id,
        tipo="principal", estado="aguardando", entrada_em=momento, versao=1,
        questao="", manifestacao="")
    from app.modelos import PreparacaoForm2
    legado = sessao.scalar(select(PreparacaoForm2).where(
        PreparacaoForm2.registro_id == registro.id, PreparacaoForm2.snapshot_id == snapshot_id))
    if legado:
        from app.form2_preparacao import _historico_integro
        _historico_integro(sessao, legado)
        p.conteudo = deepcopy(legado.conteudo)
    sessao.add(p)
    sessao.flush()
    aviso(sessao, p, "ciencia")
    evento(sessao, comando, p, "form2_ingresso_fila")
    return p


def aviso(sessao, p, tipo):
    registro = sessao.get(Registro, p.registro_id)
    sessao.add(AvisoDpo(id=str(uuid4()), participacao_id=p.id, tipo=tipo,
        criado_em=agora(), metadados={"identificador_lgpd": registro.codigo_lgpd,
        "secretaria_id": registro.unidade_principal_atual_id,
        "fila_id": p.unidade_id, "entrada_em": p.entrada_em.isoformat(),
        "participacao_id": p.id}))


def evento(sessao, comando, p, tipo, ordem=20):
    registrar_evento(sessao, comando, "participacao_form2", p.id, tipo,
        {"registro_id": p.registro_id, "snapshot_id": p.snapshot_id,
         "unidade_id": p.unidade_id, "tipo": p.tipo, "estado": p.estado,
         "responsavel_id": p.responsavel_id, "versao": p.versao,
         "questao": p.questao, "manifestacao": p.manifestacao,
         "conteudo": p.conteudo or {}},
        registro_id=p.registro_id, ordem_no_comando=ordem, versao_regra="F2-FILA-REV22")
    registrar_auditoria(sessao, tipo, comando.ator_tipo, comando.ator_id,
                       {"participacao_id": p.id}, comando_id=comando.id)


def executar(sessao, *, conta_id, comando_id, participacao_id, acao, versao,
             texto="", unidade_id=None, tipo=None):
    pessoa = pessoa_ativa(sessao, conta_id)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.id == participacao_id).with_for_update())
    if not p or not autorizado(sessao, pessoa, p):
        raise PermissionError("A participação exige autorização vigente na unidade destinatária.")
    parametros = dict(conta_id=conta_id, participacao_id=participacao_id,
        acao=acao, versao=versao, texto=texto, unidade_id=unidade_id, tipo=tipo)
    comando, resposta = abrir_comando(sessao, comando_id, "fila_form2_"+acao,
        parametros, "pessoa", pessoa.id, conta_id)
    if resposta is not None:
        return resposta
    if p.versao != versao:
        raise ValueError("A participação foi alterada. Atualize a página.")
    if not isinstance(texto, str) or len(texto) > 10000:
        raise ValueError("Texto limitado a 10000 caracteres.")
    registro = sessao.get(Registro, p.registro_id)
    if registro.estado_atual != "em_andamento":
        raise ValueError("A participação exige registro em andamento.")
    if acao == "assumir":
        historico = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
            HistoricoConferenciaForm1Integral.snapshot_id == p.snapshot_id))
        if historico and historico.solicitada_por_id == pessoa.id:
            raise PermissionError("Quem apresentou a origem não pode assumir sua validação.")
        if p.estado != "aguardando":
            raise ValueError("Participação já assumida.")
        p.responsavel_id = pessoa.id
        p.assumida_em = agora()
        p.estado = "em_atendimento"
    else:
        if p.estado != "em_atendimento" or p.responsavel_id != pessoa.id:
            raise PermissionError("A operação exige o responsável da participação aberta.")
        if acao == "salvar":
            p.manifestacao = texto
        elif acao == "consultar":
            if p.tipo != "principal" or tipo not in {"dpo", "juridico", "tematica"} or not texto.strip():
                raise ValueError("A participação principal deve informar tipo, destino e questão.")
            destino = sessao.get(Unidade, unidade_id)
            if not destino or not destino.ativa:
                raise ValueError("Unidade destinatária indisponível.")
            filho = ParticipacaoForm2(id=str(uuid4()), registro_id=p.registro_id,
                snapshot_id=p.snapshot_id, unidade_id=unidade_id, origem_id=p.id,
                tipo=tipo, estado="aguardando", entrada_em=agora(), versao=1,
                questao=texto.strip(), manifestacao="")
            sessao.add(filho)
            sessao.flush()
            if tipo == "dpo":
                aviso(sessao, filho, "manifestacao")
            evento(sessao, comando, filho, "form2_consulta_aberta")
            p.versao += 1
            evento(sessao, comando, p, "form2_consulta_encaminhada", ordem=21)
            return fechar_comando(comando, {"permitido": True, "participacao_id": filho.id})
        elif acao == "concluir":
            if p.tipo == "principal":
                raise ValueError("Conclusão consolidada aguarda as regras de pendência e D11.")
            if not texto.strip():
                raise ValueError("Registre a manifestação antes de concluir.")
            p.manifestacao = texto.strip()
            p.estado = "concluida"
            p.concluida_em = agora()
        else:
            raise ValueError("Operação desconhecida.")
    p.versao += 1
    evento(sessao, comando, p, "form2_"+acao)
    return fechar_comando(comando, {"permitido": True, "participacao_id": p.id})


def painel(sessao, conta_id):
    pessoa = pessoa_ativa(sessao, conta_id)
    dpo = bool(unidades(sessao, pessoa.id, "governanca_protecao_dados"))
    filas = {tipo: unidades(sessao, pessoa.id, papel) for tipo, papel in PAPEIS.items()}
    todas = sessao.scalars(select(ParticipacaoForm2).order_by(ParticipacaoForm2.entrada_em)).all()
    visiveis = [p for p in todas if p.unidade_id in filas[p.tipo]]
    principais = [p for p in todas if p.tipo == "principal"] if dpo else []
    return pessoa, visiveis, principais, dpo


def importar_confirmada(sessao, *, conta_id, comando_id, registro_id):
    pessoa = pessoa_ativa(sessao, conta_id)
    registro = sessao.scalar(select(Registro).where(Registro.id == registro_id).with_for_update())
    if not registro or not pessoa_e_apa_em_exercicio(
            sessao, pessoa.id, registro.unidade_principal_atual_id):
        raise PermissionError("Somente o APA em exercício encaminha a origem confirmada.")
    historico = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.registro_id == registro_id,
        HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada"
    ).order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc()).limit(1))
    if not historico:
        raise ValueError("O FORM 1 precisa de conferência interna confirmada.")
    comando, repeticao = abrir_comando(sessao, comando_id, "encaminhar_form2_fila",
        {"conta_id": conta_id, "registro_id": registro_id}, "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    p = ingresso(sessao, registro, historico.snapshot_id, comando)
    return fechar_comando(comando, {"permitido": True, "participacao_id": p.id})


def salvar_bloco(sessao, *, conta_id, comando_id, participacao_id, versao,
                  bloco, campos, complementos=None):
    """Usa os contratos existentes dos blocos, inclusive os limites D11."""
    from app.respostas_form2 import aplicar_bloco, aplicar_revisao
    from app.origem_form2 import ler_origem
    from app.form2_rev212 import ramos_origem
    pessoa = pessoa_ativa(sessao, conta_id)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.id == participacao_id).with_for_update())
    if (not p or not autorizado(sessao, pessoa, p) or p.tipo != "principal"
            or p.estado != "em_atendimento" or p.responsavel_id != pessoa.id):
        raise PermissionError("Somente o AAL responsável edita o formulário principal.")
    parametros = dict(conta_id=conta_id, participacao_id=participacao_id,
        versao=versao, bloco=bloco, campos=campos, complementos=complementos)
    comando, repeticao = abrir_comando(sessao, comando_id, "fila_form2_bloco",
        parametros, "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if p.versao != versao:
        raise ValueError("Atualize a página antes de salvar.")
    if sessao.get(Registro, p.registro_id).estado_atual != "em_andamento":
        raise ValueError("Registro fora de andamento.")
    origem = ler_origem(sessao, p.registro_id, p.snapshot_id)
    if bloco in (1, 2):
        novo, _ = aplicar_bloco(p.conteudo or {}, bloco=bloco, alteracoes={k:v for k,v in campos.items() if ":" not in k},
            complementos=complementos, proxima_versao=p.versao+1)
        candidatos = {k:v for k,v in campos.items() if ":" in k}
        if candidatos:
            novo, _ = aplicar_revisao(novo, bloco, candidatos, ramos_origem(origem), demonstrativo=True)
    else:
        novo, _ = aplicar_revisao(p.conteudo or {}, bloco, campos, ramos_origem(origem), demonstrativo=True)
    complemento_solicitado = False
    texto_complemento = novo.get("respostas_etapa1", {}).get("F2-1.3.1")
    if texto_complemento:
        from app.modelos import ComplementoForm2
        pendencia = sessao.scalar(select(ComplementoForm2).where(
            ComplementoForm2.participacao_id == p.id))
        if pendencia is None:
            pendencia = ComplementoForm2(id=str(uuid4()), participacao_id=p.id,
                snapshot_origem_id=p.snapshot_id, solicitacao=texto_complemento,
                estado="aberta", criada_em=agora())
            sessao.add(pendencia)
        elif pendencia.solicitacao != texto_complemento:
            pendencia.solicitacao = texto_complemento
            pendencia.estado = "aberta"
            pendencia.snapshot_resposta_id = None
            pendencia.respondida_em = None
            pendencia.resolvida_em = None
    if texto_complemento and bloco == 1:
        complemento_solicitado = pendencia.estado == "aberta"
    p.conteudo = novo
    p.versao += 1
    evento(sessao, comando, p, "form2_bloco_salvo")
    return fechar_comando(comando, {"permitido": True, "participacao_id": p.id,
        "bloco": bloco, "versao": p.versao,
        "complemento_solicitado": complemento_solicitado})


def reatribuir(sessao, *, conta_id, comando_id, participacao_id, versao,
               responsavel_id, motivo):
    pessoa = pessoa_ativa(sessao, conta_id)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.id == participacao_id).with_for_update())
    if not p or p.unidade_id not in unidades(sessao, pessoa.id, "gestor_fila"):
        raise PermissionError("A reatribuição exige gestor autorizado da fila.")
    alvo = sessao.get(Pessoa, responsavel_id)
    if not alvo or not alvo.ativa or not autorizado(sessao, alvo, p):
        raise ValueError("O novo responsável precisa de autorização vigente na unidade.")
    historico = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
        HistoricoConferenciaForm1Integral.snapshot_id == p.snapshot_id))
    if historico and historico.solicitada_por_id == responsavel_id:
        raise PermissionError("Quem apresentou a origem não pode assumir sua validação.")
    if not motivo or not motivo.strip() or len(motivo) > 2000:
        raise ValueError("Informe o motivo da reatribuição em até 2000 caracteres.")
    comando, repeticao = abrir_comando(sessao, comando_id, "reatribuir_fila_form2",
        dict(conta_id=conta_id, participacao_id=p.id, versao=versao,
             responsavel_id=responsavel_id, motivo=motivo),
        "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if p.versao != versao or p.estado == "concluida":
        raise ValueError("Participação alterada ou concluída.")
    p.responsavel_id = responsavel_id
    p.assumida_em = p.assumida_em or agora()
    p.estado = "em_atendimento"
    p.versao += 1
    evento(sessao, comando, p, "form2_reatribuida")
    registrar_auditoria(sessao, "motivo_reatribuicao_form2", "pessoa", pessoa.id,
        {"participacao_id": p.id, "motivo": motivo}, comando_id=comando.id)
    return fechar_comando(comando, {"permitido": True, "participacao_id": p.id})


def complementar(sessao, *, conta_id, comando_id, participacao_id, acao, snapshot_id=None):
    from app.modelos import ComplementoForm2, AtribuicaoForm1Integral, VersaoForm1Integral
    pessoa = pessoa_ativa(sessao, conta_id)
    p = sessao.scalar(select(ParticipacaoForm2).where(
        ParticipacaoForm2.id == participacao_id).with_for_update())
    if not p:
        raise ValueError("Participação inexistente.")
    pendencia = sessao.scalar(select(ComplementoForm2).where(
        ComplementoForm2.participacao_id == p.id).with_for_update())
    if not pendencia:
        raise ValueError("Nenhuma complementação solicitada.")
    registro = sessao.get(Registro, p.registro_id)
    atribuicao = sessao.get(AtribuicaoForm1Integral, registro.id)
    origem_autorizada = pessoa_e_apa_em_exercicio(
        sessao, pessoa.id, registro.unidade_principal_atual_id) or (
        atribuicao and atribuicao.arp_atual_id == pessoa.id
        and registro.unidade_principal_atual_id in unidades(sessao, pessoa.id, "preenchedor"))
    if acao == "responder":
        if not origem_autorizada:
            raise PermissionError("Somente APA ou ARP atual pode responder pela origem.")
    elif acao == "resolver":
        if not autorizado(sessao, pessoa, p) or p.responsavel_id != pessoa.id:
            raise PermissionError("Somente o AAL responsável confere a resposta.")
    else:
        raise ValueError("Operação inválida.")
    comando, repeticao = abrir_comando(sessao, comando_id, "complemento_form2_"+acao,
        dict(conta_id=conta_id, participacao_id=p.id, acao=acao, snapshot_id=snapshot_id),
        "pessoa", pessoa.id, conta_id)
    if repeticao is not None:
        return repeticao
    if acao == "responder":
        historico = sessao.scalar(select(HistoricoConferenciaForm1Integral).where(
            HistoricoConferenciaForm1Integral.registro_id == registro.id,
            HistoricoConferenciaForm1Integral.snapshot_id == snapshot_id,
            HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada"))
        anterior = sessao.get(VersaoForm1Integral, pendencia.snapshot_origem_id)
        resposta = sessao.get(VersaoForm1Integral, snapshot_id)
        if (not historico or not resposta or resposta.numero <= anterior.numero
                or pendencia.estado != "aberta"):
            raise ValueError("A resposta exige nova versão confirmada do FORM 1.")
        pendencia.snapshot_resposta_id = snapshot_id
        pendencia.respondida_em = agora()
        pendencia.estado = "respondida"
    else:
        if pendencia.estado != "respondida":
            raise ValueError("A complementação ainda aguarda resposta.")
        pendencia.estado = "resolvida"
        pendencia.resolvida_em = agora()
    p.versao += 1
    registrar_evento(sessao, comando, "participacao_form2", p.id, "form2_complemento_"+acao,
        {"pendencia_id": pendencia.id, "origem_1_3_1": pendencia.solicitacao,
         "destino_14_2": True, "snapshot_origem_id": pendencia.snapshot_origem_id,
         "snapshot_resposta_id": pendencia.snapshot_resposta_id, "estado": pendencia.estado},
        registro_id=p.registro_id, versao_regra="F2-FILA-REV22")
    return fechar_comando(comando, {"permitido": True, "participacao_id": p.id})
