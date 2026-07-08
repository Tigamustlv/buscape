import sqlite3

conn = sqlite3.connect("clientes.db")
cursor = conn.cursor()

# Cria a tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    originador TEXT NOT NULL,
    fundo TEXT NOT NULL,
    operacao TEXT NOT NULL,
    cessao TEXT,
    ccb TEXT,
    documento TEXT,
    nome TEXT
);
""")

conn.commit()
conn.close()

print("Tabela 'clientes' criada com sucesso!")