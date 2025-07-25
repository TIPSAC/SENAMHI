import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, time
import io

st.set_page_config(page_title="Conversor a MED/H", layout="centered")

st.markdown("""
    <style>
        body {
            background-color: black;
            color: white;
        }
        .title {
            color: black;
            background-color: #FF4500;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            font-size: 2rem;
            font-weight: bold;
        }
        .stRadio > div {
            color: white !important;
        }
        .stButton button {
            background-color: #FF6347;
            color: white;
        }
        .stDownloadButton button {
            background-color: #FF6347;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">CONVERSOR A MED/H</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader("📤 Suba su archivo CSV con datos de UV Erítémico (W/m²)", type=["csv"])

if uploaded_file:
    # Leer el archivo ignorando las 7 primeras filas
    try:
        df = pd.read_csv(uploaded_file, skiprows=7)
    except Exception as e:
        st.error(f"❌ Error al leer el archivo CSV: {e}")
        st.stop()

    # Revisar que existan las columnas necesarias
    columnas_necesarias = ['Date', 'Time']
    if not all(col in df.columns for col in columnas_necesarias):
        st.error("❌ El archivo no contiene las columnas 'Date' y 'Time'")
        st.stop()

    # Combinar columnas de fecha y hora
    df["FechaHora"] = df["Date"].astype(str).str.strip() + " " + df["Time"].astype(str).str.strip()

    # Parseo robusto a datetime (considerando que Time es tipo MM.S)
    def parse_custom_datetime(row):
        try:
            time_float = float(row["Time"])
            minutes = int(time_float)
            seconds = int(round((time_float - minutes) * 60))
            return datetime.strptime(row["Date"], "%d/%m/%Y").replace(minute=minutes, second=seconds)
        except:
            return pd.NaT

    df["fecha"] = df.apply(parse_custom_datetime, axis=1)
    df = df.dropna(subset=["fecha"])

    # Selección de columna UV
    posibles_uv = [col for col in df.columns if "irradiance" in col.lower()]
    if not posibles_uv:
        st.error("❌ No se encontró una columna de irradiancia (UV)")
        st.stop()
    col_uv = posibles_uv[0]
    df = df.rename(columns={col_uv: "uv"})
    df['fecha'] = df['fecha'].dt.tz_localize(None)

    # Selección de tipo de piel
    st.subheader("👤 Seleccione su tipo de piel")
    tipos_piel = {
        "Tipo I (muy clara)": 200,
        "Tipo II (clara)": 250,
        "Tipo III (media)": 300,
        "Tipo IV (oscura clara)": 450,
        "Tipo V (oscura)": 600,
        "Tipo VI (muy oscura)": 1000,
    }
    tipo = st.selectbox("Tipo de piel", list(tipos_piel.keys()))
    med_por_joule = tipos_piel[tipo]

    # Cálculo
    df["MED/h"] = df["uv"] * 3600 / med_por_joule

    # Rango de fechas
    st.subheader("🗓️ Filtrar por rango de fechas")
    usar_rango = st.radio("¿Deseas ingresar un rango de fechas?", ("No", "Sí"))

    if usar_rango == "Sí":
        fecha_min = df['fecha'].min()
        fecha_max = df['fecha'].max()

        fecha_inicio_fecha = st.date_input("📅 Fecha de inicio", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_inicio_hora = st.time_input("⏰ Hora de inicio", value=fecha_min.time())
        fecha_fin_fecha = st.date_input("📅 Fecha de fin", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_fin_hora = st.time_input("⏰ Hora de fin", value=fecha_max.time())

        fecha_inicio = datetime.combine(fecha_inicio_fecha, fecha_inicio_hora)
        fecha_fin = datetime.combine(fecha_fin_fecha, fecha_fin_hora)

        df = df[(df['fecha'] >= fecha_inicio) & (df['fecha'] <= fecha_fin)]

    if df.empty:
        st.warning("⚠️ No hay datos en el rango seleccionado.")
        st.stop()

    # Gráfico
    st.subheader("📈 Evolución temporal de MED/h")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['fecha'], df['MED/h'], color='orange', linewidth=2)
    ax.set_title("Conversión de UV a MED/h", fontsize=14, color='white')
    ax.set_xlabel("Fecha y hora", color='white')
    ax.set_ylabel("MED/h", color='white')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(colors='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    st.pyplot(fig)

    # Descargar resultados
    st.subheader("📥 Descargar resultados")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='MED por hora')
    buffer.seek(0)
    st.download_button(
        label="Descargar archivo Excel con MED/h",
        data=buffer,
        file_name="med_por_hora.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Mensaje rango
    if usar_rango == "Sí":
        st.info(f"Mostrando datos desde **{fecha_inicio.strftime('%d/%m/%Y %H:%M')}** hasta **{fecha_fin.strftime('%d/%m/%Y %H:%M')}**")
    else:
        st.info(f"Mostrando **todos los datos** del archivo.")
