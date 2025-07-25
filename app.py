import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Configuración de página
st.set_page_config(page_title="Conversor a MED/H", layout="centered")

# Estilo visual: fondo negro, texto claro
st.markdown("""
    <style>
    body {
        background-color: #000000;
        color: white;
    }
    .stApp {
        background-color: #000000;
        color: white;
    }
    h1, h2, h3, h4, h5 {
        color: white !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #ff5722;
        color: white;
        font-weight: bold;
    }
    .stRadio > div {
        color: white !important;
    }
    .stSelectbox, .stDateInput, .stTimeInput {
        color: black !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("☀️ CONVERSOR A MED/H")

uploaded_file = st.file_uploader("📤 Suba su archivo Excel con datos de irradiancia UV (W/m²)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Detección de columnas
    posibles_col_uv = [col for col in df.columns if 'uv' in col.lower() or 'eri' in col.lower()]
    posibles_col_fecha = [col for col in df.columns if 'fecha' in col.lower() or 'date' in col.lower() or 'tiempo' in col.lower() or 'time' in col.lower()]

    if not posibles_col_uv:
        st.error("❌ No se encontró una columna de irradiancia UV.")
        st.stop()

    if not posibles_col_fecha:
        st.error("❌ No se encontró una columna de fecha.")
        st.stop()

    col_uv = st.selectbox("📡 Seleccione la columna de irradiancia UV (W/m²):", posibles_col_uv)
    col_fecha = st.selectbox("📅 Seleccione la columna de fecha:", posibles_col_fecha)

    # Conversión de fecha
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce', dayfirst=True)
    df = df.dropna(subset=[col_fecha, col_uv])
    df[col_fecha] = df[col_fecha].dt.tz_localize(None)

    # Rango de fechas
    usar_rango = st.radio("¿Deseas ingresar un rango de fechas?", ("No", "Sí"))

    if usar_rango == "Sí":
        fecha_min = df[col_fecha].min()
        fecha_max = df[col_fecha].max()

        st.markdown("### Selecciona el rango de fechas")
        fecha_inicio = st.date_input("📅 Fecha de inicio", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        hora_inicio = st.time_input("⏰ Hora de inicio", value=datetime.min.time())
        fecha_fin = st.date_input("📅 Fecha de fin", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        hora_fin = st.time_input("⏰ Hora de fin", value=datetime.max.time())

        inicio = datetime.combine(fecha_inicio, hora_inicio)
        fin = datetime.combine(fecha_fin, hora_fin)

        df = df[(df[col_fecha] >= inicio) & (df[col_fecha] <= fin)]

    if df.empty:
        st.warning("⚠️ No hay datos en el rango seleccionado.")
        st.stop()

    # Selección de tipo de piel
    tipos_piel = {
        "Tipo I (muy clara)": 200,
        "Tipo II (clara)": 250,
        "Tipo III (intermedia)": 300,
        "Tipo IV (morena clara)": 450,
        "Tipo V (morena oscura)": 600,
        "Tipo VI (negra)": 1000
    }

    tipo_elegido = st.selectbox("🧬 Seleccione su tipo de piel:", list(tipos_piel.keys()))
    valor_med_j_m2 = tipos_piel[tipo_elegido]

    # Cálculo de MED/h
    df["MED/h"] = (df[col_uv] * 3600) / valor_med_j_m2

    # Mostrar tabla
    st.subheader("📄 Resultados")
    st.dataframe(df[[col_fecha, col_uv, "MED/h"]].head(100))

    # Gráfico temporal
    st.subheader("📈 Gráfico de MED/h en el tiempo")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[col_fecha], df["MED/h"], color="#ff5722", linewidth=2)
    ax.set_xlabel("Fecha", color="white")
    ax.set_ylabel("MED/h", color="white")
    ax.set_title("MED/h vs Tiempo", fontsize=14, color="white")
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    fig.patch.set_facecolor('#000000')
    ax.set_facecolor('#000000')
    st.pyplot(fig)

    # Exportar a Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='MED_h')
        writer.save()
    buffer.seek(0)

    st.download_button(
        label="📥 Descargar Excel con MED/h",
        data=buffer,
        file_name="convertido_MED_h.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success(f"✅ Conversión realizada usando {tipo_elegido} (MED = {valor_med_j_m2} J/m²)")
