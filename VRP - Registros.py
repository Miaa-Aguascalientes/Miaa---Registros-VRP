# VRP - Registros.py
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

# --- ESTILOS CSS CON ANCHO TOTAL AL 100% EN CUADROS Y CONTENEDORES ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 2.5rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        background: #080C14;
        color: #F8FAFC;
        max-width: 100% !important;
        overflow-x: hidden;
    }
    body, [data-testid="stAppViewContainer"] {
        background: #080C14;
        color: #F8FAFC;
        overflow-x: hidden;
    }
    
    /* REJILLA EXPANDIDA Y FORZADA A BORDE A BORDE */
    .miaa-grid-container {
        display: grid;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 1px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin-bottom: 3px !important;
        padding: 0 !important;
    }

    /* Anular restricciones y paddings de Streamlit en bloques horizontales */
    [data-testid="stHorizontalBlock"] {
        display: grid !important;
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 1px !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="column"] {
        width: 100% !important;
        flex: unset !important;
        min-width: unset !important;
        max-width: 100% !important;
        padding: 0 2px !important;
        margin: 0 !important;
    }

    /* Tarjetas de registros con ancho total absoluto y cuadros de texto más anchos */
    .user-card {
        background: #0D1424;
        border: 1px solid rgba(0, 229, 255, 0.12);
        border-left: 3px solid #00E5FF;
        border-radius: 2px;
        padding: 6px 4px;
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
        border-radius: 8px;
        padding: 3px;
        gap: 3px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    div.row-widget.stRadio > div > label {
        background: #111A30;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 6px !important;
        padding: 6px 2px !important;
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

    /* Etiquetas de los inputs */
    .stTextInput label, .stSelectbox label, .stNumberInput label, [data-testid="stWidgetLabel"] p {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* Botones principales con tono azul más obscuro y con vida */
    .stButton>button {
        background: linear-gradient(135deg, #023e8a 0%, #0077b6 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(0, 229, 255, 0.3) !important;
        border-radius: 4px;
        font-weight: 700;
        padding: 0.5rem 1rem;
        width: 100%;
        box-shadow: 0 4px 15px rgba(2, 62, 138, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #03045e 0%, #023e8a 100%) !important;
        border-color: #00E5FF !important;
        box-shadow: 0 0 15px rgba(0, 229, 255, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
        opacity: 1;
    }

    /* FORZAR ANCHO TOTAL Y MAYOR EXPANSIÓN LATERAL EN TODOS LOS CUADROS DE TEXTO Y ENTRADAS */
    .stTextInput, .stNumberInput, .stSelectbox, .stDateInput, .stTextArea {
        width: 100% !important;
        max-width: 100% !important;
    }
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input, div[data-baseweb="textarea"] textarea {
        background-color: #080C14 !important;
        color: #F8FAFC !important;
        border-color: rgba(0, 229, 255, 0.25) !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
        width: 100% !important;
        max-width: 100% !important;
        padding-left: 12px !important;
        padding-right: 12px !important;
    }
    
    .stTextInput > div, .stNumberInput > div, .stSelectbox > div, .stDateInput > div {
        width: 100% !important;
    }

    /* ESTILO PARA EL EXPANDER DENTRO DE LOS REGISTROS */
    [data-testid="stExpander"] {
        background-color: #080C14 !important;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 4px !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stExpander"] summary {
        color: #00E5FF !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
    }

    /* ELIMINAR COMPLETAMENTE EL RECUADRO Y CONTENIDOS DEL FILE UPLOADER Y BOTÓN "SIN ARCHIVOS SELECCIONADOS" */
    [data-testid="stFileUploader"] {
        display: none !important;
    }
    
    /* OCULTAR EL CONTENEDOR DE VISTA PREVIA / CUADRO VACÍO DEL CAMERA_INPUT */
    [data-testid="stCameraInput"] > div:first-child {
        display: none !important;
    }
    [data-testid="stCameraInput"] {
        width: 100% !important;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; width: 100%; margin-bottom: 5px; padding: 0 2px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" style="width: 85px; height: auto; flex-shrink: 0;" />
        <div>
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.1rem; font-weight: 800; line-height: 1.2;">Gestion VRP's</h2>
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

st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.15); margin: 8px 0;'>", unsafe_allow_html=True)

COLUMNAS_VPRS = """
    fid, id_0, id, serie, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
    cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
    hora_cal, estat_valv, observ, fotos
"""

# ==========================================
# SECCIÓN 1: VER REGISTROS (VPRS) - UNA SOLA COLUMNA
# ==========================================
if st.session_state.active_tab == "📍 Registros":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; padding: 0 2px;">📂 Catálogo de Válvulas VPRS</h3>', unsafe_allow_html=True)
    
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
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px; padding: 0 2px;'>Mostrando primeros 10 registros.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px; padding: 0 2px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
            
        for idx, row in df_vprs.iterrows():
            serie_val = row['serie']
            serie_texto = "" if (pd.isna(serie_val) or str(serie_val).strip().lower() in ["nan", "none", ""]) else f" | Serie: {serie_val}"
            
            card_html = f"""
                <div class="user-card" style="margin-bottom: 2px;">
                    <span style="font-size: 0.8rem; font-weight: bold; color: #F8FAFC;">ID: {row['id']}{serie_texto}</span><br>
                    <span style="color: #00E5FF; font-size: 0.7rem;">📍 {row['domicilio'] or 'Sin domicilio'}, Col. {row['colonia'] or 'Sin colonia'}</span>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Contenedor desplegable para el detalle con título simplificado solicitado
            with st.expander("🔍 Ver detalles completos"):
                detalle_html = f"""
                    <span style="color: #94A3B8; font-size: 0.68rem; line-height: 1.4;">
                        Diámetro: {row['diametro']} pulgadas | Marca: {row['marca_valv']} | Modelo: {row['model_valv']} | Trim: {row['marca_trim']} | Cota: {row['cota_terr']}<br>
                        Sector: {row['sector_hid']} | Estado: {row['estat_valv']} | Hora Cal: {row['hora_cal']} | Fecha: {row['fecha_ult_']}<br>
                        Cal Ant Día: {row['cal_ant_d']} | Cal Ant Noche: {row['cal_ant_n']}<br>
                        Cal Act Día: {row['cal_act_d']} | Cal Act Noche: {row['cal_act_n']}<br>
                        Obs: {row['observ']}
                    </span>
                """
                st.markdown(detalle_html, unsafe_allow_html=True)
                
                foto_data = row['fotos']
                if foto_data is not None and len(foto_data) > 0:
                    try:
                        if isinstance(foto_data, bytes):
                            st.image(foto_data, caption=f"ID: {row['id']}", width=250)
                        elif isinstance(foto_data, str) and len(foto_data) > 10:
                            st.image(base64.b64decode(foto_data), caption=f"ID: {row['id']}", width=250)
                    except:
                        pass
                        
            st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)
    else:
        st.info("No se encontraron registros.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVA VÁLVULA
# ==========================================
elif st.session_state.active_tab == "➕ Añadir":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; padding: 0 2px;">✨ Registrar nueva VPRS</h3>', unsafe_allow_html=True)
    
    # Calcular automáticamente el siguiente ID_0 basado en el valor máximo existente en la base de datos
    df_max_id0, err_max = obtener_datos('SELECT MAX(id_0) as max_id FROM "Agua_potable"."VPRS"')
    siguiente_id_0 = 1
    if not err_max and not df_max_id0.empty and df_max_id0['max_id'].iloc[0] is not None:
        try:
            siguiente_id_0 = int(df_max_id0['max_id'].iloc[0]) + 1
        except:
            siguiente_id_0 = 1

    r1c1, r1c2 = st.columns(2)
    with r1c1: 
        # ID_0 asignado automáticamente y bloqueado visualmente para que el usuario no pueda editarlo directamente
        st.text_input("ID_0 (Automático)", value=str(siguiente_id_0), disabled=True, key="add_id_0_bloq")
        val_id_0 = siguiente_id_0
    with r1c2: val_id = st.text_input("ID (VRP)", key="add_id")

    r2c1, r2c2 = st.columns(2)
    with r2c1: val_serie = st.text_input("Serie", key="add_serie")
    with r2c2: val_diametro = st.number_input("Diámetro", min_value=0, value=0, key="add_diam")

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
    st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.8rem; padding: 0 2px;'>📸 Fotografía:</p>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size: 0.78rem; color: #94A3B8; margin-top: 10px; margin-bottom: 2px;'>Usar cámara:</p>", unsafe_allow_html=True)
    
    cam_key_nuevo = "cam_open_nuevo"
    if cam_key_nuevo not in st.session_state:
        st.session_state[cam_key_nuevo] = False
        
    if not st.session_state[cam_key_nuevo]:
        if st.button("📷 Activar Cámara", key="btn_open_cam_nuevo", use_container_width=True):
            st.session_state[cam_key_nuevo] = True
            st.rerun()
    else:
        if st.button("❌ Cerrar Cámara", key="btn_close_cam_nuevo", use_container_width=True):
            st.session_state[cam_key_nuevo] = False
            st.rerun()

    foto_camara = None
    if st.session_state[cam_key_nuevo]:
        foto_camara = st.camera_input("Capturar", key="camara_nuevo", label_visibility="collapsed")

    if st.button("💾 Guardar Registro", key="btn_guardar_nuevo", use_container_width=True):
        if val_id:
            try:
                foto_bytes = None
                if foto_camara is not None:
                    foto_bytes = foto_camara.getvalue()
                
                sql_insert = """
                    INSERT INTO "Agua_potable"."VPRS" (
                        id_0, id, serie, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
                        cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
                        hora_cal, estat_valv, observ, fotos
                    ) VALUES (
                        :id_0, :id, :serie, :diametro, :marca_valv, :model_valv, :marca_trim, :domicilio, :colonia, 
                        :cota_terr, :sector_hid, :cal_ant_d, :cal_ant_n, :fecha_ult_, :cal_act_d, :cal_act_n, 
                        :hora_cal, :estat_valv, :observ, :fotos
                    )
                """
                ejecutar_sql(sql_insert, {
                    "id_0": val_id_0, "id": val_id, "serie": val_serie if val_serie.strip() != "" else None, "diametro": val_diametro, "marca_valv": val_marca,
                    "model_valv": val_modelo, "marca_trim": val_trim, "domicilio": val_domicilio, "colonia": val_colonia,
                    "cota_terr": val_cota, "sector_hid": val_sector, "cal_ant_d": val_cal_ant_d, "cal_ant_n": val_cal_ant_n,
                    "fecha_ult_": val_fecha, "cal_act_d": val_cal_act_d, "cal_act_n": val_cal_act_n, "hora_cal": val_hora,
                    "estat_valv": val_estat, "observ": val_observ, "fotos": foto_bytes
                })
                st.success("¡Válvula registrada con éxito!")
                t.sleep(1)
                st.rerun()
            except Exception as ex:
                st.error(f"Error al insertar: {ex}")
        else:
            st.warning("El campo ID es obligatorio.")

# ==========================================
# SECCIÓN 3: EDITAR Y ELIMINAR
# ==========================================
elif st.session_state.active_tab == "⚙️ Editar":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; padding: 0 2px;">🛠️ Modificar o Eliminar Válvula</h3>', unsafe_allow_html=True)
    
    busqueda_edit = st.text_input("🔍 Filtrar registros a editar:", placeholder="Dejar en blanco para ver 10...")
    
    if busqueda_edit and busqueda_edit.strip() != "":
        filtro_ed = f"%{busqueda_edit.strip()}%"
        query_edit = f"""
            SELECT {COLUMNAS_VPRS} 
            FROM "Agua_potable"."VPRS" 
            WHERE id ILIKE :filtro 
               OR serie ILIKE :filtro 
               OR domicilio ILIKE :filtro 
               OR colonia ILIKE :filtro 
            ORDER BY fid
        """
        df_vprs, error_db = obtener_datos(query_edit, {"filtro": filtro_ed})
    else:
        query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid LIMIT 10'
        df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"Error: {error_db}")
    elif not df_vprs.empty:
        if not busqueda_edit or busqueda_edit.strip() == "":
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px; padding: 0 2px;'>Mostrando primeros 10 registros.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px; padding: 0 2px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
            
        for idx, row in df_vprs.iterrows():
            st.markdown(f"<div style='padding: 0 2px;'><span style='color: #00E5FF; font-weight: bold;'>FID Registro: {row['fid']}</span> | <span style='color: #F8FAFC;'>ID: {row['id']}</span></div>", unsafe_allow_html=True)
            
            # --- VISUALIZACIÓN DE FOTO ALMACENADA EN LA SECCIÓN DE EDITAR ---
            foto_actual = row['fotos']
            if foto_actual is not None and len(foto_actual) > 0:
                try:
                    st.markdown("<p style='color: #00E5FF; font-size: 0.75rem; margin-top: 6px; margin-bottom: 2px;'>📸 Fotografía almacenada:</p>", unsafe_allow_html=True)
                    if isinstance(foto_actual, bytes):
                        st.image(foto_actual, caption=f"ID: {row['id']}", width=250)
                    elif isinstance(foto_actual, str) and len(foto_actual) > 10:
                        st.image(base64.b64decode(foto_actual), caption=f"ID: {row['id']}", width=250)
                except:
                    pass

            e_r1c1, e_r1c2 = st.columns(2)
            with e_r1c1: 
                st.text_input("ID_0 (Bloqueado)", value=str(row['id_0'] or 0), disabled=True, key=f"id0_bloq_{row['fid']}")
                e_id_0 = row['id_0']
            with e_r1c2: e_id = st.text_input("ID", value=str(row['id'] or ""), key=f"id_{row['fid']}")

            e_r2c1, e_r2c2 = st.columns(2)
            e_serie_val = "" if (pd.isna(row['serie']) or str(row['serie']).strip().lower() in ["nan", "none"]) else str(row['serie'])
            with e_r2c1: e_serie = st.text_input("Serie", value=e_serie_val, key=f"serie_{row['fid']}")
            with e_r2c2: e_diametro = st.number_input("Diámetro", value=int(row['diametro'] or 0), key=f"diam_{row['fid']}")

            e_r3c1, e_r3c2 = st.columns(2)
            with e_r3c1: e_cota = st.number_input("Cota Terr", value=float(row['cota_terr'] or 0.0), key=f"cota_{row['fid']}")
            with e_r3c2: e_marca = st.text_input("Marca Valv", value=str(row['marca_valv'] or ""), key=f"mar_{row['fid']}")

            e_r4c1, e_r4c2 = st.columns(2)
            with e_r4c1: e_modelo = st.text_input("Modelo Valv", value=str(row['model_valv'] or ""), key=f"mod_{row['fid']}")
            with e_r4c2: e_trim = st.text_input("Marca Trim", value=str(row['marca_trim'] or ""), key=f"trim_{row['fid']}")

            e_r5c1, e_r5c2 = st.columns(2)
            with e_r5c1: e_sector = st.text_input("Sector Hid", value=str(row['sector_hid'] or ""), key=f"sec_{row['fid']}")
            with e_r5c2: e_domicilio = st.text_input("Domicilio", value=str(row['domicilio'] or ""), key=f"dom_{row['fid']}")

            e_r6c1, e_r6c2 = st.columns(2)
            with e_r6c1: e_colonia = st.text_input("Colonia", value=str(row['colonia'] or ""), key=f"col_{row['fid']}")
            with e_r6c2: e_estat = st.text_input("Estado Valv", value=str(row['estat_valv'] or ""), key=f"est_{row['fid']}")

            e_r7c1, e_r7c2 = st.columns(2)
            with e_r7c1: e_hora = st.text_input("Hora Cal", value=str(row['hora_cal'] or ""), key=f"hora_{row['fid']}")
            with e_r7c2: e_cal_ant_d = st.text_input("Cal Anterior Día", value=str(row['cal_ant_d'] or ""), key=f"cand_{row['fid']}")

            e_r8c1, e_r8c2 = st.columns(2)
            with e_r8c1: e_cal_ant_n = st.text_input("Cal Anterior Noche", value=str(row['cal_ant_n'] or ""), key=f"cann_{row['fid']}")
            with e_r8c2: e_cal_act_d = st.text_input("Cal Actual Día", value=str(row['cal_act_d'] or ""), key=f"cactd_{row['fid']}")

            e_r9c1, e_r9c2 = st.columns(2)
            with e_r9c1: e_cal_act_n = st.text_input("Cal Actual Noche", value=str(row['cal_act_n'] or ""), key=f"cactn_{row['fid']}")
            with e_r9c2: e_fecha = st.text_input("Fecha Ult", value=str(row['fecha_ult_']  or ""), key=f"fec_{row['fid']}")

            e_observ = st.text_input("Observaciones", value=str(row['observ'] or ""), key=f"obs_{row['fid']}")
            
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.78rem; padding: 0 2px;'>📸 Actualizar foto:</p>", unsafe_allow_html=True)
            
            st.markdown("<p style='font-size: 0.78rem; color: #94A3B8; margin-top: 10px; margin-bottom: 2px;'>Usar cámara:</p>", unsafe_allow_html=True)
            cam_key_edit = f"cam_open_edit_{row['fid']}"
            if cam_key_edit not in st.session_state:
                st.session_state[cam_key_edit] = False

            if not st.session_state[cam_key_edit]:
                if st.button("📷 Activar Cámara", key=f"btn_open_cam_edit_{row['fid']}", use_container_width=True):
                    st.session_state[cam_key_edit] = True
                    st.rerun()
            else:
                if st.button("❌ Cerrar Cámara", key=f"btn_close_cam_edit_{row['fid']}", use_container_width=True):
                    st.session_state[cam_key_edit] = False
                    st.rerun()

            actualizar_click = st.button("💾 Actualizar Registro", key=f"btn_act_{row['fid']}", use_container_width=True)

            nueva_foto_camara = None
            if st.session_state.get(f"cam_open_edit_{row['fid']}", False):
                nueva_foto_camara = st.camera_input("Tomar foto", key=f"cam_edit_{row['fid']}", label_visibility="collapsed")

            if actualizar_click:
                try:
                    foto_bytes_final = row['fotos']
                    if nueva_foto_camara is not None:
                        foto_bytes_final = nueva_foto_camara.getvalue()

                    sql_update = """
                        UPDATE "Agua_potable"."VPRS" 
                        SET id_0 = :id_0, id = :id, serie = :serie, diametro = :diametro, marca_valv = :marca_valv, 
                            model_valv = :model_valv, marca_trim = :marca_trim, domicilio = :domicilio, 
                            colonia = :colonia, cota_terr = :cota_terr, sector_hid = :sector_hid, 
                            cal_ant_d = :cal_ant_d, cal_ant_n = :cal_ant_n, fecha_ult_ = :fecha_ult_, 
                            cal_act_d = :cal_act_d, cal_act_n = :cal_act_n, hora_cal = :hora_cal, 
                            estat_valv = :estat_valv, observ = :observ, fotos = :fotos 
                        WHERE fid = :fid
                    """
                    ejecutar_sql(sql_update, {
                        "id_0": e_id_0, "id": e_id, "serie": e_serie if e_serie.strip() != "" else None, "diametro": e_diametro, "marca_valv": e_marca,
                        "model_valv": e_modelo, "marca_trim": e_trim, "domicilio": e_domicilio, "colonia": e_colonia,
                        "cota_terr": e_cota, "sector_hid": e_sector, "cal_ant_d": e_cal_ant_d, "cal_ant_n": e_cal_ant_n,
                        "fecha_ult_": e_fecha, "cal_act_d": e_cal_act_d, "cal_act_n": e_cal_act_n, "hora_cal": e_hora,
                        "estat_valv": e_estat, "observ": e_observ, "fotos": foto_bytes_final, "fid": row['fid']
                    })
                    st.success("¡Actualizado con éxito!")
                    t.sleep(0.8)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al actualizar: {ex}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🗑️ Eliminar", key=f"del_{row['fid']}", use_container_width=True):
                st.session_state.registro_to_delete = row['fid']
                st.rerun()
                
            st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.1);'>", unsafe_allow_html=True)

    if st.session_state.registro_to_delete is not None:
        target_fid = st.session_state.registro_to_delete
        st.warning(f"⚠️ Estás a punto de eliminar el registro FID: {target_fid}")
        confirm = st.text_input("Escribe 'delete' para confirmar:", key="del_confirm_input")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
                if confirm.strip().lower() == "delete":
                    try:
                        ejecutar_sql('DELETE FROM "Agua_potable"."VPRS" WHERE fid = :fid', {"fid": target_fid})
                        st.success("Registro eliminado.")
                        st.session_state.registro_to_delete = None
                        t.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al borrar: {ex}")
                else:
                    st.error("Debes escribir 'delete'.")
        with c2:
            if st.button("Cancelar", use_container_width=True):
                st.session_state.registro_to_data = None
                st.session_state.registro_to_delete = None
                st.rerun()

# --- PIE DE PÁGINA ---
st.markdown("""
    <div style="text-align: center; color: #94A3B8; font-size: 0.78rem; margin-top: 2rem; border-top: 1px solid rgba(0, 229, 255, 0.12); padding-top: 0.8rem;">
        © 2026 MIAA &bull; Sistema de Gestión PostGIS
    </div>
""", unsafe_allow_html=True)
