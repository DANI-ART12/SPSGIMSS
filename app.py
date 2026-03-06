# ============================================
# app.py - VERSIÓN CORREGIDA CON NUEVAS VISTAS
# ============================================

import streamlit as st
import pandas as pd
from PIL import Image
import io
import os
from datetime import datetime, timedelta

# ============================================
# IMPORTACIONES CORRECTAS DESDE CADA MÓDULO
# ============================================
from modules.database import inicializar_base_datos, validar_login
from modules.utils import (
    generar_folio_local,
    asegurar_hojas_excel,
    gestionar_config_permanente,
    get_base64
)
from modules.db_handler import (
    guardar_o_actualizar_pliego,
    actualizar_km_vehiculo,
    actualizar_base_datos_maestra,
    obtener_lista_usuarios,
    obtener_vehiculos  # ← AGREGADO
)
from modules.forms import (
    vista_pliego,
    vista_traslados_dia,           # ← NUEVA
    vista_traslados_programados,    # ← NUEVA
    vista_historial_maestro,
    vista_estadisticas_admin,
    vista_informe_comision,
    vista_configuracion,
    vista_configuracion_admin,
    vista_configuracion_admincompleta,
    vista_desglose_gastos
)

print("✅ Funciones importadas correctamente:")
print("   - database: inicializar_base_datos, validar_login")
print("   - utils: generar_folio_local, gestionar_config_permanente, get_base64")
print("   - db_handler: guardar_o_actualizar_pliego, actualizar_km_vehiculo, obtener_vehiculos")
print("   - forms: todas las vistas (incluyendo nuevas)")

# ============================================
# CONFIGURACIÓN INICIAL DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Sistema IMSS-SISGE", 
    page_icon="assets/logoimss.png", 
    layout="wide"
)

# ============================================
# INICIALIZAR SESIÓN
# ============================================
if "modo_claro" not in st.session_state:
    st.session_state.modo_claro = False

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

if "traslados_seleccionados" not in st.session_state:
    st.session_state.traslados_seleccionados = []

# ============================================
# VERIFICAR CONFIGURACIÓN DE FOLIOS
# ============================================
folio_foraneo = gestionar_config_permanente("folio_inicial_foraneo")
folio_local = gestionar_config_permanente("folio_inicial_local")
primera_vez = not (folio_foraneo or folio_local)

# ============================================
# INICIALIZAR Y VERIFICAR BASE DE DATOS
# ============================================
inicializar_base_datos()
print("🔧 Verificando base de datos...")
if not os.path.exists("base_datos.xlsx"):
    print("📁 Base de datos no encontrada. Creando...")
    inicializar_base_datos()
    print("✅ Base de datos creada exitosamente")
else:
    print("✅ Base de datos existente")

# ============================================
# FUNCIÓN PARA CONFIGURAR FOLIOS INICIALES
# ============================================
def configurar_folios_iniciales():
    st.title("⚙️ Configuración Inicial de Folios")
    
    st.info("Configure los folios iniciales para cada tipo de traslado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Traslados FORÁNEOS")
        st.caption("Formato: F001/2026")
        foraneo_actual = gestionar_config_permanente("folio_inicial_foraneo")
        nuevo_foraneo = st.text_input("Folio inicial FORÁNEO:", 
                                     value=foraneo_actual if foraneo_actual else "F001/2026",
                                     key="ini_foraneo")
    
    with col2:
        st.subheader("🚑 Traslados LOCALES")
        st.caption("Formato: L001/2026")
        local_actual = gestionar_config_permanente("folio_inicial_local")
        nuevo_local = st.text_input("Folio inicial LOCAL:", 
                                   value=local_actual if local_actual else "L001/2026",
                                   key="ini_local")
    
    if st.button("💾 Guardar Configuración", type="primary"):
        gestionar_config_permanente("folio_inicial_foraneo", nuevo_foraneo)
        gestionar_config_permanente("folio_inicial_local", nuevo_local)
        st.success("✅ Configuración guardada")
        st.rerun()

# ============================================
# PANTALLA DE LOGIN (DOS COLUMNAS)
# ============================================
if not st.session_state.autenticado:
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            try:
                logo = Image.open("assets/logoimss.png")
                st.image(logo, width=180)
            except:
                st.warning("Logo no encontrado")
        
        st.markdown("<h2 style='text-align:center; margin:20px 0;'>SISTEMA IMSS</h2>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            matricula = st.text_input("MATRÍCULA", placeholder="Ingrese su matrícula")
            password = st.text_input("CONTRASEÑA", type="password", placeholder="Ingrese su contraseña")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.form_submit_button("🔐 ENTRAR", use_container_width=True):
                    user = validar_login(matricula, password)
                    if user:
                        st.session_state.autenticado = True
                        st.session_state.user_data = user
                        st.rerun()
                    else:
                        st.error("❌ Matrícula o contraseña incorrecta")
    
    with col_der:
        st.markdown(f"""
            <style>
            .carousel-container {{
                width: 100%;
                height: 350px;
                position: relative;
                overflow: hidden;
                border-radius: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.2);
                background-color: #f8f9fa;
            }}
            
            .carousel-track {{
                display: flex;
                width: 300%;
                height: 100%;
                animation: carousel 12s infinite ease-in-out;
            }}
            
            .carousel-slide {{
                width: 33.333%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 10px;
            }}
            
            .carousel-slide img {{
                max-width: 100%;
                max-height: 100%;
                width: auto;
                height: auto;
                object-fit: contain;
                border-radius: 10px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            @keyframes carousel {{
                0%, 25% {{ transform: translateX(0); }}
                33%, 58% {{ transform: translateX(-33.333%); }}
                66%, 91% {{ transform: translateX(-66.666%); }}
                100% {{ transform: translateX(0); }}
            }}
            </style>
            
            <div class="carousel-container">
                <div class="carousel-track">
                    <div class="carousel-slide">
                        <img src="data:image/webp;base64,{get_base64('assets/imagen1.webp')}" alt="IMSS 1">
                    </div>
                    <div class="carousel-slide">
                        <img src="data:image/webp;base64,{get_base64('assets/imagen2.webp')}" alt="IMSS 2">
                    </div>
                    <div class="carousel-slide">
                        <img src="data:image/webp;base64,{get_base64('assets/imagen3.webp')}" alt="IMSS 3">
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.stop()

# ============================================
# APP PRINCIPAL (USUARIO AUTENTICADO)
# ============================================
u = st.session_state.user_data

# ============================================
# BARRA LATERAL: DATOS DEL USUARIO Y APARIENCIA
# ============================================
st.sidebar.title(f"👤 {u['nombre']}")
st.sidebar.caption(f"Rol: {u['rol']}")
st.sidebar.divider()

st.sidebar.markdown("### 🎨 Apariencia")
modo = st.sidebar.toggle("Modo Claro", value=st.session_state.modo_claro)
st.session_state.modo_claro = modo
st.sidebar.divider()

# ============================================
# CONFIGURACIÓN INICIAL DE FOLIOS (SI ES PRIMERA VEZ)
# ============================================
if u['rol'] == "Administrador" and primera_vez:
    st.warning("⚠️ Es la primera vez que ejecutas el sistema. Configura los folios iniciales.")
    configurar_folios_iniciales()
    st.stop()

# OPCIÓN DE CONFIGURACIÓN DE FOLIOS EN MENÚ
if u['rol'] == "Administrador" and st.sidebar.button("⚙️ Configurar Folios", use_container_width="stretch"):
    configurar_folios_iniciales()
    st.stop()

# ============================================
# MENÚ PRINCIPAL (REESTRUCTURADO)
# ============================================
opciones_menu = []

# Opciones para todos los usuarios
opciones_menu.append("🚑 Traslados del Día (HOY)")
opciones_menu.append("📋 Pliego Comisión (FORÁNEOS)")
opciones_menu.append("📝 Informe Comisión")
opciones_menu.append("🧾 Desglose de Gastos")
opciones_menu.append("📊 Historial Pliegos e Informes")

# Opciones solo para administradores
if u['rol'] == "Administrador":
    opciones_menu.append("📅 Traslados Programados")  # ← NUEVA (solo admin)
    opciones_menu.append("👥 Historial Pacientes")
    opciones_menu.append("📈 Estadísticas Admin")
    opciones_menu.append("⚙️ Configuración")

# Opción de cerrar sesión para todos
opciones_menu.append("🚪 Cerrar sesión")

menu = st.sidebar.radio("📌 Menú Principal", opciones_menu)

# ============================================
# ESTILOS (MODO CLARO / OSCURO)
# ============================================
if st.session_state.modo_claro:
    st.markdown("""
        <style>
        .stApp { background-color: #FFFFFF !important; color: #000000 !important; }
        div[data-testid="stDialog"], div[role="dialog"], div[data-baseweb="modal"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DDE1E6 !important;
            box-shadow: 0px 4px 16px rgba(0,0,0,0.1) !important;
        }
        div[role="dialog"] * { color: #000000 !important; }
        div[data-baseweb="select"] > div, div[data-baseweb="popover"] {
            background-color: #F8F9FA !important;
            color: #000000 !important;
        }
        div[data-baseweb="select"] * {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }
        button[kind="primary"], .stButton > button {
            background-color: #004a44 !important;
            color: #FFFFFF !important;
            border: none !important;
        }
        input, textarea {
            background-color: #F8F9FA !important;
            color: #000000 !important;
            border: 1px solid #CED4DA !important;
            -webkit-text-fill-color: #000000 !important;
        }
        .stTextInput label, .stTextArea label, .stSelectbox label, 
        .stDateInput label, .stTimeInput label, .stNumberInput label,
        [data-testid="stWidgetLabel"] p {
            color: #000000 !important;
            font-weight: 600 !important;
        }
        input::placeholder, textarea::placeholder {
            color: #6c757d !important;
            opacity: 1 !important;
        }
        [data-testid="stSidebar"] { background-color: #F1F3F5 !important; }
        [data-testid="stSidebar"] * { color: #000000 !important; }
        div[data-testid="stDataFrame"], div[data-testid="stDataFrameViewPort"] {
            background-color: #FFFFFF !important;
        }
        [data-testid="stTable"] td, [data-testid="stTable"] th,
        div[role="gridcell"], div[role="columnheader"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #EEEEEE !important;
        }
        .st-expanderHeader {
            background-color: #F0F2F6 !important;
            border: 1px solid #CED4DA !important;
            border-radius: 10px !important;
            transition: background-color 0.3s ease !important;
        }
        .st-expanderHeader p, .st-expanderHeader svg {
            color: #1F2937 !important;
            fill: #1F2937 !important;
        }
        .st-expanderHeader:hover {
            background-color: #E2E8F0 !important;
            border-color: #004a44 !important;
        }
        .st-expanderContent {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #CED4DA !important;
            border-top: none !important;
        }
        p, h1, h2, h3, h4, h5, h6, span, div { color: #000000 !important; }
        .stTextInput label, .stButton button { color: #000000 !important; }
        .stButton button p { color: inherit !important; }
        </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117 !important; color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #161B22 !important; }
        [data-testid="stSidebar"] * { color: #FFFFFF !important; }
        div.stButton > button { 
            background-color: #004a44 !important; 
            color: #FFFFFF !important; 
            border: 1px solid #2d5a5a !important;
        }
        div.stButton > button:hover { background-color: #005f56 !important; }
        [data-testid="stExpander"] {
            border: 1px solid #30363D !important;
            background-color: #0D1117 !important;
        }
        [data-testid="stExpander"] summary { color: #FFFFFF !important; }
        input, textarea, .stTextInput input, .stTextArea textarea {
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 1px solid #404040 !important;
            -webkit-text-fill-color: #FFFFFF !important;
        }
        .stTextInput label, .stTextArea label, .stSelectbox label, 
        .stDateInput label, .stTimeInput label, .stNumberInput label {
            color: #CCCCCC !important;
            font-weight: 500 !important;
        }
        input::placeholder, textarea::placeholder {
            color: #AAAAAA !important;
            opacity: 1 !important;
        }
        div[data-baseweb="select"] > div {
            background-color: #262730 !important;
            color: #FFFFFF !important;
            border: 1px solid #404040 !important;
        }
        div[data-baseweb="select"] * { color: #FFFFFF !important; }
        div[data-testid="stDialog"], div[role="dialog"], div[data-baseweb="modal"] {
            background-color: #1E1E1E !important;
            border: 1px solid #404040 !important;
        }
        div[role="dialog"] * { color: #FFFFFF !important; }
        div[data-baseweb="popover"] {
            background-color: #1E1E1E !important;
            color: #FFFFFF !important;
        }
        p, h1, h2, h3, h4, h5, h6, span, div, .stMarkdown { color: #FFFFFF !important; }
        .stTextInput label { color: #CCCCCC !important; }
        </style>
    """, unsafe_allow_html=True)

# ============================================
# ESTILOS FIJOS PARA PLIEGO E INFORME (SIEMPRE BLANCO)
# ============================================
st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] > div > div > .stMarkdown,
    .stMarkdown:has(> .informe-contenido),
    .informe-contenido {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 20px !important;
        border-radius: 8px !important;
        border: 1px solid #CED4DA !important;
    }
    div[data-testid="stVerticalBlock"] > div > div > .stMarkdown *,
    .informe-contenido * {
        color: #000000 !important;
    }
    img[alt="IMSS"] {
        background-color: transparent !important;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# NAVEGACIÓN SEGÚN OPCIÓN DEL MENÚ (ACTUALIZADA)
# ============================================
try:
    if menu == "🚪 Cerrar sesión":
        for key in ['autenticado', 'user_data', 'folio_actual', 'pliego_desglose', 'traslados_seleccionados','busqueda_actual']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
    
    elif menu == "🚑 Traslados del Día (HOY)":
        vista_traslados_dia(u)  # ← NUEVA - Todos pueden ver
    
    elif menu == "📅 Traslados Programados":
        if u['rol'] == "Administrador":
            vista_traslados_programados(u)  # ← NUEVA - Solo admin
        else:
            st.error("🚫 Acceso restringido a Administradores")
    
    elif menu == "📋 Pliego Comisión (FORÁNEOS)":
        vista_pliego(u)
    
    elif menu == "📝 Informe Comisión":
        vista_informe_comision(u)
    
    elif menu == "🧾 Desglose de Gastos":
        vista_desglose_gastos(u)
    
    elif menu == "📊 Historial Pliegos e Informes":
        vista_historial_maestro(u)
    
    elif menu == "👥 Historial Pacientes":
        if u['rol'] == "Administrador":
            st.info("📋 Historial detallado de pacientes traslados.")
        else:
            st.error("🚫 Acceso restringido.")
    
    elif menu == "📈 Estadísticas Admin":
        if u['rol'] == "Administrador":
            vista_estadisticas_admin(u)
        else:
            st.error("🚫 Acceso denegado.")
    
    elif menu == "⚙️ Configuración":
        if u['rol'] == "Administrador":
            vista_configuracion_admincompleta(u) 
        else:
            st.error("🚫 Acceso restringido.")
            
except Exception as e:
    st.error(f"Error en la navegación: {e}")
    st.exception(e)