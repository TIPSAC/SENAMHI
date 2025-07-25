import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io
from datetime import datetime

# Configuración visual general
st.set_page_config(page_title="CONVERSOR A MED/H", layout="wide")

st.markdown("""
    <style>
    body { background-color: black; color: white; }
    .stApp { background-color: black; }
    h1 {
        color: black;
        background-color: orange;
        padding: 10px;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>CONVERSOR A MED/H</h1>", unsafe_allow_html=True)

# Instrucción de carga
st.markdown("Sube un archivo Excel que contenga una columna con la fecha y otra con datos de **UV eritémica ponderada (W/m²)**.")

# Carga de archivo
uploaded_file = st.file_uploader("Subir archivo Excel", type=["xlsx"])

# Diccionario de MED por tipo de piel
piel_med = {
    "Tipo I (muy clara)": 200,
    "Tipo II (clara)": 250,
    "Tipo III (intermedia)": 300,
    "Tipo IV (morena)": 450,
    "Tipo V (oscura)": 600,
    "Tipo VI (muy oscura)": 1000,
}

# Selección de tipo de piel
tipo_piel = st.selectbox("Selecciona tu tipo de piel:", list(piel_med.keys()))
valor_med = piel_med[tipo_piel]

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # Detectar columnas automáticamente
        columnas = df.columns.str.lower()
        fecha_col = [col for col in columnas if "fecha" in col or "time" in col]
        uv_col = [col for col in columnas if "uv" in col]

        if fecha_col and uv_col:
            df['fecha'] = pd.to_datetime(df[fecha_col[0]])
            df['uv'] = df[uv_col[0]]
        else:
            st.error("No se encontraron columnas adecuadas para fecha y UV.")
            st.stop()

        # Ordenar por fecha
        df = df.sort_values("fecha")

        # Calcular diferencia de tiempo entre filas
        df['delta_s'] = df['fecha'].diff().dt.total_seconds()
        df['delta_s'].fillna(method='bfill', inplace=True)

        # Calcular MED correspondiente: MED = UV_erythemal * Δt / MED_skin
        df['med_h'] = df['uv'] * df['delta_s'] / valor_med

        # Selector de rango de fecha opcional
        fecha_min = df['fecha'].min()
        fecha_max = df['fecha'].max()
        fecha_ini, fecha_fin = st.date_input("Selecciona el rango de fechas:", [fecha_min, fecha_max])

        mask = (df['fecha'] >= pd.to_datetime(fecha_ini)) & (df['fecha'] <= pd.to_datetime(fecha_fin))
        df_filtrado = df.loc[mask]

        if df_filtrado.empty:
            st.warning("No hay datos en el rango seleccionado.")
            st.stop()

        # Gráfico
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_filtrado['fecha'], df_filtrado['med_h'], color='orange', linewidth=1)
        ax.set_facecolor("black")
        fig.patch.set_facecolor("black")
        ax.set_title("Conversión de UV a MED/h", color='white')
        ax.set_xlabel("Fecha y hora", color='white')
        ax.set_ylabel("MED (cada intervalo)", color='white')
        ax.tick_params(colors='white')
        ax.grid(True, linestyle="--", alpha=0.3)
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()
        st.pyplot(fig)

        # Exportar Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="MED_Resultados")
        st.download_button("📥 Descargar resultados en Excel", buffer.getvalue(), file_name="med_resultados.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")

