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
# FUNCIONES DE GUARDADO/ACTUALIZACIÓN (VERSIÓN ÚNICA)
# ============================================

def guardar_o_actualizar_pliego(datos):
    """
    Guarda o actualiza un pliego en el Excel
    🔴 AHORA ACTUALIZA si el folio existe
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
        
        # Verificar si el folio ya existe
        folio = datos.get('folio', '')
        if folio in df_p['folio'].values:
            # ACTUALIZAR registro existente
            idx = df_p[df_p['folio'] == folio].index[0]
            
            # 🔴 Asegurar que todas las columnas existan antes de actualizar
            for key in datos.keys():
                if key not in df_p.columns:
                    df_p[key] = ""  # Agregar columna vacía si no existe
            
            for key, value in datos.items():
                if key in df_p.columns:
                    df_p.at[idx, key] = value
            print(f"✅ Pliego {folio} actualizado")
        else:
            # Agregar nuevo registro
            df_p = pd.concat([df_p, pd.DataFrame([datos])], ignore_index=True)
            print(f"✅ Pliego {folio} guardado")
        
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
    Guarda o actualiza un traslado local
    🔴 AHORA incluye todos los campos nuevos
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
        
        # Verificar si el folio ya existe
        folio = datos.get('folio', '')
        if folio in df_t['folio'].values:
            # ACTUALIZAR registro existente
            idx = df_t[df_t['folio'] == folio].index[0]
            
            # 🔴 Asegurar que todas las columnas existan antes de actualizar
            for key in datos.keys():
                if key not in df_t.columns:
                    df_t[key] = ""  # Agregar columna vacía si no existe
            
            for key, value in datos.items():
                if key in df_t.columns:
                    df_t.at[idx, key] = value
            print(f"✅ Traslado {folio} actualizado")
        else:
            # Agregar nuevo registro con todos los campos
            df_t = pd.concat([df_t, pd.DataFrame([datos])], ignore_index=True)
            print(f"✅ Traslado {folio} guardado")
        
        # Guardar todo
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_t.to_excel(writer, sheet_name='traslados_locales', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        return True
    except Exception as e:
        print(f"Error al guardar traslado: {e}")
        return False

def actualizar_traslado_local(datos):
    """
    🔴 Alias para guardar_traslado_local (para tomar/cerrar)
    """
    return guardar_traslado_local(datos)

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

def actualizar_base_datos_maestra(df_editado, tipo_doc=None):
    """
    🔴 Actualiza la base de datos con los cambios del editor
    NO crea duplicados - actualiza los registros existentes
    """
    try:
        if not os.path.exists(DB_FILE):
            asegurar_hojas_excel()
            return False
        
        if df_editado.empty:
            return True
        
        xls = pd.ExcelFile(DB_FILE)
        
        # Determinar qué hoja actualizar
        if 'tipo_doc' in df_editado.columns:
            if df_editado['tipo_doc'].iloc[0] == "Pliego/Informe":
                hoja = 'pliegos'
            else:
                hoja = 'traslados_locales'
        else:
            # Intentar determinar por columnas
            if 'paciente' in df_editado.columns:
                hoja = 'traslados_locales'
            else:
                hoja = 'pliegos'
        
        # Leer la hoja correspondiente
        if hoja in xls.sheet_names:
            df_original = pd.read_excel(xls, sheet_name=hoja)
        else:
            df_original = pd.DataFrame()
        
        # Guardar otras hojas
        otras_hojas = {}
        for sheet in xls.sheet_names:
            if sheet != hoja:
                otras_hojas[sheet] = pd.read_excel(xls, sheet)
        
        # Actualizar registros existentes
        for idx, row in df_editado.iterrows():
            folio = row.get('folio', '')
            if folio and folio in df_original['folio'].values:
                # Encontrar el índice en el original
                orig_idx = df_original[df_original['folio'] == folio].index[0]
                # Actualizar campos
                for col in row.index:
                    if col in df_original.columns and col != 'folio':
                        df_original.at[orig_idx, col] = row[col]
        
        # Guardar todo
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_original.to_excel(writer, sheet_name=hoja, index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        print(f"✅ Base de datos actualizada en hoja {hoja}")
        return True
    except Exception as e:
        print(f"Error al actualizar: {e}")
        return False

# ============================================
# FUNCIONES DE CONFIGURACIÓN ADMIN
# ============================================

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
        
        # Valores por defecto si no existe
        return {
            'titular_unidad': '',
            'unidad_administrativa': '',
            'adscripcion': '',
            'cargo_titular': '',
            'folio_inicial_sistema': 'F001/2026',
            'folio_inicial_local': 'L001/2026'
        }
    except Exception as e:
        print(f"Error al obtener configuración: {e}")
        return {
            'titular_unidad': '',
            'unidad_administrativa': '',
            'adscripcion': '',
            'cargo_titular': '',
            'folio_inicial_sistema': 'F001/2026',
            'folio_inicial_local': 'L001/2026'
        }

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
        
        # Guardar
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_conf.to_excel(writer, sheet_name='config_admin', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        print(f"✅ Configuración guardada exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error al guardar configuración: {e}")
        return False        


# ============================================
# FUNCIÓN: GUARDAR GASTOS (DESGLOSE)
# ============================================

def guardar_gastos(datos_gastos, folio_pliego):
    """
    Guarda los gastos del desglose en la hoja 'gastos' de Excel.
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
        
        if nuevos_registros:
            df_nuevos = pd.DataFrame(nuevos_registros)
            df_gastos = pd.concat([df_gastos, df_nuevos], ignore_index=True)
        
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_gastos.to_excel(writer, sheet_name='gastos', index=False)
            for nombre, df in otras_hojas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        
        print(f"✅ Gastos guardados correctamente para folio {folio_pliego}")
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar gastos: {e}")
        return False