"""Validações dos campos especializados, aplicadas também a envios diretos."""
import re
from datetime import date


def validar_referencia_temporal(valor):
    if len(valor) > 200:
        raise ValueError('Informe a referência temporal em até 200 caracteres.')
    if re.match(r'^\d{4}-\d{2}-\d{2}$', valor):
        try:
            date.fromisoformat(valor)
        except ValueError:
            raise ValueError('Informe uma data válida.') from None
    return valor


def data_exata(valor):
    try:
        return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}', valor) and date.fromisoformat(valor))
    except ValueError:
        return False


def normalizar_cnpj(valor):
    if not valor.strip():
        return ''
    if not re.fullmatch(r'(?:\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', valor.strip()):
        raise ValueError('Informe o CNPJ no formato 00.000.000/0000-00.')
    digitos = re.sub(r'\D', '', valor)
    if len(set(digitos)) == 1:
        raise ValueError('Confira os dígitos verificadores do CNPJ.')
    for tamanho, pesos in ((12, (5,4,3,2,9,8,7,6,5,4,3,2)), (13, (6,5,4,3,2,9,8,7,6,5,4,3,2))):
        resto = sum(int(d) * p for d, p in zip(digitos[:tamanho], pesos)) % 11
        if int(digitos[tamanho]) != (0 if resto < 2 else 11 - resto):
            raise ValueError('Confira os dígitos verificadores do CNPJ.')
    return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
