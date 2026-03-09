import sqlite3

print("🔧 Creando tabla 'gastos' en SQLite...")

conn = sqlite3.connect("base_datos.db")
cursor = conn.cursor()

# Crear tabla gastos con estructura típica
cursor.execute('''
CREATE TABLE IF NOT EXISTS gastos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folio_pliego TEXT,
    categoria TEXT,
    factura TEXT,
    proveedor TEXT,
    fecha TEXT,
    importe REAL,
    concepto TEXT,
    justificacion TEXT,
    tipo TEXT
)
''')

conn.commit()
conn.close()

print("✅ Tabla 'gastos' creada exitosamente")
print("📋 Estructura: id, folio_pliego, categoria, factura, proveedor, fecha, importe, concepto, justificacion, tipo")
