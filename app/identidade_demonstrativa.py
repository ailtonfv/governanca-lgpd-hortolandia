"""Formatação exclusiva da demonstração; nunca altera Pessoa ou eventos."""
import re
from markupsafe import Markup


def identidade_demonstrativa(nome):
    if not nome:
        return nome
    texto = str(nome).strip()
    return texto if re.search(r'\(fict[ií]ci[oa]\)', texto, re.I) else texto + ' (fictício)'


def nomes_em_texto(valor):
    # Compatibilidade com mensagens e nomes históricos da massa demonstrativa.
    if not isinstance(valor, str) or isinstance(valor, Markup):
        return valor
    return re.sub(r'\bServidor (?:Alfa|Beta|Gama|Delta|Épsilon|Epsilon|Zeta|Eta)\b(?! \(fictício\))',
                  lambda m: identidade_demonstrativa(m[0]), valor)


def configurar_identidade(paginas):
    from app.obrigatoriedade_forms import metadado_pergunta
    paginas.env.globals['metadado_r17'] = metadado_pergunta
    paginas.env.filters['identidade_demonstrativa'] = identidade_demonstrativa
    paginas.env.finalize = nomes_em_texto
