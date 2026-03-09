# ============================================
# modules/database.py - VERSIÓN SQLITE
# ============================================
# Este archivo reemplaza al anterior que usaba Excel.
# Mantiene los mismos nombres de funciones para que
# forms.py SIGA FUNCIONANDO IGUAL, sin modificaciones.
# ============================================

import sqlite3
import pandas as pd
import os
from datetime import datetime

# ============================================
# CONFIGURACIÓN
# ============================================
DB_FILE = "base_datos.db"  # 💾 Ahora usamos SQLite en lugar de Excel

# ============================================
# FUNCIÓN AUXILIAR: Obtener conexión
# ============================================
def get_connection():
    """
    Retorna una conexión a la base de datos SQLite.
    Esta función es interna, no se usa desde forms.py
    """
    return sqlite3.connect(DB_FILE)

# ============================================
# INICIALIZACIÓN DE BASE DE DATOS
# ============================================
def inicializar_base_datos():
    """
    Crea la base de datos SQLite con todas las tablas necesarias.
    Es el equivalente a cuando creabas el Excel con pestañas.
    """
    print("🔧 Ejecutando inicializar_base_datos...")
    
    if not os.path.exists(DB_FILE):
        print("📁 Creando nueva base de datos SQLite...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # --- TABLA usuarios ---
        # Almacena todos los datos del personal
        cursor.execute('''
            CREATE TABLE usuarios (
                matricula TEXT PRIMARY KEY,      -- Identificador único
                nombre TEXT,
                apellido_p TEXT,
                apellido_m TEXT,
                curp TEXT,
                rfc TEXT,
                departamento TEXT,
                tipo_contrato TEXT,
                gj TEXT,                          -- Grupo Jerárquico
                categoria TEXT,
                password TEXT,                     -- Contraseña (pronto será hash)
                rol TEXT,                          -- Administrador / Usuario
                estatus TEXT,                       -- Alta / Baja
                cuota_diaria TEXT,
                tel_oficina TEXT
            )
        ''')
        
        # --- TABLA pliegos ---
        # Almacena los pliegos de comisión (traslados foráneos)
        cursor.execute('''
            CREATE TABLE pliegos (
                folio TEXT PRIMARY KEY,            -- Folio único del pliego
                fecha_elaboracion TEXT,
                matricula TEXT,                     -- Matrícula del empleado
                estatus_pliego TEXT,                 -- Pendiente, Autorizado, etc.
                f_solicitante TEXT,
                f_cp TEXT,
                f_categoria TEXT,
                f_area TEXT,
                f_tel TEXT,
                m_objeto TEXT,
                p_a TEXT, p_b TEXT, p_c TEXT,
                m_destino TEXT,
                fecha_inicio TEXT,
                fecha_fin TEXT,
                medio_transporte TEXT,
                chofer TEXT,
                acompañante TEXT,
                ecco TEXT,                           -- Vehículo asignado
                anticipo_viaticos TEXT,
                anticipo_gasolina TEXT,
                anticipo_peaje TEXT,
                anticipo_transporte_t TEXT,
                anticipo_avion TEXT,
                total_anticipo TEXT,
                subtotal_sin_avion TEXT,
                observaciones TEXT,
                autoriza_nombre TEXT,
                dias_comision TEXT,
                comp_hospedaje_cargo TEXT,
                comp_hospedaje_abono TEXT,
                comp_alimentos_cargo TEXT,
                comp_alimentos_abono TEXT,
                comp_pasajes_cargo TEXT,
                comp_pasajes_abono TEXT,
                comp_combustible_cargo TEXT,
                comp_combustible_abono TEXT,
                comp_otros_cargo TEXT,
                comp_otros_abono TEXT,
                suma_cargos TEXT,
                suma_abonos TEXT,
                importe_total_comprobacion TEXT,
                elaboro_nombre TEXT,
                reviso_nombre TEXT,
                bueno_por_monto TEXT,
                recibi_letras TEXT,
                mostrar_bloque_especial TEXT,
                paciente TEXT,
                nss TEXT,
                FOREIGN KEY (matricula) REFERENCES usuarios(matricula)
            )
        ''')
        
        # --- TABLA informes ---
        # Almacena los informes posteriores al viaje
        cursor.execute('''
            CREATE TABLE informes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio_pliego TEXT,
                fecha_informe TEXT,
                no_cama TEXT,
                hora_salida_hgz TEXT,
                hora_llegada_destino TEXT,
                hora_regreso_hgz TEXT,
                km_inicial INTEGER,
                km_final INTEGER,
                km_total_recorrido INTEGER,
                resultados TEXT,
                contribuciones TEXT,
                ecco_utilizado TEXT,
                FOREIGN KEY (folio_pliego) REFERENCES pliegos(folio)
            )
        ''')
        
        # --- TABLA vehiculos ---
        cursor.execute('''
            CREATE TABLE vehiculos (
                ecco TEXT PRIMARY KEY,              -- Número ECCO del vehículo
                tipo TEXT,
                placas TEXT,
                marca TEXT,
                modelo TEXT,
                km_actual INTEGER,
                km_servicio INTEGER,
                estatus TEXT                          -- Alta, Baja, Mantenimiento
            )
        ''')
        
        # --- TABLA traslados_locales ---
        cursor.execute('''
            CREATE TABLE traslados_locales (
                folio TEXT PRIMARY KEY,
                fecha_creacion TEXT,
                fecha_traslado TEXT,
                turno TEXT,                            -- MATUTINO, VESPERTINO, NOCTURNO
                paciente TEXT,
                nss TEXT,
                domicilio TEXT,
                telefono TEXT,
                fecha_hora TEXT,
                empleado_comisionado TEXT,
                matricula_asignado TEXT,
                fecha_asignacion TEXT,
                vehiculo TEXT,
                km_inicial INTEGER,
                km_final INTEGER,
                cerrado_por TEXT,
                fecha_cierre TEXT,
                destino TEXT,
                servicio TEXT,
                cama TEXT,
                requiere TEXT,
                estatus TEXT,                           -- Programado, En Curso, Completado
                observaciones TEXT,
                matricula_admin TEXT
            )
        ''')
        
        # --- TABLA config_admin ---
        # Guarda la configuración institucional
        cursor.execute('''
            CREATE TABLE config_admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titular_unidad TEXT,
                unidad_administrativa TEXT,
                adscripcion TEXT,
                cargo_titular TEXT,
                folio_inicial_sistema TEXT,
                folio_inicial_local TEXT
            )
        ''')
        
        # --- TABLA hospitales ---
        cursor.execute('''
            CREATE TABLE hospitales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estado TEXT,
                nombre_hosp TEXT,
                direccion TEXT,
                alto_costo TEXT
            )
        ''')
        
        # --- TABLA mantenimientos ---
        cursor.execute('''
            CREATE TABLE mantenimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecco TEXT,
                fecha TEXT,
                tipo_servicio TEXT,
                lugar TEXT,
                km_registro INTEGER,
                observaciones TEXT,
                FOREIGN KEY (ecco) REFERENCES vehiculos(ecco)
            )
        ''')
        
        # --- TABLA gastos ---
        cursor.execute('''
            CREATE TABLE gastos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folio_pliego TEXT,
                categoria TEXT,
                factura TEXT,
                proveedor TEXT,
                fecha TEXT,
                importe REAL,
                concepto TEXT,
                justificacion TEXT,
                tipo TEXT,
                FOREIGN KEY (folio_pliego) REFERENCES pliegos(folio)
            )
        ''')
        
        # --- USUARIO ADMIN INICIAL ---
        # Insertamos el primer usuario administrador
        cursor.execute('''
            INSERT INTO usuarios (
                matricula, nombre, apellido_p, password, rol, estatus
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', ('123', 'ADMIN', 'SISTEMA', 'admin', 'Administrador', 'Alta'))
        
        # --- CONFIGURACIÓN INSTITUCIONAL INICIAL ---
        cursor.execute('''
            INSERT INTO config_admin (
                titular_unidad, unidad_administrativa, adscripcion, 
                folio_inicial_sistema, folio_inicial_local
            ) VALUES (?, ?, ?, ?, ?)
        ''', ('LIC. RICARDO REYES', 'DEPARTAMENTO DE PERSONAL', 'HGZ No. 1', 
              'F001/2026', 'L001/2026'))
        
        conn.commit()
        conn.close()
        print("✅ Base de datos SQLite creada con éxito.")
    else:
        print("✅ Base de datos SQLite ya existe")

# ============================================
# FUNCIONES DE LECTURA (SELECT)
# ============================================

def obtener_lista_usuarios():
    """
    Retorna lista de usuarios activos para selectboxes.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="usuarios")
    """
    try:
        conn = get_connection()
        query = "SELECT * FROM usuarios WHERE estatus = 'Alta' ORDER BY nombre"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records')  # Convertimos a lista de diccionarios
    except Exception as e:
        print(f"Error obteniendo usuarios: {e}")
        return []

def obtener_vehiculos():
    """
    Retorna lista de vehículos.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="vehiculos")
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM vehiculos ORDER BY ecco", conn)
        conn.close()
        return df.to_dict('records')
    except:
        return []

def obtener_hospitales():
    """
    Retorna lista de hospitales.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="hospitales")
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM hospitales ORDER BY nombre_hosp", conn)
        conn.close()
        return df.to_dict('records')
    except:
        return []

def obtener_pliegos():
    """
    Retorna TODOS los pliegos como DataFrame.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="pliegos")
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM pliegos ORDER BY fecha_elaboracion DESC", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error obteniendo pliegos: {e}")
        return pd.DataFrame()

def obtener_traslados_locales():
    """
    Retorna TODOS los traslados locales como DataFrame.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="traslados_locales")
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM traslados_locales ORDER BY fecha_creacion DESC", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error obteniendo traslados: {e}")
        return pd.DataFrame()

def obtener_configuracion_admin():
    """
    Retorna la configuración administrativa como diccionario.
    EQUIVALENTE a: pd.read_excel(DB_FILE, sheet_name="config_admin")
    """
    try:
        conn = get_connection()
        df = pd.read_sql_query("SELECT * FROM config_admin LIMIT 1", conn)
        conn.close()
        if not df.empty:
            return df.iloc[0].to_dict()
        return {}
    except:
        return {}

# ============================================
# FUNCIONES DE AUTENTICACIÓN
# ============================================

def validar_login(matricula, password):
    """
    Valida las credenciales del usuario.
    EQUIVALENTE a la función original pero con SQLite.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Buscar usuario por matrícula
        cursor.execute('''
            SELECT * FROM usuarios 
            WHERE matricula = ? AND estatus = 'Alta'
        ''', (str(matricula).strip(),))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Convertir a diccionario (los índices son por posición)
            columnas = ['matricula', 'nombre', 'apellido_p', 'apellido_m', 'curp', 'rfc',
                       'departamento', 'tipo_contrato', 'gj', 'categoria', 'password',
                       'rol', 'estatus', 'cuota_diaria', 'tel_oficina']
            
            user_dict = dict(zip(columnas, user))
            
            # Verificar contraseña
            if user_dict['password'] == str(password).strip():
                return {
                    "matricula": user_dict['matricula'],
                    "nombre": f"{user_dict['nombre']} {user_dict.get('apellido_p', '')} {user_dict.get('apellido_m', '')}".strip(),
                    "rol": user_dict['rol'],
                    "categoria": user_dict.get('categoria', 'PERSONAL'),
                    "departamento": user_dict.get('departamento', ''),
                    "gj": user_dict.get('gj', ''),
                    "tipo_contrato": user_dict.get('tipo_contrato', '')
                }
    except Exception as e:
        print(f"Error en login: {e}")
    
    return None

# ============================================
# FUNCIONES DE ESCRITURA (INSERT / UPDATE)
# ============================================

def guardar_o_actualizar_pliego(datos):
    """
    Guarda un pliego nuevo o actualiza uno existente.
    EQUIVALENTE a guardar_pliego_completo() pero más genérico.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si el folio ya existe
        cursor.execute("SELECT folio FROM pliegos WHERE folio = ?", (datos.get('folio'),))
        existe = cursor.fetchone()
        
        if existe:
            # ACTUALIZAR registro existente
            # Construir SET dinámicamente
            set_clause = ", ".join([f"{k} = ?" for k in datos.keys() if k != 'folio'])
            valores = [v for k, v in datos.items() if k != 'folio']
            valores.append(datos.get('folio'))  # Para el WHERE
            
            query = f"UPDATE pliegos SET {set_clause} WHERE folio = ?"
            cursor.execute(query, valores)
        else:
            # INSERTAR nuevo registro
            columnas = ", ".join(datos.keys())
            placeholders = ", ".join(["?"] * len(datos))
            query = f"INSERT INTO pliegos ({columnas}) VALUES ({placeholders})"
            cursor.execute(query, list(datos.values()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando pliego: {e}")
        return False

def guardar_traslado_local(datos):
    """
    Guarda un traslado local nuevo o actualiza uno existente.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar si el folio ya existe
        cursor.execute("SELECT folio FROM traslados_locales WHERE folio = ?", (datos.get('folio'),))
        existe = cursor.fetchone()
        
        if existe:
            # ACTUALIZAR
            set_clause = ", ".join([f"{k} = ?" for k in datos.keys() if k != 'folio'])
            valores = [v for k, v in datos.items() if k != 'folio']
            valores.append(datos.get('folio'))
            
            query = f"UPDATE traslados_locales SET {set_clause} WHERE folio = ?"
            cursor.execute(query, valores)
        else:
            # INSERTAR
            columnas = ", ".join(datos.keys())
            placeholders = ", ".join(["?"] * len(datos))
            query = f"INSERT INTO traslados_locales ({columnas}) VALUES ({placeholders})"
            cursor.execute(query, list(datos.values()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando traslado: {e}")
        return False

def actualizar_traslado_local(datos):
    """
    Alias de guardar_traslado_local para compatibilidad.
    """
    return guardar_traslado_local(datos)

def guardar_configuracion_admin(config):
    """
    Guarda la configuración administrativa.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eliminar configuración anterior
        cursor.execute("DELETE FROM config_admin")
        
        # Insertar nueva
        columnas = ", ".join(config.keys())
        placeholders = ", ".join(["?"] * len(config))
        query = f"INSERT INTO config_admin ({columnas}) VALUES ({placeholders})"
        cursor.execute(query, list(config.values()))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        return False

def guardar_gastos(gastos_dict, folio_pliego):
    """
    Guarda los gastos asociados a un pliego.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Eliminar gastos anteriores del mismo pliego
        cursor.execute("DELETE FROM gastos WHERE folio_pliego = ?", (folio_pliego,))
        
        # Insertar nuevos gastos
        for categoria, lista_gastos in gastos_dict.items():
            for gasto in lista_gastos:
                cursor.execute('''
                    INSERT INTO gastos (
                        folio_pliego, categoria, factura, proveedor, 
                        fecha, importe, concepto, justificacion, tipo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    folio_pliego,
                    categoria,
                    gasto.get('factura', ''),
                    gasto.get('proveedor', ''),
                    gasto.get('fecha', ''),
                    gasto.get('importe', 0),
                    gasto.get('concepto', ''),
                    gasto.get('justificacion', ''),
                    gasto.get('tipo', '')
                ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error guardando gastos: {e}")
        return False

def actualizar_km_vehiculo(ecco, km_nuevo):
    """
    Actualiza el kilometraje de un vehículo.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE vehiculos SET km_actual = ? WHERE ecco = ?", (km_nuevo, ecco))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def actualizar_base_datos_maestra(df_editado):
    """
    Función para compatibilidad con forms.py.
    En SQLite no se usa directamente, pero la mantenemos.
    """
    print("⚠️ actualizar_base_datos_maestra no implementada en SQLite")
    return True

# ============================================
# FUNCIONES DE SEGURIDAD (HASH Y CONTROL DE INTENTOS)
# ============================================
from modules.security import (
    verificar_password, hash_password, registrar_intento_fallido,
    esta_bloqueado, resetear_intentos, generar_contraseña_temporal
)

# Configuración de seguridad
MAX_INTENTOS = 3
TIEMPO_BLOQUEO_MINUTOS = 5

def validar_login_seguro(matricula, password):
    """
    Versión mejorada de validar_login con:
    - Hash de contraseñas
    - Control de intentos fallidos
    - Bloqueo temporal
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Buscar usuario por matrícula
        cursor.execute('''
            SELECT * FROM usuarios 
            WHERE matricula = ?
        ''', (str(matricula).strip(),))
        
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return {
                "exito": False,
                "error": "CREDENCIALES_INVALIDAS",
                "mensaje": "Matrícula o contraseña incorrectos",
                "intentos_restantes": None
            }
        
        # Obtener columnas
        columnas = [description[0] for description in cursor.description]
        user_dict = dict(zip(columnas, user))
        
        # Verificar si está bloqueado
        bloqueado, minutos = esta_bloqueado(user_dict)
        if bloqueado:
            conn.close()
            return {
                "exito": False,
                "error": "BLOQUEADO",
                "mensaje": f"Demasiados intentos. Espere {minutos} minutos.",
                "minutos_restantes": minutos
            }
        
        # Verificar contraseña con hash
        hash_guardado = user_dict.get('password', '')
        
        if verificar_password(password, hash_guardado):
            # ✅ LOGIN EXITOSO
            # Resetear intentos
            cursor.execute('''
                UPDATE usuarios 
                SET intentos_fallidos = 0, bloqueado_hasta = NULL 
                WHERE matricula = ?
            ''', (matricula,))
            conn.commit()
            conn.close()
            
            return {
                "exito": True,
                "matricula": user_dict['matricula'],
                "nombre": f"{user_dict['nombre']} {user_dict.get('apellido_p', '')} {user_dict.get('apellido_m', '')}".strip(),
                "rol": user_dict['rol'],
                "categoria": user_dict.get('categoria', 'PERSONAL'),
                "departamento": user_dict.get('departamento', ''),
                "gj": user_dict.get('gj', ''),
                "tipo_contrato": user_dict.get('tipo_contrato', '')
            }
        else:
            # ❌ LOGIN FALLIDO
            # Registrar intento fallido
            intentos_actuales = user_dict.get('intentos_fallidos', 0) + 1
            bloqueado = intentos_actuales >= MAX_INTENTOS
            
            if bloqueado:
                from datetime import datetime, timedelta
                bloqueado_hasta = (datetime.now() + timedelta(minutes=TIEMPO_BLOQUEO_MINUTOS)).strftime("%d/%m/%Y %H:%M")
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_fallidos = ?, bloqueado_hasta = ? 
                    WHERE matricula = ?
                ''', (intentos_actuales, bloqueado_hasta, matricula))
            else:
                cursor.execute('''
                    UPDATE usuarios 
                    SET intentos_fallidos = ? 
                    WHERE matricula = ?
                ''', (intentos_actuales, matricula))
            
            conn.commit()
            conn.close()
            
            intentos_restantes = max(0, MAX_INTENTOS - intentos_actuales)
            
            return {
                "exito": False,
                "error": "CREDENCIALES_INVALIDAS",
                "mensaje": f"Matrícula o contraseña incorrectos. Intentos restantes: {intentos_restantes}",
                "intentos_restantes": intentos_restantes
            }
            
    except Exception as e:
        print(f"Error en login seguro: {e}")
        return {
            "exito": False,
            "error": "SISTEMA",
            "mensaje": "Error interno del sistema"
        }

def cambiar_password(matricula, password_actual, nueva_password):
    """
    Cambia la contraseña de un usuario (cuando CONOCE la actual)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Obtener usuario
        cursor.execute("SELECT password FROM usuarios WHERE matricula = ?", (matricula,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return {"exito": False, "mensaje": "Usuario no encontrado"}
        
        hash_actual = result[0]
        
        # Verificar contraseña actual
        if not verificar_password(password_actual, hash_actual):
            conn.close()
            return {"exito": False, "mensaje": "Contraseña actual incorrecta"}
        
        # Generar nuevo hash y guardar
        nuevo_hash = hash_password(nueva_password)
        cursor.execute('''
            UPDATE usuarios 
            SET password = ?, intentos_fallidos = 0, bloqueado_hasta = NULL 
            WHERE matricula = ?
        ''', (nuevo_hash, matricula))
        
        conn.commit()
        conn.close()
        
        return {"exito": True, "mensaje": "Contraseña cambiada exitosamente"}
        
    except Exception as e:
        return {"exito": False, "mensaje": f"Error: {e}"}

def resetear_password_admin(matricula):
    """
    Genera una nueva contraseña temporal para un usuario (solo admin)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verificar que el usuario existe
        cursor.execute("SELECT matricula FROM usuarios WHERE matricula = ?", (matricula,))
        if not cursor.fetchone():
            conn.close()
            return {"exito": False, "mensaje": "Usuario no encontrado"}
        
        # Generar contraseña temporal
        temp_password = generar_contraseña_temporal()
        nuevo_hash = hash_password(temp_password)
        
        # Actualizar en base de datos
        cursor.execute('''
            UPDATE usuarios 
            SET password = ?, intentos_fallidos = 0, bloqueado_hasta = NULL 
            WHERE matricula = ?
        ''', (nuevo_hash, matricula))
        
        conn.commit()
        conn.close()
        
        return {
            "exito": True,
            "password_temporal": temp_password,
            "mensaje": "Contraseña restablecida"
        }
        
    except Exception as e:
        return {"exito": False, "mensaje": f"Error: {e}"}

# ============================================
# NOTA IMPORTANTE:
# ============================================
# Este archivo mantiene los mismos nombres de funciones
# que el original. NO necesitas modificar forms.py
#
# La magia está en que forms.py llama a estas funciones
# y ahora trabajan con SQLite en lugar de Excel.
# ============================================