# Segregação de funções (O-66): a regra compara a PESSOA, nunca a conta.

from sqlalchemy import update
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Conta
from app.permissoes import executar_acao, verificar_acao, autor_da_submissao
from app.eventos import verificar_cadeia

REG, UNID = "REG-T-SEG", "UNID-NORTE"


def acao(conta, nome, cmd):
    with Session(motor) as s, s.begin():
        return executar_acao(s, conta, REG, UNID, nome, {"versao": 1}, cmd)


def test_cenarios_de_segregacao():
    assert acao("CONTA-A1", "submeter", "CMD-S-01")[0] is True
    assert acao("CONTA-A2", "validar", "CMD-S-02")[0] is False     # (a) outra conta, mesma pessoa
    assert acao("CONTA-A1", "validar", "CMD-S-03")[0] is False     # (b) mesma conta
    assert acao("CONTA-A2", "devolver", "CMD-S-04")[0] is False    # (e) devolver a própria versão
    assert acao("CONTA-B1", "analisar", "CMD-S-05")[0] is True
    assert acao("CONTA-B1", "validar", "CMD-S-06")[0] is True      # (c) outra pessoa
    with Session(motor) as s:
        assert verificar_cadeia(s, REG)[0]


def test_conta_desativada_nao_muda_a_autoria():                    # (f)
    acao("CONTA-A1", "submeter", "CMD-S-07")
    with Session(motor) as s:
        s.execute(update(Conta).where(Conta.id == "CONTA-A1").values(ativa=False))
        assert autor_da_submissao(s, REG) == "PESSOA-A"
        assert verificar_acao(s, "CONTA-A2", REG, UNID, "validar")[0] is False
        s.rollback()
