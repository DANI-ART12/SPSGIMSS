# ============================================
# migrar_sqlite.py (VERSIÓN MEJORADA)
# ============================================
import pandas as pd
import sqlite3
import os
import re

print("🚀 Migrando Excel a SQLite...")

EXCEL_FILE = "base_datos.xlsx"
DB_FILE = "base_datos.db"

# Verificar que el Excel existe
if not os.path.exists(EXCEL_FILE):
    print("❌ ERROR: No se encuentra base_datos.xlsx")
    print(f"   Buscando en: {os.getcwd()}")
    exit(1)

# Conectar a SQLite (crea el archivo)
conn = sqlite3.connect(DB_FILE)
print(f"✅ Conectado a {DB_FILE}")

# Leer todas las hojas del Excel
xls = pd.ExcelFile(EXCEL_FILE)
print(f"📑 Hojas encontradas: {xls.sheet_names}")

# Función para limpiar nombres de columnas
def limpiar_nombre_columna(nombre):
    """Convierte nombres a formato seguro para SQLite"""
    if not isinstance(nombre, str):
        nombre = str(nombre)
    # Reemplazar espacios y caracteres especiales con _
    nombre = re.sub(r'[^a-zA-Z0-9_]', '_', nombre)
    # Eliminar guiones bajos múltiples
    nombre = re.sub(r'_+', '_', nombre)
    # Quitar guiones bajos al inicio o final
    nombre = nombre.strip('_')
    # Si queda vacío, poner nombre genérico
    if not nombre:
        nombre = 'columna'
    return nombre.lower()

# Migrar cada hoja
for hoja in xls.sheet_names:
    try:
        print(f"📄 Migrando: {hoja}")
        df = pd.read_excel(xls, sheet_name=hoja)
        
        # Limpiar nombres de columnas
        df.columns = [limpiar_nombre_columna(col) for col in df.columns]
        
        # Mostrar columnas (debug)
        print(f"   Columnas: {list(df.columns)}")
        
        # Guardar en SQLite
        df.to_sql(hoja, conn, if_exists='replace', index=False)
        print(f"   ✅ {len(df)} registros")
        
    except Exception as e:
        print(f"   ❌ Error en hoja '{hoja}': {e}")
        print("   Continuando con la siguiente hoja...")

conn.close()
print("\n✅ Migración completada")
print(f"📁 Archivo creado: {DB_FILE}")