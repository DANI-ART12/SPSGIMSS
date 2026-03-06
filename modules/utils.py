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
            'config_admin',
            'gastos'
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

def generar_folio_foraneo(df_actual=None, folio_inicial=None):
    """
    Genera un nuevo folio para traslados foráneos
    Si no se proporciona folio_inicial, lo obtiene de la configuración
    """
    try:
        # Si no se proporciona folio_inicial, obtenerlo de la configuración
        if folio_inicial is None:
            from modules.db_handler import obtener_configuracion_admin
            config = obtener_configuracion_admin()
            folio_inicial = config.get('folio_inicial_sistema', 'F001/2026')
        
        if df_actual is None:
            from modules.db_handler import obtener_pliegos
            df_actual = obtener_pliegos()
        
        # Extraer prefijo y año del folio_inicial
        prefijo = folio_inicial[0]
        partes = folio_inicial.split('/')
        try:
            numero_inicial = int(partes[0].replace(prefijo, ''))
            anio = partes[1]
        except:
            numero_inicial = 1
            anio = str(datetime.now().year)
        
        if df_actual is None or df_actual.empty:
            return folio_inicial
        
        if 'folio' in df_actual.columns:
            folios_mismo_anio = []
            for folio in df_actual['folio'].astype(str):
                if f"/{anio}" in folio and str(folio).startswith(prefijo):
                    try:
                        num = int(folio.split('/')[0].replace(prefijo, ''))
                        folios_mismo_anio.append(num)
                    except:
                        pass
            
            if folios_mismo_anio:
                ultimo_num = max(folios_mismo_anio)
                # Si el último número es menor que el inicial, usar el inicial
                if ultimo_num < numero_inicial:
                    return f"{prefijo}{str(numero_inicial).zfill(3)}/{anio}"
                else:
                    return f"{prefijo}{ultimo_num + 1:03d}/{anio}"
        
        return folio_inicial
    except Exception as e:
        print(f"Error al generar folio foráneo: {e}")
        return folio_inicial or f"F001/{datetime.now().year}"

def generar_folio_local(df_actual=None):
    """
    Genera un nuevo folio para traslados locales
    Obtiene el folio inicial de la configuración
    """
    try:
        # Obtener folio inicial de la configuración
        from modules.db_handler import obtener_configuracion_admin
        config = obtener_configuracion_admin()
        folio_inicial = config.get('folio_inicial_local', 'L001/2026')
        
        if df_actual is None:
            from modules.db_handler import obtener_traslados_locales
            df_actual = obtener_traslados_locales()
        
        # Extraer prefijo y año
        prefijo = folio_inicial[0]
        partes = folio_inicial.split('/')
        try:
            numero_inicial = int(partes[0].replace(prefijo, ''))
            anio = partes[1]
        except:
            numero_inicial = 1
            anio = str(datetime.now().year)
        
        if df_actual is None or df_actual.empty:
            return folio_inicial
        
        if 'folio' in df_actual.columns:
            folios_mismo_anio = []
            for folio in df_actual['folio'].astype(str):
                if f"/{anio}" in folio and str(folio).startswith(prefijo):
                    try:
                        num = int(folio.split('/')[0].replace(prefijo, ''))
                        folios_mismo_anio.append(num)
                    except:
                        pass
            
            if folios_mismo_anio:
                ultimo_num = max(folios_mismo_anio)
                if ultimo_num < numero_inicial:
                    return f"{prefijo}{str(numero_inicial).zfill(3)}/{anio}"
                else:
                    return f"{prefijo}{ultimo_num + 1:03d}/{anio}"
        
        return folio_inicial
    except Exception as e:
        print(f"Error al generar folio local: {e}")
        return f"L001/{datetime.now().year}"

# ============================================
# FUNCIÓN PARA CALCULAR TOTAL KM
# ============================================
def calcular_total_km(datos):
    """Calcula el total de kilómetros recorridos"""
    try:
        if datos.get('km_inicial') and datos.get('km_final'):
            km_i = int(datos['km_inicial'])
            km_f = int(datos['km_final'])
            return f"{km_f - km_i} km"
    except (ValueError, TypeError):
        return "Error en datos"
    return "No disponible"

# ============================================
# FUNCIÓN PARA IMPRIMIR HOJA DE TRASLADO LOCAL (CON OPCIONES)
# ============================================
def generar_html_traslado_imprimible(datos, opciones):
    """
    Genera HTML para impresión de hoja de traslado local
    Args:
        datos: Diccionario con los datos del traslado
        opciones: Diccionario con las opciones de impresión
    """
    logo_b64 = obtener_logo_base64()
    
    # Construir secciones según opciones
    cama_html = ""
    if opciones.get('cama', True) and datos.get('cama'):
        cama_html = f"""
            <div class="campo">
                <span class="label">Cama:</span> {datos.get('cama', 'N/A')}
            </div>
        """
    
    domicilio_html = ""
    if opciones.get('domicilio', True) and datos.get('domicilio'):
        domicilio_html = f"""
            <div class="campo">
                <span class="label">Domicilio:</span> {datos.get('domicilio', 'N/A')}
            </div>
        """
    
    telefono_html = ""
    if opciones.get('telefono', True) and datos.get('telefono'):
        telefono_html = f"""
            <div class="campo">
                <span class="label">Teléfono:</span> {datos.get('telefono', 'N/A')}
            </div>
        """
    
    vehiculo_html = ""
    km_html = ""
    if opciones.get('vehiculo', True):
        if datos.get('vehiculo'):
            vehiculo_html = f"""
                <div class="campo">
                    <span class="label">Vehículo:</span> {datos.get('vehiculo', 'N/A')}
                </div>
            """
        if opciones.get('km', True):
            km_inicial = datos.get('km_inicial', 'N/A')
            km_final = datos.get('km_final', 'N/A')
            if km_inicial != 'N/A' and km_final != 'N/A':
                try:
                    total = int(km_final) - int(km_inicial)
                    km_html = f"""
                        <div class="campo">
                            <span class="label">KM Inicial:</span> {km_inicial} |
                            <span class="label">KM Final:</span> {km_final} |
                            <span class="label">Total:</span> {total} km
                        </div>
                    """
                except:
                    km_html = f"""
                        <div class="campo">
                            <span class="label">KM Inicial:</span> {km_inicial} |
                            <span class="label">KM Final:</span> {km_final}
                        </div>
                    """
            else:
                km_html = f"""
                    <div class="campo">
                        <span class="label">KM Inicial:</span> {km_inicial} |
                        <span class="label">KM Final:</span> {km_final}
                    </div>
                """
    
    chofer_html = ""
    if opciones.get('chofer', True) and datos.get('empleado_comisionado'):
        chofer_html = f"""
            <div class="campo">
                <span class="label">Chofer/Responsable:</span> {datos.get('empleado_comisionado', 'N/A')}
            </div>
        """
    
    observaciones_html = ""
    if opciones.get('observaciones', True) and datos.get('observaciones'):
        observaciones_html = f"""
            <div class="campo">
                <span class="label">Observaciones:</span> {datos.get('observaciones', 'Sin observaciones')}
            </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Hoja de Ruta - Traslado Local</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 2cm;
                color: #000000;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                max-width: 150px;
                margin-bottom: 10px;
            }}
            h1 {{
                color: #004a44;
                font-size: 24px;
                margin: 10px 0;
            }}
            h2 {{
                color: #004a44;
                font-size: 18px;
                border-bottom: 2px solid #004a44;
                padding-bottom: 5px;
                margin-top: 20px;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin: 15px 0;
            }}
            .campo {{
                margin: 8px 0;
            }}
            .label {{
                font-weight: bold;
                color: #004a44;
            }}
            .firma {{
                margin-top: 50px;
                text-align: center;
            }}
            .firma-linea {{
                border-top: 1px solid #000;
                width: 300px;
                margin: 0 auto;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="data:image/png;base64,{logo_b64}" class="logo" alt="IMSS Logo">
            <h1>INSTITUTO MEXICANO DEL SEGURO SOCIAL</h1>
            <h2>HOJA DE RUTA - TRASLADO LOCAL</h2>
        </div>
        
        <div class="info-grid">
            <div class="campo">
                <span class="label">Folio:</span> {datos.get('folio', 'N/A')}
            </div>
            <div class="campo">
                <span class="label">Fecha:</span> {datos.get('fecha_traslado', datos.get('fecha_creacion', 'N/A'))}
            </div>
            <div class="campo">
                <span class="label">Turno:</span> {datos.get('turno', 'N/A')}
            </div>
            <div class="campo">
                <span class="label">Estatus:</span> {datos.get('estatus', 'N/A')}
            </div>
        </div>

        <h2>DATOS DEL PACIENTE</h2>
        <div class="info-grid">
            <div class="campo">
                <span class="label">Paciente:</span> {datos.get('paciente', 'N/A')}
            </div>
            <div class="campo">
                <span class="label">NSS:</span> {datos.get('nss', 'N/A')}
            </div>
            {cama_html}
            {domicilio_html}
            {telefono_html}
            <div class="campo">
                <span class="label">Destino:</span> {datos.get('destino', 'N/A')}
            </div>
            <div class="campo">
                <span class="label">Servicio:</span> {datos.get('servicio', 'N/A')}
            </div>
        </div>

        <h2>DATOS DE ASIGNACIÓN</h2>
        <div class="info-grid">
            {chofer_html}
            <div class="campo">
                <span class="label">Matrícula:</span> {datos.get('matricula_asignado', 'N/A')}
            </div>
            <div class="campo">
                <span class="label">Fecha Asignación:</span> {datos.get('fecha_asignacion', 'N/A')}
            </div>
        </div>

        <h2>DATOS DEL VEHÍCULO</h2>
        <div class="info-grid">
            {vehiculo_html}
            {km_html}
        </div>

        <h2>OBSERVACIONES</h2>
        <div class="campo">
            {observaciones_html}
        </div>

        <div class="firma">
            <div class="firma-linea">
                Firma del responsable
            </div>
        </div>
    </body>
    </html>
    """
    return html