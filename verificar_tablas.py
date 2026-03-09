import sqlite3

conn = sqlite3.connect("base_datos.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = cursor.fetchall()

print("📋 TABLAS EN BASE_DATOS.DB")
print("="*40)
for tabla in tablas:
    cursor.execute(f"SELECT COUNT(*) FROM {tabla[0]}")
    count = cursor.fetchone()[0]
    print(f"✅ {tabla[0]}: {count} registros")

conn.close()
