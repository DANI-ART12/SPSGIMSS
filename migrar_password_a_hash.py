# ============================================
# migrar_passwords_a_hash.py
# ============================================
# EJECUTAR UNA SOLA VEZ para convertir todas las contraseñas
# existentes a hash seguro.
# ============================================

import sqlite3
from modules.security import hash_password

print("🔐 MIGRANDO CONTRASEÑAS A HASH")
print("="*50)

# Conectar a la base de datos
conn = sqlite3.connect("base_datos.db")
cursor = conn.cursor()

# Verificar si ya existen las columnas necesarias
cursor.execute("PRAGMA table_info(usuarios)")
columnas = [col[1] for col in cursor.fetchall()]

# Agregar columnas si no existen
if 'intentos_fallidos' not in columnas:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN intentos_fallidos INTEGER DEFAULT 0")
    print("✅ Columna 'intentos_fallidos' agregada")

if 'bloqueado_hasta' not in columnas:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TEXT")
    print("✅ Columna 'bloqueado_hasta' agregada")

if 'ultimo_intento' not in columnas:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN ultimo_intento TEXT")
    print("✅ Columna 'ultimo_intento' agregada")

if 'codigo_recuperacion' not in columnas:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN codigo_recuperacion TEXT")
    print("✅ Columna 'codigo_recuperacion' agregada")

if 'codigo_expiracion' not in columnas:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN codigo_expiracion TEXT")
    print("✅ Columna 'codigo_expiracion' agregada")

# Obtener todos los usuarios
cursor.execute("SELECT matricula, password FROM usuarios")
usuarios = cursor.fetchall()

print(f"\n📊 Usuarios encontrados: {len(usuarios)}")
print("-" * 50)

# Migrar cada contraseña a hash
for matricula, password_actual in usuarios:
    print(f"Procesando: {matricula}")
    
    # Verificar si ya es un hash (empieza con $2b$)
    if password_actual and password_actual.startswith('$2b$'):
        print(f"   ⏭️  Ya es hash, saltando...")
        continue
    
    # Convertir a hash
    if password_actual:
        nuevo_hash = hash_password(password_actual)
        cursor.execute("UPDATE usuarios SET password = ? WHERE matricula = ?", 
                      (nuevo_hash, matricula))
        print(f"   ✅ Migrada: '{password_actual}' → hash")
    else:
        print(f"   ⚠️  Contraseña vacía, ignorando")

# Guardar cambios
conn.commit()
conn.close()

print("\n" + "="*50)
print("✅ MIGRACIÓN COMPLETADA")
print("="*50)
print("\n📌 Ahora las contraseñas están seguras en la base de datos.")