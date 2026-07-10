from fastapi import FastAPI, Response, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from rotas import login

import sqlite3
import io
import pandas as pd

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)

# CORS (front pode chamar API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- HOME ----------------
@app.get("/")
async def front_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "titulo": "Buscapé",
            "versao": "1.0.0",
        }
    )


# ---------------- FRONT ----------------
#@app.get("/menu")
#def menu():
#    return FileResponse("index.html")

# ---------------- BUSCA ----------------
@app.get("/buscar")
def buscar(q: str, limit: int = 1000, offset: int = 0):

    # Divide por vírgula e remove espaços
    termos = [t.strip() for t in q.split(",") if t.strip()]

    if not termos:
        return {"total": 0, "data": []}

    con = sqlite3.connect("clientes.db")
    con.row_factory = sqlite3.Row
    cursor = con.cursor()

    # Monta os WHEREs dinamicamente
    where = " OR ".join(
        "(nome LIKE ? OR documento LIKE ? OR ccb LIKE ? OR operacao LIKE ?)"
        for _ in termos
    )

    params = []
    for termo in termos:
        like = f"%{termo}%"
        params.extend([like, like, like, like])

    # COUNT
    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM clientes
        WHERE {where}
        """,
        params,
    )

    total = cursor.fetchone()[0]

    # SELECT
    cursor.execute(
        f"""
        SELECT originador, fundo, operacao, cessao, ccb, documento, nome
        FROM clientes
        WHERE {where}
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )

    rows = cursor.fetchall()
    con.close()

    return {
        "total": total,
        "data": [dict(r) for r in rows]
    }



@app.get("/exportar")
def exportar(q: str):

    termos = [t.strip() for t in q.split(",") if t.strip()]

    if not termos:
        return {"erro": "Consulta vazia"}

    con = sqlite3.connect("clientes.db")

    where = " OR ".join(
        "(nome LIKE ? OR documento LIKE ? OR ccb LIKE ? OR operacao LIKE ?)"
        for _ in termos
    )

    params = []

    for termo in termos:
        like = f"%{termo}%"
        params.extend([like, like, like, like])

    query = f"""
        SELECT originador, fundo, operacao, cessao, ccb, documento, nome
        FROM clientes
        WHERE {where}
    """

    df = pd.read_sql_query(query, con, params=params)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="resultado")

    con.close()

    output.seek(0)

    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=buscape_resultado.xlsx"
        }
    )



@app.get("/consulta")
async def consulta(request: Request):
    return templates.TemplateResponse(
        name="consulta.html",
        request=request,
        context={
            "request": request,
            "titulo": "Consulta",
        }
    )


@app.get("/relatorios")
async def relatorios(request: Request):
    return templates.TemplateResponse(
        name="relatorios.html",
        request=request,
        context={
            "request": request,
            "titulo": "Relatórios",
        }
    )


@app.get("/")
async def front_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "titulo": "Buscapé",
            "versao": "1.0.0",
        }
    )



# ===

@app.get("/ops")
def listar_operacoes():

    con = sqlite3.connect("clientes.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT DISTINCT operacao
        FROM clientes
        ORDER BY operacao
    """)

    data = [r[0] for r in cursor.fetchall()]
    con.close()

    return data



@app.get("/cessoes")
def listar_cessoes(operacao: str):

    con = sqlite3.connect("clientes.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT DISTINCT cessao
        FROM clientes
        WHERE operacao = ?
        ORDER BY CAST(cessao AS INTEGER)
    """, (operacao,))

    data = [r[0] for r in cursor.fetchall()]
    con.close()

    return data



@app.post("/relatorio/exportar")
def exportar_relatorio(payload: dict):

    operacao = payload["operacao"]
    cessoes = payload["cessoes"]
    colunas = payload["colunas"]

    con = sqlite3.connect("clientes.db")

    base_query = f"""
        SELECT {", ".join(colunas)}
        FROM clientes
        WHERE operacao = ?
    """

    params = [operacao]

    if cessoes:
        placeholders = ",".join(["?"] * len(cessoes))
        base_query += f" AND cessao IN ({placeholders})"
        params += cessoes

    chunk_size = 250000
    chunks = pd.read_sql_query(base_query, con, params=params, chunksize=chunk_size)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        for i, chunk in enumerate(chunks):
            sheet_name = f"parte_{i+1}"
            chunk.to_excel(writer, index=False, sheet_name=sheet_name)

    con.close()
    output.seek(0)

    return Response(
        content=output.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=relatorio.xlsx"}
    )