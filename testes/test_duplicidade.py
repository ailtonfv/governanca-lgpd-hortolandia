# Prevenção de duplicidade no G1: objeto + contexto, papéis explícitos, família e alertas
# (DA-36, DA-38, D1, D2). Somente dados fictícios.

from sqlalchemy import update
from sqlalchemy.orm import Session
from app.banco import motor
from app.modelos import Conta, ContextoAtuacao, ObjetoCatalogo, FamiliaContexto, BaseDados, ObjetoBase
from testes.apoio import g1, evento_g1, mudar_estado, CADASTRO, LANCAMENTO


# ------------------------------------------------ verificação 1: equivalência

def test_mesmo_objeto_mesmo_contexto_e_bloqueado():
    assert g1("CMD-D-01", CADASTRO, "CTX-TRIB-01")["permitido"]
    r = g1("CMD-D-02", CADASTRO, "CTX-TRIB-01", titulo="Outro título")
    assert not r["permitido"] and len(r["conflitos"]) == 1


def test_varios_objetos_ocupados_listam_todos_os_conflitos():
    a = g1("CMD-D-03", "OBJ-SRV-001", "CTX-TRIB-03")
    b = g1("CMD-D-04", "OBJ-SRV-002", "CTX-TRIB-03")
    r = g1("CMD-D-05", "OBJ-SRV-001", "CTX-TRIB-03", objetos_abrangidos_ids=["OBJ-SRV-002"])
    assert not r["permitido"]
    assert {c["registro_existente"] for c in r["conflitos"]} == {a["codigo_lgpd"], b["codigo_lgpd"]}


def test_papel_nao_depende_da_ordem():
    r = g1("CMD-D-06", "OBJ-SRV-002", "CTX-TRIB-03", objetos_abrangidos_ids=["OBJ-SRV-001"])
    objetos = {o["id"]: o["papel"] for o in evento_g1(r["codigo_lgpd"]).conteudo["objetos"]}
    assert objetos == {"OBJ-SRV-002": "PRINCIPAL", "OBJ-SRV-001": "ABRANGIDO"}


def test_citado_nao_trava_e_nao_ganha_contexto():
    g1("CMD-D-07", "OBJ-SRV-001", "CTX-TRIB-03")
    r = g1("CMD-D-08", "OBJ-SRV-901", "CTX-ATD-01", objetos_citados={"OBJ-SRV-001": "RELACIONADO"})
    assert r["permitido"]


def test_objeto_citado_tambem_como_assunto_e_recusado():
    r = g1("CMD-D-09", "OBJ-SRV-001", "CTX-TRIB-03", objetos_citados={"OBJ-SRV-001": "APOIO"})
    assert not r["permitido"] and "mais de um papel" in r["motivo"]


# ------------------------------------------------ barreiras de sempre

def test_contexto_desativado_e_recusado():
    with Session(motor) as s, s.begin():
        s.get(ContextoAtuacao, "CTX-URB-02").ativo = False
    assert not g1("CMD-D-10", CADASTRO, "CTX-URB-02")["permitido"]


def test_objeto_desativado_e_recusado():
    with Session(motor) as s, s.begin():
        s.get(ObjetoCatalogo, "OBJ-SRV-900").ativo = False
    assert not g1("CMD-D-11", "OBJ-SRV-900", "CTX-TRIB-03")["permitido"]


def test_conta_inativa_e_recusada():
    with Session(motor) as s, s.begin():
        s.execute(update(Conta).where(Conta.id == "CONTA-A1").values(ativa=False))
    r = g1("CMD-D-12", CADASTRO, "CTX-TRIB-01")
    assert not r["permitido"] and "conta" in r["motivo"]


def test_sem_papel_de_responsavel_pelo_registro_e_recusado():
    r = g1("CMD-D-13", CADASTRO, "CTX-TRIB-01", conta="CONTA-B1")
    assert not r["permitido"] and "responsável pelo Registro" in r["motivo"]


def test_preenchedor_sem_papel_de_responsavel_nao_abre_registro():
    r = g1("CMD-D-13-PREENCHEDOR", CADASTRO, "CTX-TRIB-01", conta="CONTA-G1")
    assert not r["permitido"] and "responsável pelo Registro" in r["motivo"]


# ------------------------------------------------ verificação 2: família (D2)

def test_outra_familia_nao_gera_advertencia():
    g1("CMD-D-14", CADASTRO, "CTX-TRIB-01")
    r = g1("CMD-D-15", CADASTRO, "CTX-URB-01")
    assert r["permitido"] and r["advertencia"] is None


def test_mesma_familia_sem_resolucao_e_recusada():
    g1("CMD-D-16", CADASTRO, "CTX-TRIB-01")
    r = g1("CMD-D-17", CADASTRO, "CTX-TRIB-03")
    assert not r["permitido"] and r["advertencia"]["familia"] == "TRIB"


def test_justificativa_vazia_ou_so_espacos_e_recusada():
    g1("CMD-D-18", CADASTRO, "CTX-TRIB-01")
    for n, texto in enumerate(["", "   ", None]):
        r = g1(f"CMD-D-19-{n}", CADASTRO, "CTX-TRIB-03",
               resolucao_familia="tratamento_autonomo", justificativa=texto)
        assert not r["permitido"]


def test_justificativa_cria_e_fica_no_evento_g1():
    g1("CMD-D-20", CADASTRO, "CTX-TRIB-01")
    r = g1("CMD-D-21", CADASTRO, "CTX-TRIB-03", resolucao_familia="tratamento_autonomo",
           justificativa="Tratamento próprio da cobrança (fictício)")
    assert r["permitido"] and r["motivo"] == "criado com justificativa"
    adv = evento_g1(r["codigo_lgpd"]).conteudo["advertencia_familia"]
    assert adv["resolucao"] == "tratamento_autonomo" and adv["justificativa"].startswith("Tratamento próprio")


def test_familia_mutuamente_exclusiva_bloqueia():
    with Session(motor) as s, s.begin():
        s.get(FamiliaContexto, "URB").mutuamente_exclusiva = True
    g1("CMD-D-22", CADASTRO, "CTX-URB-01")
    r = g1("CMD-D-23", CADASTRO, "CTX-URB-03", resolucao_familia="tratamento_autonomo", justificativa="x")
    assert not r["permitido"] and "exclusiva" in r["motivo"]


# ------------------------------------------------ verificação 3: alerta estrutural

def test_alerta_por_base_comum_sem_repeticao():
    with Session(motor) as s, s.begin():                 # uma segunda base usada pelos dois objetos
        s.add(BaseDados(id="BAS-003", nome_canonico="Planta genérica de valores (fictícia)", suporte="planilha"))
        s.flush()
        s.add_all([ObjetoBase(objeto_id=CADASTRO, base_id="BAS-003"),
                   ObjetoBase(objeto_id=LANCAMENTO, base_id="BAS-003")])
    lanc = g1("CMD-D-24", LANCAMENTO, "CTX-TRIB-02")
    r = g1("CMD-D-25", CADASTRO, "CTX-TRIB-01")
    assert r["permitido"] and len(r["alertas"]) == 1
    assert r["alertas"][0]["registro"] == lanc["codigo_lgpd"]
    assert r["alertas"][0]["bases"] == ["BAS-001", "BAS-003"]


# ------------------------------------------------ situação bloqueadora (provisório até o M1b.1)

def test_suspenso_e_concluido_continuam_bloqueando():
    a = g1("CMD-D-26", CADASTRO, "CTX-TRIB-01")
    for estado, acao in [("suspenso", "retomar (G8)"), ("concluido", "reabrir (G10)")]:
        mudar_estado(a["codigo_lgpd"], estado)
        r = g1(f"CMD-D-27-{estado}", CADASTRO, "CTX-TRIB-01")
        assert not r["permitido"]
        acoes = [x["acao"] for x in r["conflitos"][0]["acoes"]["dependem_de_competencia"]]
        assert acao in acoes and "cancelar (G11)" in acoes


def test_cancelado_libera_nova_criacao():
    a = g1("CMD-D-28", CADASTRO, "CTX-TRIB-01")
    mudar_estado(a["codigo_lgpd"], "cancelado", liberar_vinculos=True)
    assert g1("CMD-D-29", CADASTRO, "CTX-TRIB-01")["permitido"]


def test_acoes_consideram_quem_pede():
    g1("CMD-D-30", CADASTRO, "CTX-TRIB-01")
    de_fora = g1("CMD-D-31", CADASTRO, "CTX-TRIB-01", conta="CONTA-C1", unidade="UNID-SUL")
    de_dentro = g1("CMD-D-32", CADASTRO, "CTX-TRIB-01")
    assert de_fora["conflitos"][0]["acoes"]["solicitaveis"] == ["solicitar acesso"]
    assert de_dentro["conflitos"][0]["acoes"]["possiveis"] == ["abrir"]
