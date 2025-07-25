import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import io

# Configuración de página
st.set_page_config(page_title="Conversor a MED/H", layout="centered")

# Estilo visual
st.markdown("""
    <style>
    body {
        background-color: #fff4f0;
    }
    .stApp {
        background-color: #fff4f0;
    }
    h1, h2, h3, h4, h5 {
        color: black !important;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #e64a19;
        color: white;
        font-weight: bold;
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
