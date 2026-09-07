import datetime
import calendar
import streamlit as st
import streamlit.components.v1 as components

# Configuración básica de la página
st.set_page_config(
    page_title="Calendario Avanzado MIAA",
    page_icon="📅",
    layout="centered"
)

st.title("📅 Selector de Fecha Avanzado")
st.write("Solución para cambiar de año y mes directamente sin dar clics infinitos en las flechas.")

st.divider()

# ==========================================
# OPCIÓN 1: SELECTOR DIRECTO CON DROPDOWNS
# ==========================================
st.subheader("Opción 1: Selector por Desplegables Directos")

# 1. Inicializar la fecha en Session State si no existe
if "fecha_seleccionada" not in st.session_state:
    st.session_state.fecha_seleccionada = datetime.date.today()

fecha_actual = st.session_state.fecha_seleccionada

# 2. Definir rangos y nombres
anios_disponibles = list(range(1970, 2051))
nombres_meses = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

# 3. Crear columnas para los selectores
col_anio, col_mes, col_dia = st.columns([1, 1, 1])

with col_anio:
    indice_anio = anios_disponibles.index(fecha_actual.year) if fecha_actual.year in anios_disponibles else 0
    anio_elegido = st.selectbox(
        "Año",
        options=anios_disponibles,
        index=indice_anio,
        key="selector_anio"
    )

with col_mes:
    mes_elegido_num = st.selectbox(
        "Mes",
        options=list(range(1, 13)),
        format_func=lambda m: nombres_meses[m - 1],
        index=fecha_actual.month - 1,
        key="selector_mes"
    )

# Validar días máximos según año y mes (ej. febrero o meses de 30 días)
max_dias_mes = calendar.monthrange(anio_elegido, mes_elegido_num)[1]
dias_disponibles = list(range(1, max_dias_mes + 1))
dia_seguro = min(fecha_actual.day, max_dias_mes)

with col_dia:
    dia_elegido = st.selectbox(
        "Día",
        options=dias_disponibles,
        index=dias_disponibles.index(dia_seguro),
        key="selector_dia"
    )

# 4. Guardar fecha final armada
fecha_final_op1 = datetime.date(anio_elegido, mes_elegido_num, dia_elegido)
st.session_state.fecha_seleccionada = fecha_final_op1

st.success(f"Fecha seleccionada (Opción 1): **{fecha_final_op1.strftime('%Y-%m-%d')}**")

st.divider()

# ==========================================
# OPCIÓN 2: CALENDARIO FLATPICKR (POP-UP)
# ==========================================
st.subheader("Opción 2: Calendario Pop-Up con Dropdowns de Año y Mes")
st.write("Haz clic en el cuadro de texto para abrir el calendario. Puedes hacer clic sobre el mes o año para seleccionarlos de una lista.")

# HTML/JS con librería Flatpickr y tema oscuro
flatpickr_code = f"""
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/themes/dark.css">
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://npmcdn.com/flatpickr/dist/l10n/es.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: transparent;
            margin: 0;
            padding: 5px;
        }}
        .flatpickr-input {{
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #4e4e4e;
            background-color: #262730;
            color: #ffffff;
            font-size: 16px;
            outline: none;
            box-sizing: border-box;
        }}
        .flatpickr-input:focus {{
            border-color: #ff4b4b;
        }}
    </style>
</head>
<body>
    <input type="text" id="flatpickr-date" placeholder="Selecciona una fecha...">

    <script>
        flatpickr("#flatpickr-date", {{
            locale: "es",
            dateFormat: "Y-m-d",
            defaultDate: "{fecha_final_op1.strftime('%Y-%m-%d')}",
            monthSelectorType: "dropdown",
            yearDropdown: true,
            animate: true,
            onChange: function(selectedDates, dateStr, instance) {{
                // Envía el valor seleccionado a la consola o contenedor
                console.log("Fecha seleccionada:", dateStr);
            }}
        }});
    </script>
</body>
</html>
"""

components.html(flatpickr_code, height=380)
