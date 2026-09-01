import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestión de Destinatarios - Telegram", page_icon="https://www.miaa.mx/favicon.ico")

# --- ESTADO DE SESIÓN ---
if 'user_to_delete' not in st.session_state: st.session_state.user_to_delete = None
if 'active_tab' not in st.session_state: st.session_state.active_tab = "👥 Usuarios"

zona_mx = ZoneInfo("America/Mexico_City")

# --- CONEXIÓN A BASE DE DATOS ---
def crear_nuevo_engine():
    return create_engine(
        st.secrets["databases"]["url_dic"],
        pool_pre_ping=True, 
        pool_recycle=1800, 
        pool_timeout=30,
        connect_args={'connect_timeout': 30}
    )

if 'db_engine' not in st.session_state:
    st.session_state.db_engine = crear_nuevo_engine()

def obtener_datos(query):
    """Ejecuta consultas devolviendo tanto el dataframe como el error exacto si ocurre."""
    try:
        with st.session_state.db_engine.connect() as conn:
            df = pd.read_sql(query, conn)
            return df, None
    except Exception as e:
        try:
            st.session_state.db_engine.dispose()
            st.session_state.db_engine = crear_nuevo_engine()
            with st.session_state.db_engine.connect() as conn:
                df = pd.read_sql(query, conn)
                return df, None
        except Exception as e2:
            return pd.DataFrame(), str(e2)

def ejecutar_sql(query, params=None):
    """Ejecuta sentencias SQL de escritura/actualización."""
    with st.session_state.db_engine.connect() as conn:
        with conn.begin():
            conn.execute(text(query) if isinstance(query, str) else query, params or {})
    return True

# --- ESTILOS CSS CON TEXTOS DE INPUTS EN BLANCO BRILLANTE ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0.2rem !important; 
        padding-bottom: 2rem !important;
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
        max-width: 1200px;
    }
    body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
    }
    
    /* Convertir st.radio horizontal en pestañas */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        background: rgba(15, 32, 66, 0.8);
        border: 1px solid rgba(0, 229, 255, 0.2);
        border-radius: 12px;
        padding: 5px;
        gap: 10px;
    }
    div.row-widget.stRadio > div > label {
        background: linear-gradient(135deg, #1A2A56 0%, #162247 100%);
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        border-radius: 8px !important;
        padding: 8px 18px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        flex: 1;
        text-align: center;
        cursor: pointer;
    }
    
    /* OCULTAR COMPLETAMENTE LOS CÍRCULOS NATIVOS DE RADIO */
    div.row-widget.stRadio input[type="radio"] {
        display: none !important;
    }
    div.row-widget.stRadio div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* FORZAR AZUL TURQUESA EN CUALQUIER ELEMENTO DE TEXTO DENTRO DEL RADIO */
    div.row-widget.stRadio div[role="radiogroup"] label span,
    div.row-widget.stRadio div[role="radiogroup"] label p,
    div.row-widget.stRadio [data-testid="stMarkdownContainer"] *,
    div.row-widget.stRadio span {
        color: #00E5FF !important;
        -webkit-text-fill-color: #00E5FF !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    div.row-widget.stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #0077B6, #00E5FF) !important;
        border-color: #00E5FF !important;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.5);
    }
    
    /* Si la pestaña está activa, el texto cambia a color oscuro para contraste perfecto */
    div.row-widget.stRadio > div > label[data-checked="true"] span,
    div.row-widget.stRadio > div > label[data-checked="true"] p,
    div.row-widget.stRadio > div > label[data-checked="true"] [data-testid="stMarkdownContainer"] * {
        color: #070D1B !important;
        -webkit-text-fill-color: #070D1B !important;
        font-weight: 700 !important;
    }

    /* FORZAR ETIQUETAS DE INPUTS Y TEXTOS DE FORMULARIOS A BLANCO BRILLANTE */
    .stTextInput label, .stSelectbox label, .stMultiSelect label, .stSlider label, .stNumberInput label, 
    [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span, [data-testid="stForm"] label {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    .user-card {
        background: linear-gradient(90deg, #1A2A56 0%, #162247 100%);
        border: 1px solid rgba(0, 229, 255, 0.15);
        border-left: 4px solid #00E5FF;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077B6, #00E5FF);
        color: #070D1B;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 0.5rem 0.2rem;
        font-size: 0.85rem;
        box-shadow: 0 4px 15px rgba(0, 229, 255, 0.3);
        width: 100%;
        white-space: nowrap;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #00E5FF, #90E0EF);
        color: #070D1B;
    }
    
    div[data-baseweb="input"] input, 
    div[data-baseweb="base-input"] input, 
    input[type="text"] {
        background-color: #070D1B !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border-color: rgba(0, 229, 255, 0.3) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    
    .footer-miaa {
        text-align: center;
        color: #8D99AE;
        font-size: 0.85rem;
        margin-top: 3rem;
        border-top: 1px solid rgba(0, 229, 255, 0.1);
        padding-top: 1.5rem;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="text-align: center; margin-bottom: 0px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" 
             style="width: 130px; height: auto; display: inline-block; filter: drop-shadow(0 0 8px rgba(0,229,255,0.3));">
    </div>
""", unsafe_allow_html=True)

col_title_1, col_title_2, col_title_3 = st.columns([1, 6, 1])
with col_title_2:
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 0rem;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" style="width: 28px; height: 28px; filter: drop-shadow(0 0 6px rgba(0,229,255,0.4));">
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.4rem; font-weight: 800; letter-spacing: 0.5px; text-shadow: 0 0 10px rgba(0,229,255,0.3);">Gestión de Usuarios</h2>
        </div>
    """, unsafe_allow_html=True)

# --- MENÚ DE NAVEGACIÓN HORIZONTAL ---
opciones_menu = ["👥 Usuarios", "➕ Añadir", "⚙️ Editar"]

seleccion_tab = st.radio(
    "Navegación", 
    options=opciones_menu, 
    index=opciones_menu.index(st.session_state.active_tab) if st.session_state.active_tab in opciones_menu else 0,
    horizontal=True,
    label_visibility="collapsed"
)

if seleccion_tab != st.session_state.active_tab:
    st.session_state.active_tab = seleccion_tab
    st.rerun()

# Línea azul brillante pegada justo debajo de los botones de navegación
st.markdown("""
    <div style="margin-top: 4px; margin-bottom: 12px; height: 2px; background: linear-gradient(90deg, rgba(0,229,255,0) 0%, rgba(0,229,255,0.8) 50%, rgba(0,229,255,0) 100%); box-shadow: 0 0 10px #00E5FF;"></div>
""", unsafe_allow_html=True)

# ==========================================
# SECCIÓN 1: USUARIOS REGISTRADOS
# ==========================================
if st.session_state.active_tab == "👥 Usuarios":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 0px; font-size: 1.2rem;">📂 Destinatarios activos </h3>', unsafe_allow_html=True)
    
    df_destinatarios, error_db = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")
    
    if error_db:
        st.error(f"❌ Error al consultar la base de datos: {error_db}")
    elif not df_destinatarios.empty:
        for _, row_user in df_destinatarios.iterrows():
            estado_badge = '<span style="color: #00FF66; font-weight: 700; text-shadow: 0 0 8px rgba(0,255,102,0.4);">● Activo</span>' if str(row_user['activo']).strip().lower() == 'si' else '<span style="color: #FF3366; font-weight: 700;">● Inactivo</span>'
            st.markdown(f"""
                <div class="user-card">
                    <div>
                        <span style="font-size: 1.15rem; font-weight: bold; color: #FFFFFF;">👤 {row_user['nombre']}</span><br>
                        <span style="color: #00E5FF; font-size: 0.85rem; font-family: monospace;">ID Telegram: {row_user['chart_id']}</span> &nbsp;|&nbsp; 
                        <span style="color: #8D99AE; font-size: 0.9rem;">🏢 {row_user['departamento']}</span>
                    </div>
                    <div>
                        {estado_badge}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("La tabla 'Diccionario_telegram' está vacía o no devolvió registros.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVO
# ==========================================
elif st.session_state.active_tab == "➕ Añadir":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 0px; font-size: 1.2rem;">✨ Registrar nuevo destinatario</h3>', unsafe_allow_html=True)
    
    with st.form("form_nuevo_usuario_dinamico_unico"):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            nuevo_nombre = st.text_input("Nombre completo", key="input_nuevo_nombre")
        with f_col2:
            nuevo_chart = st.text_input("Chart ID (Telegram)", key="input_nuevo_chart")
        with f_col3:
            nuevo_depto = st.text_input("Departamento", key="input_nuevo_depto")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_crear = st.form_submit_button("💾 Guardar nuevo usuario")
        if btn_crear:
            if nuevo_nombre and nuevo_chart:
                try:
                    df_max_id, err = obtener_datos("SELECT MAX(CAST(id AS UNSIGNED)) as max_id FROM Diccionario_telegram")
                    siguiente_id = 1
                    if not df_max_id.empty and pd.notnull(df_max_id.iloc[0]['max_id']):
                        siguiente_id = int(df_max_id.iloc[0]['max_id']) + 1
                    
                    nuevo_id_str = f"{siguiente_id:03d}"

                    ejecutar_sql(
                        "INSERT INTO Diccionario_telegram (id, nombre, chart_id, activo, departamento) VALUES (:id, :nombre, :chart_id, 'Si', :depto)",
                        {"id": nuevo_id_str, "nombre": nuevo_nombre, "chart_id": nuevo_chart, "depto": nuevo_depto}
                    )
                    st.success(f"¡Usuario {nuevo_nombre} añadido correctamente con ID {nuevo_id_str}!")
                    t.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al insertar el usuario: {ex}")
            else:
                st.warning("Por favor completa los campos obligatorios (Nombre y Chart ID).")

# ==========================================
# SECCIÓN 3: EDITAR Y ELIMINAR
# ==========================================
elif st.session_state.active_tab == "⚙️ Editar":
    st.markdown('<h3 style="color: #00E5FF; margin-top: 0px; font-size: 1.2rem;">🛠️ Gestión, estados y eliminación</h3>', unsafe_allow_html=True)
    
    df_destinatarios, error_db = obtener_datos("SELECT id, nombre, chart_id, activo, departamento FROM Diccionario_telegram")
    
    if error_db:
        st.error(f"❌ Error al consultar la base de datos: {error_db}")
    elif not df_destinatarios.empty:
        for idx, row_user in df_destinatarios.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #162247 0%, #0F1A36 100%); border: 1px solid rgba(0,229,255,0.15); border-radius: 10px 10px 0 0; padding: 8px 15px;">
                        <span style="color: #00E5FF; font-size: 0.85rem; font-family: monospace;">ID Registro BD: <b>{row_user['id']}</b></span>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form(key=f"form_edit_user_{row_user['id']}_{idx}"):
                    e_col1, e_col2, e_col3 = st.columns([3, 3, 2])
                    with e_col1:
                        edit_nombre = st.text_input("Nombre completo", value=str(row_user['nombre']), key=f"edit_nom_{row_user['id']}_{idx}")
                    with e_col2:
                        edit_chart = st.text_input("Chart ID (Telegram)", value=str(row_user['chart_id']), key=f"edit_chart_{row_user['id']}_{idx}")
                    with e_col3:
                        edit_depto = st.text_input("Departamento", value=str(row_user['departamento']), key=f"edit_depto_{row_user['id']}_{idx}")
                    
                    sub_col1, sub_col2, sub_col3 = st.columns([3, 2, 2])
                    with sub_col1:
                        actual_val = True if str(row_user['activo']).strip().lower() == 'si' else False
                        edit_activo = st.toggle("Activo / Habilitado", value=actual_val, key=f"toggle_user_{row_user['id']}_{idx}")
                    with sub_col2:
                        btn_guardar_cambios = st.form_submit_button("💾 Guardar cambios", use_container_width=True)
                    with sub_col3:
                        pass # Espacio reservado
                    
                    if btn_guardar_cambios:
                        try:
                            nuevo_str_activo = "Si" if edit_activo else "No"
                            ejecutar_sql(
                                "UPDATE Diccionario_telegram SET nombre = :nom, chart_id = :ch, departamento = :dep, activo = :act WHERE id = :uid",
                                {
                                    "nom": edit_nombre, 
                                    "ch": edit_chart, 
                                    "dep": edit_depto, 
                                    "act": nuevo_str_activo, 
                                    "uid": row_user['id']
                                }
                            )
                            st.success(f"¡Usuario '{edit_nombre}' actualizado correctamente!")
                            t.sleep(0.8)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Error al actualizar el registro: {ex}")
                
                # Botón independiente de eliminación fuera del formulario para evitar conflictos
                del_col1, del_col2 = st.columns([6, 2])
                with del_col2:
                    if st.button("🗑️ Eliminar", key=f"del_user_{row_user['id']}_{idx}", use_container_width=True):
                        st.session_state.user_to_delete = row_user['id']
                        st.rerun()
                        
                st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.2); margin: 15px 0;'>", unsafe_allow_html=True)
    else:
        st.info("No hay usuarios disponibles para editar.")

    if st.session_state.user_to_delete is not None:
        uid_Target = st.session_state.user_to_delete
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #3A1C1C 0%, #2A0E0E 100%); border: 1px solid #FF3366; padding: 18px; border-radius: 12px; margin-top: 20px; box-shadow: 0 4px 20px rgba(255,51,102,0.3);">
                <h4 style="color: #FF4D6D; margin-top: 0;">⚠️ Advertencia de eliminación permanente</h4>
                <p style="color: #FFFFFF;">Estás a punto de eliminar al usuario con ID: <b>{uid_Target}</b>.</p>
            </div>
        """, unsafe_allow_html=True)
        
        confirm_text = st.text_input("Para confirmar, escribe 'delete':", key="input_confirm_delete")
        
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("Sí, confirmar eliminación", type="primary", key="btn_ejecutar_eliminar_def", use_container_width=True):
                if confirm_text.strip().lower() == "delete":
                    try:
                        ejecutar_sql("DELETE FROM Diccionario_telegram WHERE id = :uid", {"uid": uid_Target})
                        st.success("Registro eliminado correctamente.")
                        st.session_state.user_to_delete = None
                        t.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al eliminar: {ex}")
                else:
                    st.error("Escribe 'delete' para confirmar.")
        with c_btn2:
            if st.button("Cancelar", key="btn_cancelar_eliminar_def", use_container_width=True):
                st.session_state.user_to_delete = None
                st.rerun()

# --- PIE DE PÁGINA ---
st.markdown("""
    <div class="footer-miaa">
        🔒 Política de privacidad &nbsp;&bull;&nbsp; © 2026 MIAA. Todos los derechos reservados.
    </div>
""", unsafe_allow_html=True)
