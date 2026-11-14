"""Identificação pública das apresentações do FORM 1."""
from app.modelos import VersaoForm1Integral


def rotulo_apresentacao(versao):
    """Nomeia a apresentação pelo histórico, inclusive em consultas a versões antigas."""
    historico = versao.apresentacao if isinstance(versao, VersaoForm1Integral) else versao
    if historico is None:
        return f"Rascunho {versao.versao_rascunho} (sem apresentação registrada)"
    return f"Apresentação {historico.numero_apresentacao} (rascunho {historico.versao_rascunho})"
