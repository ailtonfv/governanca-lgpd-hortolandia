"""Marca de apresentação por conta e navegador; não concede autorização."""
from hashlib import sha256


def chave(conta_id):
    return 'entrada_' + sha256(conta_id.encode()).hexdigest()[:24]


def apresentada(request, conta_id):
    return request.cookies.get(chave(conta_id)) == '1'


def marcar(response, conta_id):
    response.set_cookie(chave(conta_id), '1', max_age=31536000,
                        httponly=True, samesite='lax')
    return response
