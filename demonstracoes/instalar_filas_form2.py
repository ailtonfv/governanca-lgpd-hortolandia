"""Instalação aditiva e papéis de demonstração exclusivamente fictícios."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Pessoa, Designacao, Registro, HistoricoConferenciaForm1Integral
from app.eventos import registrar_auditoria
from migracoes.fila_form2 import aplicar

def instalar():
    with Session(motor) as sessao, sessao.begin():
        aplicar(sessao)
        papeis = [("PESSOA-B", "UNID-NORTE", "aal_form2"),
                  ("PESSOA-A", "UNID-NORTE", "gestor_fila"),
                  ("PESSOA-F", "SEC-AJ", "juridico_form2")]
        for pessoa_id, unidade_id, papel in papeis:
            pessoa = sessao.get(Pessoa,pessoa_id)
            if not pessoa or not pessoa.matricula.startswith("MAT-FICT-"):
                raise RuntimeError("Carga demonstrativa incompatível. Nenhum perfil alterado.")
            existente = sessao.scalar(select(Designacao).where(
                Designacao.pessoa_id == pessoa_id, Designacao.unidade_id == unidade_id,
                Designacao.papel == papel))
            if existente is None:
                sessao.add(Designacao(pessoa_id=pessoa_id, unidade_id=unidade_id,
                    papel=papel, ativa=True, fundamento_administrativo="Ensaio fictício autorizado REV22"))
                registrar_auditoria(sessao, "papel_ficticio_fila_form2", "conta_servico",
                    "instalador_demo", {"pessoa_id":pessoa_id,"unidade_id":unidade_id,"papel":papel})
        from app.comandos import abrir_comando, fechar_comando
        from app.fila_form2 import ingresso
        vistos = set()
        historicos = sessao.scalars(select(HistoricoConferenciaForm1Integral).where(
            HistoricoConferenciaForm1Integral.situacao == "conferencia_interna_confirmada"
        ).order_by(HistoricoConferenciaForm1Integral.numero_apresentacao.desc())).all()
        for historico in historicos:
            if historico.registro_id in vistos:
                continue
            vistos.add(historico.registro_id)
            autor = sessao.get(Pessoa,historico.solicitada_por_id)
            registro = sessao.scalar(select(Registro).where(
                Registro.id == historico.registro_id).with_for_update())
            if (not autor or not autor.matricula.startswith("MAT-FICT-")
                    or registro.estado_atual != "em_andamento"):
                continue
            comando, repeticao = abrir_comando(sessao, "fila-rev22-"+historico.snapshot_id,
                "migrar_origem_confirmada_fila", {"snapshot_id":historico.snapshot_id},
                "conta_servico","instalador_demo")
            if repeticao is None:
                p = ingresso(sessao,registro,historico.snapshot_id,comando)
                fechar_comando(comando,{"permitido":True,"participacao_id":p.id})
        from copy import deepcopy
        from app.modelos import ParticipacaoForm2, PreparacaoForm2
        from app.fila_form2 import evento
        from app.form2_preparacao import _historico_integro
        for participacao, legado in sessao.execute(select(ParticipacaoForm2, PreparacaoForm2).join(
                PreparacaoForm2, ParticipacaoForm2.snapshot_id == PreparacaoForm2.snapshot_id
        ).where(ParticipacaoForm2.tipo == "principal")):
            if participacao.conteudo or participacao.responsavel_id:
                continue
            _historico_integro(sessao, legado)
            comando, repeticao = abrir_comando(sessao, "fila-legado-"+participacao.id,
                "copiar_rascunho_anterior_fila", {"preparacao_id":legado.id,"participacao_id":participacao.id},
                "conta_servico","instalador_demo")
            if repeticao is None:
                participacao.conteudo = deepcopy(legado.conteudo)
                participacao.versao += 1
                evento(sessao,comando,participacao,"form2_rascunho_anterior_reaproveitado")
                fechar_comando(comando,{"permitido":True,"participacao_id":participacao.id})
    print("Filas instaladas. Beta assume o AAL, Delta demonstra o Jurídico e Épsilon mantém seu perfil anterior.")

if __name__ == "__main__":
    instalar()
