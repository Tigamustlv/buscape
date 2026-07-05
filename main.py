from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

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
def home():
    return {"message": "Olá, FastAPI"}

# ---------------- FRONT ----------------
@app.get("/menu")
def menu():
    return FileResponse("index.html")

# ---------------- BUSCA ----------------
@app.get("/buscar")
def buscar(q: str):

    con = sqlite3.connect("clientes.db")
    cursor = con.cursor()

    cursor.execute("""
        SELECT originador, fundo, operacao, cliente, documento, contrato, cessao
        FROM clientes
        WHERE cliente LIKE ?
           OR documento LIKE ?
           OR contrato LIKE ?
           OR originador LIKE ?
    """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))

    rows = cursor.fetchall()
    con.close()

    return [
        {
            "originador": r[0],
            "fundo": r[1],
            "operacao": r[2],
            "cliente": r[3],
            "documento": r[4],
            "contrato": r[5],
            "cessao": r[6],
        }
        for r in rows
    ]