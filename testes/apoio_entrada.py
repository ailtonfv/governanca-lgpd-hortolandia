"""Cliente dos testes operacionais: apresentação inicial já consultada.

O primeiro acesso é exercitado com TestClient original em test_lote14_parte2.
As verificações de escopo, conteúdo e autorização dos demais testes permanecem.
"""
from urllib.parse import urlsplit, parse_qs
from fastapi.testclient import TestClient
from app.apresentacao_entrada import chave


class ClienteAposApresentacao(TestClient):
    def request(self, method, url, **kwargs):
        params = parse_qs(urlsplit(str(url)).query)
        conta = params.get('conta_id', ['CONTA-A1'])[0]
        extras = kwargs.get('params') or {}
        if hasattr(extras, 'get'):
            conta = extras.get('conta_id', conta)
        self.cookies.set(chave(conta), '1')
        return super().request(method, url, **kwargs)
