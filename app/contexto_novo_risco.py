"""A6: cópia explícita do contexto, sem avaliações ou atos do risco anterior."""
from copy import deepcopy
BLOCOS={1,2,3,6,7,8,9,10,11,12,13}

def copiar(estado,codigo):
    from app.questionario_forms34 import perguntas
    ids={q['id'] for q in perguntas(3) if q['bloco'] in BLOCOS}
    respostas={k:deepcopy(v) for k,v in estado.get('respostas',{}).items() if k in ids}
    return dict(respostas=respostas,contexto_copiado={k:dict(codigo=codigo,versao=estado['versao']) for k in respostas},
        complementos={k:v for k,v in deepcopy(estado.get('complementos',{})).items() if k in respostas},
        controles_bloco13=deepcopy(estado.get('controles_bloco13',{})),observacoes_controles=estado.get('observacoes_controles',''))
