import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time as t
from zoneinfo import ZoneInfo
import base64

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestion VRP's - MIAA", page_icon="https://www.miaa.mx/favicon.ico")

# --- ESTADO DE SESIÓN ---
if 'registro_to_delete' not in st.session_state: st.session_state.registro_to_delete = None
if 'active_tab' not in st.session_state: st.session_state.active_tab = "📍 Registros"

zona_mx = ZoneInfo("America/Mexico_City")

# --- CONEXIÓN A BASE DE DATOS POSTGRESQL ---
def crear_nuevo_engine():
    pg = st.secrets["postgres"]
    db_url = f"postgresql+psycopg2://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
    return create_engine(
        db_url,
        pool_pre_ping=True, 
        pool_recycle=1800, 
        pool_timeout=60,
        connect_args={'connect_timeout': 60}
    )

if 'db_engine' not in st.session_state:
    st.session_state.db_engine = crear_nuevo_engine()

def obtener_datos(query, params=None):
    for intento in range(2):
        try:
            with st.session_state.db_engine.connect() as conn:
                df = pd.read_sql(text(query) if isinstance(query, str) else query, conn, params=params or {})
                return df, None
        except Exception:
            try:
                st.session_state.db_engine.dispose()
                st.session_state.db_engine = crear_nuevo_engine()
                with st.session_state.db_engine.connect() as conn:
                    df = pd.read_sql(text(query) if isinstance(query, str) else query, conn, params=params or {})
                    return df, None
            except Exception as e2:
                if intento == 1:
                    return pd.DataFrame(), str(e2)
    return pd.DataFrame(), "Error de conexión persistente."

def ejecutar_sql(query, params=None):
    with st.session_state.db_engine.connect() as conn:
        with conn.begin():
            conn.execute(text(query) if isinstance(query, str) else query, params or {})
    return True

# --- ESTILOS CSS CON GRID FORZADO DE 2 COLUMNAS (MÓVIL Y PC) ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0.2rem !important; 
        padding-bottom: 2.5rem !important;
        background: #080C14;
        color: #F8FAFC;
        max-width: 1350px;
        overflow-x: hidden;
    }
    body, [data-testid="stAppViewContainer"] {
        background: #080C14;
        color: #F8FAFC;
        overflow-x: hidden;
    }
    
    /* REJILLA DE 2 COLUMNAS REALES PARA TARJETAS DE REGISTROS */
    .miaa-grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin-bottom: 10px !important;
    }

    /* Tarjetas de registros adaptadas a la rejilla */
    .user-card {
        background: #0D1424;
        border: 1px solid rgba(0, 229, 255, 0.12);
        border-left: 4px solid #00E5FF;
        border-radius: 10px;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        word-break: break-word;
        box-sizing: border-box;
        width: 100% !important;
        height: 100% !important;
    }

    /* Menú de navegación / Pestañas estilo tarjeta MIAA */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        justify-content: center;
        background: #0D1424;
        border: 1px solid rgba(0, 229, 255, 0.12);
        border-radius: 14px;
        padding: 6px;
        gap: 6px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    div.row-widget.stRadio > div > label {
        background: #111A30;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 10px !important;
        padding: 8px 4px !important;
        flex: 1;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    div.row-widget.stRadio input[type="radio"] { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] label span,
    div.row-widget.stRadio div[role="radiogroup"] label p {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.75rem;
    }
    div.row-widget.stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #0A2540 0%, #0077B6 100%) !important;
        border-color: #00E5FF !important;
        box-shadow: 0 0 12px rgba(0, 229, 255, 0.25);
    }
    div.row-widget.stRadio > div > label[data-checked="true"] span,
    div.row-widget.stRadio > div > label[data-checked="true"] p {
        color: #00E5FF !important;
        font-weight: 700 !important;
    }

    /* Etiquetas compactas para evitar desbordes móviles */
    .stTextInput label, .stSelectbox label, .stNumberInput label, [data-testid="stWidgetLabel"] p {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Botones principales */
    .stButton>button {
        background: linear-gradient(135deg, #0077B6 0%, #00E5FF 100%);
        color: #080C14;
        border: none;
        border-radius: 9px;
        font-weight: 700;
        padding: 0.5rem 1rem;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0, 229, 255, 0.2);
    }
    .stButton>button:hover {
        opacity: 0.95;
    }

    /* Campos de entrada compactos */
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input {
        background-color: #080C14 !important;
        color: #F8FAFC !important;
        border-color: rgba(0, 229, 255, 0.25) !important;
        border-radius: 8px !important;
        font-size: 0.8rem !important;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; width: 100%; margin-bottom: 5px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" style="width: 100px; height: auto; flex-shrink: 0;" />
        <div>
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.2rem; font-weight: 800; line-height: 1.2;">Gestion VRP's</h2>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- MENÚ DE NAVEGACIÓN ---
opciones_menu = ["📍 Registros", "➕ Añadir", "⚙️ Editar"]

if 'active_tab' not in st.session_state or st.session_state.active_tab not in opciones_menu:
    st.session_state.active_tab = opciones_menu[0]

seleccion_tab = st.radio(
    "Navegación", 
    options=opciones_menu, 
    index=opciones_menu.index(st.session_state.active_tab), 
    horizontal=True, 
    label_visibility="collapsed"
)

if seleccion_tab != st.session_state.active_tab:
    st.session_state.active_tab = seleccion_tab
    st.rerun()

st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.15); margin: 12px 0;'>", unsafe_allow_html=True)

COLUMNAS_VPRS = """
    fid, id_0, id, serie, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
    cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
    hora_cal, estat_valv, observ, fotos
"""

# ==========================================
# SECCIÓN 1: VER REGISTROS (VPRS) EN 2 COLUMNAS CSS GRID
# ==========================================
if st.session_state.active_tab == "📍 Registros":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.1rem; font-weight: 700; margin-bottom: 12px;">📂 Catálogo de Válvulas VPRS</h3>', unsafe_allow_html=True)
    
    busqueda = st.text_input("🔍 Buscar válvula (ID, Serie, Domicilio, Col.):", placeholder="Ej. VF01, Centro...")
    
    if busqueda and busqueda.strip() != "":
        filtro = f"%{busqueda.strip()}%"
        query = f"""
            SELECT {COLUMNAS_VPRS} 
            FROM "Agua_potable"."VPRS" 
            WHERE id ILIKE :filtro 
               OR serie ILIKE :filtro 
               OR domicilio ILIKE :filtro 
               OR colonia ILIKE :filtro 
            ORDER BY fid
        """
        df_vprs, error_db = obtener_datos(query, {"filtro": filtro})
    else:
        query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid LIMIT 10'
        df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"❌ Error al consultar PostgreSQL: {error_db}")
    elif not df_vprs.empty:
        if not busqueda or busqueda.strip() == "":
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.8rem; margin-bottom: 8px;'>Mostrando primeros 10 registros.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.8rem; margin-bottom: 8px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
            
        # Renderizado utilizando CSS Grid de 2 columnas de manera nativa para evitar que Streamlit los rompa
        for i in range(0, len(df_vprs), 2):
            row1 = df_vprs.iloc[i]
            serie_val1 = row1['serie']
            serie_texto1 = "" if (pd.isna(serie_val1) or str(serie_val1).strip().lower() in ["nan", "none", ""]) else f" | Serie: {serie_val1}"
            
            card1_html = f"""
                <div class="user-card">
                    <span style="font-size: 0.85rem; font-weight: bold; color: #F8FAFC;">ID: {row1['id']}{serie_texto1}</span><br>
                    <span style="color: #00E5FF; font-size: 0.75rem;">📍 {row1['domicilio'] or 'Sin domicilio'}, Col. {row1['colonia'] or 'Sin colonia'}</span><br>
                    <span style="color: #94A3B8; font-size: 0.68rem; line-height: 1.3;">
                        Diámetro: {row1['diametro']}mm | Marca: {row1['marca_valv']} | Modelo: {row1['model_valv']} | Trim: {row1['marca_trim']} | Cota: {row1['cota_terr']}<br>
                        Sector: {row1['sector_hid']} | Estado: {row1['estat_valv']} | Hora Cal: {row1['hora_cal']} | Fecha: {row1['fecha_ult_']}<br>
                        Cal Ant Día: {row1['cal_ant_d']} | Cal Ant Noche: {row1['cal_ant_n']}<br>
                        Cal Act Día: {row1['cal_act_d']} | Cal Act Noche: {row1['cal_act_n']}<br>
                        Obs: {row1['observ']}
                    </span>
                </div>
            """
            
            card2_html = ""
            if i + 1 < len(df_vprs):
                row2 = df_vprs.iloc[i + 1]
                serie_val2 = row2['serie']
                serie_texto2 = "" if (pd.isna(serie_val2) or str(serie_val2).strip().lower() in ["nan", "none", ""]) else f" | Serie: {serie_val2}"
                
                card2_html = f"""
                    <div class="user-card">
                        <span style="font-size: 0.85rem; font-weight: bold; color: #F8FAFC;">ID: {row2['id']}{serie_texto2}</span><br>
                        <span style="color: #00E5FF; font-size: 0.75rem;">📍 {row2['domicilio'] or 'Sin domicilio'}, Col. {row2['colonia'] or 'Sin colonia'}</span><br>
                        <span style="color: #94A3B8; font-size: 0.68rem; line-height: 1.3;">
                            Diámetro: {row2['diametro']}mm | Marca: {row2['marca_valv']} | Modelo: {row2['model_valv']} | Trim: {row2['marca_trim']} | Cota: {row2['cota_terr']}<br>
                            Sector: {row2['sector_hid']} | Estado: {row2['estat_valv']} | Hora Cal: {row2['hora_cal']} | Fecha: {row2['fecha_ult_']}<br>
                            Cal Ant Día: {row2['cal_ant_d']} | Cal Ant Noche: {row2['cal_ant_n']}<br>
                            Cal Act Día: {row2['cal_act_d']} | Cal Act Noche: {row2['cal_act_n']}<br>
                            Obs: {row2['observ']}
                        </span>
                    </div>
                """

            st.markdown(f"""
                <div class="miaa-grid-container">
                    <div>{card1_html}</div>
                    <div>{card2_html}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Fotos opcionales separadas de manera limpia
            c_foto1, c_foto2 = st.columns(2)
            with c_foto1:
                foto_data1 = row1['fotos']
                if foto_data1 is not None and len(foto_data1) > 0:
                    try:
                        if isinstance(foto_data1, bytes):
                            st.image(foto_data1, caption=f"ID: {row1['id']}", width=140)
                        elif isinstance(foto_data1, str) and len(foto_data1) > 10:
                            st.image(base64.b64decode(foto_data1), caption=f"ID: {row1['id']}", width=140)
                    except:
                        pass
            if i + 1 < len(df_vprs):
                with c_foto2:
                    foto_data2 = df_vprs.iloc[i + 1]['fotos']
                    if foto_data2 is not None and len(foto_data2) > 0:
                        try:
                            if isinstance(foto_data2, bytes):
                                st.image(foto_data2, caption=f"ID: {df_vprs.iloc[i + 1]['id']}", width=140)
                            elif isinstance(foto_data2, str) and len(foto_data2) > 10:
                                st.image(base64.b64decode(foto_data2), caption=f"ID: {df_vprs.iloc[i + 1]['id']}", width=140)
                        except:
                            pass
            st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)
    else:
        st.info("No se encontraron registros.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVA VÁLVULA
# ==========================================
elif st.session_state.active_tab == "➕ Añadir":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.1rem; font-weight: 700; margin-bottom: 12px;">✨ Registrar nueva VPRS</h3>', unsafe_allow_html=True)
    
    r1c1, r1c2 = st.columns(2)
    with r1c1: val_id_0 = st.number_input("ID_0 (Int)", min_value=0, value=0, key="add_id_0")
    with r1c2: val_id = st.text_input("ID (Texto)", key="add_id")

    r2c1, r2c2 = st.columns(2)
    with r2c1: val_serie = st.text_input("Serie", key="add_serie")
    with r2c2: val_diametro = st.number_input("Diámetro (mm)", min_value=0, value=50, key="add_diam")

    r3c1, r3c2 = st.columns(2)
    with r3c1: val_cota = st.number_input("Cota Territorio", value=0.0, key="add_cota")
    with r3c2: val_marca = st.text_input("Marca Válvula", key="add_marca")

    r4c1, r4c2 = st.columns(2)
    with r4c1: val_modelo = st.text_input("Modelo Válvula", key="add_modelo")
    with r4c2: val_trim = st.text_input("Marca Trim", key="add_trim")

    r5c1, r5c2 = st.columns(2)
    with r5c1: val_sector = st.text_input("Sector Hidráulico", key="add_sector")
    with r5c2: val_domicilio = st.text_input("Domicilio", key="add_dom")

    r6c1, r6c2 = st.columns(2)
    with r6c1: val_colonia = st.text_input("Colonia", key="add_col")
    with r6c2: val_estat = st.text_input("Estado Válvula", key="add_estat")

    r7c1, r7c2 = st.columns(2)
    with r7c1: val_hora = st.text_input("Hora Calibración", key="add_hora")
    with r7c2: val_cal_ant_d = st.text_input("Cal Anterior Día", key="add_cand")

    r8c1, r8c2 = st.columns(2)
    with r8c1: val_cal_ant_n = st.text_input("Cal Anterior Noche", key="add_cann")
    with r8c2: val_cal_act_d = st.text_input("Cal Actual Día", key="add_cactd")

    r9c1, r9c2 = st.columns(2)
    with r9c1: val_cal_act_n = st.text_input("Cal Actual Noche", key="add_cactn")
    with r9c2: val_fecha = st.text_input("Fecha Última", key="add_fecha")

    val_observ = st.text_input("Observaciones", key="add_obs")

    st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
    st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.85rem;'>📸 Fotografía:</p>", unsafe_allow_html=True)
    
    col_foto1, col_foto2 = st.columns(2)
    with col_foto1:
        st.markdown("<p style='font-size: 0.8rem; color: #94A3B8;'>Subir archivo:</p>", unsafe_allow_html=True)
        foto_subida = st.file_uploader("Subir imagen", type=["jpg", "jpeg", "png"], key="subir_nuevo", label_visibility="collapsed")
    with col_foto2:
        st.markdown("<p style='font-size: 0.8rem; color: #94A3B8;'>Usar cámara:</p>", unsafe_allow_html=True)
        activar_camara_nuevo = st.checkbox("🟢 Activar cámara", key="chk_cam_nuevo")
        foto_camara = None
        if activar_camara_nuevo:
            foto_camara = st.camera_input("Capturar", key="camara_nuevo", label_visibility="collapsed")

    if st.button("💾 Guardar Registro", key="btn_guardar_nuevo"):
        if val_id:
            try:
                foto_bytes = None
                if foto_camara is not None:
                    foto_bytes = foto_camara.getvalue()
                elif foto_subida is not None:
                    foto_bytes = foto_subida.getvalue()
                
                sql_insert = """
                    INSERT INTO "Agua_potable"."VPRS" (
                        id_0, id, serie, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
                        cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n,
