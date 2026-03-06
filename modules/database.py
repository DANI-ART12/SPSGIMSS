# ============================================
# modules/database.py - INICIALIZACIÓN Y AUTENTICACIÓN
# ============================================

import pandas as pd
import os
from datetime import datetime

DB_FILE = "base_datos.xlsx"

def inicializar_base_datos():
    """Crea la base de datos con todas las pestañas necesarias si no existe."""
    print("🔧 Ejecutando inicializar_base_datos...")
    
    if not os.path.exists(DB_FILE):
        print("📁 Creando nueva base de datos...")
        
        tablas = {
            "usuarios": pd.DataFrame(columns=[
                "matricula","nombre","apellido_p","apellido_m","curp",
                "rfc","departamento","tipo_contrato","gj",
                "categoria","password","rol","estatus","cuota_diaria", "tel_oficina"
            ]),
            
            "pliegos": pd.DataFrame(columns=[
                "folio", "fecha_elaboracion", "matricula", "estatus_pliego",
                "f_solicitante", "f_cp", "f_categoria", "f_area", "f_tel",
                "m_objeto",
                "p_a", "p_b", "p_c", "m_destino",
                "fecha_inicio", "fecha_fin",
                "medio_transporte", "chofer", "acompañante", "ecco",
                "anticipo_viaticos", "anticipo_gasolina", "anticipo_peaje", 
                "anticipo_transporte_t", "anticipo_avion", "total_anticipo",
                "subtotal_sin_avion",
                "observaciones", "autoriza_nombre", "dias_comision",
                "comp_hospedaje_cargo", "comp_hospedaje_abono",
                "comp_alimentos_cargo", "comp_alimentos_abono",
                "comp_pasajes_cargo", "comp_pasajes_abono",
                "comp_combustible_cargo", "comp_combustible_abono",
                "comp_otros_cargo", "comp_otros_abono",
                "suma_cargos", "suma_abonos",
                "importe_total_comprobacion",
                "elaboro_nombre", "reviso_nombre", "bueno_por_monto", "recibi_letras",
                "mostrar_bloque_especial",
                "paciente",  # ← NUEVO CAMPO
                "nss"        # ← NUEVO CAMPO
            ]),

            "informes": pd.DataFrame(columns=[
                "folio_pliego", "fecha_informe", "no_cama",
                "hora_salida_hgz", "hora_llegada_destino", "hora_regreso_hgz",
                "km_inicial", "km_final", "km_total_recorrido",
                "resultados", "contribuciones", "ecco_utilizado"
            ]),

            "vehiculos": pd.DataFrame(columns=[
                "tipo","ecco","placas","marca","modelo",
                "km_actual","km_servicio","estatus"
            ]),

            "config_admin": pd.DataFrame(columns=[
                "titular_unidad", "unidad_administrativa", "adscripcion", "folio_inicial_sistema"
            ]),

            "hospitales": pd.DataFrame(columns=[
                "estado","nombre_hosp","direccion","alto_costo"
            ]),  

            "traslados_locales": pd.DataFrame(columns=[
                "folio", 
                "fecha_creacion",           
                "fecha_traslado",           
                "turno",                    
                "paciente", 
                "nss", 
                "domicilio", 
                "telefono", 
                "fecha_hora", 
                "empleado_comisionado",     
                "matricula_asignado",       
                "fecha_asignacion",         
                "vehiculo",                 
                "km_inicial",               
                "km_final",                 
                "cerrado_por",              
                "fecha_cierre",             
                "destino", 
                "servicio", 
                "cama", 
                "requiere",
                "estatus", 
                "observaciones", 
                "matricula_admin"           
            ]),
            
            "mantenimientos": pd.DataFrame(columns=[
                "ecco", "fecha", "tipo_servicio", "lugar", "km_registro", "observaciones"
            ]),

            "gastos": pd.DataFrame(columns=[
                "folio_pliego", "categoria", "factura", "proveedor", "fecha", "importe",
                "concepto", "justificacion", "tipo"
            ])
        }

        # --- USUARIO ADMIN INICIAL ---
        admin = {
            "matricula":"123", "nombre":"ADMIN", "apellido_p":"SISTEMA",
            "password":"admin", "rol":"Administrador", "estatus":"Alta" 
        }
        tablas["usuarios"] = pd.concat([tablas["usuarios"], pd.DataFrame([admin])], ignore_index=True)

        # --- CONFIGURACIÓN INSTITUCIONAL INICIAL ---
        config = {
            "titular_unidad": "LIC. RICARDO REYES",
            "unidad_administrativa": "DEPARTAMENTO DE PERSONAL",
            "adscripcion": "HGZ No. 1",
            "folio_inicial_sistema": "F001/2026"
        }
        tablas["config_admin"] = pd.concat([tablas["config_admin"], pd.DataFrame([config])], ignore_index=True)

        # Escritura en Excel
        with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
            for nombre, df in tablas.items():
                df.to_excel(writer, sheet_name=nombre, index=False)
        print("✅ Base de datos creada con éxito.")
    else:
        print("✅ Base de datos ya existe")

        
def validar_login(matricula, password):
    try:
        df = pd.read_excel(DB_FILE, sheet_name="usuarios")
        df["matricula"] = df["matricula"].astype(str).str.strip()
        df["password"] = df["password"].astype(str).str.strip()
        
        user = df[(df["matricula"] == str(matricula).strip()) & 
                  (df["password"] == str(password).strip()) & 
                  (df["estatus"] == "Alta")]

        if not user.empty:
            row = user.iloc[0]
            return {
                "matricula": str(row["matricula"]),
                "nombre": f"{row['nombre']} {row.get('apellido_p', '')} {row.get('apellido_m', '')}".strip(),
                "rol": str(row["rol"]),
                "categoria": str(row.get("categoria", "PERSONAL")),
                "puesto": str(row.get("puesto", "")),
                "departamento": str(row.get("departamento", "")),
                "gj": str(row.get("gj", "")),
                "tipo_contrato": str(row.get("tipo_contrato", ""))
            }
    except Exception as e:
        print("Error en login:", e)
    return None

def guardar_pliego_completo(datos_usuario, datos_traslado, datos_funcionario):
    """Combina los datos de los formularios y los guarda en la pestaña 'pliegos'."""
    try:
        df_pliegos = pd.read_excel(DB_FILE, sheet_name="pliegos")
        
        nueva_fila = {
            "folio": datos_traslado.get('m_folio'),
            "objeto_comision": datos_traslado.get('m_objeto'),
            "destino": datos_traslado.get('m_destino'),
            "fecha_inicio": datos_traslado.get('m_inicio'),
            "fecha_fin": datos_traslado.get('m_fin'),
            "medio_transporte": datos_traslado.get('m_transporte'),
            "chofer": datos_traslado.get('m_chofer'),
            "acompañante": datos_traslado.get('m_acompanante'),
            "ecco": datos_traslado.get('m_ecco'),
            "f_solicitante": datos_funcionario.get('nombre'),
            "f_categoria": datos_funcionario.get('categoria'),
            "f_area": datos_funcionario.get('departamento'),
            "f_tel": datos_funcionario.get('tel_oficina'),
            "matricula": datos_usuario.get('matricula'),
            "fecha_elaboracion": datetime.now().strftime("%d/%m/%Y"),
            "estatus_pliego": "PENDIENTE",
            "paciente": datos_traslado.get('paciente', ''),  # ← NUEVO
            "nss": datos_traslado.get('nss', '')             # ← NUEVO
        }
        
        df_pliegos = pd.concat([df_pliegos, pd.DataFrame([nueva_fila])], ignore_index=True)
        
        with pd.ExcelWriter(DB_FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_pliegos.to_excel(writer, sheet_name="pliegos", index=False)
        return True
    except Exception as e:
        print(f"Error al guardar pliego: {e}")
        return False

def obtener_lista_usuarios():
    """Retorna los registros de usuarios activos para selectbox."""
    try:
        df = pd.read_excel(DB_FILE, sheet_name="usuarios")
        return df[df["estatus"] == "Alta"].to_dict('records')
    except:
        return []