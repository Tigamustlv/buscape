import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog


def escolher_arquivo():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(
        title="Selecione a planilha",
        filetypes=[("Excel", "*.xlsx *.xls")]
    )


arquivo = escolher_arquivo()

# Lê todas as abas já como texto
planilhas = pd.read_excel(
    arquivo,
    sheet_name=None,
    dtype=str
)

conn = sqlite3.connect("clientes.db")
cursor = conn.cursor()

for nome_aba, df in planilhas.items():

    print(f"Importando aba: {nome_aba}")

    # Remove linhas totalmente vazias
    df = df.dropna(how="all")

    # Mantém apenas as colunas desejadas
    df = df[
        [
            "originador",
            "fundo",
            "operacao",
            "cessao",
            "ccb",
            "documento",
            "nome",
        ]
    ]

    # Limpa espaços e converte vazios em None
    for coluna in df.columns:
        df[coluna] = (
            df[coluna]
            .astype(str)
            .str.strip()
            .replace({"nan": None, "": None})
        )

    for indice, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO clientes (
                    originador,
                    fundo,
                    operacao,
                    cessao,
                    ccb,
                    documento,
                    nome
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row["originador"],
                row["fundo"],
                row["operacao"],
                row["cessao"],
                row["ccb"],
                row["documento"],
                row["nome"]
            ))
        except Exception as e:
            print(f"\nErro na aba '{nome_aba}', linha {indice}")
            print(row.to_dict())
            raise e

conn.commit()
conn.close()

print("Importação concluída com sucesso!")