"""Barreira de segurança para a massa exclusivamente fictícia da PoC.

O validador não tenta descobrir se uma pessoa existe. Ele aplica uma regra mais
segura para este ambiente: identidades precisam carregar marcadores sintéticos
e nenhum texto da carga pode conter identificadores pessoais usuais.
"""

import re


class MassaFicticiaInvalida(ValueError):
    """A carga contém um valor incompatível com o contrato sintético da PoC."""


_ID_PESSOA = re.compile(r"PESSOA-[A-Z0-9-]+\Z")
_MATRICULA = re.compile(r"MAT-FICT-\d{4}\Z")
_ID_CONTA = re.compile(r"CONTA-[A-Z0-9-]+\Z")

_IDENTIFICADORES_PESSOAIS = (
    ("CPF", re.compile(r"(?<!\d)\d{3}[.]?\d{3}[.]?\d{3}-?\d{2}(?!\d)")),
    ("e-mail", re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")),
    ("telefone", re.compile(
        r"(?<!\d)(?:[+]55[ .-]*)?(?:[(]?\d{2}[)]?[ .-]*)?\d{4,5}[ .-]*\d{4}(?!\d)"
    )),
)


def _percorrer(valor, caminho="raiz"):
    if isinstance(valor, dict):
        for chave, item in valor.items():
            yield from _percorrer(item, f"{caminho}.{chave}")
    elif isinstance(valor, (list, tuple, set)):
        for indice, item in enumerate(valor):
            yield from _percorrer(item, f"{caminho}[{indice}]")
    elif isinstance(valor, str):
        yield caminho, valor


def validar_ausencia_de_identificadores(nome_massa, dados):
    """Recusa identificadores pessoais sem reproduzi-los na mensagem de erro."""
    for caminho, texto in _percorrer(dados):
        for rotulo, padrao in _IDENTIFICADORES_PESSOAIS:
            if padrao.search(texto):
                raise MassaFicticiaInvalida(
                    f"{nome_massa}: possível {rotulo} encontrado em {caminho}; "
                    "o valor foi omitido por segurança"
                )


def validar_identidades(pessoas):
    """Exige marcadores inequívocos nas pessoas, matrículas, nomes e contas."""
    for indice, registro in enumerate(pessoas):
        if not isinstance(registro, (tuple, list)) or len(registro) != 4:
            raise MassaFicticiaInvalida(
                f"pessoas: estrutura inválida no item {indice}; conteúdo omitido"
            )
        pessoa_id, matricula, nome, contas = registro
        if not _ID_PESSOA.fullmatch(str(pessoa_id)):
            raise MassaFicticiaInvalida(
                f"pessoas: identificador fora do padrão sintético no item {indice}"
            )
        if not _MATRICULA.fullmatch(str(matricula)):
            raise MassaFicticiaInvalida(
                f"pessoas: matrícula fora do padrão sintético no item {indice}"
            )
        if "fictíci" not in str(nome).casefold():
            raise MassaFicticiaInvalida(
                f"pessoas: nome sem marcador de ficção no item {indice}"
            )
        if not isinstance(contas, (tuple, list)) or not contas:
            raise MassaFicticiaInvalida(
                f"pessoas: lista de contas inválida no item {indice}"
            )
        for numero, conta_id in enumerate(contas):
            if not _ID_CONTA.fullmatch(str(conta_id)):
                raise MassaFicticiaInvalida(
                    f"pessoas: conta fora do padrão sintético no item {indice}.{numero}"
                )
    validar_ausencia_de_identificadores("pessoas", pessoas)
