import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import io

st.set_page_config(page_title="Conversor a MED/H", layout="centered")

st.title("☀️ Conversor UV a MED/h")

uploaded_file = st.file_uploader("📤 Carga tu archivo CSV", type=["csv"])
if uploaded_file is not None:
    try:
        # Leer CSV omitiendo primeras 7 filas
        df = pd.read_csv(uploaded_file, skiprows=7)

        st.success("✅ Archivo cargado correctamente.")

        # Mostrar columnas para seleccionar UV
        col_uv = st.selectbox("🌞 Selecciona la columna de UV (W/m²)", df.columns)

        # Reemplazar coma decimal si fuera necesario
        df[col_uv] = df[col_uv].astype(str).str.replace(",", ".").astype(float)

        # Crear columna 'fecha' combinando Date y Time
        if 'Time' not in df.columns or 'Date' not in df.columns:
            st.error("❌ Las columnas 'Date' y 'Time' son obligatorias.")
            st.stop()

        df["fecha_str"] = df["Date"].astype(str).str.strip() + " " + df["Time"].astype(str).str.strip()

        # Parsear fecha con soporte para formato como "25/07/2025 00:36.3"
        def parse_datetime_safe(dt_str):
            try:
                return pd.to_datetime(dt_str, format="%d/%m/%Y %H:%M:%S", errors='coerce')
            except:
                try:
                    return pd.to_datetime(dt_str, format="%d/%m/%Y %H:%M.%S", errors='coerce')
                except:
                    return pd.NaT

        df["fecha"] = df["fecha_str"].apply(parse_datetime_safe)
        filas_antes = len(df)
        df = df.dropna(subset=["fecha"])
        descartadas = filas_antes - len(df)
        if descartadas > 0:
            st.warning(f"⚠️ {descartadas} filas tenían formato inválido en 'Date' o 'Time' y fueron descartadas.")

        # Calcular MED/h
        MED_J_m2 = 210  # Valor estándar para piel tipo II
        df["MED_h"] = df[col_uv] * 3600 / MED_J_m2

        # Filtros de fecha
        fecha_min = df["fecha"].min()
        fecha_max = df["fecha"].max()

        st.markdown("### 📅 Filtra por rango de fechas")
        fecha_inicio = st.date_input("Fecha de inicio", value=fecha_min.date(), min_value=fecha_min.date(), max_value=fecha_max.date())
        fecha_fin = st.date_input("Fecha de fin", value=fecha_max.date(), min_value=fecha_min.date(), max_value=fecha_max.date())

        df_filtrado = df[(df["fecha"].dt.date >= fecha_inicio) & (df["fecha"].dt.date <= fecha_fin)]

        # Mostrar gráfica
        st.markdown("### 📈 Gráfico de MED/h")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(df_filtrado["fecha"], df_filtrado["MED_h"], color="orange")
        ax.set_xlabel("Fecha y hora")
        ax.set_ylabel("MED/h")
        ax.set_title("Radiación UV en MED/h")
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

        # Descargar resultados
        st.markdown("### 💾 Descargar resultados")
        output = io.BytesIO()
        df_out = df_filtrado[["fecha", col_uv, "MED_h"]]
        df_out.columns = ["Fecha", "UV (W/m²)", "MED/h"]
        df_out.to_csv(output, index=False)
        st.download_button(label="⬇️ Descargar CSV", data=output.getvalue(), file_name="resultados_MED_h.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
