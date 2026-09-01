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
    """Ejecuta consultas devolviendo el dataframe asegurando reconexión."""
    for intento in range(2):
        try:
            with st.session_state.db_engine.connect() as conn:
                df = pd.read_sql(text(query) if isinstance(query, str) else query, conn, params=params or {})
                return df, None
        except Exception as e:
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
    """Ejecuta sentencias SQL de escritura/actualización en Postgres."""
    with st.session_state.db_engine.connect() as conn:
        with conn.begin():
            conn.execute(text(query) if isinstance(query, str) else query, params or {})
    return True

# --- ESTILOS CSS UNIFICADOS (Paleta MIAA Home Dark) ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0.2rem !important; 
        padding-bottom: 2.5rem !important;
        background: #080C14;
        color: #F8FAFC;
        max-width: 1350px;
    }
    body, [data-testid="stAppViewContainer"] {
        background: #080C14;
        color: #F8FAFC;
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
        gap: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    div.row-widget.stRadio > div > label {
        background: #111A30;
        border: 1px solid rgba(0, 229, 255, 0.15) !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        flex: 1;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
    }
    div.row-widget.stRadio > div > label:hover {
        border-color: rgba(0, 229, 255, 0.4) !important;
        background: #16223D;
    }
    div.row-widget.stRadio input[type="radio"] { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] label span,
    div.row-widget.stRadio div[role="radiogroup"] label p {
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.95rem;
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

    /* Etiquetas de formularios */
    .stTextInput label, .stSelectbox label, .stNumberInput label, [data-testid="stWidgetLabel"] p {
        color: #E2E8F0 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
    }

    /* Tarjetas de registros estilo MIAA */
    .user-card {
        background: #0D1424;
        border: 1px solid rgba(0, 229, 255, 0.12);
        border-left: 4px solid #00E5FF;
        border-radius: 12px;
        padding: 18px 22px;
        margin-bottom: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
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
        transition: all 0.2s;
    }
    .stButton>button:hover {
        opacity: 0.95;
        box-shadow: 0 4px 18px rgba(0, 229, 255, 0.4);
    }

    /* Campos de entrada de texto/números */
    div[data-baseweb="input"] input, div[data-baseweb="base-input"] input {
        background-color: #080C14 !important;
        color: #F8FAFC !important;
        border-color: rgba(0, 229, 255, 0.25) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input:focus {
        border-color: #00E5FF !important;
        box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA CON LOGOTIPO MÁS GRANDE Y TÍTULO A LA DERECHA ---
st.markdown("""
    <div style="display: flex; align-items: center; gap: 15px; width: 100%; margin-bottom: 5px;">
        <img src="https://raw.githubusercontent.com/Miaa-Aguascalientes/Logos/38504978c8f77a4dac38ad476f74dbdee6af2cad/LogoMIAA.svg" style="width: 125px; height: auto; flex-shrink: 0;" />
        <div>
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.4rem; font-weight: 800; line-height: 1.2;">Gestion VRP's</h2>
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

st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.15); margin: 15px 0;'>", unsafe_allow_html=True)

COLUMNAS_VPRS = """
    fid, id_0, id, serie, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
    cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
    hora_cal, estat_valv, observ, fotos
"""

# ==========================================
# SECCIÓN 1: VER REGISTROS (VPRS) CON BUSCADOR
# ==========================================
if st.session_state.active_tab == "📍 Registros":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">📂 Catálogo de Válvulas VPRS</h3>', unsafe_allow_html=True)
    
    busqueda = st.text_input("🔍 Buscar válvula (por ID, Serie, Domicilio o Colonia):", placeholder="Ej. VF01, Centro, etc.")
    
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
        query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid'
        df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"❌ Error al consultar PostgreSQL: {error_db}")
    elif not df_vprs.empty:
        st.markdown(f"<p style='color: #94A3B8; font-size: 0.85rem; margin-bottom: 10px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
        for _, row in df_vprs.iterrows():
            serie_val = row['serie']
            if pd.isna(serie_val) or str(serie_val).strip().lower() in ["nan", "none", ""]:
                serie_texto = ""
            else:
                serie_texto = f" | Serie: {serie_val}"

            st.markdown(f"""
                <div class="user-card">
                    <span style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC;">ID: {row['id']}{serie_texto}</span><br>
                    <span style="color: #00E5FF; font-size: 0.9rem;">📍 {row['domicilio'] or 'Sin domicilio'}, Col. {row['colonia'] or 'Sin colonia'}</span><br>
                    <span style="color: #94A3B8; font-size: 0.85rem; line-height: 1.5;">
                        Diámetro: {row['diametro']}mm | Marca: {row['marca_valv']} | Modelo: {row['model_valv']} | Trim: {row['marca_trim']} | Cota: {row['cota_terr']}<br>
                        Sector: {row['sector_hid']} | Estado: {row['estat_valv']} | Hora Cal: {row['hora_cal']} | Fecha: {row['fecha_ult_']}<br>
                        Cal Anterior Día: {row['cal_ant_d']} | Cal Anterior Noche: {row['cal_ant_n']}<br>
                        Cal Actual Día: {row['cal_act_d']} | Cal Actual Noche: {row['cal_act_n']}<br>
                        Observaciones: {row['observ']}
                    </span>
                </div>
            """, unsafe_allow_html=True)
            
            foto_data = row['fotos']
            if foto_data is not None and len(foto_data) > 0:
                try:
                    if isinstance(foto_data, bytes):
                        st.image(foto_data, caption=f"Fotografía de Válvula - ID: {row['id']}", width=300)
                    elif isinstance(foto_data, str) and len(foto_data) > 10:
                        st.image(base64.b64decode(foto_data), caption=f"Fotografía de Válvula - ID: {row['id']}", width=300)
                except Exception:
                    st.warning(f"No se pudo renderizar la fotografía para el registro {row['id']}.")
    else:
        st.info("No se encontraron registros que coincidan con la búsqueda.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVA VÁLVULA
# ==========================================
elif st.session_state.active_tab == "➕ Añadir":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">✨ Registrar nueva VPRS (Todos los campos + Fotografía)</h3>', unsafe_allow_html=True)
    
    with st.form("form_nueva_vprs"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            val_id_0 = st.number_input("ID_0 (Int)", min_value=0, value=0)
            val_id = st.text_input("ID (Texto)")
            val_serie = st.text_input("Serie")
            val_diametro = st.number_input("Diámetro (mm)", min_value=0, value=50)
        with col2:
            val_cota = st.number_input("Cota Territorio", value=0.0)
            val_marca = st.text_input("Marca Válvula (marca_valv)")
            val_modelo = st.text_input("Modelo Válvula (model_valv)")
            val_trim = st.text_input("Marca Trim (marca_trim)")
        with col3:
            val_sector = st.text_input("Sector Hidráulico")
            val_domicilio = st.text_input("Domicilio")
            val_colonia = st.text_input("Colonia")
            val_estat = st.text_input("Estado Válvula (estat_valv)")
        with col4:
            val_hora = st.text_input("Hora Calibración (hora_cal)")
            val_cal_ant_d = st.text_input("Cal Anterior Día (cal_ant_d)")
            val_cal_ant_n = st.text_input("Cal Anterior Noche (cal_ant_n)")
            val_cal_act_d = st.text_input("Cal Actual Día (cal_act_d)")
            val_cal_act_n = st.text_input("Cal Actual Noche (cal_act_n)")

        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            val_fecha = st.text_input("Fecha Última (fecha_ult_)")
        with col_extra2:
            val_observ = st.text_input("Observaciones (observ)")

        st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
        st.markdown("<p style='color: #00E5FF; font-weight: 600;'>📸 Capturar Fotografía de la Válvula:</p>", unsafe_allow_html=True)
        foto_capturada = st.camera_input("Toma una foto de la instalación", label_visibility="collapsed")

        btn_guardar = st.form_submit_button("💾 Guardar Registro Completo")
        if btn_guardar:
            if val_id:
                try:
                    foto_bytes = foto_capturada.getvalue() if foto_capturada is not None else None
                    
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
                    st.success("¡Válvula VPRS registrada exitosamente con su fotografía!")
                    t.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al insertar en la base de datos: {ex}")
            else:
                st.warning("El campo ID es obligatorio.")

# ==========================================
# SECCIÓN 3: EDITAR Y ELIMINAR
# ==========================================
elif st.session_state.active_tab == "⚙️ Editar":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px;">🛠️ Modificar o Eliminar Válvula (Incluye Actualización de Foto)</h3>', unsafe_allow_html=True)
    
    busqueda_edit = st.text_input("🔍 Filtrar registros a editar (por ID, Serie, Domicilio o Colonia):", placeholder="Dejar en blanco para ver todos o buscar uno...")
    
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
        query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid'
        df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"Error: {error_db}")
    elif not df_vprs.empty:
        st.markdown(f"<p style='color: #94A3B8; font-size: 0.85rem; margin-bottom: 10px;'>Mostrando {len(df_vprs)} registros para gestión.</p>", unsafe_allow_html=True)
        for idx, row in df_vprs.iterrows():
            with st.form(key=f"form_edit_{row['fid']}"):
                st.markdown(f"<span style='color: #00E5FF; font-weight: bold;'>FID Registro: {row['fid']}</span> | <span style='color: #F8FAFC;'>ID: {row['id']}</span>", unsafe_allow_html=True)
                
                e1, e2, e3, e4 = st.columns(4)
                with e1:
                    e_id_0 = st.number_input("ID_0", value=int(row['id_0'] or 0), key=f"id0_{row['fid']}")
                    e_id = st.text_input("ID", value=str(row['id'] or ""), key=f"id_{row['fid']}")
                    e_serie_val = "" if (pd.isna(row['serie']) or str(row['serie']).strip().lower() in ["nan", "none"]) else str(row['serie'])
                    e_serie = st.text_input("Serie", value=e_serie_val, key=f"serie_{row['fid']}")
                    e_diametro = st.number_input("Diámetro", value=int(row['diametro'] or 0), key=f"diam_{row['fid']}")
                with e2:
                    e_cota = st.number_input("Cota Terr", value=float(row['cota_terr'] or 0.0), key=f"cota_{row['fid']}")
                    e_marca = st.text_input("Marca Valv", value=str(row['marca_valv'] or ""), key=f"mar_{row['fid']}")
                    e_modelo = st.text_input("Modelo Valv", value=str(row['model_valv'] or ""), key=f"mod_{row['fid']}")
                    e_trim = st.text_input("Marca Trim", value=str(row['marca_trim'] or ""), key=f"trim_{row['fid']}")
                with e3:
                    e_sector = st.text_input("Sector Hid", value=str(row['sector_hid'] or ""), key=f"sec_{row['fid']}")
                    e_domicilio = st.text_input("Domicilio", value=str(row['domicilio'] or ""), key=f"dom_{row['fid']}")
                    e_colonia = st.text_input("Colonia", value=str(row['colonia'] or ""), key=f"col_{row['fid']}")
                    e_estat = st.text_input("Estado Valv", value=str(row['estat_valv'] or ""), key=f"est_{row['fid']}")
                with e4:
                    e_hora = st.text_input("Hora Cal", value=str(row['hora_cal'] or ""), key=f"hora_{row['fid']}")
                    e_cal_ant_d = st.text_input("Cal Anterior Día", value=str(row['cal_ant_d'] or ""), key=f"cand_{row['fid']}")
                    e_cal_ant_n = st.text_input("Cal Anterior Noche", value=str(row['cal_ant_n'] or ""), key=f"cann_{row['fid']}")
                    e_cal_act_d = st.text_input("Cal Actual Día", value=str(row['cal_act_d'] or ""), key=f"cactd_{row['fid']}")
                    e_cal_act_n = st.text_input("Cal Actual Noche", value=str(row['cal_act_n'] or ""), key=f"cactn_{row['fid']}")

                e_f1, e_f2 = st.columns(2)
                with e_f1:
                    e_fecha = st.text_input("Fecha Ult", value=str(row['fecha_ult_'] or ""), key=f"fec_{row['fid']}")
                with e_f2:
                    e_observ = st.text_input("Observaciones", value=str(row['observ'] or ""), key=f"obs_{row['fid']}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                foto_actual = row['fotos']
                if foto_actual is not None and len(foto_actual) > 0:
                    try:
                        if isinstance(foto_actual, bytes):
                            st.image(foto_actual, caption="Fotografía actual almacenada", width=200)
                        elif isinstance(foto_actual, str) and len(foto_actual) > 10:
                            st.image(base64.b64decode(foto_actual), caption="Fotografía actual almacenada", width=200)
                    except:
                        pass

                st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.85rem;'>📸 Reemplazar o tomar nueva fotografía (Opcional):</p>", unsafe_allow_html=True)
                nueva_foto_capturada = st.camera_input("Tomar nueva foto", key=f"cam_edit_{row['fid']}", label_visibility="collapsed")
                
                btn_act = st.form_submit_button("💾 Actualizar Registro y Fotografía")
                if btn_act:
                    try:
                        foto_bytes_final = nueva_foto_capturada.getvalue() if nueva_foto_capturada is not None else row['fotos']

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
                        st.success("¡Registro actualizado con éxito!")
                        t.sleep(0.8)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al actualizar: {ex}")

            d_col1, d_col2 = st.columns([6, 2])
            with d_col2:
                if st.button("🗑️ Eliminar", key=f"del_{row['fid']}", use_container_width=True):
                    st.session_state.registro_to_delete = row['fid']
                    st.rerun()
            st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.1);'>", unsafe_allow_html=True)

    if st.session_state.registro_to_delete is not None:
        target_fid = st.session_state.registro_to_delete
        st.warning(f"⚠️ Estás a punto de eliminar permanentemente el registro con FID: {target_fid}")
        confirm = st.text_input("Escribe 'delete' para confirmar la eliminación:", key="del_confirm_input")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Confirmar Eliminación", type="primary"):
                if confirm.strip().lower() == "delete":
                    try:
                        ejecutar_sql('DELETE FROM "Agua_potable"."VPRS" WHERE fid = :fid', {"fid": target_fid})
                        st.success("Registro eliminado con éxito.")
                        st.session_state.registro_to_delete = None
                        t.sleep(0.5)
                        st.rerun()
                    except Exception as ex:
                        st.error(f"Error al borrar: {ex}")
                else:
                    st.error("Debes escribir 'delete'.")
        with c2:
            if st.button("Cancelar"):
                st.session_state.registro_to_delete = None
                st.rerun()

# --- PIE DE PÁGINA ---
st.markdown("""
    <div style="text-align: center; color: #94A3B8; font-size: 0.85rem; margin-top: 3rem; border-top: 1px solid rgba(0, 229, 255, 0.12); padding-top: 1.5rem;">
        © 2026 MIAA &bull; Sistema de Gestión PostGIS
    </div>
""", unsafe_allow_html=True)
