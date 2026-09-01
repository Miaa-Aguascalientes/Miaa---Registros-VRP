import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import time as t
from zoneinfo import ZoneInfo

# Configuración de página
st.set_page_config(layout="wide", page_title="Gestión Completa VPRS - MIAA", page_icon="https://www.miaa.mx/favicon.ico")

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
        pool_timeout=30,
        connect_args={'connect_timeout': 30}
    )

if 'db_engine' not in st.session_state:
    st.session_state.db_engine = crear_nuevo_engine()

def obtener_datos(query):
    """Ejecuta consultas devolviendo el dataframe."""
    try:
        with st.session_state.db_engine.connect() as conn:
            df = pd.read_sql(text(query) if isinstance(query, str) else query, conn)
            return df, None
    except Exception as e:
        try:
            st.session_state.db_engine.dispose()
            st.session_state.db_engine = crear_nuevo_engine()
            with st.session_state.db_engine.connect() as conn:
                df = pd.read_sql(text(query) if isinstance(query, str) else query, conn)
                return df, None
        except Exception as e2:
            return pd.DataFrame(), str(e2)

def ejecutar_sql(query, params=None):
    """Ejecuta sentencias SQL de escritura/actualización en Postgres."""
    with st.session_state.db_engine.connect() as conn:
        with conn.begin():
            conn.execute(text(query) if isinstance(query, str) else query, params or {})
    return True

# --- ESTILOS CSS ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0.2rem !important; 
        padding-bottom: 2rem !important;
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
        max-width: 1300px;
    }
    body, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top center, #0F2042 0%, #070D1B 70%);
        color: #FFFFFF;
    }
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
        flex: 1;
        text-align: center;
        cursor: pointer;
    }
    div.row-widget.stRadio input[type="radio"] { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] > label > div:first-child { display: none !important; }
    div.row-widget.stRadio div[role="radiogroup"] label span,
    div.row-widget.stRadio div[role="radiogroup"] label p {
        color: #00E5FF !important;
        font-weight: 600 !important;
    }
    div.row-widget.stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #0077B6, #00E5FF) !important;
        border-color: #00E5FF !important;
    }
    div.row-widget.stRadio > div > label[data-checked="true"] span {
        color: #070D1B !important;
        font-weight: 700 !important;
    }
    .stTextInput label, .stSelectbox label, .stNumberInput label, [data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    .user-card {
        background: linear-gradient(90deg, #1A2A56 0%, #162247 100%);
        border: 1px solid rgba(0, 229, 255, 0.15);
        border-left: 4px solid #00E5FF;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0077B6, #00E5FF);
        color: #070D1B;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        width: 100%;
    }
    div[data-baseweb="input"] input {
        background-color: #070D1B !important;
        color: #FFFFFF !important;
        border-color: rgba(0, 229, 255, 0.3) !important;
    }
</style>""", unsafe_allow_html=True)

# --- CABECERA ---
col_title_1, col_title_2, col_title_3 = st.columns([1, 6, 1])
with col_title_2:
    st.markdown("""
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 1rem;">
            <h2 style="color: #00E5FF; margin: 0; font-size: 1.4rem; font-weight: 800;">Gestión Completa de Válvulas VPRS (PostgreSQL)</h2>
        </div>
    """, unsafe_allow_html=True)

# --- MENÚ DE NAVEGACIÓN ---
opciones_menu = ["📍 Registros", "➕ Añadir Válvula", "⚙️ Editar / Eliminar"]

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

st.markdown("<hr style='border: 0.5px solid rgba(0,229,255,0.3); margin: 15px 0;'>", unsafe_allow_html=True)

COLUMNAS_VPRS = """
    fid, id_0, id, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
    cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
    hora_cal, estat_valv, observ
"""

# ==========================================
# SECCIÓN 1: VER REGISTROS (VPRS)
# ==========================================
if st.session_state.active_tab == "📍 Registros":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem;">📂 Catálogo Completo de Válvulas VPRS</h3>', unsafe_allow_html=True)
    
    query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid LIMIT 50'
    df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"❌ Error al consultar PostgreSQL: {error_db}")
    elif not df_vprs.empty:
        for _, row in df_vprs.iterrows():
            st.markdown(f"""
                <div class="user-card">
                    <span style="font-size: 1.1rem; font-weight: bold; color: #FFFFFF;">ID: {row['id']} | ID_0: {row['id_0']} (FID: {row['fid']})</span><br>
                    <span style="color: #00E5FF; font-size: 0.9rem;">📍 {row['domicilio'] or 'Sin domicilio'}, Col. {row['colonia'] or 'Sin colonia'}</span><br>
                    <span style="color: #8D99AE; font-size: 0.85rem;">
                        Diámetro: {row['diametro']}mm | Marca: {row['marca_valv']} | Modelo: {row['model_valv']} | Trim: {row['marca_trim']} | Cota: {row['cota_terr']}<br>
                        Sector: {row['sector_hid']} | Estado: {row['estat_valv']} | Hora Cal: {row['hora_cal']} | Fecha: {row['fecha_ult_']}<br>
                        Cal Anterior Día: {row['cal_ant_d']} | Cal Anterior Noche: {row['cal_ant_n']}<br>
                        Cal Actual Día: {row['cal_act_d']} | Cal Actual Noche: {row['cal_act_n']}<br>
                        Observaciones: {row['observ']}
                    </span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No se encontraron registros en la tabla VPRS.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVA VÁLVULA
# ==========================================
elif st.session_state.active_tab == "➕ Añadir Válvula":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem;">✨ Registrar nueva VPRS (Todos los campos)</h3>', unsafe_allow_html=True)
    
    with st.form("form_nueva_vprs"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            val_id_0 = st.number_input("ID_0 (Int)", min_value=0, value=0)
            val_id = st.text_input("ID (Texto)")
            val_diametro = st.number_input("Diámetro (mm)", min_value=0, value=50)
            val_cota = st.number_input("Cota Territorio", value=0.0)
        with col2:
            val_marca = st.text_input("Marca Válvula (marca_valv)")
            val_modelo = st.text_input("Modelo Válvula (model_valv)")
            val_trim = st.text_input("Marca Trim (marca_trim)")
            val_sector = st.text_input("Sector Hidráulico")
        with col3:
            val_domicilio = st.text_input("Domicilio")
            val_colonia = st.text_input("Colonia")
            val_estat = st.text_input("Estado Válvula (estat_valv)")
            val_hora = st.text_input("Hora Calibración (hora_cal)")
        with col4:
            val_cal_ant_d = st.text_input("Cal Anterior Día (cal_ant_d)")
            val_cal_ant_n = st.text_input("Cal Anterior Noche (cal_ant_n)")
            val_cal_act_d = st.text_input("Cal Actual Día (cal_act_d)")
            val_cal_act_n = st.text_input("Cal Actual Noche (cal_act_n)")

        col_extra1, col_extra2 = st.columns(2)
        with col_extra1:
            val_fecha = st.text_input("Fecha Última (fecha_ult_)")
        with col_extra2:
            val_observ = st.text_input("Observaciones (observ)")

        btn_guardar = st.form_submit_button("💾 Guardar Registro Completo")
        if btn_guardar:
            if val_id:
                try:
                    sql_insert = """
                        INSERT INTO "Agua_potable"."VPRS" (
                            id_0, id, diametro, marca_valv, model_valv, marca_trim, domicilio, colonia, 
                            cota_terr, sector_hid, cal_ant_d, cal_ant_n, fecha_ult_, cal_act_d, cal_act_n, 
                            hora_cal, estat_valv, observ
                        ) VALUES (
                            :id_0, :id, :diametro, :marca_valv, :model_valv, :marca_trim, :domicilio, :colonia, 
                            :cota_terr, :sector_hid, :cal_ant_d, :cal_ant_n, :fecha_ult_, :cal_act_d, :cal_act_n, 
                            :hora_cal, :estat_valv, :observ
                        )
                    """
                    ejecutar_sql(sql_insert, {
                        "id_0": val_id_0, "id": val_id, "diametro": val_diametro, "marca_valv": val_marca,
                        "model_valv": val_modelo, "marca_trim": val_trim, "domicilio": val_domicilio, "colonia": val_colonia,
                        "cota_terr": val_cota, "sector_hid": val_sector, "cal_ant_d": val_cal_ant_d, "cal_ant_n": val_cal_ant_n,
                        "fecha_ult_": val_fecha, "cal_act_d": val_cal_act_d, "cal_act_n": val_cal_act_n, "hora_cal": val_hora,
                        "estat_valv": val_estat, "observ": val_observ
                    })
                    st.success("¡Válvula VPRS registrada exitosamente con todos sus campos!")
                    t.sleep(1)
                    st.rerun()
                except Exception as ex:
                    st.error(f"Error al insertar en la base de datos: {ex}")
            else:
                st.warning("El campo ID es obligatorio.")

# ==========================================
# SECCIÓN 3: EDITAR Y ELIMINAR
# ==========================================
elif st.session_state.active_tab == "⚙️ Editar / Eliminar":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.2rem;">🛠️ Modificar o Eliminar Válvula (Campos Completos)</h3>', unsafe_allow_html=True)
    
    query = f'SELECT {COLUMNAS_VPRS} FROM "Agua_potable"."VPRS" ORDER BY fid LIMIT 100'
    df_vprs, error_db = obtener_datos(query)
    
    if error_db:
        st.error(f"Error: {error_db}")
    elif not df_vprs.empty:
        for idx, row in df_vprs.iterrows():
            with st.form(key=f"form_edit_{row['fid']}"):
                st.markdown(f"**FID Registro: {row['fid']}** | ID: {row['id']}")
                
                e1, e2, e3, e4 = st.columns(4)
                with e1:
                    e_id_0 = st.number_input("ID_0", value=int(row['id_0'] or 0), key=f"id0_{row['fid']}")
                    e_id = st.text_input("ID", value=str(row['id'] or ""), key=f"id_{row['fid']}")
                    e_diametro = st.number_input("Diámetro", value=int(row['diametro'] or 0), key=f"diam_{row['fid']}")
                    e_cota = st.number_input("Cota Terr", value=float(row['cota_terr'] or 0.0), key=f"cota_{row['fid']}")
                with e2:
                    e_marca = st.text_input("Marca Valv", value=str(row['marca_valv'] or ""), key=f"mar_{row['fid']}")
                    e_modelo = st.text_input("Modelo Valv", value=str(row['model_valv'] or ""), key=f"mod_{row['fid']}")
                    e_trim = st.text_input("Marca Trim", value=str(row['marca_trim'] or ""), key=f"trim_{row['fid']}")
                    e_sector = st.text_input("Sector Hid", value=str(row['sector_hid'] or ""), key=f"sec_{row['fid']}")
                with e3:
                    e_domicilio = st.text_input("Domicilio", value=str(row['domicilio'] or ""), key=f"dom_{row['fid']}")
                    e_colonia = st.text_input("Colonia", value=str(row['colonia'] or ""), key=f"col_{row['fid']}")
                    e_estat = st.text_input("Estado Valv", value=str(row['estat_valv'] or ""), key=f"est_{row['fid']}")
                    e_hora = st.text_input("Hora Cal", value=str(row['hora_cal'] or ""), key=f"hora_{row['fid']}")
                with e4:
                    e_cal_ant_d = st.text_input("Cal Anterior Día", value=str(row['cal_ant_d'] or ""), key=f"cand_{row['fid']}")
                    e_cal_ant_n = st.text_input("Cal Anterior Noche", value=str(row['cal_ant_n'] or ""), key=f"cann_{row['fid']}")
                    e_cal_act_d = st.text_input("Cal Actual Día", value=str(row['cal_act_d'] or ""), key=f"cactd_{row['fid']}")
                    e_cal_act_n = st.text_input("Cal Actual Noche", value=str(row['cal_act_n'] or ""), key=f"cactn_{row['fid']}")

                e_f1, e_f2 = st.columns(2)
                with e_f1:
                    e_fecha = st.text_input("Fecha Ult", value=str(row['fecha_ult_'] or ""), key=f"fec_{row['fid']}")
                with e_f2:
                    e_observ = st.text_input("Observaciones", value=str(row['observ'] or ""), key=f"obs_{row['fid']}")
                
                btn_act = st.form_submit_button("💾 Actualizar Todos los Campos")
                if btn_act:
                    try:
                        sql_update = """
                            UPDATE "Agua_potable"."VPRS" 
                            SET id_0 = :id_0, id = :id, diametro = :diametro, marca_valv = :marca_valv, 
                                model_valv = :model_valv, marca_trim = :marca_trim, domicilio = :domicilio, 
                                colonia = :colonia, cota_terr = :cota_terr, sector_hid = :sector_hid, 
                                cal_ant_d = :cal_ant_d, cal_ant_n = :cal_ant_n, fecha_ult_ = :fecha_ult_, 
                                cal_act_d = :cal_act_d, cal_act_n = :cal_act_n, hora_cal = :hora_cal, 
                                estat_valv = :estat_valv, observ = :observ 
                            WHERE fid = :fid
                        """
                        ejecutar_sql(sql_update, {
                            "id_0": e_id_0, "id": e_id, "diametro": e_diametro, "marca_valv": e_marca,
                            "model_valv": e_modelo, "marca_trim": e_trim, "domicilio": e_domicilio, "colonia": e_colonia,
                            "cota_terr": e_cota, "sector_hid": e_sector, "cal_ant_d": e_cal_ant_d, "cal_ant_n": e_cal_ant_n,
                            "fecha_ult_": e_fecha, "cal_act_d": e_cal_act_d, "cal_act_n": e_cal_act_n, "hora_cal": e_hora,
                            "estat_valv": e_estat, "observ": e_observ, "fid": row['fid']
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
    <div style="text-align: center; color: #8D99AE; font-size: 0.85rem; margin-top: 3rem; border-top: 1px solid rgba(0, 229, 255, 0.1); padding-top: 1.5rem;">
        © 2026 MIAA &bull; Sistema de Gestión PostGIS
    </div>
""", unsafe_allow_html=True)
