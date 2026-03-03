# ============================================
# modules/db_handler.py - MANEJO DE BASE DE DATOS EXCEL
# ============================================

import pandas as pd
import os
from datetime import datetime

# ============================================
# IMPORTACIONES CORRECTAS DESDE UTILS
# ============================================
from modules.utils import (
    get_base64,
    asegurar_hojas_excel,
    generar_folio_local,
    generar_folio_foraneo
)
from modules.database import obtener_lista_usuarios as db_obtener_usuarios

# ============================================
# CONSTANTES GLOBALES
# ============================================
DB_FILE = "base_datos.xlsx"

# ============================================
# FUNCIONES DE CONSULTA
# ============================================

def obtener_lista_usuarios():
    """Wrapper para obtener usuarios desde database.py"""
    return db_obtener_usuarios()

def obtener_vehiculos():
    """
    Obtiene la lista completa de vehículos
    Returns: Lista de diccionarios con datos de vehículos
    """
    try:
        if os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name='vehiculos')
            return df.to_dict('records') if not df.empty else []
        return []
    except Exception as e:
        print(f"Error al obtener vehículos: {e}")
        return []

def obtener_hospitales():
    """
    Obtiene la lista completa de hospitales
    Returns: Lista de diccionarios con datos de hospitales
    """
    try:
        if os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name='hospitales')
            return df.to_dict('records') if not df.empty else []
        return []
    except Exception as e:
        print(f"Error al obtener hospitales: {e}")
        return []

def obtener_pliegos():
    """
    Obtiene todos los pliegos de comisión
    Returns: DataFrame con los pliegos
    """
    try:
        if os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name='pliegos')
            return df if not df.empty else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        print(f"Error al obtener pliegos: {e}")
        return pd.DataFrame()

def obtener_traslados_locales():
    """
    Obtiene todos los traslados locales
    Returns: DataFrame con los traslados
    """
    try:
        if os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name='traslados_locales')
            return df if not df.empty else pd.DataFrame()
        return pd.DataFrame()
    except Exception as e:
        print(f"Error al obtener traslados: {e}")
        return pd.DataFrame()

# ============================================
# FUNCIONES DE GUARDADO/ACTUALIZACIÓN
# ============================================

def guardar_o_actualizar_pliego(datos):
    """
    Guarda o actualiza un pliego en el Excel
    """
    try:
        if not os.path.exists(DB_FILE):
            asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        
        if 'pliegos' in xls.sheet_names:
            df_p = pd.read_excel(xls, sheet_name='pliegos')
        else:
            df_p = pd.DataFrame()
        
        # Guardar otras hojas
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != 'pliegos':
                otras_hojas[sheet] = pd.read_excel(xls, sheet)
        
        # Agregar nuevo pliego
        df_p = pd.concat([df_p, pd.DataFrame([datos])], ignore_index=True)
        
        # Guardar todo
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_p.to_excel(writer, sheet_name='pliegos', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        return True
    except Exception as e:
        print(f"Error al guardar pliego: {e}")
        return False

def guardar_traslado_local(datos):
    """
    Guarda un nuevo traslado local
    """
    try:
        if not os.path.exists(DB_FILE):
            asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        
        if 'traslados_locales' in xls.sheet_names:
            df_t = pd.read_excel(xls, sheet_name='traslados_locales')
        else:
            df_t = pd.DataFrame()
        
        # Guardar otras hojas
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != 'traslados_locales':
                otras_hojas[sheet] = pd.read_excel(xls, sheet)
        
        # Agregar nuevo traslado
        df_t = pd.concat([df_t, pd.DataFrame([datos])], ignore_index=True)
        
        # Guardar todo
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_t.to_excel(writer, sheet_name='traslados_locales', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        return True
    except Exception as e:
        print(f"Error al guardar traslado: {e}")
        return False

def actualizar_km_vehiculo(ecco_unidad, km_final_reportado):
    """
    Busca el vehículo por ECCO y actualiza su km_actual.
    """
    try:
        if not os.path.exists(DB_FILE):
            return False
            
        xls = pd.ExcelFile(DB_FILE)
        
        if 'vehiculos' not in xls.sheet_names:
            return False
            
        df_vehiculos = pd.read_excel(xls, sheet_name='vehiculos')
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != 'vehiculos':
                otras_hojas[sheet] = pd.read_excel(xls, sheet)

        if ecco_unidad in df_vehiculos['ecco'].values:
            idx = df_vehiculos.index[df_vehiculos['ecco'] == ecco_unidad].tolist()[0]
            df_vehiculos.at[idx, 'km_actual'] = km_final_reportado
            
            with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                df_vehiculos.to_excel(writer, sheet_name='vehiculos', index=False)
                for nombre_hoja, contenido_hoja in otras_hojas.items():
                    contenido_hoja.to_excel(writer, sheet_name=nombre_hoja, index=False)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error al actualizar kilometraje: {e}")
        return False

def actualizar_base_datos_maestra(df_editado):
    """
    Actualiza la base de datos con los cambios del editor
    """
    try:
        # TODO: Implementar según necesidad
        print("Función de actualización en desarrollo")
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False

# ============================================
# FUNCIONES DE CONFIGURACIÓN
# ============================================

def guardar_configuracion_admin(config):
    """
    Guarda configuración administrativa
    """
    try:
        if not os.path.exists(DB_FILE):
            asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != 'config_admin':
                otras_hojas[sheet] = pd.read_excel(xls, sheet)
        
        # Crear DataFrame con nueva configuración
        df_conf = pd.DataFrame([config])
        
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_conf.to_excel(writer, sheet_name='config_admin', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        return True
    except Exception as e:
        print(f"Error al guardar configuración: {e}")
        return False

def obtener_configuracion_admin():
    """
    Obtiene la configuración administrativa
    """
    try:
        if os.path.exists(DB_FILE):
            xls = pd.ExcelFile(DB_FILE)
            if 'config_admin' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='config_admin')
                if not df.empty:
                    return df.iloc[0].to_dict()
        return {}
    except Exception as e:
        print(f"Error al obtener configuración: {e}")
        return {}

# ============================================
# NUEVA FUNCIÓN: GUARDAR GASTOS (DESGLOSE)
# ============================================

def guardar_gastos(datos_gastos, folio_pliego):
    """
    Guarda los gastos del desglose en la hoja 'gastos' de Excel.
    
    Args:
        datos_gastos (dict): Diccionario con los gastos por categoría
        folio_pliego (str): Folio del pliego al que pertenecen los gastos
    
    Returns:
        bool: True si se guardó correctamente, False en caso de error
    """
    try:
        if not os.path.exists(DB_FILE):
            asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        
        # Cargar hoja de gastos existente o crear nueva
        if 'gastos' in xls.sheet_names:
            df_gastos = pd.read_excel(xls, sheet_name='gastos')
        else:
            df_gastos = pd.DataFrame()
        
        # Guardar otras hojas (excepto gastos)
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != 'gastos':
                otras_hojas[sheet] = pd.read_excel(xls, sheet)
        
        # Construir lista de nuevos registros
        nuevos_registros = []
        
        for categoria, gastos in datos_gastos.items():
            for gasto in gastos:
                # Determinar tipo de gasto
                tipo = "con_comprobante" if categoria != "SIN COMPROBANTE" else "sin_comprobante"
                
                nuevo_registro = {
                    "folio_pliego": folio_pliego,
                    "categoria": categoria,
                    "factura": gasto.get('factura', ''),
                    "proveedor": gasto.get('proveedor', ''),
                    "fecha": gasto.get('fecha', ''),
                    "importe": gasto.get('importe', 0.0),
                    "concepto": gasto.get('concepto', ''),
                    "justificacion": gasto.get('justificacion', ''),
                    "tipo": tipo
                }
                nuevos_registros.append(nuevo_registro)
        
        # Si hay registros nuevos, agregarlos al DataFrame
        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)
            df_gastos = pd.concat([df_gastos, df_nuevos], ignore_index=True)
        
        # Guardar todo en Excel
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_gastos.to_excel(writer, sheet_name='gastos', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        print(f"✅ Gastos guardados correctamente para folio {folio_pliego}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar gastos: {e}")
        return False