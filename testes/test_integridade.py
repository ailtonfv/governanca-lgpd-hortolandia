# Recusas do próprio banco: cada regra tem nome, e só a trava de equivalência é interpretada
# como decisão de negócio. Qualquer outra recusa precisa APARECER (Etapa 2d, item A2).

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Registro, RegistroObjeto
from app.comandos import nome_da_restricao
import app.workflow as workflow
from testes.apoio import g1, CADASTRO


def inserir(vinculo):
    with Session(motor) as s, s.begin():
        s.add(vinculo)
        s.flush()


def registro_de(codigo):
    with Session(motor) as s:
        return s.scalars(select(Registro).where(Registro.codigo_lgpd == codigo)).one()


@pytest.mark.parametrize("descricao, restricao, montar", [
    ("mesmo objeto + contexto em outro Registro", "uq_objeto_contexto_assunto_ativo",
     lambda a, b: RegistroObjeto(registro_id=b.id, objeto_id=CADASTRO, papel="ABRANGIDO",
                                 contexto_atuacao_id="CTX-TRIB-01")),
    ("segundo PRINCIPAL no mesmo Registro", "uq_um_principal_por_registro",
     lambda a, b: RegistroObjeto(registro_id=a.id, objeto_id="OBJ-ATV-002", papel="PRINCIPAL",
                                 contexto_atuacao_id="CTX-TRIB-01")),
    ("vínculo com contexto diferente do Registro (D1)", "fk_vinculo_contexto_do_registro",
     lambda a, b: RegistroObjeto(registro_id=a.id, objeto_id="OBJ-ATV-002", papel="ABRANGIDO",
                                 contexto_atuacao_id="CTX-URB-01")),
    ("objeto citado com contexto (D1)", "ck_papel_e_contexto",
     lambda a, b: RegistroObjeto(registro_id=a.id, objeto_id="OBJ-ATV-002", papel="APOIO",
                                 contexto_atuacao_id="CTX-TRIB-01")),
])
def test_o_banco_recusa_e_diz_qual_regra(descricao, restricao, montar):
    a = registro_de(g1("CMD-B-01", CADASTRO, "CTX-TRIB-01")["codigo_lgpd"])
    b = registro_de(g1("CMD-B-02", "OBJ-SRV-900", "CTX-TRIB-01")["codigo_lgpd"])
    with pytest.raises(IntegrityError) as erro:
        inserir(montar(a, b))
    assert nome_da_restricao(erro.value) == restricao


def test_outra_recusa_do_banco_nao_e_mascarada(monkeypatch):
    """Se o número do ano repetir (defeito simulado), a recusa NÃO pode virar 'já existe Registro'."""
    g1("CMD-B-03", CADASTRO, "CTX-TRIB-01")
    monkeypatch.setattr(workflow, "proximo_numero_do_ano", lambda sessao, ano: 1)
    with pytest.raises(IntegrityError) as erro:
        g1("CMD-B-04", "OBJ-SRV-900", "CTX-TRIB-03")
    assert nome_da_restricao(erro.value) in ("registro_codigo_lgpd_key", "uq_registro_ano_numero")
