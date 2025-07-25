import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, time
import io

# Estilo de página
st.set_page_config(page_title="Conversor a MED/H", layout="centered")

# Fondo oscuro con detalles rojos/naranjas
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

# Subida de archivo
uploaded_file = st.file_uploader("📤 Suba su archivo CSV con columnas 'Date', 'Time' y UV", type=["csv"])

if uploaded_file:
    # Leer desde fila 8 (skiprows=7)
    df = pd.read_csv(uploaded_file, skiprows=7)

    # Verificar que existan las columnas necesarias
    if "Date" not in df.columns or "Time" not in df.columns:
        st.error("⚠️ El archivo debe contener columnas llamadas 'Date' y 'Time'.")
        st.stop()

    # Combinar columnas Date y Time en una sola de tipo datetime
    df["fecha"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    df = df.dropna(subset=["fecha"])

    # Selección manual de la columna de UV
    st.subheader("🧩 Selección de columna UV")
    col_uv = st.selectbox("Selecciona la columna de UV ERITÉMICO (W/m²)", df.columns)
    df = df.dropna(subset=[col_uv])
    df = df.rename(columns={col_uv: "uv"})

    if not pd.api.types.is_numeric_dtype(df["uv"]):
        st.error("⚠️ La columna seleccionada como UV ERITÉMICO no contiene valores numéricos.")
        st.stop()

    df["fecha"] = df["fecha"].dt.tz_localize(None)

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

    # Cálculo de MED/h
    df["MED/h"] = df["uv"] * 3600 / med_por_joule

    # Rango de fechas
    usar_rango = st.radio("¿Deseas ingresar un rango de fechas?", ("No", "Sí"))

    if usar_rango == "Sí":
        fecha_min = df['fecha'].min()
        fecha_max = df['fecha'].max()

        st.markdown("### Selecciona el rango de fechas")
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

    # Mostrar gráfico
    st.subheader("📈 Evolución temporal de MED/h")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['fecha'], df['MED/h'], color='orange', linewidth=2)
    ax.set_title("Conversión de UV a MED/h", fontsize=14, color='white')
    ax.set_xlabel("Fecha y hora", color='white')
    ax.set_ylabel("MED/h", color='white')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.tick_params(colors='white')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
    fig.autofmt_xdate()

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    st.pyplot(fig)

    # Descargar Excel con resultados
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

    # Mostrar info del rango
    if usar_rango == "Sí":
        st.info(f"Mostrando datos desde **{fecha_inicio.strftime('%d/%m/%Y %H:%M')}** hasta **{fecha_fin.strftime('%d/%m/%Y %H:%M')}**")
    else:
        st.info(f"Mostrando **todos los datos** del archivo.")

