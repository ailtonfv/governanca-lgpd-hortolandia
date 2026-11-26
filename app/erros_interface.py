"""Erros HTTP navegáveis, sem ampliar permissões ou esconder falhas internas."""
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError

paginas = Jinja2Templates(directory=Path(__file__).parent/'paginas')


def instalar(app):
    @app.exception_handler(HTTPException)
    async def erro_http(request, erro):
        # Clientes que pedem JSON explicitamente preservam o contrato da API.
        if 'application/json' in request.headers.get('accept','') and 'text/html' not in request.headers.get('accept',''):
            return JSONResponse({'detail': erro.detail},status_code=erro.status_code,headers=erro.headers)
        conta=request.query_params.get('conta_id','')
        if not conta and request.method == 'POST':
            try: conta=(await request.form()).get('conta_id','')
            except (ValueError,RuntimeError): pass
        mensagem = ('Seu perfil não permite acessar esta página.' if erro.status_code in (401,403)
                    else 'Esta página não foi encontrada.' if erro.status_code == 404
                    else erro.detail if isinstance(erro.detail,str) else 'Confira os dados informados e tente novamente.')
        return paginas.TemplateResponse(request=request,name='erro_navegavel.html',status_code=erro.status_code,
            headers=erro.headers,context=dict(mensagem=mensagem,conta_id=conta,
                pagina_isolada='/cartilha/' in request.url.path))

    @app.exception_handler(RequestValidationError)
    async def erro_entrada(request, erro):
        return await erro_http(request,HTTPException(422,'Confira os campos informados antes de continuar.'))
