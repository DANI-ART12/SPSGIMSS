# ============================================
# modules/forms.py - VISTAS Y MODALES (VERSIÓN FINAL CORREGIDA)
# ============================================

import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from jinja2 import Template
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go

# ============================================
# IMPORTACIONES
# ============================================
from modules.utils import (
    get_base64,
    asegurar_hojas_excel,
    gestionar_config_permanente,
    generar_html_traslado_imprimible,
    calcular_total_km
)

from modules.db_handler import (
    obtener_lista_usuarios,
    obtener_vehiculos,
    obtener_hospitales,
    obtener_pliegos,
    obtener_traslados_locales,
    guardar_o_actualizar_pliego,
    guardar_traslado_local,
    actualizar_km_vehiculo,
    actualizar_base_datos_maestra,
    guardar_configuracion_admin,
    obtener_configuracion_admin,
    guardar_gastos,
    actualizar_traslado_local
)

# ============================================
# CONSTANTES GLOBALES
# ============================================
DB_FILE = "base_datos.xlsx"

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def sugerir_siguiente_folio(df, prefijo="L"):
    """
    Sugiere el siguiente folio basado en los existentes y el año actual
    """
    try:
        año_actual = datetime.now().year
        
        if df.empty or 'folio' not in df.columns:
            return f"{prefijo}001/{año_actual}"
        
        folios_anio = []
        for folio in df['folio'].astype(str):
            if str(folio).startswith(prefijo) and f"/{año_actual}" in folio:
                try:
                    num = int(folio.split('/')[0].replace(prefijo, ''))
                    folios_anio.append(num)
                except:
                    pass
        
        if folios_anio:
            ultimo_num = max(folios_anio)
            return f"{prefijo}{str(ultimo_num + 1).zfill(3)}/{año_actual}"
        else:
            return f"{prefijo}001/{año_actual}"
    except Exception as e:
        print(f"Error sugiriendo folio: {e}")
        año_actual = datetime.now().year
        return f"{prefijo}001/{año_actual}"

def validar_formato_folio(folio, prefijo):
    """
    Valida que el folio tenga el formato correcto: F123/2026 o L150/2026
    """
    try:
        if not folio or not isinstance(folio, str):
            return False
        
        folio = folio.strip().upper()
        
        if not folio.startswith(prefijo):
            return False
        
        if '/' not in folio:
            return False
            
        partes = folio.split('/')
        if len(partes) != 2:
            return False
        
        numero = partes[0].replace(prefijo, '')
        anio = partes[1]
        
        if not numero.isdigit() or len(numero) < 1 or len(numero) > 3:
            return False
        
        if not anio.isdigit() or len(anio) != 4:
            return False
        
        return True
    except:
        return False

def obtener_turno_por_hora(hora=None):
    """
    Determina el turno basado en la hora
    Returns: MATUTINO, VESPERTINO, NOCTURNO
    """
    if hora is None:
        hora = datetime.now().hour
    else:
        if isinstance(hora, str) and ':' in hora:
            hora = int(hora.split(':')[0])
    
    if 6 <= hora < 14:
        return "MATUTINO"
    elif 14 <= hora < 22:
        return "VESPERTINO"
    else:
        return "NOCTURNO"


# ============================================================================
# SECCIÓN 1: MODALES PRINCIPALES
# ============================================================================

# ----------------------------------------------------------------------------
# MODAL 1.1: VER DETALLES DE TRASLADO LOCAL (CON IMPRESIÓN INTEGRADA)
# ----------------------------------------------------------------------------
@st.dialog("📋 DETALLES COMPLETOS DEL TRASLADO")
def modal_ver_detalles_traslado(datos, u=None):
    st.markdown("### 📌 Información General")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Folio:** {datos.get('folio', 'N/A')}")
        st.markdown(f"**Fecha Creación:** {datos.get('fecha_creacion', 'N/A')}")
        st.markdown(f"**Paciente:** {datos.get('paciente', 'N/A')}")
        st.markdown(f"**NSS:** {datos.get('nss', 'N/A')}")
    with col2:
        st.markdown(f"**Domicilio:** {datos.get('domicilio', 'N/A')}")
        st.markdown(f"**Teléfono:** {datos.get('telefono', 'N/A')}")
        st.markdown(f"**Destino:** {datos.get('destino', 'N/A')}")
        st.markdown(f"**Servicio:** {datos.get('servicio', 'N/A')}")
    
    st.divider()
    st.markdown("### 🚑 Datos del Traslado")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"**Empleado:** {datos.get('empleado_comisionado', 'N/A')}")
        st.markdown(f"**Fecha/Hora:** {datos.get('fecha_hora', 'N/A')}")
        st.markdown(f"**Cama:** {datos.get('cama', 'N/A')}")
    with col4:
        st.markdown(f"**Requiere:** {datos.get('requiere', 'N/A')}")
        st.markdown(f"**Estatus:** {datos.get('estatus', 'N/A')}")
        st.markdown(f"**Observaciones:** {datos.get('observaciones', 'N/A')}")
    
    st.divider()
    st.markdown("### 🚑 Datos de Asignación")
    col5, col6 = st.columns(2)
    with col5:
        st.markdown(f"**Vehículo:** {datos.get('vehiculo', 'N/A')}")
        st.markdown(f"**KM Inicial:** {datos.get('km_inicial', 'N/A')}")
    with col6:
        st.markdown(f"**KM Final:** {datos.get('km_final', 'N/A')}")
        if datos.get('km_inicial') and datos.get('km_final'):
            try:
                total = int(datos.get('km_final', 0)) - int(datos.get('km_inicial', 0))
                st.markdown(f"**Total Recorrido:** {total} km")
            except:
                pass
    
    # ============================================
    # SECCIÓN DE IMPRESIÓN INTEGRADA (ANTIGUO MODAL 1.5)
    # ============================================
    st.divider()
    with st.expander("🖨️ CONFIGURAR IMPRESIÓN", expanded=False):
        if u and u.get('rol') == "Administrador":
            st.markdown("#### ⚙️ Opciones de impresión")
            col_op1, col_op2 = st.columns(2)
            with col_op1:
                mostrar_cama = st.checkbox("Mostrar cama", value=True, key=f"imp_cama_{datos.get('folio', '')}")
                mostrar_domicilio = st.checkbox("Mostrar domicilio", value=True, key=f"imp_domicilio_{datos.get('folio', '')}")
                mostrar_telefono = st.checkbox("Mostrar teléfono", value=True, key=f"imp_telefono_{datos.get('folio', '')}")
                mostrar_chofer = st.checkbox("Mostrar chofer/responsable", value=True, key=f"imp_chofer_{datos.get('folio', '')}")
            with col_op2:
                mostrar_observaciones = st.checkbox("Mostrar observaciones", value=True, key=f"imp_obs_{datos.get('folio', '')}")
                mostrar_vehiculo = st.checkbox("Mostrar vehículo", value=True, key=f"imp_vehiculo_{datos.get('folio', '')}")
                mostrar_km = st.checkbox("Mostrar kilometraje", value=True, key=f"imp_km_{datos.get('folio', '')}")
        else:
            mostrar_cama = mostrar_domicilio = mostrar_telefono = True
            mostrar_chofer = mostrar_observaciones = True
            mostrar_vehiculo = mostrar_km = True
        
        with st.expander("📋 Vista previa de datos a imprimir", expanded=False):
            st.markdown(f"**Folio:** {datos.get('folio', 'N/A')}")
            st.markdown(f"**Paciente:** {datos.get('paciente', 'N/A')}")
            if mostrar_cama and datos.get('cama'):
                st.markdown(f"**Cama:** {datos.get('cama', 'N/A')}")
            if mostrar_domicilio and datos.get('domicilio'):
                st.markdown(f"**Domicilio:** {datos.get('domicilio', 'N/A')}")
            if mostrar_telefono and datos.get('telefono'):
                st.markdown(f"**Teléfono:** {datos.get('telefono', 'N/A')}")
            if mostrar_chofer and datos.get('empleado_comisionado'):
                st.markdown(f"**Chofer:** {datos.get('empleado_comisionado', 'N/A')}")
            if mostrar_vehiculo and datos.get('vehiculo'):
                st.markdown(f"**Vehículo:** {datos.get('vehiculo', 'N/A')}")
            if mostrar_km:
                st.markdown(f"**KM Inicial:** {datos.get('km_inicial', 'N/A')}")
                st.markdown(f"**KM Final:** {datos.get('km_final', 'N/A')}")
            if mostrar_observaciones and datos.get('observaciones'):
                st.markdown(f"**Observaciones:** {datos.get('observaciones', 'N/A')}")
        
        col_imp1, col_imp2, col_imp3 = st.columns([1, 2, 1])
        with col_imp2:
            if st.button("🖨️ IMPRIMIR", type="primary", use_container_width=True, key=f"btn_imprimir_{datos.get('folio', '')}"):
                opciones = {
                    'cama': mostrar_cama,
                    'domicilio': mostrar_domicilio,
                    'telefono': mostrar_telefono,
                    'chofer': mostrar_chofer,
                    'observaciones': mostrar_observaciones,
                    'vehiculo': mostrar_vehiculo,
                    'km': mostrar_km
                }
                
                from modules.utils import generar_html_traslado_imprimible
                html = generar_html_traslado_imprimible(datos, opciones)
                
                html_impresion = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            body {{ margin: 0; padding: 0.5cm; }}
                        }}
                    </style>
                </head>
                <body>
                    {html}
                    <script>
                        window.onload = function() {{
                            window.print();
                        }};
                    </script>
                </body>
                </html>
                """
                st.components.v1.html(html_impresion, height=600, scrolling=True)
    
    # Botón de cerrar
    if st.button("❌ Cerrar", use_container_width=True):
        st.rerun()


# ----------------------------------------------------------------------------
# MODAL 1.2: VER DETALLES DE PLIEGO (SIN CAMBIOS)
# ----------------------------------------------------------------------------
@st.dialog("📋 DETALLES COMPLETOS DEL PLIEGO")
def modal_ver_detalles_pliego(datos, u=None):
    st.markdown("### 📌 Información General")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Folio:** {datos.get('folio', 'N/A')}")
        st.markdown(f"**Fecha Elaboración:** {datos.get('fecha_elaboracion', 'N/A')}")
        st.markdown(f"**Solicitante:** {datos.get('f_solicitante', 'N/A')}")
        st.markdown(f"**Categoría:** {datos.get('f_categoria', 'N/A')}")
    with col2:
        st.markdown(f"**Área:** {datos.get('f_area', 'N/A')}")
        st.markdown(f"**Empleado:** {datos.get('nombre', 'N/A')}")
        st.markdown(f"**Destino:** {datos.get('m_destino', 'N/A')}")
        st.markdown(f"**Objeto:** {datos.get('m_objeto', 'N/A')}")
    
    st.divider()
    st.markdown("### 💰 Anticipos")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"**Viáticos:** ${datos.get('anticipo_viaticos', '0')}")
        st.markdown(f"**Gasolina:** ${datos.get('anticipo_gasolina', '0')}")
        st.markdown(f"**Peaje:** ${datos.get('anticipo_peaje', '0')}")
    with col4:
        st.markdown(f"**Transporte T.:** ${datos.get('anticipo_transporte_t', '0')}")
        st.markdown(f"**Avión:** ${datos.get('anticipo_avion', '0')}")
        st.markdown(f"**Total:** ${datos.get('total_anticipo', '0')}")
    
    if st.button("❌ Cerrar", use_container_width=True):
        st.rerun()


# ----------------------------------------------------------------------------
# MODAL 1.3: TOMAR TRASLADO (PARA USUARIOS)
# ----------------------------------------------------------------------------
@st.dialog("👤 TOMAR TRASLADO")
def modal_tomar_traslado(datos, u):
    st.markdown(f"### ¿Tomar el traslado **{datos.get('folio')}**?")
    st.markdown(f"**Paciente:** {datos.get('paciente', 'N/A')}")
    st.markdown(f"**Destino:** {datos.get('destino', 'N/A')}")
    
    st.warning(f"Te asignarás como responsable: **{u.get('nombre')}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, tomar traslado", type="primary", use_container_width=True):
            datos['empleado_comisionado'] = f"{u.get('matricula')} - {u.get('nombre')}"
            datos['estatus'] = "En Curso"
            
            if actualizar_traslado_local(datos):
                st.success("✅ Traslado asignado correctamente")
                st.rerun()
            else:
                st.error("Error al asignar traslado")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()


# ----------------------------------------------------------------------------
# MODAL 1.4: CERRAR TRASLADO (PARA USUARIOS)
# ----------------------------------------------------------------------------
@st.dialog("✅ CERRAR TRASLADO")
def modal_cerrar_traslado(datos):
    st.markdown(f"### ¿Cerrar el traslado **{datos.get('folio')}**?")
    st.markdown(f"**Paciente:** {datos.get('paciente', 'N/A')}")
    st.markdown(f"**Destino:** {datos.get('destino', 'N/A')}")
    
    st.success("Al cerrar, el traslado se marcará como COMPLETADO")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, cerrar traslado", type="primary", use_container_width=True):
            datos['estatus'] = "Completado"
            
            if actualizar_traslado_local(datos):
                st.success("✅ Traslado cerrado correctamente")
                st.rerun()
            else:
                st.error("Error al cerrar traslado")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()


# ----------------------------------------------------------------------------
# 🔴 MODAL 1.5: ELIMINADO (AHORA ESTÁ INTEGRADO EN MODAL 1.1)
# ----------------------------------------------------------------------------
# @st.dialog("🖨️ IMPRIMIR TRASLADO")  ← YA NO SE USA

# ----------------------------------------------------------------------------
# MODAL 1.6: ASIGNAR TRASLADOS (MÚLTIPLE)
# ----------------------------------------------------------------------------
@st.dialog("🗂️ ASIGNAR TRASLADOS SELECCIONADOS")
def modal_asignar_traslados(u, df_vehiculos):
    folios = st.session_state.get('asignar_folios', [])
    
    st.markdown(f"### Asignando {len(folios)} traslado(s)")
    st.markdown(f"**Usuario:** {u.get('nombre')} (Mat: {u.get('matricula')})")
    
    opciones_vehiculos = ["-- Seleccionar vehículo --"]
    if not df_vehiculos.empty:
        opciones_vehiculos.extend([f"{row['ecco']} - {row.get('marca', '')} {row.get('modelo', '')}" 
                                   for _, row in df_vehiculos.iterrows()])
    
    vehiculo_sel = st.selectbox("🚑 Seleccionar vehículo:", opciones_vehiculos, key="modal_vehiculo_asignar")
    km_inicial = st.number_input("📊 Kilometraje Inicial:", min_value=0, step=100, key="modal_km_inicial")
    
    st.warning("⚠️ Al asignar, los traslados pasarán a estatus **En Curso**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ CONFIRMAR ASIGNACIÓN", type="primary", use_container_width=True):
            if vehiculo_sel == "-- Seleccionar vehículo --":
                st.error("Debe seleccionar un vehículo")
                return
            if km_inicial <= 0:
                st.error("Debe ingresar kilometraje inicial")
                return
            
            ecco = vehiculo_sel.split(' - ')[0]
            exitosos = 0
            
            for folio in folios:
                df_t = obtener_traslados_locales()
                if not df_t.empty and folio in df_t['folio'].values:
                    datos = df_t[df_t['folio'] == folio].iloc[0].to_dict()
                    
                    datos['empleado_comisionado'] = f"{u.get('matricula')} - {u.get('nombre')}"
                    datos['matricula_asignado'] = u.get('matricula')
                    datos['fecha_asignacion'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    datos['vehiculo'] = ecco
                    datos['km_inicial'] = km_inicial
                    datos['estatus'] = "En Curso"
                    
                    if guardar_traslado_local(datos):
                        exitosos += 1
            
            st.success(f"✅ {exitosos} de {len(folios)} traslados asignados correctamente")
            st.session_state.seleccionados = []
            st.rerun()
    with col2:
        if st.button("❌ CANCELAR", use_container_width=True):
            st.rerun()

# ----------------------------------------------------------------------------
# MODAL 1.7: NUEVO TRASLADO FORÁNEO
# ----------------------------------------------------------------------------
@st.dialog("➕ NUEVO TRASLADO FORÁNEO")
def modal_nuevo_traslado(u, df_p):
    st.write("Complete los datos del nuevo traslado FORÁNEO")
    
    col_folio1, col_folio2 = st.columns([3, 1])
    with col_folio1:
        folio_sugerido = sugerir_siguiente_folio(df_p, "F")
        folio_manual = st.text_input(
            "Folio del traslado:", 
            value=st.session_state.get('folio_foraneo_manual', folio_sugerido),
            placeholder="Ej: F001/2026",
            help="Ingrese el folio manualmente. Ej: F001/2026",
            key="modal_folio_foraneo_input"
        )
        st.session_state.folio_foraneo_manual = folio_manual
    with col_folio2:
        st.markdown("####")
        if st.button("🔄 Sugerir", use_container_width=True, key="btn_sugerir_foraneo"):
            st.session_state.folio_foraneo_manual = sugerir_siguiente_folio(df_p, "F")
            st.rerun()
    
    st.caption(f"Año actual: {datetime.now().year}")
    st.divider()
    
    es_persona_paso = False
    nombre_externo = None
    matricula_externo = None
    puesto_externo = None
    
    if u.get('rol') == "Administrador":
        es_persona_paso = st.checkbox("👤 ¿Es persona de paso? (Externo no registrado)", key="checkbox_persona_paso")
        if es_persona_paso:
            with st.container(border=True):
                st.markdown("**📝 Datos del externo**")
                col_ext1, col_ext2 = st.columns(2)
                with col_ext1:
                    nombre_externo = st.text_input("Nombre completo:", key="modal_nombre_externo")
                with col_ext2:
                    matricula_externo = st.text_input("Matrícula:", key="modal_matricula_externo")
                puesto_externo = st.text_input("Puesto:", key="modal_puesto_externo")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Destino y Motivo", "🚗 Datos del Viaje", "💰 Anticipos", "📋 Liquidación"])
    
    with tab1:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            destino = st.text_input("Destino:", placeholder="Ej: HGR 1 → HGR 2", key="modal_destino")
        with col_d2:
            motivo = st.text_input("Motivo / Paciente:", placeholder="Ej: TRASLADO DE PACIENTE - NSS", key="modal_motivo")
        
        paciente = st.text_input("Paciente:", placeholder="Nombre del paciente", key="modal_paciente")
        nss = st.text_input("NSS:", placeholder="Número de seguridad social", key="modal_nss")
        area_solicitante = st.text_input("Área solicitante:", placeholder="Ej: HOSPITAL GENERAL DE ZONA No. 01", key="modal_area")
    
    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input("Fecha de inicio:", value=datetime.now(), key="modal_fecha_inicio")
        with col_f2:
            fecha_fin = st.date_input("Fecha de fin:", value=datetime.now(), key="modal_fecha_fin")
        
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            transporte = st.text_input("Medio de transporte:", placeholder="Ej: VEHÍCULO INSTITUCIONAL", key="modal_transporte")
        with col_t2:
            chofer = st.text_input("Chofer:", placeholder="Nombre del chofer", key="modal_chofer")
        with col_t3:
            acompanante = st.text_input("Acompañante:", placeholder="Nombre del acompañante", key="modal_acompanante")
    
    with tab3:
        st.markdown("**💰 Anticipos**")
        col_a1, col_a2 = st.columns(2)
        with col_a1:
            viaticos = st.number_input("Viáticos ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_viaticos")
            gasolina = st.number_input("Gasolina ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_gasolina")
            peaje = st.number_input("Peaje ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_peaje")
        with col_a2:
            transporte_t = st.number_input("Transporte terrestre ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_transporte_t")
            avion = st.number_input("Avión ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_avion")
        
        subtotal_sin_avion = viaticos + gasolina + peaje + transporte_t
        total_anticipo = subtotal_sin_avion + avion
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Subtotal sin avión", f"${subtotal_sin_avion:,.2f}")
        with col_s2:
            st.metric("Total anticipo", f"${total_anticipo:,.2f}", delta_color="off")
    
    with tab4:
        st.markdown("**📋 Liquidación (Cargo / Abono)**")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            hospedaje_cargo = st.number_input("Hospedaje (cargo):", min_value=0.0, step=100.0, format="%.2f", key="modal_hospedaje_cargo")
            alimentos_cargo = st.number_input("Alimentos (cargo):", min_value=0.0, step=100.0, format="%.2f", key="modal_alimentos_cargo")
            pasajes_cargo = st.number_input("Pasajes (cargo):", min_value=0.0, step=100.0, format="%.2f", key="modal_pasajes_cargo")
            combustible_cargo = st.number_input("Combustible (cargo):", min_value=0.0, step=100.0, format="%.2f", key="modal_combustible_cargo")
            otros_cargo = st.number_input("Otros (cargo):", min_value=0.0, step=100.0, format="%.2f", key="modal_otros_cargo")
        with col_l2:
            hospedaje_abono = st.number_input("Hospedaje (abono):", min_value=0.0, step=100.0, format="%.2f", key="modal_hospedaje_abono")
            alimentos_abono = st.number_input("Alimentos (abono):", min_value=0.0, step=100.0, format="%.2f", key="modal_alimentos_abono")
            pasajes_abono = st.number_input("Pasajes (abono):", min_value=0.0, step=100.0, format="%.2f", key="modal_pasajes_abono")
            combustible_abono = st.number_input("Combustible (abono):", min_value=0.0, step=100.0, format="%.2f", key="modal_combustible_abono")
            otros_abono = st.number_input("Otros (abono):", min_value=0.0, step=100.0, format="%.2f", key="modal_otros_abono")
        
        suma_cargos = hospedaje_cargo + alimentos_cargo + pasajes_cargo + combustible_cargo + otros_cargo
        suma_abonos = hospedaje_abono + alimentos_abono + pasajes_abono + combustible_abono + otros_abono
        importe_total = suma_cargos - suma_abonos
        
        col_sl1, col_sl2, col_sl3 = st.columns(3)
        with col_sl1:
            st.metric("Suma cargos", f"${suma_cargos:,.2f}")
        with col_sl2:
            st.metric("Suma abonos", f"${suma_abonos:,.2f}")
        with col_sl3:
            st.metric("Importe total", f"${importe_total:,.2f}")
    
    st.divider()
    incluir_tesoreria = st.checkbox(
        "📦 ¿Incluir datos de TESORERÍA? (BUENO POR / RECIBÍ)",
        value=False,
        key="incluir_tesoreria",
        help="Si se marca, se habilitan los campos de BUENO POR y RECIBÍ."
    )
    
    if incluir_tesoreria:
        with st.container(border=True):
            st.markdown("**💰 Datos de Tesorería**")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                bueno_por = st.number_input("BUENO POR ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_bueno_por")
            with col_t2:
                recibi = st.number_input("RECIBÍ ($):", min_value=0.0, step=100.0, format="%.2f", key="modal_recibi")
            recibi_letras = st.text_input("RECIBÍ (letra):", placeholder="Ej: CIEN PESOS", key="modal_recibi_letras")
    else:
        bueno_por = 0.0
        recibi = 0.0
        recibi_letras = ""
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ CREAR TRASLADO", type="primary", use_container_width=True, key="btn_crear_traslado"):
            if destino and motivo and folio_manual:
                if not validar_formato_folio(folio_manual, "F"):
                    st.error("❌ El folio debe tener formato F001/2026")
                else:
                    st.session_state['folio_actual'] = folio_manual
                    st.session_state['nuevo_destino'] = destino.upper()
                    st.session_state['nuevo_motivo'] = motivo.upper()
                    st.session_state['nuevo_area'] = area_solicitante.upper()
                    st.session_state['nuevo_transporte'] = transporte.upper() if transporte else ""
                    st.session_state['nuevo_chofer'] = chofer.upper() if chofer else ""
                    st.session_state['nuevo_acompanante'] = acompanante.upper() if acompanante else ""
                    st.session_state['nuevo_fecha_inicio'] = fecha_inicio.strftime("%d/%m/%Y")
                    st.session_state['nuevo_fecha_fin'] = fecha_fin.strftime("%d/%m/%Y")
                    
                    st.session_state['nuevo_paciente'] = paciente.upper() if paciente else ""
                    st.session_state['nuevo_nss'] = nss.upper() if nss else ""
                    
                    st.session_state['nuevo_viaticos'] = viaticos
                    st.session_state['nuevo_gasolina'] = gasolina
                    st.session_state['nuevo_peaje'] = peaje
                    st.session_state['nuevo_transporte_t'] = transporte_t
                    st.session_state['nuevo_avion'] = avion
                    st.session_state['nuevo_subtotal_sin_avion'] = subtotal_sin_avion
                    st.session_state['nuevo_total_anticipo'] = total_anticipo
                    
                    st.session_state['nuevo_hospedaje_cargo'] = hospedaje_cargo
                    st.session_state['nuevo_hospedaje_abono'] = hospedaje_abono
                    st.session_state['nuevo_alimentos_cargo'] = alimentos_cargo
                    st.session_state['nuevo_alimentos_abono'] = alimentos_abono
                    st.session_state['nuevo_pasajes_cargo'] = pasajes_cargo
                    st.session_state['nuevo_pasajes_abono'] = pasajes_abono
                    st.session_state['nuevo_combustible_cargo'] = combustible_cargo
                    st.session_state['nuevo_combustible_abono'] = combustible_abono
                    st.session_state['nuevo_otros_cargo'] = otros_cargo
                    st.session_state['nuevo_otros_abono'] = otros_abono
                    st.session_state['nuevo_suma_cargos'] = suma_cargos
                    st.session_state['nuevo_suma_abonos'] = suma_abonos
                    st.session_state['nuevo_importe_total'] = importe_total
                    
                    st.session_state['nuevo_bueno_por'] = bueno_por
                    st.session_state['nuevo_recibi'] = recibi
                    st.session_state['nuevo_recibi_letras'] = recibi_letras
                    
                    if es_persona_paso and nombre_externo and matricula_externo:
                        st.session_state['nuevo_nombre_externo'] = nombre_externo.upper()
                        st.session_state['nuevo_matricula_externo'] = matricula_externo.upper()
                        st.session_state['nuevo_puesto_externo'] = puesto_externo.upper() if puesto_externo else ""
                    else:
                        st.session_state['nuevo_nombre_externo'] = None
                    
                    st.success(f"✅ Traslado {folio_manual} creado")
                    st.rerun()
            else:
                st.error("Complete Destino, Motivo y Folio.")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancelar_traslado"):
            st.rerun()

# ----------------------------------------------------------------------------
# MODAL 1.8: CONFIRMAR GUARDADO
# ----------------------------------------------------------------------------
@st.dialog("💾 Confirmar Guardado")
def modal_confirmar_guardado(datos_html, u):
    st.success("¿Estás seguro de guardar este pliego?")
    st.info(f"Folio: **{datos_html.get('m_folio', 'N/A')}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, guardar", type="primary", use_container_width=True, key="btn_confirmar_guardado_si"):
            try:
                registro = {
                    'folio': datos_html.get('m_folio', ''),
                    'fecha_elaboracion': datos_html.get('m_fecha_creacion', ''),
                    'matricula': datos_html.get('matricula', ''),
                    'estatus_pliego': 'ACTIVO',
                    'f_solicitante': datos_html.get('f_solicitante', ''),
                    'f_cp': datos_html.get('f_cp', ''),
                    'f_categoria': datos_html.get('f_categoria', ''),
                    'f_area': datos_html.get('f_area', ''),
                    'f_tel': datos_html.get('f_tel', ''),
                    'nombre': datos_html.get('nombre_empleado', ''),
                    'departamento': datos_html.get('departamento_empleado', ''),
                    'gj': datos_html.get('grupo_jerarquico', ''),
                    'tipo_contrato': datos_html.get('tipo_contrato', ''),
                    'm_objeto': datos_html.get('m_objeto', ''),
                    'p_a': u.get('p_a', ''),
                    'p_b': u.get('p_b', ''),
                    'p_c': u.get('p_c', ''),
                    'm_destino': datos_html.get('m_destino', ''),
                    'fecha_inicio': datos_html.get('m_inicio', ''),
                    'fecha_fin': datos_html.get('m_fin', ''),
                    'medio_transporte': datos_html.get('m_medio_transporte', ''),
                    'chofer': datos_html.get('m_chofer', ''),
                    'acompañante': datos_html.get('m_acompañante', ''),
                    'ecco': u.get('ecco', ''),
                    'dias_comision': datos_html.get('dias_comision', ''),
                    'paciente': datos_html.get('m_paciente', ''),
                    'nss': datos_html.get('nss', ''),
                    'anticipo_viaticos': datos_html.get('anticipo_viaticos', ''),
                    'anticipo_gasolina': datos_html.get('anticipo_gasolina', ''),
                    'anticipo_peaje': datos_html.get('anticipo_peaje', ''),
                    'anticipo_transporte_t': datos_html.get('anticipo_transporte_t', ''),
                    'anticipo_avion': datos_html.get('anticipo_avion', ''),
                    'total_anticipo': datos_html.get('total_anticipo', ''),
                    'subtotal_sin_avion': datos_html.get('subtotal_sin_avion', ''),
                    'observaciones': datos_html.get('observaciones', ''),
                    'comp_hospedaje_cargo': datos_html.get('comp_hospedaje_cargo', ''),
                    'comp_hospedaje_abono': datos_html.get('comp_hospedaje_abono', ''),
                    'comp_alimentos_cargo': datos_html.get('comp_alimentos_cargo', ''),
                    'comp_alimentos_abono': datos_html.get('comp_alimentos_abono', ''),
                    'comp_pasajes_cargo': datos_html.get('comp_pasajes_cargo', ''),
                    'comp_pasajes_abono': datos_html.get('comp_pasajes_abono', ''),
                    'comp_combustible_cargo': datos_html.get('comp_combustible_cargo', ''),
                    'comp_combustible_abono': datos_html.get('comp_combustible_abono', ''),
                    'comp_otros_cargo': datos_html.get('comp_otros_cargo', ''),
                    'comp_otros_abono': datos_html.get('comp_otros_abono', ''),
                    'suma_cargos': datos_html.get('suma_cargos', ''),
                    'suma_abonos': datos_html.get('suma_abonos', ''),
                    'importe_total_comprobacion': datos_html.get('importe_total_comprobacion', ''),
                    'elaboro_nombre': datos_html.get('elaboro_nombre', ''),
                    'elaboro_cargo': datos_html.get('elaboro_cargo', ''),
                    'reviso_nombre': datos_html.get('reviso_nombre', ''),
                    'reviso_cargo': datos_html.get('reviso_cargo', ''),
                    'conforme_nombre': datos_html.get('conforme_nombre', ''),
                    'conforme_cargo': datos_html.get('conforme_cargo', ''),
                    'autoriza_nombre': datos_html.get('autoriza_pago_saldo_nombre', ''),
                    'autoriza_cargo': datos_html.get('autoriza_pago_saldo_cargo', ''),
                    'bueno_por_monto': datos_html.get('bueno_por_monto', ''),
                    'recibi_monto': datos_html.get('recibi_monto', ''),
                    'recibi_letras': datos_html.get('recibi_letras', ''),
                }
                
                if guardar_o_actualizar_pliego(registro):
                    st.success("✅ Pliego guardado exitosamente")
                    st.balloons()
                    if 'folio_actual' in st.session_state:
                        del st.session_state['folio_actual']
                    st.rerun()
                else:
                    st.error("Error al guardar en Excel")
            except Exception as e:
                st.error(f"Error: {e}")
    with col2:
        if st.button("❌ No", use_container_width=True, key="btn_confirmar_guardado_no"):
            st.rerun()

# ----------------------------------------------------------------------------
# MODAL 1.9: NUEVO FUNCIONARIO
# ----------------------------------------------------------------------------
@st.dialog("👤 Nuevo Funcionario")
def modal_configurar_funcionario():
    st.write("Seleccione los funcionarios para las firmas. Puede editar C.P., Teléfono y Área si es necesario.")
    
    usuarios_db = obtener_lista_usuarios()
    
    if not usuarios_db:
        st.warning("No hay usuarios registrados en la base de datos.")
        if st.button("Cerrar", key="btn_cerrar_modal_funcionario"):
            st.rerun()
        return
    
    nombres = [usr.get('nombre', '') for usr in usuarios_db if usr.get('nombre')]
    
    if 'cargos_elaboro' not in st.session_state:
        st.session_state.cargos_elaboro = {}
    if 'cargos_reviso' not in st.session_state:
        st.session_state.cargos_reviso = {}
    if 'cargos_conforme' not in st.session_state:
        st.session_state.cargos_conforme = {}
    if 'cargos_autoriza' not in st.session_state:
        st.session_state.cargos_autoriza = {}
    
    if 'solicitante_categoria' not in st.session_state:
        st.session_state.solicitante_categoria = {}
    if 'solicitante_area' not in st.session_state:
        st.session_state.solicitante_area = {}
    
    tab1, tab2 = st.tabs(["👤 SOLICITANTE", "✍️ FIRMAS"])
    
    with tab1:
        st.subheader("Funcionario Solicitante")
        sel_solicitante = st.selectbox("Elegir funcionario solicitante:", nombres, key="sel_solicitante")
        jefe_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_solicitante), {})
        
        if sel_solicitante not in st.session_state.solicitante_categoria:
            st.session_state.solicitante_categoria[sel_solicitante] = jefe_seleccionado.get('categoria', 'SIN CATEGORÍA')
        if sel_solicitante not in st.session_state.solicitante_area:
            st.session_state.solicitante_area[sel_solicitante] = ""
        
        col1, col2 = st.columns(2)
        with col1:
            cp_default = jefe_seleccionado.get('cp', '')
            cp_editado = st.text_input("C.P. del solicitante:", value=cp_default, key="cp_solicitante")
            tel_default = jefe_seleccionado.get('tel_oficina', '')
            tel_editado = st.text_input("Teléfono Oficina:", value=tel_default, key="tel_solicitante")
        with col2:
            categoria_editada = st.text_input(
                "Categoría:", 
                value=st.session_state.solicitante_categoria[sel_solicitante], 
                key=f"solicitante_categoria_{sel_solicitante}"
            )
            st.session_state.solicitante_categoria[sel_solicitante] = categoria_editada
            departamento_valor = jefe_seleccionado.get('departamento', '')
            st.text_input("Departamento:", value=departamento_valor, disabled=True, key="depto_solicitante")
        
        area_editada = st.text_input(
            "Área solicitante:", 
            value=st.session_state.solicitante_area[sel_solicitante], 
            placeholder="Ej: HOSPITAL GENERAL DE ZONA No. 01", 
            key=f"solicitante_area_{sel_solicitante}"
        )
        st.session_state.solicitante_area[sel_solicitante] = area_editada
    
    with tab2:
        st.subheader("Funcionarios para Firmas")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.markdown("**✍️ ELABORÓ**")
            sel_elaboro = st.selectbox("Seleccionar:", nombres, key="sel_elaboro")
            elaboro_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_elaboro), {})
            if sel_elaboro not in st.session_state.cargos_elaboro:
                st.session_state.cargos_elaboro[sel_elaboro] = elaboro_seleccionado.get('categoria', 'SIN CARGO')
            cargo_elaboro = st.text_input(
                "Cargo de Elaboró:", 
                value=st.session_state.cargos_elaboro[sel_elaboro], 
                key=f"elaboro_{sel_elaboro}"
            )
            st.session_state.cargos_elaboro[sel_elaboro] = cargo_elaboro
        
        with col_f2:
            st.markdown("**✍️ REVISÓ**")
            sel_reviso = st.selectbox("Seleccionar:", nombres, key="sel_reviso")
            reviso_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_reviso), {})
            if sel_reviso not in st.session_state.cargos_reviso:
                st.session_state.cargos_reviso[sel_reviso] = reviso_seleccionado.get('categoria', 'SIN CARGO')
            cargo_reviso = st.text_input(
                "Cargo de Revisó:", 
                value=st.session_state.cargos_reviso[sel_reviso], 
                key=f"reviso_{sel_reviso}"
            )
            st.session_state.cargos_reviso[sel_reviso] = cargo_reviso
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("**✍️ CONFORME**")
            sel_conforme = st.selectbox("Seleccionar:", nombres, key="sel_conforme")
            conforme_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_conforme), {})
            if sel_conforme not in st.session_state.cargos_conforme:
                st.session_state.cargos_conforme[sel_conforme] = conforme_seleccionado.get('categoria', 'SIN CARGO')
            cargo_conforme = st.text_input(
                "Cargo de Conforme:", 
                value=st.session_state.cargos_conforme[sel_conforme], 
                key=f"conforme_{sel_conforme}"
            )
            st.session_state.cargos_conforme[sel_conforme] = cargo_conforme
        
        with col_c2:
            st.markdown("**✍️ AUTORIZA PAGO SALDO**")
            sel_autoriza = st.selectbox("Seleccionar:", nombres, key="sel_autoriza")
            autoriza_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_autoriza), {})
            if sel_autoriza not in st.session_state.cargos_autoriza:
                st.session_state.cargos_autoriza[sel_autoriza] = autoriza_seleccionado.get('categoria', 'SIN CARGO')
            cargo_autoriza = st.text_input(
                "Cargo de Autoriza:", 
                value=st.session_state.cargos_autoriza[sel_autoriza], 
                key=f"autoriza_{sel_autoriza}"
            )
            st.session_state.cargos_autoriza[sel_autoriza] = cargo_autoriza
    
    if st.button("✅ GUARDAR CONFIGURACIÓN DE FIRMAS", type="primary", use_container_width=True, key="btn_guardar_firmas"):
        config_firmas = {
            "solicitante": {
                "nombre": sel_solicitante,
                "categoria": st.session_state.solicitante_categoria.get(sel_solicitante, 'SIN CATEGORÍA'),
                "departamento": departamento_valor,
                "area": st.session_state.solicitante_area.get(sel_solicitante, ''),
                "tel_oficina": tel_editado,
                "cp": cp_editado,
                "matricula": jefe_seleccionado.get('matricula', '')
            },
            "elaboro": {
                "nombre": sel_elaboro,
                "cargo": st.session_state.cargos_elaboro.get(sel_elaboro, 'SIN CARGO'),
                "matricula": elaboro_seleccionado.get('matricula', '')
            },
            "reviso": {
                "nombre": sel_reviso,
                "cargo": st.session_state.cargos_reviso.get(sel_reviso, 'SIN CARGO'),
                "matricula": reviso_seleccionado.get('matricula', '')
            },
            "conforme": {
                "nombre": sel_conforme,
                "cargo": st.session_state.cargos_conforme.get(sel_conforme, 'SIN CARGO'),
                "matricula": conforme_seleccionado.get('matricula', '')
            },
            "autoriza": {
                "nombre": sel_autoriza,
                "cargo": st.session_state.cargos_autoriza.get(sel_autoriza, 'SIN CARGO'),
                "matricula": autoriza_seleccionado.get('matricula', '')
            }
        }
        
        gestionar_config_permanente("firmas", config_firmas)
        st.success("✅ Configuración de firmas guardada")
        st.rerun()

# ----------------------------------------------------------------------------
# MODAL 1.10: REUTILIZAR FOLIO
# ----------------------------------------------------------------------------
@st.dialog("♻️ Reutilizar Folio")
def modal_reutilizar_folio(datos, tipo_doc, u):
    st.warning(f"Reutilizando folio: **{datos.get('folio')}**")
    
    fecha_original = datos.get('fecha_elaboracion', datos.get('fecha_creacion', ''))
    st.info(f"📅 Fecha original del registro: {fecha_original}")
    
    if u.get('rol') == "Administrador":
        fecha_nueva = st.date_input("Fecha del nuevo registro:", value=datetime.now(), key="fecha_reutilizar")
        fecha_str = fecha_nueva.strftime("%d/%m/%Y")
        st.caption("✅ Como administrador, puedes modificar la fecha")
    else:
        fecha_str = datetime.now().strftime("%d/%m/%Y")
        st.write(f"📅 Fecha del nuevo registro: **{fecha_str}**")
        st.caption("ℹ️ La fecha se asignará automáticamente (hoy)")
    
    with st.expander("📋 Datos a reutilizar", expanded=False):
        st.json(datos)
    
    if st.button("✅ CONFIRMAR REUTILIZACIÓN", type="primary", use_container_width=True, key="btn_confirmar_reutilizar"):
        nuevo_registro = datos.copy()
        nuevo_registro['fecha_elaboracion'] = fecha_str
        nuevo_registro['estatus'] = "Programado" if tipo_doc == "Pliego/Informe" else "Programado"
        
        if tipo_doc == "Pliego/Informe":
            if guardar_o_actualizar_pliego(nuevo_registro):
                st.success(f"✅ Pliego {datos.get('folio')} reutilizado")
                st.rerun()
        else:
            if guardar_traslado_local(nuevo_registro):
                st.success(f"✅ Traslado {datos.get('folio')} reutilizado")
                st.rerun()

# ----------------------------------------------------------------------------
# MODAL 1.11: AGREGAR GASTO
# ----------------------------------------------------------------------------
@st.dialog("➕ AGREGAR GASTO")
def modal_agregar_gasto():
    st.write("Complete los datos del gasto")
    
    categoria = st.selectbox("Categoría:", [
        "HOSPEDAJE", "ALIMENTACIÓN", "TRASLADOS", "OTROS VIÁTICOS",
        "AUTOBÚS", "PEAJE", "GASOLINA", "OTROS GASTOS", "SIN COMPROBANTE"
    ], key="gasto_categoria_modal")
    
    col1, col2 = st.columns(2)
    with col1:
        factura = st.text_input("No. Factura:", key="gasto_factura_modal")
        proveedor = st.text_input("Proveedor:", key="gasto_proveedor_modal")
    with col2:
        fecha = st.date_input("Fecha:", value=datetime.now(), key="gasto_fecha_modal")
        importe = st.number_input("Importe ($):", min_value=0.0, step=10.0, format="%.2f", key="gasto_importe_modal")
    
    concepto = None
    justificacion = None
    if categoria == "SIN COMPROBANTE":
        concepto = st.text_input("Concepto:", key="gasto_concepto_modal")
        justificacion = st.text_area("Justificación:", key="gasto_justificacion_modal")
    
    if st.button("✅ GUARDAR GASTO", type="primary", use_container_width=True, key="btn_guardar_gasto_modal"):
        if 'pliego_desglose' not in st.session_state:
            st.error("❌ No se puede guardar: primero debe cargar un pliego")
            return
        
        nuevo_gasto = {
            "factura": factura if categoria != "SIN COMPROBANTE" else "",
            "proveedor": proveedor if categoria != "SIN COMPROBANTE" else "",
            "fecha": fecha.strftime("%d/%m/%Y"),
            "importe": importe,
            "concepto": concepto,
            "justificacion": justificacion
        }
        
        if categoria == "SIN COMPROBANTE" and (not concepto or not justificacion):
            st.error("Concepto y justificación son obligatorios para gastos sin comprobante.")
            return
        
        st.session_state['gastos_desglose'][categoria].append(nuevo_gasto)
        st.success(f"✅ Gasto agregado a {categoria}")
        st.rerun()


# ============================================================================
# SECCIÓN 2: VISTAS PRINCIPALES
# ============================================================================

# ----------------------------------------------------------------------------
# VISTA 2.1: PLIEGO DE COMISIÓN
# ----------------------------------------------------------------------------
def vista_pliego(u):
    st.title("📋 Gestión de Pliego de Comisión")
    
    df_p = obtener_pliegos()
    
    func_fijo = gestionar_config_permanente("funcionario")
    if func_fijo:
        u.update({
            "f_solicitante": func_fijo.get('nombre', ''),
            "f_categoria": func_fijo.get('categoria', ''),
            "f_tel": func_fijo.get('tel_oficina', ''),
            "f_cp": func_fijo.get('cp', '')
        })
    
    firmas_config = gestionar_config_permanente("firmas")
    if firmas_config:
        u.update({
            "f_solicitante": firmas_config.get('solicitante', {}).get('nombre', u.get('f_solicitante', '')),
            "f_categoria": firmas_config.get('solicitante', {}).get('categoria', u.get('f_categoria', '')),
            "f_tel": firmas_config.get('solicitante', {}).get('tel_oficina', u.get('f_tel', '')),
            "f_cp": firmas_config.get('solicitante', {}).get('cp', u.get('f_cp', '')),
            "elaboro_nombre": firmas_config.get('elaboro', {}).get('nombre', ''),
            "elaboro_cargo": firmas_config.get('elaboro', {}).get('cargo', ''),
            "reviso_nombre": firmas_config.get('reviso', {}).get('nombre', ''),
            "reviso_cargo": firmas_config.get('reviso', {}).get('cargo', ''),
            "conforme_nombre": firmas_config.get('conforme', {}).get('nombre', ''),
            "conforme_cargo": firmas_config.get('conforme', {}).get('cargo', ''),
            "autoriza_nombre": firmas_config.get('autoriza', {}).get('nombre', ''),
            "autoriza_cargo": firmas_config.get('autoriza', {}).get('cargo', '')
        })
    
    with st.expander("🔍 BUSCAR PLIEGO EN HISTORIAL", expanded=False):
        if not df_p.empty and 'folio' in df_p.columns:
            if u.get('rol') == "Administrador":
                opciones = df_p['folio'].unique().tolist()
            else:
                opciones = df_p[df_p['matricula'] == u.get('matricula')]['folio'].unique().tolist()
            
            sel_busqueda = st.selectbox("Cargar registro anterior:", ["-- Seleccionar --"] + opciones, key="selector_historial_pliego")
            if sel_busqueda != "-- Seleccionar --":
                reg = df_p[df_p['folio'] == sel_busqueda].iloc[0].to_dict()
                u.update(reg)
                st.session_state['folio_actual'] = sel_busqueda
                st.success(f"Pliego {sel_busqueda} cargado.")
    
    folio_config = "F001/2026"
    try:
        if os.path.exists(DB_FILE):
            df_conf = pd.read_excel(DB_FILE, sheet_name='config_admin')
            if not df_conf.empty and 'folio_inicial_sistema' in df_conf.columns:
                folio_config = str(df_conf.iloc[0]['folio_inicial_sistema'])
    except:
        pass
    
    if df_p.empty and u.get('rol') == "Administrador":
        with st.container(border=True):
            st.subheader("⚙️ Configuración de Folios Foráneos")
            st.info(f"Folio inicial configurado: **{folio_config}**")
            st.caption("Los folios se generarán automáticamente: F002/2026, F003/2026...")
    
    f_id = st.session_state.get('folio_actual', u.get('folio', '---'))
    st.subheader(f"📄 Folio: {f_id}")
    
    fecha_actual = datetime.now()
    grupo_jerarquico = u.get('gj', '')
    tipo_contrato = u.get('tipo_contrato', '')
    departamento = u.get('departamento', '')
    
    fecha_inicio = u.get('fecha_inicio', fecha_actual.strftime("%d/%m/%Y"))
    fecha_fin = u.get('fecha_fin', fecha_actual.strftime("%d/%m/%Y"))
    
    fecha_inicio = st.session_state.get('nuevo_fecha_inicio', fecha_inicio)
    fecha_fin = st.session_state.get('nuevo_fecha_fin', fecha_fin)
    transporte = st.session_state.get('nuevo_transporte', u.get('medio_transporte', ''))
    chofer = st.session_state.get('nuevo_chofer', u.get('chofer', ''))
    acompanante = st.session_state.get('nuevo_acompanante', u.get('acompañante', ''))
    area_solicitante = st.session_state.get('nuevo_area', u.get('f_area', ''))
    
    anticipos = {
        'anticipo_viaticos': u.get('anticipo_viaticos', '0.00'),
        'anticipo_gasolina': u.get('anticipo_gasolina', '0.00'),
        'anticipo_peaje': u.get('anticipo_peaje', '0.00'),
        'anticipo_transporte_t': u.get('anticipo_transporte_t', '0.00'),
        'anticipo_avion': u.get('anticipo_avion', '0.00'),
        'total_anticipo': u.get('total_anticipo', '0.00'),
        'subtotal_sin_avion': u.get('subtotal_sin_avion', '0.00')
    }
    
    comprobaciones = {
        'comp_hospedaje_cargo': u.get('comp_hospedaje_cargo', ''),
        'comp_hospedaje_abono': u.get('comp_hospedaje_abono', ''),
        'comp_alimentos_cargo': u.get('comp_alimentos_cargo', ''),
        'comp_alimentos_abono': u.get('comp_alimentos_abono', ''),
        'comp_pasajes_cargo': u.get('comp_pasajes_cargo', ''),
        'comp_pasajes_abono': u.get('comp_pasajes_abono', ''),
        'comp_combustible_cargo': u.get('comp_combustible_cargo', ''),
        'comp_combustible_abono': u.get('comp_combustible_abono', ''),
        'comp_otros_cargo': u.get('comp_otros_cargo', ''),
        'comp_otros_abono': u.get('comp_otros_abono', ''),
        'suma_cargos': u.get('suma_cargos', ''),
        'suma_abonos': u.get('suma_abonos', ''),
        'importe_total_comprobacion': u.get('importe_total_comprobacion', '')
    }
    
    firmas = {
        'elaboro_nombre': u.get('elaboro_nombre', ''),
        'elaboro_cargo': u.get('elaboro_cargo', ''),
        'reviso_nombre': u.get('reviso_nombre', ''),
        'reviso_cargo': u.get('reviso_cargo', ''),
        'conforme_nombre': u.get('conforme_nombre', ''),
        'conforme_cargo': u.get('conforme_cargo', ''),
        'autoriza_pago_saldo_nombre': u.get('autoriza_nombre', ''),
        'autoriza_pago_saldo_cargo': u.get('autoriza_cargo', ''),
        'bueno_por_monto': u.get('bueno_por_monto', ''),
        'recibi_monto': u.get('total_anticipo', ''),
        'recibi_letras': u.get('recibi_letras', '')
    }
    
    if st.session_state.get('nuevo_nombre_externo'):
        nombre_empleado = st.session_state['nuevo_nombre_externo']
        matricula = st.session_state['nuevo_matricula_externo']
        categoria_empleado = st.session_state.get('nuevo_categoria_externo', 'SIN CATEGORÍA')
    else:
        nombre_empleado = u.get('nombre', '').upper()
        matricula = u.get('matricula', '')
        categoria_empleado = u.get('categoria', 'SIN CATEGORÍA')
    
    bueno_por_monto = st.session_state.get('nuevo_bueno_por', u.get('bueno_por_monto', ''))
    recibi_monto = st.session_state.get('nuevo_recibi', u.get('recibi_monto', ''))
    recibi_letras = st.session_state.get('nuevo_recibi_letras', u.get('recibi_letras', ''))
    
    datos_html = {
        "m_folio": f_id,
        "m_fecha_creacion": fecha_actual.strftime("%d/%m/%Y"),
        "logo_base64": get_base64("assets/logoimss.png"),
        "nombre_empleado": nombre_empleado,
        "matricula": matricula,
        "categoria_empleado": categoria_empleado,
        "departamento_empleado": departamento,
        "grupo_jerarquico": grupo_jerarquico,
        "tipo_contrato": tipo_contrato,
        "f_solicitante": str(u.get('f_solicitante', '')).upper(),
        "f_categoria": str(u.get('f_categoria', '')).upper(),
        "f_area": str(area_solicitante).upper(),
        "f_tel": str(u.get('f_tel', '')),
        "f_cp": str(u.get('f_cp', '')),
        "m_paciente": st.session_state.get('nuevo_paciente', u.get('paciente', '')),
        "nss": st.session_state.get('nuevo_nss', u.get('nss', '')),
        "m_destino": st.session_state.get('nuevo_destino', u.get('m_destino', '')),
        "m_objeto": st.session_state.get('nuevo_motivo', u.get('m_objeto', '')),
        "m_inicio": fecha_inicio,
        "m_fin": fecha_fin,
        "m_medio_transporte": transporte,
        "m_chofer": chofer,
        "m_acompañante": acompanante,
        "dias_comision": u.get('dias_comision', ''),
        **anticipos,
        "observaciones": u.get('observaciones', ''),
        **comprobaciones,
        **firmas,
        "bueno_por_monto": bueno_por_monto,
        "recibi_monto": recibi_monto,
        "recibi_letras": recibi_letras,
        "mostrar_bloque_especial": u.get('mostrar_bloque_especial', False),
        "rol_usuario": u.get('rol', 'Usuario')
    }
    
    st.divider()
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        if st.button("🖨️ IMPRIMIR", use_container_width=True, type="primary", key="btn_imprimir_pliego"):
            with open("templates/pliego_template.html", "r", encoding="utf-8") as f:
                t = Template(f.read())
                html_content = t.render(datos_html)
            
            html_impresion = f"""
            <html>
            <head>
                <style>
                    @media print {{
                        body {{ margin: 0; padding: 0; }}
                        .page {{ page-break-after: always; }}
                    }}
                </style>
            </head>
            <body>
                {html_content}
                <script>
                    window.onload = function() {{
                        window.print();
                    }};
                </script>
            </body>
            </html>
            """
            st.components.v1.html(html_impresion, height=800, scrolling=True)
    
    with col2:
        if st.button("➕ NUEVO TRASLADO", use_container_width=True, type="primary", key="btn_nuevo_traslado"):
            modal_nuevo_traslado(u, df_p)
    
    with col3:
        if u.get('rol') == "Administrador":
            if st.button("👤 NUEVO FUNCIONARIO", use_container_width=True, key="btn_nuevo_funcionario"):
                modal_configurar_funcionario()
        else:
            st.button("👤 NUEVO FUNCIONARIO", use_container_width=True, disabled=True, key="btn_nuevo_funcionario_disabled")
    
    with col4:
        st.markdown("")
    
    try:
        with open("templates/pliego_template.html", "r", encoding="utf-8") as f:
            t = Template(f.read())
            st.components.v1.html(t.render(datos_html), height=1000, scrolling=True)
    except Exception as e:
        st.warning(f"Cargando vista previa... {e}")
    
    if st.button("💾 FINALIZAR Y GUARDAR EN EXCEL", use_container_width=True, type="secondary", key="btn_guardar_pliego"):
        motivo = st.session_state.get('nuevo_motivo', u.get('m_objeto', ''))
        if not motivo:
            st.error("Faltan campos obligatorios.")
        else:
            modal_confirmar_guardado(datos_html, u)

# ----------------------------------------------------------------------------
# VISTA 2.2: TRASLADOS LOCALES (DÍA)
# ----------------------------------------------------------------------------
def vista_traslados_dia(u):
    st.header("🚑 Gestión de Traslados Locales")
    
    asegurar_hojas_excel()
    
    try:
        df_traslados = obtener_traslados_locales()
        df_vehiculos = pd.DataFrame(obtener_vehiculos())
        
        with st.expander("🔍 Buscar por Folio o Paciente", expanded=False):
            col_bus1, col_bus2 = st.columns([3, 1])
            with col_bus1:
                busqueda = st.text_input("", placeholder="Ingrese folio o nombre del paciente", key="buscador_traslados")
            with col_bus2:
                if st.button("🔍 Buscar", use_container_width=True):
                    st.session_state.busqueda_actual = busqueda
                    st.rerun()
        
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        fecha_mañana = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        
        if not df_traslados.empty and 'fecha_traslado' in df_traslados.columns:
            traslados_mañana = df_traslados[df_traslados['fecha_traslado'] == fecha_mañana]
            if not traslados_mañana.empty:
                st.info(f"📅 **{len(traslados_mañana)} traslado(s) programado(s) para MAÑANA ({fecha_mañana})**")
        
        if 'seleccionados' not in st.session_state:
            st.session_state.seleccionados = []
        
        st.subheader(f"📋 Traslados del día {fecha_hoy}")
        
        if not df_traslados.empty and 'fecha_traslado' in df_traslados.columns:
            df_hoy = df_traslados[df_traslados['fecha_traslado'] == fecha_hoy].copy()
            
            if 'busqueda_actual' in st.session_state and st.session_state.busqueda_actual:
                busq = st.session_state.busqueda_actual.lower()
                df_hoy = df_hoy[
                    df_hoy['folio'].str.lower().str.contains(busq, na=False) | 
                    df_hoy['paciente'].str.lower().str.contains(busq, na=False)
                ]
            
            if not df_hoy.empty:
                turnos = ["MATUTINO", "VESPERTINO", "NOCTURNO"]
                
                for turno in turnos:
                    df_turno = df_hoy[df_hoy['turno'] == turno].copy()
                    
                    if not df_turno.empty:
                        with st.expander(f"🕒 {turno} ({len(df_turno)} traslados)", expanded=True):
                            col_h1, col_h2, col_h3, col_h4, col_h5, col_h6, col_h7 = st.columns([1, 2, 2, 2, 2, 1.5, 1.5])
                            with col_h1: st.markdown("**✅**")
                            with col_h2: st.markdown("**Folio**")
                            with col_h3: st.markdown("**Paciente**")
                            with col_h4: st.markdown("**Destino**")
                            with col_h5: st.markdown("**Asignado**")
                            with col_h6: st.markdown("**Estatus**")
                            with col_h7: st.markdown("**Acción**")
                            
                            for idx, row in df_turno.iterrows():
                                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 2, 2, 2, 2, 1.5, 1.5])
                                
                                with col1:
                                    if row.get('estatus') == "Programado" and (pd.isna(row.get('empleado_comisionado')) or row.get('empleado_comisionado') == 'Sin asignar'):
                                        checked = row.get('folio') in st.session_state.seleccionados
                                        if st.checkbox("", value=checked, key=f"chk_{row.get('folio')}_{turno}_{idx}"):
                                            if row.get('folio') not in st.session_state.seleccionados:
                                                st.session_state.seleccionados.append(row.get('folio'))
                                        else:
                                            if row.get('folio') in st.session_state.seleccionados:
                                                st.session_state.seleccionados.remove(row.get('folio'))
                                
                                with col2:
                                    st.write(row.get('folio', ''))
                                with col3:
                                    st.write(row.get('paciente', '')[:20])
                                with col4:
                                    st.write(row.get('destino', '')[:20])
                                with col5:
                                    emp = row.get('empleado_comisionado', '')
                                    if emp and emp != 'Sin asignar':
                                        st.write(emp[:20])
                                    else:
                                        st.write("—")
                                with col6:
                                    estatus = row.get('estatus', '')
                                    if estatus == "Programado":
                                        st.markdown("🟡")
                                    elif estatus == "En Curso":
                                        st.markdown("🔵")
                                    elif estatus == "Completado":
                                        st.markdown("✅")
                                    else:
                                        st.markdown("⚪")
                                with col7:
                                    if st.button("👁️", key=f"btn_ver_{row.get('folio')}_{idx}"):
                                        modal_ver_detalles_traslado(row.to_dict(), u)
                                
                                if u.get('rol') != "Administrador" and row.get('estatus') == "Programado" and (pd.isna(row.get('empleado_comisionado')) or row.get('empleado_comisionado') == 'Sin asignar'):
                                    if st.button("👤 Tomar", key=f"btn_tomar_{row.get('folio')}_{idx}"):
                                        modal_tomar_traslado(row.to_dict(), u)
                                
                                if u.get('rol') != "Administrador" and row.get('estatus') == "En Curso" and u.get('nombre') in str(row.get('empleado_comisionado', '')):
                                    if st.button("✅ Cerrar", key=f"btn_cerrar_{row.get('folio')}_{idx}"):
                                        modal_cerrar_traslado(row.to_dict())
                                
                                st.divider()
                
                if st.session_state.seleccionados:
                    st.info(f"📌 **{len(st.session_state.seleccionados)}** traslado(s) seleccionado(s)")
                    col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 2])
                    with col_sel1:
                        if st.button("🗂️ ASIGNAR SELECCIONADOS", type="primary", use_container_width=True):
                            st.session_state.asignar_folios = st.session_state.seleccionados
                            modal_asignar_traslados(u, df_vehiculos)
                    with col_sel2:
                        if st.button("❌ LIMPIAR SELECCIÓN", use_container_width=True):
                            st.session_state.seleccionados = []
                            st.rerun()
            else:
                st.info("No se encontraron traslados con los filtros actuales")
        else:
            st.info("No hay traslados registrados")
        
        if u.get('rol') == "Administrador":
            st.subheader("📝 Nuevo Registro de Traslado")
            col_sugerir1, col_sugerir2, col_sugerir3 = st.columns([1, 1, 2])
            with col_sugerir1:
                if st.button("🔄 Sugerir siguiente folio LOCAL", use_container_width=True, key="btn_sugerir_local_unique"):
                    st.session_state.folio_manual = sugerir_siguiente_folio(df_traslados, "L")
                    st.rerun()
            with col_sugerir2:
                st.caption(f"Año actual: {datetime.now().year}")
            st.divider()
            
            with st.form("form_traslado_completo_admin"):
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    folio_sugerido = sugerir_siguiente_folio(df_traslados, "L")
                    folio_default = st.session_state.get('folio_manual', folio_sugerido)
                    folio = st.text_input(
                        "Folio", 
                        value=folio_default,
                        placeholder="Ej: L001/2026",
                        key="input_folio_local_form_admin"
                    )
                    st.session_state.folio_manual = folio
                    
                    fecha_creacion = st.text_input(
                        "Fecha de Creación", 
                        value=datetime.now().strftime("%d/%m/%Y"), 
                        disabled=True,
                        key="fecha_creacion_admin"
                    )
                    
                    fecha_traslado = st.date_input(
                        "Fecha del Traslado", 
                        value=datetime.now(),
                        key="fecha_traslado_admin"
                    )
                    
                    p_nom = st.text_input("Paciente", value=st.session_state.get('p_nombre', ''), key="paciente_admin")
                    st.session_state.p_nombre = p_nom
                    nss_in = st.text_input("NSS", value=st.session_state.get('p_nss', ''), key="nss_admin")
                    st.session_state.p_nss = nss_in
                    domicilio = st.text_input("Domicilio", value=st.session_state.get('p_domicilio', ''), key="domicilio_admin")
                    st.session_state.p_domicilio = domicilio
                    telefono = st.text_input("Teléfono", value=st.session_state.get('p_telefono', ''), key="telefono_admin")
                    st.session_state.p_telefono = telefono
                
                with c2:
                    destino = st.text_input(
                        "Destino", 
                        value=st.session_state.get('p_destino', ''), 
                        key="destino_admin"
                    )
                    st.session_state.p_destino = destino
                    
                    servicio = st.text_input(
                        "Servicio / Motivo", 
                        value=st.session_state.get('p_servicio', ''), 
                        key="servicio_admin"
                    )
                    st.session_state.p_servicio = servicio
                    
                    f_h_mov = st.datetime_input(
                        "Fecha/Hora Movimiento", 
                        value=datetime.now(), 
                        key="fecha_hora_admin"
                    )
                
                with c3:
                    cama = st.text_input(
                        "Número de Cama", 
                        value=st.session_state.get('p_cama', ''), 
                        key="cama_admin"
                    )
                    st.session_state.p_cama = cama
                    
                    opciones_req = ["Ninguno", "Oxígeno", "Incubadora", "Camilla", "Silla de Ruedas", "Otro"]
                    req_default = st.session_state.get('p_requiere', 'Ninguno')
                    req_index = opciones_req.index(req_default) if req_default in opciones_req else 0
                    
                    requiere = st.selectbox(
                        "Requiere", 
                        opciones_req, 
                        index=req_index,
                        key="requiere_admin"
                    )
                    st.session_state.p_requiere = requiere
                    
                    estatus_opciones = ["Programado", "En Curso", "Completado", "Cancelado"]
                    estatus_default = st.session_state.get('p_estatus', 'Programado')
                    estatus_index = estatus_opciones.index(estatus_default) if estatus_default in estatus_opciones else 0
                    
                    estatus = st.selectbox(
                        "Estatus del Traslado", 
                        estatus_opciones, 
                        index=estatus_index, 
                        key="estatus_admin"
                    )
                    st.session_state.p_estatus = estatus
                    
                    observaciones = st.text_area(
                        "Observaciones Adicionales", 
                        value=st.session_state.get('p_observaciones', ''), 
                        height=100, 
                        key="observaciones_admin"
                    )
                    st.session_state.p_observaciones = observaciones
                
                if st.form_submit_button("💾 GUARDAR REGISTRO", type="primary", use_container_width=True):
                    nuevo = {
                        "folio": folio,
                        "fecha_creacion": fecha_creacion,
                        "fecha_traslado": fecha_traslado.strftime("%d/%m/%Y"),
                        "turno": obtener_turno_por_hora(),
                        "paciente": p_nom.upper(),
                        "nss": nss_in,
                        "domicilio": domicilio,
                        "telefono": telefono,
                        "fecha_hora": f_h_mov.strftime("%Y-%m-%d %H:%M"),
                        "empleado_comisionado": "Sin asignar",
                        "destino": destino.upper(),
                        "servicio": servicio.upper() if servicio else "",
                        "cama": cama,
                        "requiere": requiere,
                        "estatus": estatus,
                        "observaciones": observaciones,
                        "matricula_admin": u.get('matricula', '')
                    }
                    
                    if guardar_traslado_local(nuevo):
                        st.success(f"✅ Traslado {folio} registrado con éxito.")
                        for key in ['folio_manual', 'p_nombre', 'p_nss', 'p_domicilio', 'p_telefono', 'p_destino', 'p_servicio', 
                                   'p_cama', 'p_requiere', 'p_estatus', 'p_observaciones']:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(f"Error crítico al escribir en Excel")
    
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.exception(e)

# ----------------------------------------------------------------------------
# VISTA 2.3: TRASLADOS PROGRAMADOS (FUTUROS - SOLO ADMIN)
# ----------------------------------------------------------------------------
def vista_traslados_programados(u):
    st.header("📅 Traslados Programados (Futuros)")
    
    asegurar_hojas_excel()
    
    try:
        df_traslados = obtener_traslados_locales()
        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            fecha_desde = st.date_input("Desde", value=datetime.now() + timedelta(days=1), key="prog_desde")
        with col_f2:
            fecha_hasta = st.date_input("Hasta", value=datetime.now() + timedelta(days=7), key="prog_hasta")
        with col_f3:
            turno_filtro = st.selectbox("Turno", ["Todos", "MATUTINO", "VESPERTINO", "NOCTURNO"], key="prog_turno")
        
        if not df_traslados.empty and 'fecha_traslado' in df_traslados.columns:
            df_futuros = df_traslados[pd.to_datetime(df_traslados['fecha_traslado'], format='%d/%m/%Y', errors='coerce') > 
                                      pd.to_datetime(fecha_hoy, format='%d/%m/%Y')].copy()
            
            fecha_desde_str = fecha_desde.strftime("%d/%m/%Y")
            fecha_hasta_str = fecha_hasta.strftime("%d/%m/%Y")
            
            mask_fecha = (df_futuros['fecha_traslado'] >= fecha_desde_str) & (df_futuros['fecha_traslado'] <= fecha_hasta_str)
            df_futuros = df_futuros[mask_fecha]
            
            if turno_filtro != "Todos":
                df_futuros = df_futuros[df_futuros['turno'] == turno_filtro]
            
            if not df_futuros.empty:
                for fecha in sorted(df_futuros['fecha_traslado'].unique()):
                    df_fecha = df_futuros[df_futuros['fecha_traslado'] == fecha].copy()
                    
                    with st.expander(f"📅 {fecha} ({len(df_fecha)} traslados)", expanded=False):
                        col_h1, col_h2, col_h3, col_h4, col_h5, col_h6 = st.columns([1.5, 2, 2, 1.5, 2, 1])
                        with col_h1: st.markdown("**Folio**")
                        with col_h2: st.markdown("**Paciente**")
                        with col_h3: st.markdown("**Destino**")
                        with col_h4: st.markdown("**Turno**")
                        with col_h5: st.markdown("**Asignado**")
                        with col_h6: st.markdown("**Ver**")
                        
                        for idx, row in df_fecha.iterrows():
                            col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 2, 1.5, 2, 1])
                            
                            with col1:
                                st.write(row.get('folio', ''))
                            with col2:
                                st.write(row.get('paciente', '')[:20])
                            with col3:
                                st.write(row.get('destino', '')[:20])
                            with col4:
                                st.write(row.get('turno', ''))
                            with col5:
                                emp = row.get('empleado_comisionado', '')
                                st.write(emp if emp and emp != 'Sin asignar' else '—')
                            with col6:
                                if st.button("👁️", key=f"btn_prog_{row.get('folio')}_{idx}"):
                                    modal_ver_detalles_traslado(row.to_dict(), u)
                            
                            st.divider()
            else:
                st.info("No hay traslados programados en el rango seleccionado")
        else:
            st.info("No hay traslados registrados")
    
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        st.exception(e)

# ----------------------------------------------------------------------------
# VISTA 2.4: HISTORIAL MAESTRO
# ----------------------------------------------------------------------------
def vista_historial_maestro(u):
    st.header("📊 Centro de Control de Registros")
    
    asegurar_hojas_excel()
    
    try:
        df_p = obtener_pliegos()
        df_t = obtener_traslados_locales()
        
        if not df_p.empty:
            df_p['tipo_doc'] = "Pliego/Informe"
            df_p['sujeto'] = df_p.apply(lambda row: row.get('nombre', '') or row.get('paciente', ''), axis=1)
            df_p['estatus_display'] = df_p.get('estatus_pliego', 'Programado')
        
        if not df_t.empty:
            df_t['tipo_doc'] = "Traslado Local"
            df_t['sujeto'] = df_t.get('paciente', '')
            df_t['estatus_display'] = df_t.get('estatus', 'Programado')
            df_t['fecha_elaboracion'] = df_t.get('fecha_creacion', '')
        
        if not df_p.empty and not df_t.empty:
            df_unificado = pd.concat([df_p, df_t], ignore_index=True)
        elif not df_p.empty:
            df_unificado = df_p.copy()
        elif not df_t.empty:
            df_unificado = df_t.copy()
        else:
            df_unificado = pd.DataFrame()
        
        if not df_unificado.empty and 'folio' in df_unificado.columns:
            duplicados = df_unificado[df_unificado.duplicated(subset=['folio'], keep=False)]
            if not duplicados.empty:
                st.warning(f"⚠️ Se encontraron folios duplicados. Mostrando solo la primera ocurrencia.")
                df_unificado = df_unificado.drop_duplicates(subset=['folio'], keep='first')
        
        if not df_unificado.empty and 'fecha_elaboracion' in df_unificado.columns:
            df_unificado = df_unificado.sort_values(by="fecha_elaboracion", ascending=False)
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
            with c1:
                busqueda = st.text_input("🔍 Buscar por Folio, Sujeto o NSS", key="bus_uni_historial")
            with c2:
                fecha_desde = st.date_input("Fecha desde", value=datetime.now() - timedelta(days=30), key="fecha_desde")
            with c3:
                fecha_hasta = st.date_input("Fecha hasta", value=datetime.now(), key="fecha_hasta")
            with c4:
                tipo_filtro = st.selectbox("Tipo", ["Todos", "Pliegos", "Traslados"], key="tipo_filtro_historial")
                status_filtro = st.selectbox("Estatus", ["Todos", "Programado", "En Curso", "Completado", "Cancelado"], key="status_filtro_historial")
        
        df_filtrado = df_unificado.copy()
        if not df_filtrado.empty:
            if busqueda:
                df_filtrado = df_filtrado[df_filtrado.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
            
            if 'fecha_elaboracion' in df_filtrado.columns:
                df_filtrado['fecha_dt'] = pd.to_datetime(df_filtrado['fecha_elaboracion'], format='%d/%m/%Y', errors='coerce')
                mask_fecha = (df_filtrado['fecha_dt'] >= pd.Timestamp(fecha_desde)) & (df_filtrado['fecha_dt'] <= pd.Timestamp(fecha_hasta))
                df_filtrado = df_filtrado[mask_fecha]
            
            if tipo_filtro == "Pliegos" and 'tipo_doc' in df_filtrado.columns: 
                df_filtrado = df_filtrado[df_filtrado['tipo_doc'] == "Pliego/Informe"]
            if tipo_filtro == "Traslados" and 'tipo_doc' in df_filtrado.columns: 
                df_filtrado = df_filtrado[df_filtrado['tipo_doc'] == "Traslado Local"]
            if status_filtro != "Todos" and 'estatus_display' in df_filtrado.columns: 
                df_filtrado = df_filtrado[df_filtrado['estatus_display'] == status_filtro]
        
        st.divider()
        col_acc1, col_acc2, col_acc3, col_acc4 = st.columns([1, 1, 2, 2])
        
        with col_acc1:
            if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key="btn_guardar_cambios_arriba"):
                if 'df_editado' in st.session_state:
                    actualizar_base_datos_maestra(st.session_state.df_editado)
                    st.success("✅ Base de datos actualizada.")
                    st.rerun()
                else:
                    st.warning("No hay cambios para guardar")
        
        with col_acc2:
            if st.button("🔄 Refrescar", use_container_width=True, key="btn_refrescar"):
                st.rerun()
        
        with col_acc3:
            if 'folio' in df_filtrado.columns and not df_filtrado.empty:
                folios_list = df_filtrado['folio'].unique().tolist()
                folio_a_clonar = st.selectbox(
                    "📋 Folio a reutilizar:", 
                    ["-- Seleccionar --"] + folios_list, 
                    key="folio_a_clonar_arriba"
                )
        
        with col_acc4:
            if folio_a_clonar and folio_a_clonar != "-- Seleccionar --":
                if st.button("♻️ REUTILIZAR FOLIO", use_container_width=True, key="btn_reutilizar_arriba"):
                    datos_completos = df_filtrado[df_filtrado['folio'] == folio_a_clonar].iloc[0].to_dict()
                    tipo = datos_completos.get('tipo_doc', '')
                    modal_reutilizar_folio(datos_completos, tipo, u)
        
        st.divider()
        st.subheader("📋 Registros del Sistema")
        
        if not df_filtrado.empty:
            registros_por_pagina = 10
            total_registros = len(df_filtrado)
            total_paginas = (total_registros + registros_por_pagina - 1) // registros_por_pagina
            
            col_page1, col_page2 = st.columns([1, 3])
            with col_page1:
                pagina = st.number_input(
                    "Página", 
                    min_value=1, 
                    max_value=total_paginas, 
                    value=1,
                    key="pagina_historial"
                )
            with col_page2:
                st.write(f"Total: {total_registros} registros")
            
            inicio = (pagina - 1) * registros_por_pagina
            fin = min(inicio + registros_por_pagina, total_registros)
            
            df_pagina = df_filtrado.iloc[inicio:fin].copy()
            
            for idx, row in df_pagina.iterrows():
                with st.container():
                    col_r1, col_r2, col_r3, col_r4, col_r5, col_r6, col_r7 = st.columns([1.5, 2, 2, 1.5, 1.5, 1, 1])
                    
                    with col_r1:
                        st.write(row.get('fecha_elaboracion', '')[:10] if row.get('fecha_elaboracion') else '')
                    with col_r2:
                        st.write(row.get('folio', ''))
                    with col_r3:
                        sujeto = row.get('sujeto', '')
                        st.write(sujeto[:30] + '...' if len(str(sujeto)) > 30 else sujeto)
                    with col_r4:
                        st.write(row.get('tipo_doc', ''))
                    with col_r5:
                        estatus = row.get('estatus_display', '')
                        if estatus == "Programado":
                            st.markdown("🟡 Programado")
                        elif estatus == "En Curso":
                            st.markdown("🔵 En Curso")
                        elif estatus == "Completado":
                            st.markdown("✅ Completado")
                        elif estatus == "Cancelado":
                            st.markdown("❌ Cancelado")
                        else:
                            st.write(estatus)
                    with col_r6:
                        if st.button("👁️", key=f"btn_detalle_{row.get('folio', idx)}"):
                            if row.get('tipo_doc') == "Traslado Local":
                                modal_ver_detalles_traslado(row.to_dict(), u)
                            else:
                                modal_ver_detalles_pliego(row.to_dict(), u)
                    with col_r7:
                        if st.button("📋", key=f"btn_editar_{row.get('folio', idx)}"):
                            st.session_state['folio_actual'] = row.get('folio')
                            st.rerun()
                    
                    st.divider()
            
            st.caption(f"Mostrando registros {inicio+1} a {fin} de {total_registros}")
        else:
            st.info("No hay registros para mostrar")
    
    except Exception as e:
        st.error(f"Error al cargar historial: {e}")
        with st.expander("Ver detalles del error"):
            st.write(f"Tipo de error: {type(e).__name__}")
            st.exception(e)


# ============================================================================
# SECCIÓN 3: VISTAS DE CONFIGURACIÓN Y ESTADÍSTICAS
# ============================================================================

# ----------------------------------------------------------------------------
# VISTA 3.1: CONFIGURACIÓN GENERAL (Usuarios, Vehículos, Hospitales)
# ----------------------------------------------------------------------------
def vista_configuracion():
    st.subheader("⚙️ Configuración del Sistema")
    
    t1, t2, t3 = st.tabs(["👤 Usuarios", "🚗 Vehículos", "🏥 Hospitales"])
    
    with t1:
        try:
            xls = pd.ExcelFile(DB_FILE)
            df_usuarios = pd.read_excel(xls, sheet_name='usuarios').fillna("")
            hojas_restantes = {s: pd.read_excel(xls, s) for s in xls.sheet_names if s != 'usuarios'}
        except:
            df_usuarios = pd.DataFrame(columns=["matricula","nombre","apellido_p","apellido_m","curp","rfc","departamento","tipo_contrato","gj","categoria","password","rol","estatus"])
            hojas_restantes = {}
        
        with st.popover("➕ Registrar Nuevo Usuario"):
            with st.form("f_u", clear_on_submit=True):
                c1, c2 = st.columns(2)
                mat = c1.text_input("Matrícula", key="reg_matricula")
                nom = c2.text_input("Nombre(s)", key="reg_nombre")
                ap_p = c1.text_input("Apellido Paterno", key="reg_ap_p")
                ap_m = c2.text_input("Apellido Materno", key="reg_ap_m")
                curp = c1.text_input("CURP", key="reg_curp")
                rfc = c2.text_input("RFC", key="reg_rfc")
                c3, c4, c5 = st.columns(3)
                depto = c3.text_input("Departamento", key="reg_depto")
                tipoc = c4.text_input("Tipo de Contrato", key="reg_tipoc")
                gj = c5.text_input("G-J", key="reg_gj")
                categoria = c1.text_input("Categoría", key="reg_categoria")
                pas = c2.text_input("Contraseña", type="password", key="reg_password")
                rol = c1.selectbox("Rol", ["Usuario", "Administrador"], key="reg_rol")
                est = c2.selectbox("Estatus", ["Alta", "Baja", "Baja Temporal"], key="reg_estatus")
                
                if st.form_submit_button("Guardar Usuario", use_container_width=True):
                    if mat and nom and pas:
                        nueva = {
                            "matricula": mat, 
                            "nombre": nom, 
                            "apellido_p": ap_p, 
                            "apellido_m": ap_m, 
                            "curp": curp, 
                            "rfc": rfc, 
                            "departamento": depto, 
                            "tipo_contrato": tipoc, 
                            "gj": gj, 
                            "categoria": categoria, 
                            "password": pas, 
                            "rol": rol, 
                            "estatus": est
                        }
                        df_usuarios = pd.concat([df_usuarios, pd.DataFrame([nueva])], ignore_index=True)
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_usuarios.to_excel(writer, sheet_name='usuarios', index=False)
                            for n, d in hojas_restantes.items(): 
                                d.to_excel(writer, sheet_name=n, index=False)
                        st.success("✅ Usuario registrado")
                        st.rerun()
        
        st.write("### Personal Registrado")
        cols_mostrar = [c for c in df_usuarios.columns if c != 'password']
        st.dataframe(df_usuarios[cols_mostrar], use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 🔑 Editar Usuario / Contraseña")
        mat_edit = st.text_input("Matrícula a buscar para editar", key="mat_edit")
        if mat_edit:
            df_usuarios['matricula'] = df_usuarios['matricula'].astype(str).str.replace(r'\.0$', '', regex=True)
            idx = df_usuarios.index[df_usuarios['matricula'] == str(mat_edit).strip()].tolist()
            if idx:
                u_idx = idx[0]
                with st.form("edit_u"):
                    e_categoria = st.text_input("Categoría", value=df_usuarios.at[u_idx, 'categoria'], key="edit_categoria")
                    e_pass = st.text_input("Contraseña", value=df_usuarios.at[u_idx, 'password'], key="edit_password")
                    e_est = st.selectbox("Estatus", ["Alta", "Baja", "Baja Temporal"], 
                                        index=["Alta", "Baja", "Baja Temporal"].index(df_usuarios.at[u_idx, 'estatus']),
                                        key="edit_estatus")
                    if st.form_submit_button("Actualizar Datos", use_container_width=True):
                        df_usuarios.at[u_idx, 'categoria'] = e_categoria
                        df_usuarios.at[u_idx, 'password'] = e_pass
                        df_usuarios.at[u_idx, 'estatus'] = e_est
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_usuarios.to_excel(writer, sheet_name='usuarios', index=False)
                            for n, d in hojas_restantes.items(): 
                                d.to_excel(writer, sheet_name=n, index=False)
                        st.success("✨ Actualizado")
                        st.rerun()
    
    with t2:
        try:
            xls = pd.ExcelFile(DB_FILE)
            df_v = pd.read_excel(xls, sheet_name='vehiculos').fillna("")
            hojas_restantes = {s: pd.read_excel(xls, s) for s in xls.sheet_names if s != 'vehiculos'}
        except:
            df_v = pd.DataFrame(columns=["tipo", "ecco", "placas", "marca", "modelo", "km_actual", "km_servicio", "estatus"])
            hojas_restantes = {}
        
        with st.popover("➕ Registrar Vehículo"):
            with st.form("f_v", clear_on_submit=True):
                c1, c2 = st.columns(2)
                v_tip = c1.text_input("Tipo", key="reg_v_tipo")
                v_ecc = c2.text_input("ECCO", key="reg_v_ecco")
                v_pla = c1.text_input("Placas", key="reg_v_placas")
                v_mar = c2.text_input("Marca", key="reg_v_marca")
                v_mod = c1.text_input("Modelo", key="reg_v_modelo")
                v_kma = c2.number_input("Kilometraje Actual", min_value=0, key="reg_v_kma")
                v_kms = st.text_input("KM Próximo Servicio", key="reg_v_kms")
                v_est = st.selectbox("Estatus", ["Alta", "Baja", "Mantenimiento"], key="reg_v_estatus")
                if st.form_submit_button("Guardar Vehículo", use_container_width=True):
                    nueva_v = {
                        "tipo": v_tip, 
                        "ecco": v_ecc, 
                        "placas": v_pla, 
                        "marca": v_mar, 
                        "modelo": v_mod, 
                        "km_actual": v_kma, 
                        "km_servicio": v_kms, 
                        "estatus": v_est
                    }
                    df_v = pd.concat([df_v, pd.DataFrame([nueva_v])], ignore_index=True)
                    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                        df_v.to_excel(writer, sheet_name='vehiculos', index=False)
                        for n, d in hojas_restantes.items(): 
                            d.to_excel(writer, sheet_name=n, index=False)
                    st.success("✅ Vehículo guardado")
                    st.rerun()
        
        st.write("### Flota Vehicular")
        st.dataframe(df_v, use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 🔧 Actualizar KM / Estatus")
        ecco_edit = st.text_input("Ingresa ECCO para actualizar", key="ecco_edit")
        if ecco_edit:
            df_v['ecco'] = df_v['ecco'].astype(str).str.replace(r'\.0$', '', regex=True)
            idx_v = df_v.index[df_v['ecco'] == str(ecco_edit).strip()].tolist()
            if idx_v:
                v_idx = idx_v[0]
                with st.form("edit_v"):
                    n_km = st.number_input("Nuevo KM", value=int(df_v.at[v_idx, 'km_actual']), key="edit_v_km")
                    n_est = st.selectbox("Estatus", ["Alta", "Baja", "Mantenimiento"], 
                                        index=["Alta", "Baja", "Mantenimiento"].index(df_v.at[v_idx, 'estatus']),
                                        key="edit_v_estatus")
                    if st.form_submit_button("Actualizar Unidad", use_container_width=True):
                        df_v.at[v_idx, 'km_actual'] = n_km
                        df_v.at[v_idx, 'estatus'] = n_est
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_v.to_excel(writer, sheet_name='vehiculos', index=False)
                            for n, d in hojas_restantes.items(): 
                                d.to_excel(writer, sheet_name=n, index=False)
                        st.success("✨ Unidad actualizada")
                        st.rerun()
    
    with t3:
        try:
            xls = pd.ExcelFile(DB_FILE)
            df_h = pd.read_excel(xls, sheet_name='hospitales').fillna("")
            hojas_restantes = {s: pd.read_excel(xls, s) for s in xls.sheet_names if s != 'hospitales'}
        except:
            df_h = pd.DataFrame(columns=["estado", "nombre_hosp", "direccion", "alto_costo"])
            hojas_restantes = {}
        
        with st.popover("➕ Registrar Hospital"):
            with st.form("f_h", clear_on_submit=True):
                h_est = st.text_input("Estado", key="reg_h_estado")
                h_nom = st.text_input("Nombre Hospital", key="reg_h_nombre")
                h_dir = st.text_input("Dirección", key="reg_h_direccion")
                h_ac = st.radio("¿Alto Costo?", ["No", "Sí"], key="reg_h_alto_costo")
                if st.form_submit_button("Guardar Hospital", use_container_width=True):
                    nueva_h = {
                        "estado": h_est, 
                        "nombre_hosp": h_nom, 
                        "direccion": h_dir, 
                        "alto_costo": h_ac
                    }
                    df_h = pd.concat([df_h, pd.DataFrame([nueva_h])], ignore_index=True)
                    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                        df_h.to_excel(writer, sheet_name='hospitales', index=False)
                        for n, d in hojas_restantes.items(): 
                            d.to_excel(writer, sheet_name=n, index=False)
                    st.success("✅ Hospital registrado")
                    st.rerun()
        
        st.write("### Catálogo de Hospitales")
        st.dataframe(df_h, use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("### 🏥 Editar Hospital")
        h_sel = st.selectbox("Selecciona hospital para modificar", [""] + df_h['nombre_hosp'].tolist(), key="h_sel")
        if h_sel:
            h_idx = df_h.index[df_h['nombre_hosp'] == h_sel][0]
            with st.form("edit_h"):
                n_dir = st.text_input("Dirección", value=df_h.at[h_idx, 'direccion'], key="edit_h_dir")
                n_ac = st.radio("Alto Costo", ["No", "Sí"], index=0 if df_h.at[h_idx, 'alto_costo'] == "No" else 1, key="edit_h_ac")
                if st.form_submit_button("Actualizar Hospital", use_container_width=True):
                    df_h.at[h_idx, 'direccion'] = n_dir
                    df_h.at[h_idx, 'alto_costo'] = n_ac
                    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                        df_h.to_excel(writer, sheet_name='hospitales', index=False)
                        for n, d in hojas_restantes.items(): 
                            d.to_excel(writer, sheet_name=n, index=False)
                    st.success("✨ Hospital actualizado")
                    st.rerun()

# ----------------------------------------------------------------------------
# VISTA 3.2: CONFIGURACIÓN ADMIN (DATOS INSTITUCIONALES)
# ----------------------------------------------------------------------------
def vista_configuracion_admin(u):
    st.subheader("🏢 Configuración de Datos Institucionales")
    
    asegurar_hojas_excel()
    
    config_actual = obtener_configuracion_admin()
    
    if 'folio_foraneo_temp' not in st.session_state:
        st.session_state.folio_foraneo_temp = config_actual.get('folio_inicial_sistema', 'F001/2026')
    
    if 'folio_local_temp' not in st.session_state:
        st.session_state.folio_local_temp = config_actual.get('folio_inicial_local', 'L001/2026')
    
    try:
        with st.form("form_config_institucional"):
            col1, col2 = st.columns(2)
            
            with col1:
                titular = st.text_input("Titular de la Unidad", value=config_actual.get('titular_unidad', ''), key="config_titular")
                unidad = st.text_input("Unidad Administrativa", value=config_actual.get('unidad_administrativa', ''), key="config_unidad")
                
                st.markdown("---")
                st.markdown("**📌 Traslados FORÁNEOS**")
                st.caption("Formato: F123/2026")
                
                folio_foraneo = st.text_input("Folio inicial FORÁNEO:", value=st.session_state.folio_foraneo_temp, key="input_folio_foraneo_admin")
                st.session_state.folio_foraneo_temp = folio_foraneo
            
            with col2:
                adscripcion = st.text_input("Adscripción", value=config_actual.get('adscripcion', ''), key="config_adscripcion")
                cargo = st.text_input("Cargo del Titular", value=config_actual.get('cargo_titular', ''), key="config_cargo")
                
                st.markdown("---")
                st.markdown("**🚑 Traslados LOCALES**")
                st.caption("Formato: L150/2026")
                
                folio_local = st.text_input("Folio inicial LOCAL:", value=st.session_state.folio_local_temp, key="input_folio_local_admin")
                st.session_state.folio_local_temp = folio_local
            
            if st.form_submit_button("💾 Guardar Configuración", type="primary", use_container_width=True):
                errores = []
                
                if not validar_formato_folio(folio_foraneo, "F"):
                    errores.append("❌ El folio FORÁNEO debe tener formato F123/2026")
                
                if not validar_formato_folio(folio_local, "L"):
                    errores.append("❌ El folio LOCAL debe tener formato L150/2026")
                
                if errores:
                    for error in errores:
                        st.error(error)
                else:
                    nueva_conf = {
                        'titular_unidad': titular,
                        'unidad_administrativa': unidad,
                        'adscripcion': adscripcion,
                        'cargo_titular': cargo,
                        'folio_inicial_sistema': folio_foraneo,
                        'folio_inicial_local': folio_local
                    }
                    
                    if guardar_configuracion_admin(nueva_conf):
                        st.success("✅ Configuración guardada correctamente")
                        st.balloons()
                        st.session_state.folio_foraneo_temp = folio_foraneo
                        st.session_state.folio_local_temp = folio_local
                    else:
                        st.error("❌ Error al guardar configuración")
    
    except Exception as e:
        st.error(f"Error al cargar configuración: {e}")

# ----------------------------------------------------------------------------
# VISTA 3.3: CONFIGURACIÓN ADMIN COMPLETA (PANEL DE CONTROL)
# ----------------------------------------------------------------------------
def vista_configuracion_admincompleta(u):
    st.header("⚙️ Panel de Control Administrativo")
    
    tab1, tab2, tab3 = st.tabs([
        "👥 Gestión de Usuarios", 
        "🏢 Datos Institucionales",
        "📊 Respaldo y Mantenimiento"
    ])
    
    with tab1:
        vista_configuracion()
    
    with tab2:
        vista_configuracion_admin(u)
    
    with tab3:
        st.subheader("💾 Respaldo de Base de Datos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Crear Respaldo", use_container_width=True, key="btn_respaldo"):
                if os.path.exists(DB_FILE):
                    import shutil
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    shutil.copy2(DB_FILE, backup_name)
                    st.success(f"✅ Respaldo creado: {backup_name}")
        
        with col2:
            if st.button("🔄 Verificar Integridad", use_container_width=True, key="btn_verificar"):
                try:
                    if os.path.exists(DB_FILE):
                        xls = pd.ExcelFile(DB_FILE)
                        hojas = xls.sheet_names
                        st.success(f"✅ Base de datos OK - {len(hojas)} hojas encontradas")
                        st.json(hojas)
                    else:
                        st.warning("⚠️ No se encontró la base de datos")
                except Exception as e:
                    st.error(f"❌ Error en la base de datos: {e}")

# ----------------------------------------------------------------------------
# VISTA 3.4: ESTADÍSTICAS ADMIN
# ----------------------------------------------------------------------------
def vista_estadisticas_admin(u):
    st.title("📊 Panel de Inteligencia Administrativa")
    
    try:
        asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        
        df_p = pd.read_excel(xls, sheet_name='pliegos').fillna("") if 'pliegos' in xls.sheet_names else pd.DataFrame()
        df_t = pd.read_excel(xls, sheet_name='traslados_locales').fillna("") if 'traslados_locales' in xls.sheet_names else pd.DataFrame()
        df_v = pd.read_excel(xls, sheet_name='vehiculos').fillna(0) if 'vehiculos' in xls.sheet_names else pd.DataFrame()
        
        otras_hojas = {sh: pd.read_excel(xls, sh) for sh in xls.sheet_names if sh not in ['vehiculos', 'pliegos', 'traslados_locales', 'informes']}
        
        st.subheader("📈 Indicadores de Desempeño")
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("### 1. Traslados Locales")
            if not df_t.empty and 'estatus' in df_t.columns:
                estatus_counts = df_t['estatus'].value_counts().reset_index()
                estatus_counts.columns = ['estatus', 'count']
                fig1 = px.bar(estatus_counts, x='estatus', y='count', 
                              color='estatus', title="Distribución por Estatus")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay datos de traslados")
        
        with row1_col2:
            st.markdown("### 2. Traslados Foráneos (Pliegos)")
            if not df_p.empty and 'destino' in df_p.columns:
                destino_counts = df_p['destino'].value_counts().reset_index()
                destino_counts.columns = ['destino', 'count']
                fig2 = px.pie(destino_counts, values='count', names='destino', title="Destinos más frecuentes")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay datos de pliegos")
        
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("### 3. Traslados por Día")
            if not df_t.empty and 'fecha_creacion' in df_t.columns:
                df_t['fecha'] = pd.to_datetime(df_t['fecha_creacion'], format='%d/%m/%Y', errors='coerce')
                df_dia = df_t.groupby(df_t['fecha'].dt.date).size().reset_index()
                df_dia.columns = ['fecha', 'cantidad']
                fig3 = px.line(df_dia, x='fecha', y='cantidad', title="Traslados por día")
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Sin datos de fechas")
        
        with row2_col2:
            st.markdown("### 4. Productividad por Empleado")
            if not df_t.empty and 'empleado_comisionado' in df_t.columns:
                emp_counts = df_t['empleado_comisionado'].value_counts().head(10).reset_index()
                emp_counts.columns = ['empleado', 'cantidad']
                fig4 = px.bar(emp_counts, x='empleado', y='cantidad', title="Top 10 empleados")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Sin datos de empleados")
        
        st.divider()
        st.markdown("### 5. Estado de Vehículos")
        
        if not df_v.empty and all(col in df_v.columns for col in ['km_servicio', 'km_actual']):
            df_v['km_restantes'] = df_v['km_servicio'] - df_v['km_actual']
            df_v = df_v[df_v['km_restantes'] > 0]
            if not df_v.empty:
                fig5 = px.bar(df_v, x='km_restantes', y='ecco', orientation='h',
                              title="Kilómetros para Mantenimiento",
                              labels={'km_restantes': 'KM restantes', 'ecco': 'Vehículo'})
                st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("Todos los vehículos están al día")
        else:
            st.info("No hay datos de vehículos")
    
    except Exception as e:
        st.error(f"Error en estadísticas: {e}")
        st.exception(e)

# ----------------------------------------------------------------------------
# VISTA 3.5: INFORME DE COMISIÓN
# ----------------------------------------------------------------------------
def vista_informe_comision(u):
    st.header("📝 Generar Informe de Comisión")
    
    asegurar_hojas_excel()
    
    if 'datos_pliego_cargado' not in st.session_state:
        st.session_state.datos_pliego_cargado = {
            'chofer': 'JUAN PEREZ',
            'destino': 'HOSPITAL GENERAL',
            'paciente': 'MARIA GARCIA',
            'objeto_comision': 'TRASLADO DE PACIENTE',
            'ecco': 'ECCO-001',
            'km_salida': 12500,
            'folio': 'PLG-2024-001 (EJEMPLO)'
        }
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        with st.popover("🔍 BUSCAR PLIEGO PARA RELLENAR", use_container_width=True):
            st.markdown("### 📋 Seleccionar Pliego")
            
            try:
                df_p = obtener_pliegos()
                if not df_p.empty:
                    if u.get('rol') == "Administrador":
                        df_filtrado = df_p
                    else:
                        df_filtrado = df_p[df_p['matricula'] == u.get('matricula')]
                    
                    if not df_filtrado.empty:
                        df_show = df_filtrado[['folio', 'nombre', 'm_destino', 'fecha_elaboracion']].copy()
                        df_show.columns = ['Folio', 'Empleado', 'Destino', 'Fecha']
                        st.dataframe(df_show, use_container_width=True, hide_index=True)
                        
                        lista_folios = ["-- Seleccionar --"] + df_filtrado['folio'].tolist()
                        folio_sel = st.selectbox("Seleccione Folio:", lista_folios, key="selector_folio_modal")
                        
                        if st.button("📥 CARGAR PLIEGO", type="primary", use_container_width=True, key="btn_cargar_pliego"):
                            if folio_sel != "-- Seleccionar --":
                                datos_cargados = df_filtrado[df_filtrado['folio'] == folio_sel].iloc[0].to_dict()
                                st.session_state.datos_pliego_cargado = datos_cargados
                                st.success(f"✅ Pliego {folio_sel} cargado")
                                st.rerun()
                    else:
                        st.info("No hay pliegos disponibles")
                else:
                    st.info("No hay pliegos registrados")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    datos_p = st.session_state.datos_pliego_cargado
    
    st.subheader("📋 Datos del Pliego")
    col_datos1, col_datos2, col_datos3 = st.columns(3)
    
    with col_datos1:
        st.text_input("Folio", value=datos_p.get('folio', 'N/A'), disabled=True, key="folio_display")
        st.text_input("Chofer", value=datos_p.get('chofer', 'N/A'), disabled=True, key="chofer_display")
    
    with col_datos2:
        st.text_input("Destino", value=datos_p.get('m_destino', 'N/A'), disabled=True, key="destino_display")
        st.text_input("Paciente", value=datos_p.get('paciente', 'N/A'), disabled=True, key="paciente_display")
    
    with col_datos3:
        st.text_input("Objeto", value=datos_p.get('m_objeto', 'N/A'), disabled=True, key="objeto_display")
        st.text_input("ECCO", value=datos_p.get('ecco', 'N/A'), disabled=True, key="ecco_display")
    
    st.divider()
    
    st.subheader("📝 Completar Informe")
    
    with st.form("form_informe_comision"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            no_cama = st.text_input("Número de Cama", value="101-A", key="cama_input")
            km_i = st.number_input("Kilometraje Inicial", 
                                   value=int(datos_p.get('km_salida', 12500)), 
                                   key="km_i_input")
        
        with col2:
            h_salida = st.time_input("Hora Salida", value=datetime.now().replace(hour=8, minute=30), key="hora_salida_input")
            h_llegada = st.time_input("Hora Llegada", value=datetime.now().replace(hour=10, minute=15), key="hora_llegada_input")
        
        with col3:
            h_regreso = st.time_input("Hora Regreso", value=datetime.now().replace(hour=16, minute=45), key="hora_regreso_input")
            km_f = st.number_input("Kilometraje Final", 
                                   min_value=km_i, 
                                   value=int(datos_p.get('km_salida', 12500)) + 250, 
                                   key="km_f_input")
        
        st.divider()
        
        res_final = st.text_area("RESULTADOS OBTENIDOS", 
                                 value="SE TRASLADA PACIENTE SIN NINGUNA NOVEDAD", 
                                 height=100, key="resultados_input")
        
        con_final = st.text_area("CONTRIBUCIONES", 
                                 value="SE CUMPLE CON EL TRASLADO EN TIEMPO Y FORMA", 
                                 height=100, key="contribuciones_input")
        
        guardar_click = st.form_submit_button("💾 GUARDAR INFORME", type="primary", use_container_width=True)
    
    total_recorrido = km_f - km_i
    
    fecha_actual = datetime.now()
    dia_actual = fecha_actual.strftime("%d")
    mes_actual = fecha_actual.strftime("%m")
    mes_nombre = {
        "01": "ENERO", "02": "FEBRERO", "03": "MARZO", "04": "ABRIL",
        "05": "MAYO", "06": "JUNIO", "07": "JULIO", "08": "AGOSTO",
        "09": "SEPTIEMBRE", "10": "OCTUBRE", "11": "NOVIEMBRE", "12": "DICIEMBRE"
    }.get(mes_actual, mes_actual)
    
    categoria_user = u.get('categoria', 'PERSONAL')
    matricula_user = u.get('matricula', '')
    
    config = obtener_configuracion_admin()
    adscripcion = config.get('adscripcion', 'HGZ No. 1 OAXACA')
    titular_unidad = config.get('titular_unidad', '')
    unidad_administrativa = config.get('unidad_administrativa', '')
    
    fecha_salida = datos_p.get('fecha_salida', fecha_actual.strftime("%d/%m/%Y"))
    direccion_destino = datos_p.get('direccion', '')
    nombre_empleado = u.get('nombre', '').upper()
    
    datos_para_html = {
        "num_pliego": datos_p.get('folio', 'N/A'),
        "folio_sistema": datos_p.get('folio', 'N/A'),
        "dia_hoy": dia_actual,
        "mes_hoy": mes_nombre,
        "fecha_inicio": datos_p.get('fecha_inicio', fecha_actual.strftime("%d/%m/%Y")),
        "fecha_fin": datos_p.get('fecha_fin', fecha_actual.strftime("%d/%m/%Y")),
        "fecha_salida": fecha_salida,
        "adscripcion": adscripcion,
        "titular_unidad": titular_unidad,
        "unidad_administrativa": unidad_administrativa,
        "lugar_comision": datos_p.get('m_destino', 'N/A'),
        "objeto_comision": datos_p.get('m_objeto', 'N/A'),
        "direccion_destino": direccion_destino,
        "paciente": datos_p.get('paciente', 'N/A'),
        "ecco": datos_p.get('ecco', 'N/A'),
        "cama": no_cama,
        "km_inicial": km_i,
        "km_total_recorrido": total_recorrido,
        "hora_salida": h_salida.strftime("%H:%M") if h_salida else "",
        "hora_llegada_destino": h_llegada.strftime("%H:%M") if h_llegada else "",
        "hora_regreso_hgz": h_regreso.strftime("%H:%M") if h_regreso else "",
        "resultados": res_final,
        "contribuciones": con_final,
        "categoria_user": categoria_user,
        "matricula_user": matricula_user,
        "logo_base64": get_base64("assets/logoimss.png"),
        "nombre_empleado": nombre_empleado,
    }
    
    col_print1, col_print2, col_print3 = st.columns([1, 2, 1])
    with col_print2:
        if st.button("🖨️ IMPRIMIR INFORME", use_container_width=True, type="primary", key="btn_imprimir_informe"):
            template_path = "templates/informe_template.html"
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template = Template(f.read())
                    html_content = template.render(datos_para_html)
                
                html_impresion = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            body {{ margin: 1cm; }}
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                    <script>
                        window.onload = function() {{
                            window.print();
                        }};
                    </script>
                </body>
                </html>
                """
                st.components.v1.html(html_impresion, height=800, scrolling=True)
            else:
                st.error("❌ Plantilla de informe no encontrada")
    
    st.divider()
    
    st.subheader("👁️ Vista Previa del Informe")
    
    try:
        template_path = "templates/informe_template.html"
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                template = Template(f.read())
                html_final = template.render(datos_para_html)
            
            html_con_estilos = f"""
            <style>
                @media print {{
                    .no-print {{
                        display: none !important;
                    }}
                    body {{
                        margin: 0;
                        padding: 1cm;
                    }}
                }}
            </style>
            <div class="informe-contenido">
                {html_final}
            </div>
            """
            components.html(html_con_estilos, height=1000, scrolling=True)
        else:
            st.warning(f"⚠️ Plantilla no encontrada")
            st.json(datos_para_html)
    except Exception as e:
        st.error(f"Error al renderizar template: {e}")
        st.json(datos_para_html)
    
    if guardar_click and "(EJEMPLO)" not in datos_p.get('folio', ''):
        try:
            nuevo_informe = {
                "folio_pliego": datos_p.get('folio', ''),
                "fecha_informe": datetime.now().strftime("%d/%m/%Y"),
                "no_cama": no_cama,
                "hora_salida_hgz": h_salida.strftime("%H:%M") if h_salida else "",
                "hora_llegada_destino": h_llegada.strftime("%H:%M") if h_llegada else "",
                "hora_regreso_hgz": h_regreso.strftime("%H:%M") if h_regreso else "",
                "km_inicial": km_i,
                "km_final": km_f,
                "km_total_recorrido": total_recorrido,
                "resultados": res_final,
                "contribuciones": con_final,
                "ecco_utilizado": datos_p.get('ecco', '')
            }
            
            xls = pd.ExcelFile(DB_FILE)
            if 'informes' in xls.sheet_names:
                df_inf = pd.read_excel(DB_FILE, sheet_name='informes')
            else:
                df_inf = pd.DataFrame()
            
            df_inf = pd.concat([df_inf, pd.DataFrame([nuevo_informe])], ignore_index=True)
            
            otras_hojas = {s: pd.read_excel(xls, s) for s in xls.sheet_names if s != 'informes'}
            
            with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                df_inf.to_excel(writer, sheet_name='informes', index=False)
                for n, d in otras_hojas.items():
                    d.to_excel(writer, sheet_name=n, index=False)
            
            if datos_p.get('ecco'):
                actualizar_km_vehiculo(datos_p['ecco'], km_f)
            
            st.success(f"✅ Informe Guardado. KM actualizado: {km_f}")
        
        except Exception as e:
            st.error(f"Error al guardar: {e}")
    elif guardar_click:
        st.warning("⚠️ No se puede guardar: Estás usando datos de ejemplo. Carga un pliego real primero.")

# ----------------------------------------------------------------------------
# VISTA 3.6: DESGLOSE DE GASTOS
# ----------------------------------------------------------------------------
def vista_desglose_gastos(u):
    st.header("🧾 Desglose Pormenorizado de Gastos")
    
    if 'gastos_desglose' not in st.session_state:
        st.session_state['gastos_desglose'] = {
            "HOSPEDAJE": [],
            "ALIMENTACIÓN": [],
            "TRASLADOS": [],
            "OTROS VIÁTICOS": [],
            "AUTOBÚS": [],
            "PEAJE": [],
            "GASOLINA": [],
            "OTROS GASTOS": [],
            "SIN COMPROBANTE": []
        }
    
    with st.expander("🔍 BUSCAR PLIEGO PARA DESGLOSE", expanded=False):
        df_p = obtener_pliegos()
        
        if not df_p.empty:
            if u.get('rol') == "Administrador":
                df_filtrado = df_p
            else:
                df_filtrado = df_p[df_p['matricula'] == u.get('matricula')]
            
            if not df_filtrado.empty:
                folios = df_filtrado['folio'].tolist()
                folio_sel = st.selectbox("Seleccionar folio:", ["-- Seleccionar --"] + folios, key="selector_folio_gastos")
                
                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if st.button("📥 CARGAR PLIEGO", use_container_width=True, key="btn_cargar_pliego_gastos"):
                        if folio_sel != "-- Seleccionar --":
                            datos_pliego = df_filtrado[df_filtrado['folio'] == folio_sel].iloc[0].to_dict()
                            st.session_state['pliego_desglose'] = datos_pliego
                            st.success(f"✅ Pliego {folio_sel} cargado")
                            st.rerun()
                with col_b2:
                    if st.button("🔄 LIMPIAR", use_container_width=True, key="btn_limpiar_gastos"):
                        if 'pliego_desglose' in st.session_state:
                            del st.session_state['pliego_desglose']
                        st.rerun()
            else:
                st.info("No hay pliegos disponibles para tu usuario")
        else:
            st.info("No hay pliegos registrados")
    
    if 'pliego_desglose' in st.session_state:
        pliego = st.session_state['pliego_desglose']
    else:
        pliego = {
            "folio": "________",
            "nombre": "____________________",
            "m_destino": "____________________",
            "matricula": "________",
            "tipo_contrato": "________",
            "medio_transporte": "____________________",
            "fecha_inicio": "__/__/____",
            "fecha_fin": "__/__/____",
            "dias_comision": "__"
        }
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("➕ AGREGAR GASTO", use_container_width=True, type="primary", key="btn_agregar_gasto"):
            modal_agregar_gasto()
    
    with col_btn2:
        if st.button("🗑️ LIMPIAR GASTOS", use_container_width=True, key="btn_limpiar_todo_gastos"):
            for cat in st.session_state['gastos_desglose']:
                st.session_state['gastos_desglose'][cat] = []
            st.rerun()
    
    if 'pliego_desglose' in st.session_state:
        st.subheader("📋 Gastos registrados")
        
        total_general = 0.0
        categorias_mostrar = [
            "HOSPEDAJE", "ALIMENTACIÓN", "TRASLADOS", "OTROS VIÁTICOS",
            "AUTOBÚS", "PEAJE", "GASOLINA", "OTROS GASTOS", "SIN COMPROBANTE"
        ]
        
        for categoria in categorias_mostrar:
            gastos = st.session_state['gastos_desglose'].get(categoria, [])
            if gastos:
                with st.expander(f"📂 {categoria} ({len(gastos)} gastos)"):
                    df_cat = pd.DataFrame(gastos)
                    st.dataframe(df_cat, use_container_width=True, hide_index=True)
                    subtotal = sum(g.get('importe', 0) for g in gastos)
                    st.metric(f"Subtotal {categoria}", f"${subtotal:,.2f}")
                    total_general += subtotal
        
        if total_general > 0:
            st.metric("💰 TOTAL GENERAL", f"${total_general:,.2f}")
    
    fecha_actual = datetime.now()
    fecha_emision = fecha_actual.strftime("%d DE %B %Y").upper()
    
    categorias_primera_pagina = []
    for nombre in ["HOSPEDAJE", "ALIMENTACIÓN", "TRASLADOS", "OTROS VIÁTICOS"]:
        gastos = st.session_state['gastos_desglose'].get(nombre, [])
        subtotal = sum(g.get('importe', 0) for g in gastos)
        categorias_primera_pagina.append({
            "nombre": nombre,
            "gastos": gastos,
            "subtotal": subtotal
        })
    
    categorias_segunda_pagina = []
    for nombre in ["AUTOBÚS", "PEAJE", "GASOLINA", "OTROS GASTOS"]:
        gastos = st.session_state['gastos_desglose'].get(nombre, [])
        subtotal = sum(g.get('importe', 0) for g in gastos)
        categorias_segunda_pagina.append({
            "nombre": nombre,
            "gastos": gastos,
            "subtotal": subtotal
        })
    
    gastos_sin_comprobante = st.session_state['gastos_desglose'].get("SIN COMPROBANTE", [])
    subtotal_sin_comprobante = sum(g.get('importe', 0) for g in gastos_sin_comprobante)
    total_general = (
        sum(c["subtotal"] for c in categorias_primera_pagina) +
        sum(c["subtotal"] for c in categorias_segunda_pagina) +
        subtotal_sin_comprobante
    )
    
    datos_gastos = {
        "logo_base64": get_base64("assets/logoimss.png"),
        "folio": pliego.get('folio', '________'),
        "fecha_emision": fecha_emision,
        "comisionado": pliego.get('nombre', '____________________'),
        "destino": pliego.get('m_destino', '____________________'),
        "matricula": pliego.get('matricula', '________'),
        "tipo_contrato": pliego.get('tipo_contrato', '________'),
        "transporte": pliego.get('medio_transporte', '____________________'),
        "fecha_inicio": pliego.get('fecha_inicio', '__/__/____'),
        "fecha_fin": pliego.get('fecha_fin', '__/__/____'),
        "total_dias": pliego.get('dias_comision', '__'),
        "categorias_primera_pagina": categorias_primera_pagina,
        "categorias_segunda_pagina": categorias_segunda_pagina,
        "gastos_sin_comprobante": gastos_sin_comprobante,
        "subtotal_sin_comprobante": subtotal_sin_comprobante,
        "total_general": total_general
    }
    
    st.divider()
    st.subheader("👁️ Vista Previa del Desglose")
    
    try:
        template_path = "templates/gastos_template.html"
        
        if not os.path.exists(template_path):
            st.error(f"❌ No se encuentra el template")
            st.stop()
        
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())
            html_final = template.render(datos_gastos)
        
        st.components.v1.html(html_final, height=1000, scrolling=True)
    
    except Exception as e:
        st.error(f"❌ Error al renderizar template: {e}")
        st.exception(e)
    
    col_fin1, col_fin2 = st.columns(2)
    
    with col_fin1:
        if st.button("💾 GUARDAR GASTOS EN EXCEL", use_container_width=True, type="secondary", key="btn_guardar_gastos"):
            if 'pliego_desglose' in st.session_state:
                folio = pliego.get('folio', '')
                if guardar_gastos(st.session_state['gastos_desglose'], folio):
                    st.success(f"✅ Gastos guardados correctamente para folio {folio}")
                else:
                    st.error("Error al guardar gastos en Excel")
            else:
                st.warning("⚠️ No se puede guardar: primero debe cargar un pliego")
    
    with col_fin2:
        if st.button("🖨️ IMPRIMIR DESGLOSE", use_container_width=True, type="primary", key="btn_imprimir_gastos"):
            try:
                with open("templates/gastos_template.html", "r", encoding="utf-8") as f:
                    template = Template(f.read())
                    html_content = template.render(datos_gastos)
                
                html_impresion = f"""
                <html>
                <head>
                    <style>
                        @media print {{
                            body {{ margin: 0; padding: 0.5cm; }}
                        }}
                    </style>
                </head>
                <body>
                    {html_content}
                    <script>window.onload = function() {{ window.print(); }}</script>
                </body>
                </html>
                """
                st.components.v1.html(html_impresion, height=800, scrolling=True)
            except Exception as e:
                st.error(f"Error al preparar impresión: {e}")