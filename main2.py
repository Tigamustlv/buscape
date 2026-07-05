
import sqlite3

con = sqlite3.connect("clientes.db")
cursor = con.cursor()

clientes = [
("Empresa 1","FGTS","Empréstimo","João Andrade","11111111111","100001","Sim"),
("Empresa 2","FGTS","Empréstimo","João Lima","48484848484","100050","Sim"),
]

cursor.executemany("""
INSERT INTO clientes
VALUES (?, ?, ?, ?, ?, ?, ?)
""", clientes)

con.commit()