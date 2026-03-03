# ============================================
# modules/utils.py - FUNCIONES DE UTILIDAD
# ============================================

import os
import base64
import json
from jinja2 import Template
from datetime import datetime
import pandas as pd

# ============================================
# CONSTANTES
# ============================================
DB_FILE = "base_datos.xlsx"

# ============================================
# FUNCIONES DE IMAGENES Y TEMPLATES
# ============================================

def obtener_logo_base64(ruta=None):
    """
    Obtiene el logo en base64 para informes
    Args:
        ruta: Ruta al archivo de logo (opcional, por defecto "assets/logoimss.png")
    """
    if ruta is None:
        ruta = "assets/logoimss.png"
    
    if os.path.exists(ruta):
        with open(ruta, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    return ""

# Alias para compatibilidad
get_base64 = obtener_logo_base64

def generar_html_impresion(datos):
    """Genera HTML para impresión de pliegos"""
    logo_b64 = obtener_logo_base64()
    datos["logo_b64"] = logo_b64

    with open("templates/pliego_template.html", encoding="utf-8") as f:
        template = Template(f.read())

    return template.render(**datos)

# ============================================
# FUNCIONES DE CONFIGURACIÓN PERSISTENTE (JSON)
# ============================================

def gestionar_config_permanente(clave, datos=None):
    """Guarda o lee configuraciones en un JSON para que no se borren con apagones."""
    archivo = "config_sistema.json"
    config = {}
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            config = json.load(f)
    
    if datos is not None:  # Escribir
        config[clave] = datos
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return datos
    else:  # Leer
        return config.get(clave, {})

# ============================================
# FUNCIONES DE EXCEL (HOJAS)
# ============================================

def asegurar_hojas_excel(archivo=DB_FILE):
    """Asegura que existan todas las hojas necesarias en el Excel"""
    try:
        hojas_necesarias = [
            'pliegos', 
            'traslados_locales', 
            'usuarios', 
            'vehiculos', 
            'hospitales', 
            'mantenimientos', 
            'informes', 
            'config_admin'
        ]
        
        if not os.path.exists(archivo):
            with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
                for hoja in hojas_necesarias:
                    pd.DataFrame().to_excel(writer, sheet_name=hoja, index=False)
            print(f"✅ Archivo Excel creado con todas las hojas")
            return True
        
        xl = pd.ExcelFile(archivo)
        hojas_existentes = xl.sheet_names
        hojas_faltantes = [h for h in hojas_necesarias if h not in hojas_existentes]
        
        if hojas_faltantes:
            with pd.ExcelWriter(archivo, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                for hoja in hojas_faltantes:
                    pd.DataFrame().to_excel(writer, sheet_name=hoja, index=False)
            
            print(f"📝 Hojas agregadas: {hojas_faltantes}")
        
        return True
    except Exception as e:
        print(f"Error al asegurar hojas: {e}")
        return False

# ============================================
# FUNCIONES DE GENERACIÓN DE FOLIOS
# ============================================

def generar_folio_local(df_actual=None):
    """
    Genera un nuevo folio para traslados locales
    Formato: L001/2026
    """
    try:
        if df_actual is None:
            from modules.db_handler import obtener_traslados_locales
            df_actual = obtener_traslados_locales()
            
        if df_actual is None or df_actual.empty:
            anio_actual = datetime.now().year
            return f"L001/{anio_actual}"
        
        anio_actual = datetime.now().year
        if 'folio' in df_actual.columns:
            folios_anio = []
            for folio in df_actual['folio'].astype(str):
                if f"/{anio_actual}" in folio and str(folio).startswith('L'):
                    try:
                        num = int(folio.split('/')[0].replace('L', ''))
                        folios_anio.append(num)
                    except:
                        pass
            
            if folios_anio:
                ultimo_num = max(folios_anio)
                return f"L{ultimo_num + 1:03d}/{anio_actual}"
        
        return f"L001/{anio_actual}"
    except Exception as e:
        print(f"Error al generar folio: {e}")
        anio_actual = datetime.now().year
        return f"L001/{anio_actual}"

def generar_folio_foraneo(df_actual=None, folio_inicial="F001/2026"):
    """
    Genera un nuevo folio para traslados foráneos
    Formato: F001/2026
    """
    try:
        if df_actual is None:
            from modules.db_handler import obtener_pliegos
            df_actual = obtener_pliegos()
            
        if df_actual is None or df_actual.empty:
            return folio_inicial
        
        anio_actual = datetime.now().year
        if 'folio' in df_actual.columns:
            folios_anio = []
            for folio in df_actual['folio'].astype(str):
                if f"/{anio_actual}" in folio and str(folio).startswith('F'):
                    try:
                        num = int(folio.split('/')[0].replace('F', ''))
                        folios_anio.append(num)
                    except:
                        pass
            
            if folios_anio:
                ultimo_num = max(folios_anio)
                return f"F{ultimo_num + 1:03d}/{anio_actual}"
        
        return folio_inicial
    except Exception as e:
        print(f"Error al generar folio foráneo: {e}")
        return folio_inicial