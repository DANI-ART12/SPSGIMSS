# ============================================
# limpiar_para_pruebas_corregido.py
# ============================================
import sqlite3
import os
from datetime import datetime
import shutil
from modules.security import hash_password

print("="*70)
print("🧹 LIMPIEZA PARA INICIO DE PRUEBAS (VERSIÓN CORREGIDA)")
print("="*70)

# Backup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_name = f"backup_antes_pruebas_{timestamp}.db"
shutil.copy2("base_datos.db", backup_name)
print(f"✅ Backup: {backup_name}")

# Conectar
conn = sqlite3.connect("base_datos.db")
cursor = conn.cursor()

# 1. Limpiar todas las tablas de datos
tablas = ["gastos", "informes", "mantenimientos", "pliegos", 
          "traslados_locales", "vehiculos", "hospitales"]

for tabla in tablas:
    cursor.execute(f"DELETE FROM {tabla}")
    print(f"✅ {tabla} limpiada")

# 2. Verificar estructura de config_admin
cursor.execute("PRAGMA table_info(config_admin)")
columnas = [col[1] for col in cursor.fetchall()]
print(f"\n📋 Columnas en config_admin: {columnas}")

# 3. Limpiar config_admin según su estructura real
if columnas:
    # Construir INSERT dinámico según las columnas existentes
    columnas_insert = []
    valores_insert = []
    
    for col in columnas:
        if col in ['titular_unidad', 'unidad_administrativa', 'adscripcion', 'cargo_titular']:
            columnas_insert.append(col)
            valores_insert.append("PENDIENTE")
        elif col in ['folio_inicial_sistema', 'folio_inicial_foraneo', 'folio_inicial_local']:
            columnas_insert.append(col)
            if 'foraneo' in col:
                valores_insert.append("F001/2026")
            else:
                valores_insert.append("L001/2026")
    
    if columnas_insert:
        # Limpiar primero
        cursor.execute("DELETE FROM config_admin")
        
        # Insertar con las columnas correctas
        query = f"INSERT INTO config_admin ({', '.join(columnas_insert)}) VALUES ({', '.join(['?']*len(columnas_insert))})"
        cursor.execute(query, valores_insert)
        print(f"✅ config_admin limpiada y reiniciada con valores básicos")
else:
    print("⚠️  No hay columnas en config_admin, creando tabla...")
    # Si no existe la tabla, la creamos con estructura básica
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titular_unidad TEXT,
            unidad_administrativa TEXT,
            adscripcion TEXT,
            cargo_titular TEXT,
            folio_inicial_sistema TEXT,
            folio_inicial_local TEXT
        )
    """)
    cursor.execute("""
        INSERT INTO config_admin 
        (titular_unidad, unidad_administrativa, adscripcion, 
         folio_inicial_sistema, folio_inicial_local)
        VALUES (?, ?, ?, ?, ?)
    """, ("PENDIENTE", "PENDIENTE", "PENDIENTE", "F001/2026", "L001/2026"))
    print("✅ config_admin creada")

# 4. Usuarios: solo admin
print("\n👤 Procesando usuarios...")
cursor.execute("SELECT COUNT(*) FROM usuarios WHERE matricula = '123'")
if cursor.fetchone()[0] > 0:
    cursor.execute("DELETE FROM usuarios WHERE matricula != '123'")
    cursor.execute("""
        UPDATE usuarios SET 
            password = ?,
            nombre = 'ADMIN',
            apellido_p = 'SISTEMA',
            rol = 'Administrador',
            estatus = 'Alta',
            intentos_fallidos = 0,
            bloqueado_hasta = NULL
        WHERE matricula = '123'
    """, (hash_password("admin"),))
    print("✅ Admin actualizado: 123 / admin")
else:
    cursor.execute("""
        INSERT INTO usuarios (
            matricula, nombre, apellido_p, password, rol, estatus,
            intentos_fallidos, bloqueado_hasta
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('123', 'ADMIN', 'SISTEMA', hash_password('admin'), 
          'Administrador', 'Alta', 0, None))
    print("✅ Admin creado: 123 / admin")

# 5. Resetear secuencias
try:
    cursor.execute("DELETE FROM sqlite_sequence")
    print("\n🔄 Secuencias reiniciadas")
except:
    pass

# 6. Guardar cambios
conn.commit()

# 7. Verificación final
print("\n📊 VERIFICACIÓN FINAL:")

# Tablas vacías
print("\n   📌 Tablas vacías:")
for tabla in tablas:
    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
    count = cursor.fetchone()[0]
    print(f"   {tabla}: {count} registros {'✅' if count == 0 else '❌'}")

# Config_admin
cursor.execute("SELECT COUNT(*) FROM config_admin")
count_config = cursor.fetchone()[0]
print(f"\n   ⚙️  config_admin: {count_config} registro(s)")

if count_config > 0:
    cursor.execute("SELECT * FROM config_admin LIMIT 1")
    config_data = cursor.fetchone()
    print(f"      Configuración guardada")

# Usuarios
cursor.execute("SELECT COUNT(*) FROM usuarios")
total_usuarios = cursor.fetchone()[0]
print(f"\n   👥 Usuarios totales: {total_usuarios}")

if total_usuarios == 1:
    cursor.execute("SELECT matricula, nombre, rol FROM usuarios")
    admin_data = cursor.fetchone()
    print(f"      Único usuario: {admin_data[0]} - {admin_data[1]} ({admin_data[2]})")

conn.close()

print("\n" + "="*70)
print("✅ BASE DE DATOS LISTA PARA PRUEBAS")
print("="*70)
print(f"\n📌 Usuario ADMIN:")
print("   Matrícula: 123")
print("   Contraseña: admin")
print(f"\n📁 Backup guardado: {backup_name}")