"""Classificação informativa e versionada das alternativas do catálogo 5.1.

Esta sinalização não calcula risco, não define hipótese legal e não substitui
as análises dos FORMS 2 e 3. Ela é uma propriedade somente leitura do catálogo.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


VERSAO_CLASSIFICACAO_CATALOGO_5_1 = "F1-CLASS-5.1-v1"

PESSOAL_COMUM = "PESSOAL_COMUM"
SENSIVEL = "SENSIVEL"
AVALIAR_CONTEXTO = "AVALIAR_CONTEXTO"


@dataclass(frozen=True, slots=True)
class ClassificacaoCategoriaDados:
    codigo: str
    rotulo: str
    explicacao: str
    alerta: str | None = None


_PESSOAIS_COMUNS = (
    "Nome", "CPF", "RG ou documento de identificação", "Data de nascimento",
    "Endereço", "Telefone", "E-mail", "Matrícula funcional",
    "Dados funcionais ou profissionais", "Dados escolares ou acadêmicos",
    "Dados familiares", "Dados financeiros", "Dados socioeconômicos",
    "Localização", "Número de protocolo, processo ou cadastro", "Nacionalidade",
    "País de origem", "Idioma ou necessidade de atendimento em outro idioma",
    "Situação ou documentação migratória",
)

_SENSIVEIS = (
    "Dados de saúde", "Dados biométricos", "Dados genéticos",
    "Origem racial ou étnica", "Convicção religiosa", "Opinião política",
    "Filiação sindical", "Dados sobre vida sexual",
    "Pertencimento a comunidade tradicional, quando efetivamente tratado",
)

_AVALIAR_CONTEXTO = (
    "Fotografia ou imagem", "Vídeo", "Voz ou áudio",
    "Informações contidas em documentos apresentados",
    "Pertencimento a povos ciganos / Roma, quando efetivamente tratado",
    "Outro", "A confirmar",
)

_PROTECAO_REFORCADA = {
    "CPF": "Atenção reforçada ao potencial de fraude e uso indevido de identificadores.",
    "RG ou documento de identificação": "Atenção reforçada ao potencial de fraude e uso indevido de documentos.",
    "Dados financeiros": "Embora seja dado pessoal comum, pode produzir dano patrimonial e exige proteção reforçada.",
    "Dados socioeconômicos": "Embora seja dado pessoal comum, pode expor vulnerabilidade e exige proteção reforçada.",
    "Localização": "Embora seja dado pessoal comum, pode afetar a segurança da pessoa e exige proteção reforçada.",
    "Situação ou documentação migratória": "Embora seja dado pessoal comum nesta matriz, pode expor vulnerabilidade ou revelar indiretamente informação sensível.",
}

_ALERTAS_CONTEXTO = {
    "Fotografia ou imagem": "O conteúdo ou o uso pode revelar biometria, saúde, origem étnica, religião ou outra informação sensível.",
    "Vídeo": "Imagem, som e contexto podem revelar indiretamente informações sensíveis.",
    "Voz ou áudio": "O conteúdo ou o uso técnico da voz pode revelar informação sensível ou biométrica.",
    "Informações contidas em documentos apresentados": "A classificação depende do conteúdo do documento e pode envolver dados sensíveis.",
    "Pertencimento a povos ciganos / Roma, quando efetivamente tratado": "O enquadramento pode envolver origem étnica e exige validação jurídica; não há classificação automática de risco.",
    "Outro": "A categoria descrita no complemento deverá ser avaliada antes da futura submissão.",
    "A confirmar": "A categoria ainda precisa ser identificada; esta opção não constitui classificação jurídica.",
}


def _construir_matriz():
    matriz: dict[str, ClassificacaoCategoriaDados] = {}
    for categoria in _PESSOAIS_COMUNS:
        matriz[categoria] = ClassificacaoCategoriaDados(
            PESSOAL_COMUM, "Pessoal comum",
            "Classificação informativa: dado pessoal comum não significa risco baixo.",
            _PROTECAO_REFORCADA.get(categoria),
        )
    for categoria in _SENSIVEIS:
        alerta = None
        if categoria == "Pertencimento a comunidade tradicional, quando efetivamente tratado":
            alerta = "Pode revelar origem racial ou étnica; o enquadramento concreto exige validação jurídica."
        matriz[categoria] = ClassificacaoCategoriaDados(
            SENSIVEL, "Dado pessoal sensível",
            "Indicação informativa associada às categorias do art. 5º, II, da LGPD.",
            alerta,
        )
    for categoria in _AVALIAR_CONTEXTO:
        rotulo = {"Outro": "Pendente de avaliação",
                  "A confirmar": "Pendente de identificação"}.get(
                      categoria, "Depende do contexto"
                  )
        matriz[categoria] = ClassificacaoCategoriaDados(
            AVALIAR_CONTEXTO, rotulo,
            "A classificação depende do conteúdo e do contexto; não há enquadramento automático.",
            _ALERTAS_CONTEXTO[categoria],
        )
    return MappingProxyType(matriz)


CLASSIFICACOES_CATALOGO_5_1 = _construir_matriz()


def validar_classificacoes_catalogo_5_1(alternativas: tuple[str, ...]) -> list[str]:
    """Exige correspondência exata entre catálogo REV13 e matriz informativa."""

    catalogo = set(alternativas)
    classificados = set(CLASSIFICACOES_CATALOGO_5_1)
    problemas = []
    if catalogo != classificados:
        ausentes = sorted(catalogo - classificados)
        extras = sorted(classificados - catalogo)
        if ausentes:
            problemas.append("categorias sem classificação: " + ", ".join(ausentes))
        if extras:
            problemas.append("classificações sem categoria: " + ", ".join(extras))
    return problemas
