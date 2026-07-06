
import sqlite3

conn = sqlite3.connect("clientes.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT COUNT(*) FROM clientes"
    )
print(cursor.fetchone()[0])

conn.close()



