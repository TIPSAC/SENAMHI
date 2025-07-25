import streamlit as st
import pandas as pd
import io

# Configuración de página
st.set_page_config(page_title="Conversor MED/h por tipo de piel", layout="centered")

# Título
st.markdown("<h1 style='text-align: center; color: white;'>Conversor a MED/h</h1>", unsafe_allow_html=True)

# Subida del archivo
uploaded_file = st.file_uploader("📤 Suba su archivo CSV con irradiancia (W/m²)", type=["csv"])

if uploaded_file:
    try:
        # Leer el CSV, omitiendo las primeras 7 filas
        df = pd.read_csv(uploaded_file, skiprows=7)

        # Buscar automáticamente la columna de irradiancia
        columnas_posibles = [col for col in df.columns if "W" in col and "/" in col]
        if not columnas_posibles:
            st.error("No se encontró una columna con irradiancia en W/m².")
            st.stop()

        columna_uv = st.selectbox("Selecciona la columna de Irradiancia (W/m²)", columnas_posibles)
        df = df.rename(columns={columna_uv: "uv"})

        # Selección múltiple de tipos de piel
        st.subheader("👤 Seleccione uno o más tipos de piel")
        tipos_piel = {
            "Tipo I (muy clara)": 200,
            "Tipo II (clara)": 250,
            "Tipo III (media)": 300,
            "Tipo IV (oscura clara)": 450,
            "Tipo V (oscura)": 600,
            "Tipo VI (muy oscura)": 1000,
        }

        seleccionados = st.multiselect("Tipos de piel", list(tipos_piel.keys()))

        if seleccionados:
            for tipo in seleccionados:
                med_por_joule = tipos_piel[tipo]
                nombre_columna = f"MED/h - {tipo}"
                df[nombre_columna] = df["uv"] * 3600 / med_por_joule

            # Descargar resultados
            st.subheader("📥 Descargar archivo con resultados")
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="MED_h")

            buffer.seek(0)
            st.download_button(
                label="📄 Descargar Excel con MED/h",
                data=buffer,
                file_name="med_por_tipo_de_piel.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("Por favor, seleccione al menos un tipo de piel para continuar.")
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")


