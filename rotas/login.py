from typing import Annotated

from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates




router = APIRouter(
    prefix="/login"
)


templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def pagina_login(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )





@router.post("/")
async def login(request: Request, email=Form(...), senha=Form(...)):

    if email == "admin@buscape.com.br" and senha == "senha124":

        response = RedirectResponse(
            url="/",
            status_code=303
        )

        response.set_cookie(
            key="session_token",
            value="token_senha",
            httponly=True
        )

        return response

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "email": email,
            "error": "Credenciais invalidas"
        }
    )

