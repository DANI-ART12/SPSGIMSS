# ============================================
# modules/forms.py - VISTAS Y MODALES (VERSIÓN FINAL CORREGIDA)
# ============================================

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from jinja2 import Template
import streamlit.components.v1 as components
import plotly.express as px

# ============================================
# IMPORTACIONES CORREGIDAS
# ============================================
from modules.utils import (
    get_base64,
    asegurar_hojas_excel,
    generar_folio_local,
    generar_folio_foraneo,
    gestionar_config_permanente
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
    guardar_gastos
)

# ============================================
# CONSTANTES GLOBALES
# ============================================
DB_FILE = "base_datos.xlsx"

# ============================================
# MODALES
# ============================================

# --- MODAL: NUEVO TRASLADO FORÁNEO (COMPLETO) ---
@st.dialog("➕ NUEVO TRASLADO FORÁNEO")
def modal_nuevo_traslado(u, df_p):
    st.write("Complete los datos del nuevo traslado FORÁNEO")
    
    # ============================================
    # SELECCIÓN DE TIPO DE FOLIO
    # ============================================
    tipo_folio = st.radio(
        "Tipo de folio:",
        ["🔖 Folio nuevo", "♻️ Reutilizar folio cancelado"],
        horizontal=True,
        key="tipo_folio_radio"
    )
    
    folio_seleccionado = None
    
    if tipo_folio == "🔖 Folio nuevo":
        # Obtener folio inicial desde Excel
        folio_inicial = "F001/2026"
        try:
            if os.path.exists(DB_FILE):
                df_config = pd.read_excel(DB_FILE, sheet_name='config_admin')
                if not df_config.empty and 'folio_inicial_sistema' in df_config.columns:
                    folio_config = str(df_config.iloc[0]['folio_inicial_sistema'])
                    if not folio_config.startswith('F'):
                        partes = folio_config.split('/')
                        if len(partes) == 2:
                            num = partes[0].zfill(3)
                            anio = partes[1]
                            folio_inicial = f"F{num}/{anio}"
                    else:
                        folio_inicial = folio_config
        except:
            pass
        
        siguiente_folio = generar_folio_foraneo(df_p, folio_inicial)
        st.info(f"Folio nuevo asignado: **{siguiente_folio}**")
        folio_seleccionado = siguiente_folio
        
    else:
        # Mostrar lista de folios cancelados
        if not df_p.empty and 'folio' in df_p.columns and 'estatus_pliego' in df_p.columns:
            folios_cancelados = df_p[df_p['estatus_pliego'] == "Cancelado"]['folio'].tolist()
            if folios_cancelados:
                folio_sel = st.selectbox("Seleccionar folio cancelado:", folios_cancelados)
                folio_seleccionado = folio_sel
                st.warning(f"♻️ Reutilizando folio: {folio_sel}")
            else:
                st.error("No hay folios cancelados disponibles.")
        else:
            st.error("No hay datos de pliegos.")
    
    st.divider()
    
    # ============================================
    # CHECKBOX: ¿ES PERSONA DE PASO?
    # ============================================
    es_persona_paso = st.checkbox("👤 ¿Es persona de paso? (Externo no registrado)")
    
    nombre_externo = None
    matricula_externo = None
    puesto_externo = None
    
    if es_persona_paso:
        with st.container(border=True):
            st.markdown("**📝 Datos del externo**")
            col_ext1, col_ext2 = st.columns(2)
            with col_ext1:
                nombre_externo = st.text_input(
                    "Nombre completo:",
                    value=st.session_state.get('persona_paso', {}).get('nombre', ''),
                    key="modal_nombre_externo"
                )
            with col_ext2:
                matricula_externo = st.text_input(
                    "Matrícula:",
                    value=st.session_state.get('persona_paso', {}).get('matricula', ''),
                    key="modal_matricula_externo"
                )
            puesto_externo = st.text_input(
                "Puesto:",
                value=st.session_state.get('persona_paso', {}).get('puesto', ''),
                key="modal_puesto_externo"
            )
    
    st.divider()
    
    # ============================================
    # PESTAÑAS DE DATOS DEL VIAJE
    # ============================================
    tab1, tab2, tab3, tab4 = st.tabs(["📍 Destino y Motivo", "🚗 Datos del Viaje", "💰 Anticipos", "📋 Liquidación"])
    
    with tab1:
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            destino = st.text_input("Destino:", placeholder="Ej: HGR 1 → HGR 2", key="modal_destino")
        with col_d2:
            motivo = st.text_input("Motivo / Paciente:", placeholder="Ej: TRASLADO DE PACIENTE - NSS", key="modal_motivo")
    
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
    
    # ============================================
    # SECCIÓN DE TESORERÍA (BUENO POR / RECIBÍ)
    # ============================================
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
                bueno_por = st.number_input(
                    "BUENO POR ($):", 
                    min_value=0.0, 
                    step=100.0, 
                    format="%.2f",
                    key="modal_bueno_por"
                )
            with col_t2:
                recibi = st.number_input(
                    "RECIBÍ ($):", 
                    min_value=0.0, 
                    step=100.0, 
                    format="%.2f",
                    key="modal_recibi"
                )
            recibi_letras = st.text_input(
                "RECIBÍ (letra):", 
                placeholder="Ej: CIEN PESOS",
                key="modal_recibi_letras"
            )
    else:
        bueno_por = 0.0
        recibi = 0.0
        recibi_letras = ""
    
    # ============================================
    # BOTONES
    # ============================================
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ CREAR TRASLADO", type="primary", use_container_width=True):
            if destino and motivo and folio_seleccionado:
                # Guardar datos generales
                st.session_state['folio_actual'] = folio_seleccionado
                st.session_state['nuevo_destino'] = destino.upper()
                st.session_state['nuevo_motivo'] = motivo.upper()
                st.session_state['nuevo_transporte'] = transporte.upper() if transporte else ""
                st.session_state['nuevo_chofer'] = chofer.upper() if chofer else ""
                st.session_state['nuevo_acompanante'] = acompanante.upper() if acompanante else ""
                st.session_state['nuevo_fecha_inicio'] = fecha_inicio.strftime("%d/%m/%Y")
                st.session_state['nuevo_fecha_fin'] = fecha_fin.strftime("%d/%m/%Y")
                
                # Guardar anticipos
                st.session_state['nuevo_viaticos'] = viaticos
                st.session_state['nuevo_gasolina'] = gasolina
                st.session_state['nuevo_peaje'] = peaje
                st.session_state['nuevo_transporte_t'] = transporte_t
                st.session_state['nuevo_avion'] = avion
                st.session_state['nuevo_subtotal_sin_avion'] = subtotal_sin_avion
                st.session_state['nuevo_total_anticipo'] = total_anticipo
                
                # Guardar liquidación
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
                
                # Guardar tesorería
                st.session_state['nuevo_bueno_por'] = bueno_por
                st.session_state['nuevo_recibi'] = recibi
                st.session_state['nuevo_recibi_letras'] = recibi_letras
                
                # Guardar datos de externo si aplica
                if es_persona_paso and nombre_externo and matricula_externo:
                    st.session_state['nuevo_nombre_externo'] = nombre_externo.upper()
                    st.session_state['nuevo_matricula_externo'] = matricula_externo.upper()
                    st.session_state['nuevo_puesto_externo'] = puesto_externo.upper() if puesto_externo else ""
                else:
                    st.session_state['nuevo_nombre_externo'] = None
                
                st.success(f"✅ Traslado {folio_seleccionado} creado")
                st.rerun()
            else:
                st.error("Complete Destino, Motivo y seleccione un folio válido.")
    with col_btn2:
        if st.button("❌ Cancelar", use_container_width=True):
            st.rerun()


# --- MODAL: CONFIRMAR GUARDADO ---
@st.dialog("💾 Confirmar Guardado")
def modal_confirmar_guardado(datos_html, u):
    st.success("¿Estás seguro de guardar este pliego?")
    
    st.info(f"Folio: **{datos_html.get('m_folio', 'N/A')}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Sí, guardar", type="primary", use_container_width=True):
            try:
                # Construir registro completo con TODOS los datos
                registro = {
                    'folio': datos_html.get('m_folio', ''),
                    'fecha_elaboracion': datos_html.get('m_fecha_creacion', ''),
                    'matricula': datos_html.get('matricula', ''),
                    'estatus_pliego': 'ACTIVO',
                    
                    # Solicitante
                    'f_solicitante': datos_html.get('f_solicitante', ''),
                    'f_cp': datos_html.get('f_cp', ''),
                    'f_categoria': datos_html.get('f_categoria', ''),
                    'f_area': datos_html.get('f_area', ''),
                    'f_tel': datos_html.get('f_tel', ''),
                    
                    # Empleado
                    'nombre': datos_html.get('nombre_empleado', ''),
                    'departamento': datos_html.get('departamento_empleado', ''),
                    'gj': datos_html.get('grupo_jerarquico', ''),
                    'tipo_contrato': datos_html.get('tipo_contrato', ''),
                    
                    # Comisión
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
                    
                    # Anticipos
                    'anticipo_viaticos': datos_html.get('anticipo_viaticos', ''),
                    'anticipo_gasolina': datos_html.get('anticipo_gasolina', ''),
                    'anticipo_peaje': datos_html.get('anticipo_peaje', ''),
                    'anticipo_transporte_t': datos_html.get('anticipo_transporte_t', ''),
                    'anticipo_avion': datos_html.get('anticipo_avion', ''),
                    'total_anticipo': datos_html.get('total_anticipo', ''),
                    'subtotal_sin_avion': datos_html.get('subtotal_sin_avion', ''),
                    
                    # Observaciones
                    'observaciones': datos_html.get('observaciones', ''),
                    
                    # Comprobaciones (reverso)
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
                    
                    # Firmas
                    'elaboro_nombre': datos_html.get('elaboro_nombre', ''),
                    'elaboro_cargo': datos_html.get('elaboro_cargo', ''),
                    'reviso_nombre': datos_html.get('reviso_nombre', ''),
                    'reviso_cargo': datos_html.get('reviso_cargo', ''),
                    'conforme_nombre': datos_html.get('conforme_nombre', ''),
                    'conforme_cargo': datos_html.get('conforme_cargo', ''),
                    'autoriza_nombre': datos_html.get('autoriza_pago_saldo_nombre', ''),
                    'autoriza_cargo': datos_html.get('autoriza_pago_saldo_cargo', ''),
                    
                    # Tesorería
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
        if st.button("❌ No", use_container_width=True):
            st.rerun()


# --- MODAL: NUEVO FUNCIONARIO (COMPLETO CON FIRMAS) ---
@st.dialog("👤 Nuevo Funcionario")
def modal_configurar_funcionario():
    st.write("Seleccione los funcionarios para las firmas. Puede editar C.P. y Teléfono si es necesario.")
    
    # Cargar lista de usuarios
    usuarios_db = obtener_lista_usuarios()
    
    if not usuarios_db:
        st.warning("No hay usuarios registrados en la base de datos.")
        if st.button("Cerrar"):
            st.rerun()
        return
    
    # Crear lista de nombres para los selectbox
    nombres = [usr.get('nombre', '') for usr in usuarios_db if usr.get('nombre')]
    
    # Organizar en pestañas
    tab1, tab2 = st.tabs(["👤 SOLICITANTE", "✍️ FIRMAS"])
    
    with tab1:
        st.subheader("Funcionario Solicitante")
        
        # Selección de funcionario solicitante
        sel_solicitante = st.selectbox("Elegir funcionario solicitante:", nombres, key="sel_solicitante")
        
        # Buscar el funcionario seleccionado
        jefe_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_solicitante), {})
        
        # Mostrar campos EDITABLES para solicitante
        col1, col2 = st.columns(2)
        
        with col1:
            # C.P. - EDITABLE
            cp_default = jefe_seleccionado.get('cp', '')
            cp_editado = st.text_input("C.P. del solicitante:", value=cp_default, key="cp_solicitante")
        
        with col2:
            # Teléfono - EDITABLE
            tel_default = jefe_seleccionado.get('tel_oficina', '')
            tel_editado = st.text_input("Teléfono Oficina:", value=tel_default, key="tel_solicitante")
        
        # Mostrar datos fijos del solicitante
        st.info(f"**Categoría:** {jefe_seleccionado.get('categoria', '')} | **Departamento:** {jefe_seleccionado.get('departamento', '')}")
    
    with tab2:
        st.subheader("Funcionarios para Firmas")
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            # ELABORÓ
            st.markdown("**✍️ ELABORÓ**")
            sel_elaboro = st.selectbox("Seleccionar:", nombres, key="sel_elaboro")
            elaboro_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_elaboro), {})
            
            # Campos editables para ELABORÓ
            cargo_elaboro = st.text_input("Cargo de Elaboró:", 
                                         value=elaboro_seleccionado.get('categoria', ''),
                                         key="cargo_elaboro")
        
        with col_f2:
            # REVISÓ
            st.markdown("**✍️ REVISÓ**")
            sel_reviso = st.selectbox("Seleccionar:", nombres, key="sel_reviso")
            reviso_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_reviso), {})
            
            # Campos editables para REVISÓ
            cargo_reviso = st.text_input("Cargo de Revisó:", 
                                        value=reviso_seleccionado.get('categoria', ''),
                                        key="cargo_reviso")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # CONFORME
            st.markdown("**✍️ CONFORME**")
            sel_conforme = st.selectbox("Seleccionar:", nombres, key="sel_conforme")
            conforme_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_conforme), {})
            
            # Campos editables para CONFORME
            cargo_conforme = st.text_input("Cargo de Conforme:", 
                                          value=conforme_seleccionado.get('categoria', ''),
                                          key="cargo_conforme")
        
        with col_c2:
            # AUTORIZA PAGO SALDO
            st.markdown("**✍️ AUTORIZA PAGO SALDO**")
            sel_autoriza = st.selectbox("Seleccionar:", nombres, key="sel_autoriza")
            autoriza_seleccionado = next((i for i in usuarios_db if i.get('nombre') == sel_autoriza), {})
            
            # Campos editables para AUTORIZA
            cargo_autoriza = st.text_input("Cargo de Autoriza:", 
                                          value=autoriza_seleccionado.get('categoria', ''),
                                          key="cargo_autoriza")
    
    # Botón de guardar
    if st.button("✅ GUARDAR CONFIGURACIÓN DE FIRMAS", type="primary", use_container_width=True):
        # Reunir todos los datos
        config_firmas = {
            # Solicitante
            "solicitante": {
                "nombre": sel_solicitante,
                "categoria": jefe_seleccionado.get('categoria', ''),
                "departamento": jefe_seleccionado.get('departamento', ''),
                "tel_oficina": tel_editado,
                "cp": cp_editado,
                "matricula": jefe_seleccionado.get('matricula', '')
            },
            # Elaboró
            "elaboro": {
                "nombre": sel_elaboro,
                "cargo": cargo_elaboro,
                "matricula": elaboro_seleccionado.get('matricula', '')
            },
            # Revisó
            "reviso": {
                "nombre": sel_reviso,
                "cargo": cargo_reviso,
                "matricula": reviso_seleccionado.get('matricula', '')
            },
            # Conforme
            "conforme": {
                "nombre": sel_conforme,
                "cargo": cargo_conforme,
                "matricula": conforme_seleccionado.get('matricula', '')
            },
            # Autoriza Pago Saldo
            "autoriza": {
                "nombre": sel_autoriza,
                "cargo": cargo_autoriza,
                "matricula": autoriza_seleccionado.get('matricula', '')
            }
        }
        
        # Guardar en JSON
        gestionar_config_permanente("firmas", config_firmas)
        st.success("✅ Configuración de firmas guardada")
        st.rerun()


# --- MODAL: REUTILIZAR FOLIO (DESDE HISTORIAL) ---
@st.dialog("♻️ Reutilizar Folio")
def modal_reutilizar_folio(datos, tipo_doc, u):
    st.warning(f"Reutilizando folio: **{datos.get('folio')}**")
    
    # Mostrar fecha original
    fecha_original = datos.get('fecha_elaboracion', datos.get('fecha_creacion', ''))
    st.info(f"📅 Fecha original del registro: {fecha_original}")
    
    # Control de fecha según rol
    if u.get('rol') == "Administrador":
        fecha_nueva = st.date_input(
            "Fecha del nuevo registro:", 
            value=datetime.now(),
            key="fecha_reutilizar"
        )
        fecha_str = fecha_nueva.strftime("%d/%m/%Y")
        st.caption("✅ Como administrador, puedes modificar la fecha")
    else:
        fecha_str = datetime.now().strftime("%d/%m/%Y")
        st.write(f"📅 Fecha del nuevo registro: **{fecha_str}**")
        st.caption("ℹ️ La fecha se asignará automáticamente (hoy)")
    
    # Mostrar datos a reutilizar
    with st.expander("📋 Datos a reutilizar", expanded=False):
        st.json(datos)
    
    # Confirmación
    if st.button("✅ CONFIRMAR REUTILIZACIÓN", type="primary", use_container_width=True):
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





# ============================================
# VISTA: PLIEGO DE COMISIÓN (VERSIÓN FINAL)
# ============================================
def vista_pliego(u):
    st.title("📋 Gestión de Pliego de Comisión")

    df_p = obtener_pliegos()

    # ============================================
    # CARGAR CONFIGURACIÓN DE FUNCIONARIO Y FIRMAS
    # ============================================
    func_fijo = gestionar_config_permanente("funcionario")
    if func_fijo:
        u.update({
            "f_solicitante": func_fijo.get('nombre', ''),
            "f_categoria": func_fijo.get('categoria', ''),
            "f_area": func_fijo.get('departamento', ''),
            "f_tel": func_fijo.get('tel_oficina', '')
        })

    # Cargar configuración completa de firmas
    firmas_config = gestionar_config_permanente("firmas")
    if firmas_config:
        u.update({
            # Solicitante (puede venir de firmas)
            "f_solicitante": firmas_config.get('solicitante', {}).get('nombre', u.get('f_solicitante', '')),
            "f_categoria": firmas_config.get('solicitante', {}).get('categoria', u.get('f_categoria', '')),
            "f_area": firmas_config.get('solicitante', {}).get('departamento', u.get('f_area', '')),
            "f_tel": firmas_config.get('solicitante', {}).get('tel_oficina', u.get('f_tel', '')),
            "f_cp": firmas_config.get('solicitante', {}).get('cp', u.get('f_cp', '')),
            
            # Elaboró
            "elaboro_nombre": firmas_config.get('elaboro', {}).get('nombre', ''),
            "elaboro_cargo": firmas_config.get('elaboro', {}).get('cargo', ''),
            
            # Revisó
            "reviso_nombre": firmas_config.get('reviso', {}).get('nombre', ''),
            "reviso_cargo": firmas_config.get('reviso', {}).get('cargo', ''),
            
            # Conforme
            "conforme_nombre": firmas_config.get('conforme', {}).get('nombre', ''),
            "conforme_cargo": firmas_config.get('conforme', {}).get('cargo', ''),
            
            # Autoriza Pago Saldo
            "autoriza_nombre": firmas_config.get('autoriza', {}).get('nombre', ''),
            "autoriza_cargo": firmas_config.get('autoriza', {}).get('cargo', '')
        })

    with st.expander("🔍 BUSCAR PLIEGO EN HISTORIAL", expanded=False):
        if not df_p.empty and 'folio' in df_p.columns:
            if u.get('rol') == "Administrador":
                opciones = df_p['folio'].unique().tolist()
            else:
                opciones = df_p[df_p['matricula'] == u.get('matricula')]['folio'].unique().tolist()
            
            sel_busqueda = st.selectbox("Cargar registro anterior:", ["-- Seleccionar --"] + opciones)
            if sel_busqueda != "-- Seleccionar --":
                reg = df_p[df_p['folio'] == sel_busqueda].iloc[0].to_dict()
                u.update(reg)
                st.session_state['folio_actual'] = sel_busqueda
                st.success(f"Pliego {sel_busqueda} cargado.")

    # --- CONFIGURACIÓN INICIAL (ahora desde Excel) ---
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










    # Obtener el folio actual
    f_id = st.session_state.get('folio_actual', u.get('folio', '---'))
    st.subheader(f"📄 Folio: {f_id}")

    # ============================================
    # CONSTRUIR datos_html
    # ============================================
    fecha_actual = datetime.now()
    
    # Obtener datos adicionales del usuario
    grupo_jerarquico = u.get('gj', '')
    tipo_contrato = u.get('tipo_contrato', '')
    departamento = u.get('departamento', '')
    f_cp = u.get('f_cp', '')
    
    # Fechas por defecto
    fecha_inicio = u.get('fecha_inicio', fecha_actual.strftime("%d/%m/%Y"))
    fecha_fin = u.get('fecha_fin', fecha_actual.strftime("%d/%m/%Y"))
    
    # Datos de session_state (prioridad)
    fecha_inicio = st.session_state.get('nuevo_fecha_inicio', fecha_inicio)
    fecha_fin = st.session_state.get('nuevo_fecha_fin', fecha_fin)
    transporte = st.session_state.get('nuevo_transporte', u.get('medio_transporte', ''))
    chofer = st.session_state.get('nuevo_chofer', u.get('chofer', ''))
    acompanante = st.session_state.get('nuevo_acompanante', u.get('acompañante', ''))

    # Anticipos (valores por defecto)
    anticipos = {
        'anticipo_viaticos': u.get('anticipo_viaticos', '0.00'),
        'anticipo_gasolina': u.get('anticipo_gasolina', '0.00'),
        'anticipo_peaje': u.get('anticipo_peaje', '0.00'),
        'anticipo_transporte_t': u.get('anticipo_transporte_t', '0.00'),
        'anticipo_avion': u.get('anticipo_avion', '0.00'),
        'total_anticipo': u.get('total_anticipo', '0.00'),
        'subtotal_sin_avion': u.get('subtotal_sin_avion', '0.00')
    }
    
    # Comprobaciones (reverso)
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
    
    # Firmas
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
    
    # ============================================
    # DATOS DEL EMPLEADO (prioridad a persona de paso)
    # ============================================
    if st.session_state.get('nuevo_nombre_externo'):
        nombre_empleado = st.session_state['nuevo_nombre_externo']
        matricula = st.session_state['nuevo_matricula_externo']
        puesto = st.session_state['nuevo_puesto_externo']
    else:
        nombre_empleado = u.get('nombre', '').upper()
        matricula = u.get('matricula', '')
        puesto = u.get('puesto', '')
    
    # ============================================
    # TESORERÍA (prioridad a session_state)
    # ============================================
    bueno_por_monto = st.session_state.get('nuevo_bueno_por', u.get('bueno_por_monto', ''))
    recibi_monto = st.session_state.get('nuevo_recibi', u.get('recibi_monto', ''))
    recibi_letras = st.session_state.get('nuevo_recibi_letras', u.get('recibi_letras', ''))
    
    datos_html = {
        # Datos básicos
        "m_folio": f_id,
        "m_fecha_creacion": fecha_actual.strftime("%d/%m/%Y"),
        "logo_base64": get_base64("assets/logoimss.png"),
        
        # Datos del empleado
        "nombre_empleado": nombre_empleado,
        "matricula": matricula,
        "puesto": puesto,
        "departamento_empleado": departamento,
        "grupo_jerarquico": grupo_jerarquico,
        "tipo_contrato": tipo_contrato,
        
        # Datos del solicitante
        "f_solicitante": u.get('f_solicitante', '').upper(),
        "f_categoria": u.get('f_categoria', '').upper(),
        "f_area": u.get('f_area', '').upper(),
        "f_tel": u.get('f_tel', ''),
        "f_cp": f_cp,
        
        # Datos de la comisión
        "m_destino": st.session_state.get('nuevo_destino', u.get('m_destino', '')),
        "m_objeto": st.session_state.get('nuevo_motivo', u.get('m_objeto', '')),
        "m_inicio": fecha_inicio,
        "m_fin": fecha_fin,
        "m_medio_transporte": transporte,
        "m_chofer": chofer,
        "m_acompañante": acompanante,
        "dias_comision": u.get('dias_comision', ''),
        
        # Anticipos
        **anticipos,
        
        # Observaciones
        "observaciones": u.get('observaciones', ''),
        
        # Comprobaciones (reverso)
        **comprobaciones,
        
        # Firmas
        **firmas,
        
        # Tesorería
        "bueno_por_monto": bueno_por_monto,
        "recibi_monto": recibi_monto,
        "recibi_letras": recibi_letras,
        
        # Variables adicionales
        "mostrar_bloque_especial": u.get('mostrar_bloque_especial', False),
        "rol_usuario": u.get('rol', 'Usuario')
    }

    # ============================================
    # BOTONES
    # ============================================
    st.divider()
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
    
    with col1:
        if st.button("🖨️ IMPRIMIR", use_container_width=True, type="primary"):
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
        if st.button("➕ NUEVO TRASLADO", use_container_width=True, type="primary"):
            modal_nuevo_traslado(u, df_p)

    with col3:
        if u.get('rol') == "Administrador":
            if st.button("👤 NUEVO FUNCIONARIO", use_container_width=True):
                modal_configurar_funcionario()
        else:
            st.button("👤 NUEVO FUNCIONARIO", use_container_width=True, disabled=True)

    with col4:
        st.markdown("")

    # ============================================
    # VISTA PREVIA DEL PLIEGO
    # ============================================
    try:
        with open("templates/pliego_template.html", "r", encoding="utf-8") as f:
            t = Template(f.read())
            st.components.v1.html(t.render(datos_html), height=1000, scrolling=True)
    except Exception as e:
        st.warning(f"Cargando vista previa... {e}")
    
    # ============================================
    # BOTÓN DE GUARDADO
    # ============================================
    if st.button("💾 FINALIZAR Y GUARDAR EN EXCEL", use_container_width=True, type="secondary"):
        motivo = st.session_state.get('nuevo_motivo', u.get('m_objeto', ''))
        if not motivo:
            st.error("Faltan campos obligatorios.")
        else:
            modal_confirmar_guardado(datos_html, u)


# ============================================
# VISTA: TRASLADOS LOCALES (CON BUSCADOR POR FOLIO)
# ============================================
def vista_traslados(u):
    st.header("🚑 Gestión de Traslados Locales")

    asegurar_hojas_excel()

    try:
        df_traslados = obtener_traslados_locales()
        df_usuarios = pd.DataFrame(obtener_lista_usuarios())
        
        if df_usuarios.empty:
            df_usuarios = pd.DataFrame(columns=["matricula", "nombre"])
                
    except Exception as e:
        st.error(f"Error al cargar base de datos: {e}")
        return

    # ============================================
    # BUSCADORES
    # ============================================
    with st.expander("🔍 Búsqueda Rápida de Pacientes"):
        nss_buscar = st.text_input("Buscar por NSS o Nombre del Paciente")
        if nss_buscar and not df_traslados.empty:
            paciente_encontrado = df_traslados[
                (df_traslados['nss'].astype(str).str.contains(nss_buscar, na=False)) | 
                (df_traslados['paciente'].str.contains(nss_buscar, case=False, na=False))
            ]
            if not paciente_encontrado.empty:
                ult = paciente_encontrado.iloc[-1]
                st.session_state.p_nombre = ult['paciente']
                st.session_state.p_nss = ult['nss']
                st.success(f"✅ Datos recuperados de: {st.session_state.p_nombre}")

    with st.expander("🔍 BUSCAR POR FOLIO", expanded=False):
        if not df_traslados.empty and 'folio' in df_traslados.columns:
            opciones_folio = df_traslados['folio'].unique().tolist()
            folio_sel = st.selectbox("Seleccionar folio:", ["-- Seleccionar --"] + opciones_folio)
            if folio_sel != "-- Seleccionar --":
                reg = df_traslados[df_traslados['folio'] == folio_sel].iloc[0].to_dict()
                st.session_state.p_nombre = reg.get('paciente', '')
                st.session_state.p_nss = reg.get('nss', '')
                st.session_state.f_temp = reg.get('folio', '')
                st.success(f"✅ Datos de {folio_sel} cargados")
                st.rerun()

    st.subheader("📝 Nuevo Registro de Traslado")
    
    with st.form("form_traslado_completo", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            if 'f_temp' not in st.session_state or not st.session_state.get('f_temp'):
                st.session_state.f_temp = generar_folio_local(df_traslados)
                st.session_state.fecha_temp = datetime.now().strftime("%d/%m/%Y")
            
            folio = st.text_input("Folio", value=st.session_state.f_temp)
            fecha_creacion = st.text_input("Fecha de Creación", value=st.session_state.fecha_temp, disabled=True)
            
            p_nom = st.text_input("Paciente *", value=st.session_state.get('p_nombre', ''))
            nss_in = st.text_input("NSS", value=st.session_state.get('p_nss', ''))

        with c2:
            lista_emp = []
            if not df_usuarios.empty and 'matricula' in df_usuarios.columns and 'nombre' in df_usuarios.columns:
                lista_emp = [f"{row['matricula']} - {row['nombre']}" for _, row in df_usuarios.iterrows()]
            
            emp_sel = st.selectbox("Asignar Empleado Comisionado *", ["-- Seleccionar --"] + lista_emp)
            
            f_h_mov = st.datetime_input("Fecha/Hora Movimiento", value=datetime.now())
            destino = st.text_input("Destino *")
            servicio = st.text_input("Servicio / Motivo")

        with c3:
            cama = st.text_input("Número de Cama")
            
            opciones_req = ["Ninguno", "Oxígeno", "Incubadora", "Camilla", "Silla de Ruedas", "Otro"]
            requiere = st.selectbox("Requiere", opciones_req)
            
            estatus_opciones = ["Programado", "En Curso", "Completado", "Cancelado"]
            estatus = st.selectbox("Estatus del Traslado", estatus_opciones, index=2)
            
            observaciones = st.text_area("Observaciones Adicionales", height=100)

        st.markdown("***Los campos con * son obligatorios**")
        
        if st.form_submit_button("💾 GUARDAR REGISTRO COMPLETO", type="primary", use_container_width=True):
            if emp_sel == "-- Seleccionar --" or not p_nom or not destino:
                st.error("⚠️ El Empleado, Paciente y Destino son obligatorios.")
            else:
                nuevo = {
                    "folio": folio,
                    "fecha_creacion": fecha_creacion,
                    "paciente": p_nom.upper(),
                    "nss": nss_in,
                    "fecha_hora": f_h_mov.strftime("%Y-%m-%d %H:%M"),
                    "empleado_comisionado": emp_sel,
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
                    for key in ['f_temp', 'p_nombre', 'p_nss']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
                else:
                    st.error(f"Error crítico al escribir en Excel")
    
    st.divider()
    st.subheader("📋 Registro de Traslados Locales")
    
    if not df_traslados.empty:
        col_est1, col_est2, col_est3, col_est4 = st.columns(4)
        with col_est1:
            st.metric("Total Traslados", len(df_traslados))
        with col_est2:
            if 'estatus' in df_traslados.columns:
                completados = len(df_traslados[df_traslados['estatus'] == "Completado"])
                st.metric("Completados", completados)
        with col_est3:
            if 'estatus' in df_traslados.columns:
                programados = len(df_traslados[df_traslados['estatus'] == "Programado"])
                st.metric("Programados", programados)
        with col_est4:
            if 'estatus' in df_traslados.columns:
                cancelados = len(df_traslados[df_traslados['estatus'] == "Cancelado"])
                st.metric("Cancelados", cancelados)
        
        columnas_mostrar = ['fecha_creacion', 'folio', 'paciente', 'destino', 'empleado_comisionado', 'estatus']
        columnas_existentes = [col for col in columnas_mostrar if col in df_traslados.columns]
        
        st.dataframe(
            df_traslados[columnas_existentes].sort_values('fecha_creacion', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay registros de traslados")


# ============================================
# VISTA: CONFIGURACIÓN (Usuarios, Vehículos, Hospitales)
# ============================================
def vista_configuracion():
    st.subheader("⚙️ Configuración del Sistema")

    t1, t2, t3 = st.tabs(["👤 Usuarios", "🚗 Vehículos", "🏥 Hospitales"])

    # ==========================================
    # PESTAÑA 1: USUARIOS
    # ==========================================
    with t1:
        try:
            xls = pd.ExcelFile(DB_FILE)
            df_usuarios = pd.read_excel(xls, sheet_name='usuarios').fillna("")
            hojas_restantes = {s: pd.read_excel(xls, s) for s in xls.sheet_names if s != 'usuarios'}
        except:
            df_usuarios = pd.DataFrame(columns=["matricula","nombre","apellido_p","apellido_m","curp","rfc","departamento","tipo_contrato","gj","puesto","password","rol","estatus"])
            hojas_restantes = {}

        # Registro
        with st.popover("➕ Registrar Nuevo Usuario"):
            with st.form("f_u", clear_on_submit=True):
                c1, c2 = st.columns(2)
                mat = c1.text_input("Matrícula")
                nom = c2.text_input("Nombre(s)")
                ap_p = c1.text_input("Apellido Paterno")
                ap_m = c2.text_input("Apellido Materno")
                curp = c1.text_input("CURP")
                rfc = c2.text_input("RFC")
                c3, c4, c5 = st.columns(3)
                depto = c3.text_input("Departamento")
                tipoc = c4.text_input("Tipo de Contrato")
                gj = c5.text_input("G-J")
                pue = c1.text_input("Puesto")
                pas = c2.text_input("Contraseña", type="password")
                rol = c1.selectbox("Rol", ["Usuario", "Administrador"])
                est = c2.selectbox("Estatus", ["Alta", "Baja", "Baja Temporal"])

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
                            "puesto": pue, 
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

        # Edición
        st.divider()
        st.write("### 🔑 Editar Usuario / Contraseña")
        mat_edit = st.text_input("Matrícula a buscar para editar")
        if mat_edit:
            df_usuarios['matricula'] = df_usuarios['matricula'].astype(str).str.replace(r'\.0$', '', regex=True)
            idx = df_usuarios.index[df_usuarios['matricula'] == str(mat_edit).strip()].tolist()
            if idx:
                u_idx = idx[0]
                with st.form("edit_u"):
                    e_puesto = st.text_input("Puesto", value=df_usuarios.at[u_idx, 'puesto'])
                    e_pass = st.text_input("Contraseña", value=df_usuarios.at[u_idx, 'password'])
                    e_est = st.selectbox("Estatus", ["Alta", "Baja", "Baja Temporal"], 
                                        index=["Alta", "Baja", "Baja Temporal"].index(df_usuarios.at[u_idx, 'estatus']))
                    if st.form_submit_button("Actualizar Datos"):
                        df_usuarios.at[u_idx, 'puesto'] = e_puesto
                        df_usuarios.at[u_idx, 'password'] = e_pass
                        df_usuarios.at[u_idx, 'estatus'] = e_est
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_usuarios.to_excel(writer, sheet_name='usuarios', index=False)
                            for n, d in hojas_restantes.items(): 
                                d.to_excel(writer, sheet_name=n, index=False)
                        st.success("✨ Actualizado")
                        st.rerun()

    # ==========================================
    # PESTAÑA 2: VEHÍCULOS
    # ==========================================
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
                v_tip = c1.text_input("Tipo")
                v_ecc = c2.text_input("ECCO")
                v_pla = c1.text_input("Placas")
                v_mar = c2.text_input("Marca")
                v_mod = c1.text_input("Modelo")
                v_kma = c2.number_input("Kilometraje Actual", min_value=0)
                v_kms = st.text_input("KM Próximo Servicio")
                v_est = st.selectbox("Estatus", ["Alta", "Baja", "Mantenimiento"])
                if st.form_submit_button("Guardar Vehículo"):
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
        ecco_edit = st.text_input("Ingresa ECCO para actualizar")
        if ecco_edit:
            df_v['ecco'] = df_v['ecco'].astype(str).str.replace(r'\.0$', '', regex=True)
            idx_v = df_v.index[df_v['ecco'] == str(ecco_edit).strip()].tolist()
            if idx_v:
                v_idx = idx_v[0]
                with st.form("edit_v"):
                    n_km = st.number_input("Nuevo KM", value=int(df_v.at[v_idx, 'km_actual']))
                    n_est = st.selectbox("Estatus", ["Alta", "Baja", "Mantenimiento"], 
                                        index=["Alta", "Baja", "Mantenimiento"].index(df_v.at[v_idx, 'estatus']))
                    if st.form_submit_button("Actualizar Unidad"):
                        df_v.at[v_idx, 'km_actual'] = n_km
                        df_v.at[v_idx, 'estatus'] = n_est
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_v.to_excel(writer, sheet_name='vehiculos', index=False)
                            for n, d in hojas_restantes.items(): 
                                d.to_excel(writer, sheet_name=n, index=False)
                        st.success("✨ Unidad actualizada")
                        st.rerun()

    # ==========================================
    # PESTAÑA 3: HOSPITALES
    # ==========================================
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
                h_est = st.text_input("Estado")
                h_nom = st.text_input("Nombre Hospital")
                h_dir = st.text_input("Dirección")
                h_ac = st.radio("¿Alto Costo?", ["No", "Sí"])
                if st.form_submit_button("Guardar Hospital"):
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
        h_sel = st.selectbox("Selecciona hospital para modificar", [""] + df_h['nombre_hosp'].tolist())
        if h_sel:
            h_idx = df_h.index[df_h['nombre_hosp'] == h_sel][0]
            with st.form("edit_h"):
                n_dir = st.text_input("Dirección", value=df_h.at[h_idx, 'direccion'])
                n_ac = st.radio("Alto Costo", ["No", "Sí"], index=0 if df_h.at[h_idx, 'alto_costo'] == "No" else 1)
                if st.form_submit_button("Actualizar Hospital"):
                    df_h.at[h_idx, 'direccion'] = n_dir
                    df_h.at[h_idx, 'alto_costo'] = n_ac
                    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                        df_h.to_excel(writer, sheet_name='hospitales', index=False)
                        for n, d in hojas_restantes.items(): 
                            d.to_excel(writer, sheet_name=n, index=False)
                    st.success("✨ Hospital actualizado")
                    st.rerun()


# ============================================
# VISTA: HISTORIAL MAESTRO (CON REUTILIZACIÓN)
# ============================================
def vista_historial_maestro(u):
    st.header("📊 Centro de Control de Registros")

    asegurar_hojas_excel()

    try:
        # 1. CARGA UNIFICADA
        df_p = obtener_pliegos()
        df_t = obtener_traslados_locales()
        
        if not df_p.empty:
            df_p['tipo_doc'] = "Pliego/Informe"
            if 'nombre_comisionado' in df_p.columns:
                df_p = df_p.rename(columns={'nombre_comisionado': 'sujeto'})
            else:
                df_p['sujeto'] = ""
        
        if not df_t.empty:
            df_t['tipo_doc'] = "Traslado Local"
            if 'paciente' in df_t.columns:
                df_t = df_t.rename(columns={'paciente': 'sujeto'})
            else:
                df_t['sujeto'] = ""

        # 2. FILTROS
        with st.container():
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                busqueda = st.text_input("🔍 Buscar por Folio, Sujeto o NSS", key="bus_uni")
            with c2:
                tipo_filtro = st.selectbox("Tipo de Registro", ["Todos", "Pliegos", "Traslados"])
            with c3:
                status_filtro = st.selectbox("Filtrar Estatus", ["Todos", "Programado", "En Curso", "Completado", "Cancelado"])

        # 3. UNIFICACIÓN
        if not df_p.empty:
            if 'fecha_elaboracion' in df_p.columns:
                df_p["fecha_evento"] = df_p["fecha_elaboracion"]
            else:
                df_p["fecha_evento"] = datetime.now().strftime("%d/%m/%Y")
        
        if not df_t.empty:
            if 'fecha_creacion' in df_t.columns:
                df_t["fecha_evento"] = df_t["fecha_creacion"]
            else:
                df_t["fecha_evento"] = datetime.now().strftime("%d/%m/%Y")

        # Crear DataFrame unificado
        if not df_p.empty and not df_t.empty:
            df_unificado = pd.concat([df_p, df_t], ignore_index=True)
        elif not df_p.empty:
            df_unificado = df_p.copy()
        elif not df_t.empty:
            df_unificado = df_t.copy()
        else:
            df_unificado = pd.DataFrame()
        
        # Ordenar por fecha_evento
        if not df_unificado.empty and 'fecha_evento' in df_unificado.columns:
            df_unificado = df_unificado.sort_values(by="fecha_evento", ascending=False)

        # Aplicar filtros
        if not df_unificado.empty:
            if busqueda:
                df_unificado = df_unificado[df_unificado.apply(lambda row: busqueda.lower() in str(row).lower(), axis=1)]
            if tipo_filtro == "Pliegos" and 'tipo_doc' in df_unificado.columns: 
                df_unificado = df_unificado[df_unificado['tipo_doc'] == "Pliego/Informe"]
            if tipo_filtro == "Traslados" and 'tipo_doc' in df_unificado.columns: 
                df_unificado = df_unificado[df_unificado['tipo_doc'] == "Traslado Local"]
            if status_filtro != "Todos" and 'estatus' in df_unificado.columns: 
                df_unificado = df_unificado[df_unificado['estatus'] == status_filtro]

        # 4. TABLA INTERACTIVA
        st.write(f"Mostrando {min(len(df_unificado), 50) if not df_unificado.empty else 0} registros recientes")
        
        if not df_unificado.empty:
            cols_disponibles = []
            for col in ['fecha_evento', 'folio', 'sujeto', 'tipo_doc', 'estatus']:
                if col in df_unificado.columns:
                    cols_disponibles.append(col)
            
            if not cols_disponibles:
                cols_disponibles = df_unificado.columns[:5].tolist()
            
            df_display = df_unificado[cols_disponibles].head(50)
            
            edited_df = st.data_editor(
                df_display,
                column_config={
                    "estatus": st.column_config.SelectboxColumn("Estatus", options=["Programado", "En Curso", "Completado", "Cancelado"]),
                    "folio": st.column_config.TextColumn("Folio"),
                    "fecha_evento": st.column_config.TextColumn("Fecha")
                },
                use_container_width=True,
                hide_index=True,
                key="main_editor"
            )

            # 5. BOTONES DE ACCIÓN
            st.divider()
            col_acc1, col_acc2 = st.columns(2)
            
            with col_acc1:
                if st.button("💾 Guardar Cambios", type="primary", use_container_width=True):
                    actualizar_base_datos_maestra(edited_df)
                    st.success("✅ Base de datos actualizada.")
                    st.rerun()

            with col_acc2:
                if 'folio' in df_unificado.columns:
                    folio_a_clonar = st.selectbox("Seleccionar folio para reutilizar:", ["-- Seleccionar --"] + df_unificado['folio'].tolist())
                    if st.button("♻️ REUTILIZAR FOLIO", use_container_width=True):
                        if folio_a_clonar != "-- Seleccionar --":
                            datos_completos = df_unificado[df_unificado['folio'] == folio_a_clonar].iloc[0].to_dict()
                            tipo = datos_completos.get('tipo_doc', '')
                            modal_reutilizar_folio(datos_completos, tipo, u)
        else:
            st.info("No hay registros para mostrar")
            
    except Exception as e:
        st.error(f"Error al cargar historial: {e}")
        with st.expander("Ver detalles del error"):
            st.write(f"Tipo de error: {type(e).__name__}")
            st.write(f"DataFrame pliegos vacío? {df_p.empty if 'df_p' in locals() else 'No definido'}")
            st.write(f"DataFrame traslados vacío? {df_t.empty if 'df_t' in locals() else 'No definido'}")


# ============================================
# VISTA: ESTADÍSTICAS ADMIN
# ============================================
def vista_estadisticas_admin(u):
    st.title("📊 Panel de Inteligencia Administrativa")
    
    try:
        asegurar_hojas_excel()
        
        xls = pd.ExcelFile(DB_FILE)
        
        df_p = pd.read_excel(xls, sheet_name='pliegos').fillna("") if 'pliegos' in xls.sheet_names else pd.DataFrame()
        df_t = pd.read_excel(xls, sheet_name='traslados_locales').fillna("") if 'traslados_locales' in xls.sheet_names else pd.DataFrame()
        df_v = pd.read_excel(xls, sheet_name='vehiculos').fillna(0) if 'vehiculos' in xls.sheet_names else pd.DataFrame()
        df_inf = pd.read_excel(xls, sheet_name='informes').fillna("") if 'informes' in xls.sheet_names else pd.DataFrame()
        
        otras_hojas = {sh: pd.read_excel(xls, sh) for sh in xls.sheet_names if sh not in ['vehiculos', 'pliegos', 'traslados_locales', 'informes']}

        st.subheader("📈 Indicadores de Desempeño")
        
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            st.markdown("### 1. Traslados Locales")
            if not df_t.empty and 'estatus' in df_t.columns:
                fig1 = px.bar(df_t['estatus'].value_counts().reset_index(), x='index', y='estatus', 
                              color='index', labels={'index':'Estatus', 'estatus':'Total'})
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No hay datos de traslados")

        with row1_col2:
            st.markdown("### 2. Traslados Foráneos (Pliegos)")
            if not df_p.empty and 'destino' in df_p.columns:
                fig2 = px.pie(df_p, names='destino', hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No hay datos de pliegos")

        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            st.markdown("### 3. Frecuencia de Hospitales")
            if not df_t.empty and 'destino' in df_t.columns:
                destinos_t = df_t['destino'].dropna()
                destinos_p = df_p['destino'].dropna() if not df_p.empty else pd.Series()
                hosp_total = pd.concat([destinos_t, destinos_p])
                if not hosp_total.empty:
                    fig3 = px.bar(hosp_total.value_counts().head(8), orientation='h', color_discrete_sequence=['#007155'])
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("Sin datos de destinos")

        with row2_col2:
            st.markdown("### 4. Productividad Choferes")
            if not df_t.empty and 'empleado_comisionado' in df_t.columns:
                fig4 = px.bar(df_t['empleado_comisionado'].value_counts().head(10), color_discrete_sequence=['#1f77b4'])
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Sin datos de choferes")

        st.divider()
        st.markdown("### 5. Estado de Vehículos (Mantenimiento)")
        
        if not df_v.empty and all(col in df_v.columns for col in ['km_servicio', 'km_actual', 'marca', 'ecco']):
            df_v['km_restantes'] = df_v['km_servicio'] - df_v['km_actual']
            df_v['nombre_unidad'] = df_v['marca'] + " (ECCO: " + df_v['ecco'].astype(str) + ")"
            fig5 = px.bar(df_v, x='km_restantes', y='nombre_unidad', orientation='h',
                          color='km_restantes', color_continuous_scale='RdYlGn',
                          title="Kilómetros para el Próximo Servicio")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No hay datos de vehículos")

        st.divider()
        st.subheader("🛠️ Gestión Directa de Unidades")
        
        if not df_v.empty and 'ecco' in df_v.columns:
            col_sel, col_info = st.columns([1, 2])
            
            with col_sel:
                vehiculo_sel = st.selectbox("Seleccione unidad para gestionar:", ["-- Unidades --"] + df_v['ecco'].tolist())
            
            if vehiculo_sel != "-- Unidades --":
                datos_v = df_v[df_v['ecco'] == vehiculo_sel].iloc[0]
                
                st.divider()
                st.subheader(f"📋 Historial de Servicios: {vehiculo_sel}")
                
                try:
                    df_m = pd.read_excel(DB_FILE, sheet_name='mantenimientos').fillna("") if 'mantenimientos' in xls.sheet_names else pd.DataFrame()
                    historial_v = df_m[df_m['ecco'] == vehiculo_sel].sort_values(by='fecha', ascending=False) if not df_m.empty else pd.DataFrame()
                    
                    if not historial_v.empty:
                        cols_mostrar = [c for c in ['fecha', 'tipo_servicio', 'lugar', 'km_registro', 'observaciones'] if c in historial_v.columns]
                        st.table(historial_v[cols_mostrar].head(10))
                    else:
                        st.info("No hay mantenimientos previos registrados.")
                except:
                    st.info("No hay mantenimientos previos registrados.")

                with st.expander(f"🛠️ Registrar Nuevo Servicio para {vehiculo_sel}"):
                    with st.form("form_nuevo_servicio"):
                        c1, c2 = st.columns(2)
                        with c1:
                            f_serv = st.date_input("Fecha del Servicio", value=datetime.now())
                            t_serv = st.selectbox("Tipo de Mantenimiento", ["Cambio de Aceite", "Frenos", "Llantas", "Motor", "Estético", "Traslado"])
                            lugar_serv = st.text_input("Lugar / Taller", placeholder="Ej. Taller Central")
                        with c2:
                            km_recorridos = st.number_input("Kilómetros recorridos:", min_value=0)
                            prox_mant = st.number_input("Próximo servicio a los (KM):", value=int(datos_v['km_servicio']) if 'km_servicio' in datos_v else 0)
                            obs = st.text_area("Notas/Detalles")
                        
                        if st.form_submit_button("💾 Guardar y Actualizar"):
                            idx = df_v.index[df_v['ecco'] == vehiculo_sel].tolist()[0]
                            df_v.at[idx, 'km_actual'] = datos_v['km_actual'] + km_recorridos
                            df_v.at[idx, 'km_servicio'] = prox_mant
                            
                            nuevo_m = {
                                "ecco": vehiculo_sel,
                                "fecha": f_serv.strftime("%d/%m/%Y"),
                                "tipo_servicio": t_serv,
                                "lugar": lugar_serv,
                                "km_registro": df_v.at[idx, 'km_actual'],
                                "observaciones": obs
                            }
                            
                            try:
                                df_m_existente = pd.read_excel(DB_FILE, sheet_name='mantenimientos') if 'mantenimientos' in pd.ExcelFile(DB_FILE).sheet_names else pd.DataFrame()
                                df_m_final = pd.concat([df_m_existente, pd.DataFrame([nuevo_m])], ignore_index=True)
                            except:
                                df_m_final = pd.DataFrame([nuevo_m])
                            
                            with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                                df_v.to_excel(writer, sheet_name='vehiculos', index=False)
                                df_m_final.to_excel(writer, sheet_name='mantenimientos', index=False)
                                for h, d in otras_hojas.items():
                                    if h not in ['vehiculos', 'mantenimientos']: 
                                        d.to_excel(writer, sheet_name=h, index=False)
                            
                            st.success("✅ Vehículo y Historial actualizados.")
                            st.rerun()
        else:
            st.info("No hay vehículos registrados")
                            
    except Exception as e:
        st.error(f"Error en el sistema de estadísticas: {e}")

# ============================================
# VISTA: INFORME DE COMISIÓN (VERSIÓN CORREGIDA CON PERMISOS)
# ============================================
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
                    # Filtrar según el rol del usuario
                    if u.get('rol') == "Administrador":
                        df_filtrado = df_p  # Admin ve todos
                    else:
                        # Usuario normal: solo sus pliegos
                        df_filtrado = df_p[df_p['matricula'] == u.get('matricula')]
                    
                    if not df_filtrado.empty:
                        st.dataframe(
                            df_filtrado[['folio', 'chofer', 'destino', 'fecha_elaboracion']],
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        lista_folios = ["-- Seleccionar --"] + df_filtrado['folio'].tolist()
                        folio_sel = st.selectbox("Seleccione Folio:", lista_folios, key="selector_folio_modal")
                        
                        if st.button("📥 CARGAR PLIEGO", type="primary", use_container_width=True):
                            if folio_sel != "-- Seleccionar --":
                                datos_cargados = df_filtrado[df_filtrado['folio'] == folio_sel].iloc[0].to_dict()
                                st.session_state.datos_pliego_cargado = datos_cargados
                                st.success(f"✅ Pliego {folio_sel} cargado")
                                st.rerun()
                    else:
                        st.info("No hay pliegos disponibles para tu usuario")
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
        st.text_input("Destino", value=datos_p.get('destino', 'N/A'), disabled=True, key="destino_display")
        st.text_input("Paciente", value=datos_p.get('paciente', 'N/A'), disabled=True, key="paciente_display")
    
    with col_datos3:
        st.text_input("Objeto", value=datos_p.get('objeto_comision', 'N/A'), disabled=True, key="objeto_display")
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
        "lugar_comision": datos_p.get('destino', 'N/A'),
        "objeto_comision": datos_p.get('objeto_comision', 'N/A'),
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
        if st.button("🖨️ IMPRIMIR INFORME", use_container_width=True, type="primary"):
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
                .print-button-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .print-button {{
                    background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
                    border: none;
                    color: white;
                    padding: 15px 40px;
                    font-size: 18px;
                    font-weight: bold;
                    border-radius: 50px;
                    cursor: pointer;
                    width: 100%;
                }}
                .informe-contenido {{
                    font-family: Arial, sans-serif;
                    font-size: 10px;
                    line-height: 1.2;
                }}
            </style>
            
            <div class="informe-contenido">
                {html_final}
            </div>
            """
            
            components.html(html_con_estilos, height=1000, scrolling=True)
        else:
            st.warning(f"⚠️ Plantilla no encontrada en: {template_path}")
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



# ============================================
# VISTA: CONFIGURACIÓN ADMIN
# ============================================
def vista_configuracion_admin(u):
    st.subheader("🏢 Configuración de Datos Institucionales")
    
    asegurar_hojas_excel()
    
    try:
        config_actual = obtener_configuracion_admin()
        
        with st.form("form_config_institucional"):
            col1, col2 = st.columns(2)
            
            with col1:
                titular = st.text_input("Titular de la Unidad", 
                                       value=config_actual.get('titular_unidad', ''))
                unidad = st.text_input("Unidad Administrativa",
                                      value=config_actual.get('unidad_administrativa', ''))
            
            with col2:
                adscripcion = st.text_input("Adscripción",
                                          value=config_actual.get('adscripcion', ''))
                cargo = st.text_input("Cargo del Titular",
                                    value=config_actual.get('cargo_titular', ''))
            
            if st.form_submit_button("💾 Guardar Configuración", type="primary"):
                nueva_conf = {
                    'titular_unidad': titular,
                    'unidad_administrativa': unidad,
                    'adscripcion': adscripcion,
                    'cargo_titular': cargo
                }
                
                if guardar_configuracion_admin(nueva_conf):
                    st.success("✅ Configuración institucional guardada")
                    st.rerun()
                else:
                    st.error("Error al guardar configuración")
                    
    except Exception as e:
        st.error(f"Error al cargar configuración: {e}")


# ============================================
# VISTA: CONFIGURACIÓN ADMIN COMPLETA
# ============================================
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
            if st.button("📥 Crear Respaldo", use_container_width=True):
                if os.path.exists(DB_FILE):
                    import shutil
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    shutil.copy2(DB_FILE, backup_name)
                    st.success(f"✅ Respaldo creado: {backup_name}")
        
        with col2:
            if st.button("🔄 Verificar Integridad", use_container_width=True):
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

# ============================================
# VISTA: DESGLOSE DE GASTOS (COMPLETA CON MODAL SIEMPRE VISIBLE)
# ============================================
def vista_desglose_gastos(u):
    st.header("🧾 Desglose Pormenorizado de Gastos")

    # ============================================
    # INICIALIZAR SESSION STATE PARA GASTOS
    # ============================================
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

    # ============================================
    # BUSCADOR DE PLIEGOS (CON PERMISOS)
    # ============================================
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
                    if st.button("📥 CARGAR PLIEGO", use_container_width=True):
                        if folio_sel != "-- Seleccionar --":
                            datos_pliego = df_filtrado[df_filtrado['folio'] == folio_sel].iloc[0].to_dict()
                            st.session_state['pliego_desglose'] = datos_pliego
                            st.success(f"✅ Pliego {folio_sel} cargado")
                            st.rerun()
                with col_b2:
                    if st.button("🔄 LIMPIAR", use_container_width=True):
                        if 'pliego_desglose' in st.session_state:
                            del st.session_state['pliego_desglose']
                        st.rerun()
            else:
                st.info("No hay pliegos disponibles para tu usuario")
        else:
            st.info("No hay pliegos registrados")

    # ============================================
    # OBTENER DATOS DEL PLIEGO (O VALORES POR DEFECTO)
    # ============================================
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

    # ============================================
    # BOTONES SUPERIORES (SIEMPRE VISIBLES)
    # ============================================
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("➕ AGREGAR GASTO", use_container_width=True, type="primary"):
            # El modal se abre siempre, la validación se hace al guardar
            modal_agregar_gasto()
    
    with col_btn2:
        if st.button("🗑️ LIMPIAR GASTOS", use_container_width=True):
            for cat in st.session_state['gastos_desglose']:
                st.session_state['gastos_desglose'][cat] = []
            st.rerun()

    # ============================================
    # MOSTRAR GASTOS INGRESADOS (SOLO SI HAY PLIEGO)
    # ============================================
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

    # ============================================
    # CONSTRUIR DATOS PARA EL TEMPLATE
    # ============================================
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

    # ============================================
    # VISTA PREVIA DEL DESGLOSE (SIEMPRE VISIBLE)
    # ============================================
    st.divider()
    st.subheader("👁️ Vista Previa del Desglose")

    try:
        template_path = "templates/gastos_template.html"
        
        if not os.path.exists(template_path):
            st.error(f"❌ No se encuentra el template en: {os.path.abspath(template_path)}")
            st.stop()
        
        with open(template_path, "r", encoding="utf-8") as f:
            template = Template(f.read())
            html_final = template.render(datos_gastos)
        
        st.components.v1.html(html_final, height=1000, scrolling=True)
        
    except Exception as e:
        st.error(f"❌ Error al renderizar template: {e}")
        st.exception(e)

    # ============================================
    # BOTONES FINALES (SIEMPRE VISIBLES)
    # ============================================
    col_fin1, col_fin2 = st.columns(2)
    
    with col_fin1:
        if st.button("💾 GUARDAR GASTOS EN EXCEL", use_container_width=True, type="secondary"):
            if 'pliego_desglose' in st.session_state:
                folio = pliego.get('folio', '')
                if guardar_gastos(st.session_state['gastos_desglose'], folio):
                    st.success(f"✅ Gastos guardados correctamente para folio {folio}")
                else:
                    st.error("Error al guardar gastos en Excel")
            else:
                st.warning("⚠️ No se puede guardar: primero debe cargar un pliego")

    with col_fin2:
        if st.button("🖨️ IMPRIMIR DESGLOSE", use_container_width=True, type="primary"):
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


# ============================================
# MODAL: AGREGAR GASTO (CON VALIDACIÓN DE PLIEGO)
# ============================================
@st.dialog("➕ AGREGAR GASTO")
def modal_agregar_gasto():
    st.write("Complete los datos del gasto")

    categoria = st.selectbox("Categoría:", [
        "HOSPEDAJE", "ALIMENTACIÓN", "TRASLADOS", "OTROS VIÁTICOS",
        "AUTOBÚS", "PEAJE", "GASOLINA", "OTROS GASTOS", "SIN COMPROBANTE"
    ], key="gasto_categoria")

    col1, col2 = st.columns(2)
    with col1:
        factura = st.text_input("No. Factura:", key="gasto_factura")
        proveedor = st.text_input("Proveedor:", key="gasto_proveedor")
    with col2:
        fecha = st.date_input("Fecha:", value=datetime.now(), key="gasto_fecha")
        importe = st.number_input("Importe ($):", min_value=0.0, step=10.0, format="%.2f", key="gasto_importe")

    concepto = None
    justificacion = None
    if categoria == "SIN COMPROBANTE":
        concepto = st.text_input("Concepto:", key="gasto_concepto")
        justificacion = st.text_area("Justificación:", key="gasto_justificacion")

    if st.button("✅ GUARDAR GASTO", type="primary", use_container_width=True):
        # Validar que haya un pliego cargado
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