import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuración inicial de la página
st.set_page_config(page_title="Gestor de Válvulas VRP y Telemetría", layout="wide")

# ---------------------------------------------------------
# CONEXIONES A LAS BASES DE DATOS (Motores SQLAlchemy)
# ---------------------------------------------------------

# Motor para PostgreSQL (Datos espaciales QGIS / mapas)
def crear_motor_postgres():
    pg = st.secrets["postgres"]
    db_url = f"postgresql+psycopg2://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)

# Motor para MySQL (Tabla de usuarios y autenticación en miaamx_telemetria2)
def crear_motor_mysql():
    ms = st.secrets["mysql_usuarios"]
    db_url = f"mysql+pymysql://{ms['user']}:{ms['password']}@{ms['host']}:{ms.get('port', 3306)}/{ms['database']}"
    return create_engine(db_url, pool_pre_ping=True, pool_recycle=1800)

# Inicializar motores en session_state para mantener la persistencia
if 'db_engine_pg' not in st.session_state:
    st.session_state.db_engine_pg = crear_motor_postgres()

if 'db_engine_mysql' not in st.session_state:
    st.session_state.db_engine_mysql = crear_motor_mysql()

# ---------------------------------------------------------
# FUNCIONES DE CONSULTA
# ---------------------------------------------------------

def consultar_mysql(query, params=None):
    try:
        with st.session_state.db_engine_mysql.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params or {})
            return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

def consultar_postgres(query, params=None):
    try:
        with st.session_state.db_engine_pg.connect() as conn:
            df = pd.read_sql(text(query), conn, params=params or {})
            return df, None
    except Exception as e:
        return pd.DataFrame(), str(e)

# ---------------------------------------------------------
# ESTADO DE AUTENTICACIÓN
# ---------------------------------------------------------
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_actual' not in st.session_state:
    st.session_state.usuario_actual = None
if 'tipo_usuario' not in st.session_state:
    st.session_state.tipo_usuario = None
if 'departamento' not in st.session_state:
    st.session_state.departamento = None

# ---------------------------------------------------------
# PANTALLA DE LOGIN
# ---------------------------------------------------------
if not st.session_state.autenticado:
    st.title("🔐 Iniciar Sesión - Sistema MIAA")
    
    with st.form("form_login"):
        input_usuario = st.text_input("Usuario")
        input_password = st.text_input("Contraseña", type="password")
        submit_login = st.form_submit_button("Ingresar")
        
        if submit_login:
            if not input_usuario or not input_password:
                st.warning("Por favor, introduce tu usuario y contraseña.")
            else:
                # Consulta a MySQL (tabla usuarios_vrp)
                query_login = """
                    SELECT id, usuario, password, tipo_usuario, departamento 
                    FROM usuarios_vrp 
                    WHERE usuario = :usuario AND password = :password
                """
                df_user, err_login = consultar_mysql(
                    query_login, 
                    {"usuario": input_usuario.strip(), "password": input_password.strip()}
                )
                
                if err_login:
                    st.error(f"Error de conexión con la base de datos de usuarios: {err_login}")
                elif not df_user.empty:
                    st.session_state.autenticado = True
                    st.session_state.usuario_actual = df_user.iloc[0]['usuario']
                    st.session_state.tipo_usuario = df_user.iloc[0]['tipo_usuario']
                    st.session_state.departamento = df_user.iloc[0]['departamento']
                    st.success("¡Bienvenido! Accediendo...")
                    st.rerun()
                else:
                    st.error("Usuario o contraseña incorrectos.")
else:
    # ---------------------------------------------------------
    # APLICACIÓN PRINCIPAL (POST-LOGIN)
    # ---------------------------------------------------------
    st.sidebar.title("Menú Principal")
    st.sidebar.write(f"**Usuario:** {st.session_state.usuario_actual}")
    st.sidebar.write(f"**Tipo:** {st.session_state.tipo_usuario}")
    st.sidebar.write(f"**Departamento:** {st.session_state.departamento}")
    
    menu_opcion = st.sidebar.radio("Navegación", ["Gestor de Válvulas", "Consultas PostgreSQL", "Estado del Sistema"])
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.session_state.usuario_actual = None
        st.session_state.tipo_usuario = None
        st.session_state.departamento = None
        st.rerun()

    if menu_opcion == "Gestor de Válvulas":
        st.title("🚰 Módulo de Gestor de Válvulas VRP")
        st.write("Bienvenido al panel de control operativo. Aquí puedes administrar las instalaciones de válvulas.")
        
        # Formulario o elementos del gestor de válvulas
        with st.form("form_valvula"):
            st.subheader("Registrar / Modificar Válvula")
            col1, col2 = st.columns(2)
            with col1:
                val_nombre = st.text_input("Identificador / Nombre de Válvula")
                val_sector = st.text_input("Sector Hidráulico")
            with col2:
                val_tipo = st.selectbox("Tipo de Válvula", ["VRP", "Compuerta", "Seccionamiento", "Alivio"])
                val_estado = st.selectbox("Estado Operativo", ["Activo", "Mantenimiento", "Fuera de Servicio"])
            
            submit_valvula = st.form_submit_button("Guardar Cambios")
            if submit_valvula:
                st.success(f"Válvula '{val_nombre}' procesada correctamente para el sector {val_sector}.")

    elif menu_opcion == "Consultas PostgreSQL":
        st.title("🗺️ Capas y Datos de PostgreSQL (qgis)")
        st.write("Consulta directa sobre la infraestructura geoespacial.")
        
        # Ejemplo completo de consulta a PostgreSQL (ajusta el esquema y tabla según necesites)
        tabla_input = st.text_input("Nombre de la tabla en PostgreSQL", value="Agua_potable.usuarios_vrp")
        if st.button("Cargar Datos de Postgres"):
            query_pg = f'SELECT * FROM "{tabla_input.split(".")[0]}"."{tabla_input.split(".")[1]}" LIMIT 50' if "." in tabla_input else f'SELECT * FROM "{tabla_input}" LIMIT 50'
            df_pg, err_pg = consultar_postgres(query_pg)
            if err_pg:
                st.error(f"Error al consultar PostgreSQL: {err_pg}")
            else:
                st.dataframe(df_pg)

    elif menu_opcion == "Estado del Sistema":
        st.title("📊 Estado de Conexiones")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("MySQL (miaamx_telemetria2)")
            df_test_my, err_my = consultar_mysql("SELECT VERSION() as version_mysql")
            if err_my:
                st.error(f"Estado: Desconectado ({err_my})")
            else:
                st.success("Estado: Conectado OK")
                st.write(df_test_my)
                
        with col_c2:
            st.subheader("PostgreSQL (qgis)")
            df_test_pg, err_pg = consultar_postgres("SELECT version()")
            if err_pg:
                st.error(f"Estado: Desconectado ({err_pg})")
            else:
                st.success("Estado: Conectado OK")
                st.write("Versión de Postgres obtenida correctamente.")
