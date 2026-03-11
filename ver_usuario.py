# ver_usuario.py
import sqlite3
from modules.security import verificar_password

conn = sqlite3.connect("base_datos.db")
cursor = conn.cursor()

matricula = input("Ingresa la matrícula del nuevo usuario: ")

cursor.execute("SELECT password FROM usuarios WHERE matricula = ?", (matricula,))
result = cursor.fetchone()

if result:
    password_guardada = result[0]
    print(f"📌 Contraseña guardada: {password_guardada}")
    print(f"📌 Longitud: {len(password_guardada)}")
    print(f"📌 Empieza con $2b$? {'✅ Sí' if password_guardada.startswith('$2b$') else '❌ No'}")
    
    # Probar con la contraseña que crees que es
    prueba = input("Ingresa la contraseña que usaste: ")
    if verificar_password(prueba, password_guardada):
        print("✅ La contraseña ES correcta (el hash funciona)")
    else:
        print("❌ La contraseña NO es correcta")
else:
    print("❌ Usuario no encontrado")

conn.close()