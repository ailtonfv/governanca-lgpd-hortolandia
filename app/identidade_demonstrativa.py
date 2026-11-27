"""Formatação exclusiva da demonstração; nunca altera Pessoa ou eventos."""
import re
from jinja2 import pass_context
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


@pass_context
def sessao_cabecalho(contexto):
    """Resolve a conta explícita desta página para a faixa compartilhada."""
    from sqlalchemy.orm import Session
    from app.banco import motor
    from app.consultas_interface import _identidade, papeis_em_sessao

    request = contexto.get('request')
    conta = contexto.get('conta_id') or request.query_params.get('conta_id')
    if not conta:
        return None
    with Session(motor) as sessao:
        identidade = _identidade(sessao, conta, vinculos_vigentes=True)
        if not identidade:
            return None
        papel = contexto.get('papel_principal34')
        if not papel or papel == 'Consulta':
            papeis = papeis_em_sessao(sessao, conta, identidade=identidade).split(' · ')
            dpo = 'Encarregado de Dados (DPO)'
            papel = dpo if dpo in papeis else papeis[0]
        return {'nome': identidade['nome'], 'papel': papel}


def papel_principal_forms34(papeis):
    rotulos = (
        ('dpo', 'Encarregado de Dados (DPO)'), ('aal', 'AAL'),
        ('secretario', 'Secretário(a)'), ('gabinete', 'Gabinete do Prefeito'),
        ('relator', 'Relator do Comitê'), ('verificador', 'Verificador do Comitê'),
        ('secretaria', 'Secretaria'), ('executor_unidade', 'Executor habilitado'),
    )
    return next((rotulo for papel, rotulo in rotulos if papel in papeis), 'Consulta')


def configurar_identidade(paginas):
    from app.identificacao_registro import identificar
    paginas.env.globals['identificar_registro']=identificar
    paginas.env.globals['sessao_cabecalho'] = sessao_cabecalho
    from app.obrigatoriedade_forms import metadado_pergunta
    paginas.env.globals['metadado_r17'] = metadado_pergunta
    from app.apresentacao_atos34 import data_br
    paginas.env.filters['data_br'] = data_br
    paginas.env.filters['identidade_demonstrativa'] = identidade_demonstrativa
    paginas.env.finalize = nomes_em_texto
