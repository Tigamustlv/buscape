from fastapi import FastAPI, Response, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from rotas import login
from pathlib import Path

import sqlite3
import io
import pandas as pd
import boto3
import zipfile
import pandas
import os




app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(login.router)


PASTA_RESULTADOS = "resultados"

os.makedirs(
    PASTA_RESULTADOS,
    exist_ok=True
)



### CORS - front pra chamar API ###

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
        SELECT id, originador, fundo, operacao, cessao, ccb, documento, nome, lastro
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
        SELECT originador, fundo, operacao, cessao, ccb, documento, nome, lastro
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


@app.get("/calculadora")
async def calculadora(request: Request):
    return templates.TemplateResponse(
        name="calculadora.html",
        request=request,
        context={
            "request": request,
            "titulo": "Calculadora",
        }
    )


@app.get("/identifica-fundo")
async def consultaplan(request: Request):
    return templates.TemplateResponse(
        name="identifica-fundo.html",
        request=request,
        context={
            "request": request,
            "titulo": "Identifica Fundo",
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


AWS_ACCESS_KEY_ID=''
AWS_SECRET_ACCESS_KEY=''
AWS_REGION=''
AWS_BUCKET_NAME=''


def obter_documento(id):
    con = sqlite3.connect("clientes.db")
    con.row_factory = sqlite3.Row

    cursor = con.cursor()

    cursor.execute(
        """
        SELECT id, lastro, ccb
        FROM clientes
        WHERE id = ?
        """,
        (id,)
    )

    row = cursor.fetchone()

    con.close()

    if row is None:
        return None

    return row


@app.get("/download-lastro/{id}")
async def baixar_lastro(id: int):

    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )




    documento = obter_documento(id)

    if documento is None:
        raise HTTPException(
            status_code=404,
            detail="Documento não encontrado"
        )

    prefixo = documento["lastro"]
    ccb = documento["ccb"]



    objetos = s3.list_objects_v2(
        Bucket=AWS_BUCKET_NAME,
        Prefix=prefixo,
    )


    zip_buffer = io.BytesIO()


    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zip_file:


        for obj in objetos.get("Contents", []):

            chave = obj["Key"]

            if chave.endswith("/"):
                continue


            arquivo = s3.get_object(
                Bucket=AWS_BUCKET_NAME,
                Key=chave,
            )


            conteudo = arquivo["Body"].read()


            nome_arquivo = chave[len(prefixo):].lstrip("/")


            zip_file.writestr(
                nome_arquivo,
                conteudo
            )


    zip_buffer.seek(0)


    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition":
            f'attachment; filename="lastro_{ccb}.zip"'
        },
    )




###

@app.post("/identificar-fundo")
async def identificar_fundo(
    file: UploadFile = File(...)
):

    if not file.filename.lower().endswith(
        (".xlsx", ".xls")
    ):
        raise HTTPException(
            status_code=400,
            detail="O arquivo precisa ser Excel (.xlsx ou .xls)"
        )


    try:

        df = pd.read_excel(
            file.file,
            dtype=str
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=f"Erro ao ler planilha: {str(e)}"
        )



    obrigatorias = [
        "CPF",
        "CCB",
        "ORIGEM"
    ]


    faltantes = [
        coluna
        for coluna in obrigatorias
        if coluna not in df.columns
    ]


    if faltantes:

        raise HTTPException(
            status_code=400,
            detail=f"Colunas faltantes: {faltantes}"
        )



    # normaliza CCB

    df["CCB"] = (
        df["CCB"]
        .fillna("")
        .astype(str)
        .str.strip()
    )


    lista_ccb = [
        ccb
        for ccb in df["CCB"].unique()
        if ccb
    ]



    if not lista_ccb:

        raise HTTPException(
            status_code=400,
            detail="Nenhuma CCB encontrada na planilha"
        )



    con = sqlite3.connect(
        "clientes.db"
    )

    con.row_factory = sqlite3.Row

    cursor = con.cursor()



    placeholders = ",".join(
        ["?"] * len(lista_ccb)
    )


    cursor.execute(
        f"""
        SELECT
            ccb,
            operacao
        FROM clientes
        WHERE ccb IN ({placeholders})
        """,
        lista_ccb
    )


    registros = cursor.fetchall()


    con.close()



    mapa_fundos = {}

    for row in registros:

        ccb = str(row["ccb"]).strip()

        fundo = row["operacao"]


        if fundo is None:

            fundo = "Operação não encontrada"


        mapa_fundos[ccb] = fundo




    df["ORIGEM"] = (

        df["CCB"]
        .map(mapa_fundos)
        .fillna("Não encontrado")

    )



    nome_original = Path(
        file.filename
    ).stem



    nome_resultado = (
        nome_original
        + "-resultado.xlsx"
    )



    caminho = os.path.join(
        PASTA_RESULTADOS,
        nome_resultado
    )



    # salva excel

    df.to_excel(
        caminho,
        index=False
    )



    # ===========================
    # LIMPEZA PARA JSON
    # ===========================


    df_json = df.copy()


    df_json = df_json.replace(
        [
            float("inf"),
            float("-inf"),
            float("nan")
        ],
        None
    )


    df_json = df_json.fillna(
        ""
    )


    dados = []


    for linha in df_json.to_dict(
        orient="records"
    ):

        nova_linha = {}

        for chave, valor in linha.items():


            # converte numpy types

            if pd.isna(valor):

                valor = ""


            elif not isinstance(
                valor,
                (str, int, float, bool)
            ):

                valor = str(valor)


            nova_linha[chave] = valor


        dados.append(
            nova_linha
        )




    return {

        "sucesso": True,

        "arquivo": nome_resultado,

        "total_linhas": len(df),

        "fundos_encontrados": len(registros),

        "data": dados

    }


@app.get("/baixar-resultado/{arquivo}")
def baixar_resultado(
    arquivo: str
):

    caminho = os.path.join(
        PASTA_RESULTADOS,
        arquivo
    )


    if not os.path.exists(caminho):

        raise HTTPException(
            status_code=404,
            detail="Arquivo não encontrado"
        )



    return FileResponse(

        path=caminho,

        filename=arquivo,

        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )




'''
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

'''