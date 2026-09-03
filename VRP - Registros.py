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

# --- ESTILOS CSS ---
st.write("""<style>
    #MainMenu, header {visibility: hidden;} 
    .block-container {
        padding-top: 0rem !important; 
        padding-bottom: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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

    /* Tarjetas de registros principales a ancho completo (1 columna) */
    .user-card {
        background: #0D1424;
        border: 1px solid rgba(0, 229, 255, 0.12);
        border-left: 4px solid #00E5FF;
        border-radius: 4px;
        padding: 10px 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        word-break: break-word;
        box-sizing: border-box;
        width: 100% !important;
        margin-bottom: 8px;
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

    .stButton>button {
        background: linear-gradient(135deg, #0077B6 0%, #00E5FF 100%);
        color: #080C14;
        border: none;
        border-radius: 4px;
        font-weight: 700;
        padding: 0.5rem 1rem;
        width: 100%;
        box-shadow: 0 4px 12px rgba(0, 229, 255, 0.2);
    }
    .stButton>button:hover {
        opacity: 0.95;
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
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 6px; padding: 0 2px;'>Mostrando primeros 10 registros.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 6px; padding: 0 2px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
            
        for idx, row in df_vprs.iterrows():
            serie_val = row['serie']
            serie_texto = "" if (pd.isna(serie_val) or str(serie_val).strip().lower() in ["nan", "none", ""]) else f" | Serie: {serie_val}"
            
            card_html = f"""
                <div class="user-card">
                    <span style="font-size: 0.85rem; font-weight: bold; color: #F8FAFC;">ID: {row['id']}{serie_texto}</span><br>
                    <span style="color: #00E5FF; font-size: 0.75rem;">📍 {row['domicilio'] or 'Sin domicilio'}, Col. {row['colonia'] or 'Sin colonia'}</span><br>
                    <span style="color: #94A3B8; font-size: 0.7rem; line-height: 1.3;">
                        Diámetro: {row['diametro']}mm | Marca: {row['marca_valv']} | Modelo: {row['model_valv']} | Trim: {row['marca_trim']} | Cota: {row['cota_terr']}<br>
                        Sector: {row['sector_hid']} | Estado: {row['estat_valv']} | Hora Cal: {row['hora_cal']} | Fecha: {row['fecha_ult_']}<br>
                        Cal Ant Día: {row['cal_ant_d']} | Cal Ant Noche: {row['cal_ant_n']}<br>
                        Cal Act Día: {row['cal_act_d']} | Cal Act Noche: {row['cal_act_n']}<br>
                        Obs: {row['observ']}
                    </span>
                </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            foto_data = row['fotos']
            if foto_data is not None and len(foto_data) > 0:
                try:
                    if isinstance(foto_data, bytes):
                        st.image(foto_data, caption=f"ID: {row['id']}", width=220)
                    elif isinstance(foto_data, str) and len(foto_data) > 10:
                        st.image(base64.b64decode(foto_data), caption=f"ID: {row['id']}", width=220)
                except:
                    pass
            st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)
    else:
        st.info("No se encontraron registros.")

# ==========================================
# SECCIÓN 2: AÑADIR NUEVA VÁLVULA
# ==========================================
elif st.session_state.active_tab == "➕ Añadir":
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;">✨ Registrar nueva VPRS</h3>', unsafe_allow_html=True)
    
    val_id_0 = st.number_input("ID_0 (Int)", min_value=0, value=0)
    val_id = st.text_input("ID (Texto)")
    val_serie = st.text_input("Serie")
    val_diametro = st.number_input("Diámetro (mm)", min_value=0, value=50)
    val_cota = st.number_input("Cota Territorio", value=0.0)
    val_marca = st.text_input("Marca Válvula")
    val_modelo = st.text_input("Modelo Válvula")
    val_trim = st.text_input("Marca Trim")
    val_sector = st.text_input("Sector Hidráulico")
    val_domicilio = st.text_input("Domicilio")
    val_colonia = st.text_input("Colonia")
    val_estat = st.text_input("Estado Válvula")
    val_hora = st.text_input("Hora Calibración")
    val_cal_ant_d = st.text_input("Cal Anterior Día")
    val_cal_ant_n = st.text_input("Cal Anterior Noche")
    val_cal_act_d = st.text_input("Cal Actual Día")
    val_cal_act_n = st.text_input("Cal Actual Noche")
    val_fecha = st.text_input("Fecha Última")
    val_observ = st.text_input("Observaciones")

    st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.2);'>", unsafe_allow_html=True)
    st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.8rem;'>📸 Fotografía:</p>", unsafe_allow_html=True)
    
    foto_subida = st.file_uploader("Subir imagen", type=["jpg", "jpeg", "png"], key="subir_nuevo")
    activar_camara_nuevo = st.checkbox("🟢 Activar cámara", key="chk_cam_nuevo")
    foto_camara = None
    if activar_camara_nuevo:
        foto_camara = st.camera_input("Capturar", key="camara_nuevo")

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
    st.markdown('<h3 style="color: #00E5FF; font-size: 1.05rem; font-weight: 700; margin-bottom: 8px;">🛠️ Modificar o Eliminar Válvula</h3>', unsafe_allow_html=True)
    
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
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px;'>Mostrando primeros 10 registros.</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #94A3B8; font-size: 0.78rem; margin-bottom: 4px;'>Se encontraron {len(df_vprs)} registros.</p>", unsafe_allow_html=True)
            
        for idx, row in df_vprs.iterrows():
            st.markdown(f"<span style='color: #00E5FF; font-weight: bold;'>FID Registro: {row['fid']}</span> | <span style='color: #F8FAFC;'>ID: {row['id']}</span>", unsafe_allow_html=True)
            
            e_id_0 = st.number_input("ID_0", value=int(row['id_0'] or 0), key=f"id0_{row['fid']}")
            e_id = st.text_input("ID", value=str(row['id'] or ""), key=f"id_{row['fid']}")
            
            e_serie_val = "" if (pd.isna(row['serie']) or str(row['serie']).strip().lower() in ["nan", "none"]) else str(row['serie'])
            e_serie = st.text_input("Serie", value=e_serie_val, key=f"serie_{row['fid']}")
            e_diametro = st.number_input("Diámetro", value=int(row['diametro'] or 0), key=f"diam_{row['fid']}")
            e_cota = st.number_input("Cota Terr", value=float(row['cota_terr'] or 0.0), key=f"cota_{row['fid']}")
            e_marca = st.text_input("Marca Valv", value=str(row['marca_valv'] or ""), key=f"mar_{row['fid']}")
            e_modelo = st.text_input("Modelo Valv", value=str(row['model_valv'] or ""), key=f"mod_{row['fid']}")
            e_trim = st.text_input("Marca Trim", value=str(row['marca_trim'] or ""), key=f"trim_{row['fid']}")
            e_sector = st.text_input("Sector Hid", value=str(row['sector_hid'] or ""), key=f"sec_{row['fid']}")
            e_domicilio = st.text_input("Domicilio", value=str(row['domicilio'] or ""), key=f"dom_{row['fid']}")
            e_colonia = st.text_input("Colonia", value=str(row['colonia'] or ""), key=f"col_{row['fid']}")
            e_estat = st.text_input("Estado Valv", value=str(row['estat_valv'] or ""), key=f"est_{row['fid']}")
            e_hora = st.text_input("Hora Cal", value=str(row['hora_cal'] or ""), key=f"hora_{row['fid']}")
            e_cal_ant_d = st.text_input("Cal Anterior Día", value=str(row['cal_ant_d'] or ""), key=f"cand_{row['fid']}")
            e_cal_ant_n = st.text_input("Cal Anterior Noche", value=str(row['cal_ant_n'] or ""), key=f"cann_{row['fid']}")
            e_cal_act_d = st.text_input("Cal Actual Día", value=str(row['cal_act_d'] or ""), key=f"cactd_{row['fid']}")
            e_cal_act_n = st.text_input("Cal Actual Noche", value=str(row['cal_act_n'] or ""), key=f"cactn_{row['fid']}")
            e_fecha = st.text_input("Fecha Ult", value=str(row['fecha_ult_'] or ""), key=f"fec_{row['fid']}")
            e_observ = st.text_input("Observaciones", value=str(row['observ'] or ""), key=f"obs_{row['fid']}")
            
            foto_actual = row['fotos']
            if foto_actual is not None and len(foto_actual) > 0:
                try:
                    if isinstance(foto_actual, bytes):
                        st.image(foto_actual, caption="Fotografía actual", width=200)
                    elif isinstance(foto_actual, str) and len(foto_actual) > 10:
                        st.image(base64.b64decode(foto_actual), caption="Fotografía actual", width=200)
                except:
                    pass

            st.markdown("<p style='color: #00E5FF; font-weight: 600; font-size: 0.78rem;'>📸 Actualizar foto:</p>", unsafe_allow_html=True)
            nueva_foto_subida = st.file_uploader("Subir foto", type=["jpg", "jpeg", "png"], key=f"up_edit_{row['fid']}")
            activar_camara_edit = st.checkbox("🟢 Activar cámara", key=f"chk_cam_edit_{row['fid']}")
            nueva_foto_camara = None
            if activar_camara_edit:
                nueva_foto_camara = st.camera_input("Tomar foto", key=f"cam_edit_{row['fid']}")
            
            if st.button("💾 Actualizar Registro", key=f"btn_act_{row['fid']}"):
                try:
                    foto_bytes_final = row['fotos']
                    if nueva_foto_camara is not None:
                        foto_bytes_final = nueva_foto_camara.getvalue()
                    elif nueva_foto_subida is not None:
                        foto_bytes_final = nueva_foto_subida.getvalue()

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

            if st.button("🗑️ Eliminar", key=f"del_{row['fid']}"):
                st.session_state.registro_to_delete = row['fid']
                st.rerun()
            st.markdown("<hr style='border: 0.3px solid rgba(0,229,255,0.1);'>", unsafe_allow_html=True)

    if st.session_state.registro_to_delete is not None:
        target_fid = st.session_state.registro_to_delete
        st.warning(f"⚠️ Estás a punto de eliminar el registro FID: {target_fid}")
        confirm = st.text_input("Escribe 'delete' para confirmar:", key="del_confirm_input")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Confirmar Eliminación", type="primary"):
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
            if st.button("Cancelar"):
                st.session_state.registro_to_delete = None
                st.rerun()

# --- PIE DE PÁGINA ---
st.markdown("""
    <div style="text-align: center; color: #94A3B8; font-size: 0.78rem; margin-top: 2rem; border-top: 1px solid rgba(0, 229, 255, 0.12); padding-top: 0.8rem;">
        © 2026 MIAA &bull; Sistema de Gestión PostGIS
    </div>
""", unsafe_allow_html=True)
