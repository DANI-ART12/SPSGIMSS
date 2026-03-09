# ============================================
# modules/security.py - Manejo de contraseñas con hash
# ============================================
import bcrypt
import random
import string
from datetime import datetime, timedelta

# Configuración
MAX_INTENTOS = 3
TIEMPO_BLOQUEO_MINUTOS = 5  # 5 minutos de bloqueo
TIEMPO_CODIGO_MINUTOS = 10   # Código válido por 10 minutos

def hash_password(contraseña_plana):
    """
    Convierte una contraseña en texto plano a hash seguro.
    
    Ejemplo: "admin123" → "$2b$12$K8mH1Q9XqK1sZ1q1q1q1q1q1..."
    
    Args:
        contraseña_plana (str): La contraseña sin cifrar
    
    Returns:
        str: Hash de la contraseña
    """
    # Convertir a bytes y generar hash con salt automático
    contraseña_bytes = contraseña_plana.encode('utf-8')
    salt = bcrypt.gensalt()  # Genera un salt único
    hash_bytes = bcrypt.hashpw(contraseña_bytes, salt)
    return hash_bytes.decode('utf-8')

def verificar_password(contraseña_ingresada, hash_almacenado):
    """
    Verifica si la contraseña ingresada coincide con el hash guardado.
    
    Args:
        contraseña_ingresada (str): La contraseña que el usuario tecleó
        hash_almacenado (str): El hash guardado en la base de datos
    
    Returns:
        bool: True si coincide, False si no
    """
    try:
        contraseña_bytes = contraseña_ingresada.encode('utf-8')
        hash_bytes = hash_almacenado.encode('utf-8')
        return bcrypt.checkpw(contraseña_bytes, hash_bytes)
    except Exception as e:
        print(f"Error verificando password: {e}")
        return False

def generar_contraseña_temporal(longitud=8):
    """
    Genera una contraseña aleatoria segura.
    
    Args:
        longitud (int): Longitud de la contraseña
    
    Returns:
        str: Contraseña aleatoria
    """
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choices(caracteres, k=longitud))

def generar_codigo_recuperacion(longitud=6):
    """
    Genera un código numérico para recuperación.
    
    Args:
        longitud (int): Número de dígitos
    
    Returns:
        str: Código de dígitos
    """
    return ''.join(random.choices(string.digits, k=longitud))

def registrar_intento_fallido(usuario_df, idx):
    """
    Registra un intento fallido y determina si debe bloquear.
    
    Args:
        usuario_df: DataFrame de usuarios
        idx: Índice del usuario
    
    Returns:
        tuple: (bloqueado, minutos_restantes, intentos_restantes)
    """
    # Obtener intentos actuales
    intentos = int(usuario_df.at[idx, 'intentos_fallidos']) if 'intentos_fallidos' in usuario_df.columns else 0
    intentos += 1
    usuario_df.at[idx, 'intentos_fallidos'] = intentos
    
    # Registrar fecha del último intento
    usuario_df.at[idx, 'ultimo_intento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    # Verificar si alcanzó el máximo
    if intentos >= MAX_INTENTOS:
        # Bloquear por X minutos
        bloqueado_hasta = datetime.now() + timedelta(minutes=TIEMPO_BLOQUEO_MINUTOS)
        usuario_df.at[idx, 'bloqueado_hasta'] = bloqueado_hasta.strftime("%d/%m/%Y %H:%M")
        return True, TIEMPO_BLOQUEO_MINUTOS, 0
    
    return False, 0, MAX_INTENTOS - intentos

def esta_bloqueado(usuario):
    """
    Verifica si un usuario está bloqueado.
    
    Args:
        usuario (dict): Datos del usuario
    
    Returns:
        tuple: (bloqueado, minutos_restantes)
    """
    if 'bloqueado_hasta' not in usuario or not usuario['bloqueado_hasta']:
        return False, 0
    
    try:
        bloqueado_hasta = datetime.strptime(usuario['bloqueado_hasta'], "%d/%m/%Y %H:%M")
        ahora = datetime.now()
        
        if ahora < bloqueado_hasta:
            minutos = int((bloqueado_hasta - ahora).total_seconds() / 60)
            return True, minutos
        else:
            return False, 0
    except:
        return False, 0

def resetear_intentos(usuario_df, idx):
    """
    Resetea los intentos fallidos después de login exitoso.
    """
    usuario_df.at[idx, 'intentos_fallidos'] = 0
    usuario_df.at[idx, 'bloqueado_hasta'] = None

def crear_codigo_recuperacion(usuario_df, idx):
    """
    Genera código de recuperación y su expiración.
    
    Returns:
        str: Código generado
    """
    codigo = generar_codigo_recuperacion()
    expiracion = datetime.now() + timedelta(minutes=TIEMPO_CODIGO_MINUTOS)
    
    usuario_df.at[idx, 'codigo_recuperacion'] = codigo
    usuario_df.at[idx, 'codigo_expiracion'] = expiracion.strftime("%d/%m/%Y %H:%M")
    
    return codigo

def verificar_codigo_recuperacion(usuario_df, idx, codigo_ingresado):
    """
    Verifica si el código es válido y no ha expirado.
    """
    if 'codigo_recuperacion' not in usuario_df.columns:
        return False
    
    codigo_guardado = str(usuario_df.at[idx, 'codigo_recuperacion']) if usuario_df.at[idx, 'codigo_recuperacion'] else ""
    expiracion_str = usuario_df.at[idx, 'codigo_expiracion'] if usuario_df.at[idx, 'codigo_expiracion'] else ""
    
    if not codigo_guardado or not expiracion_str:
        return False
    
    # Verificar código
    if codigo_guardado != codigo_ingresado:
        return False
    
    # Verificar expiración
    try:
        expiracion = datetime.strptime(expiracion_str, "%d/%m/%Y %H:%M")
        if datetime.now() > expiracion:
            return False
    except:
        return False
    
    return True

def limpiar_codigo_recuperacion(usuario_df, idx):
    """
    Elimina el código de recuperación después de usarlo.
    """
    usuario_df.at[idx, 'codigo_recuperacion'] = None
    usuario_df.at[idx, 'codigo_expiracion'] = None