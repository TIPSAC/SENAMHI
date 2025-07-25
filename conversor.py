import streamlit as st
import pandas as pd

st.set_page_config(page_title="Conversor W/m² a MED/h", layout="centered")

st.title("☀️ Conversor a MED/h")
st.markdown("Sube un archivo.")

archivo = st.file_uploader("📁 Sube tu archivo CSV", type=["csv"])

if archivo:
    try:
        # Leer CSV desde la fila 8 (omitimos 7 primeras)
        df = pd.read_csv(archivo, skiprows=7)

        # Buscar columna que contenga "Irradiance"
        col_irr = next((col for col in df.columns if "irradiance" in col.lower()), None)

        if not col_irr:
            st.error("❌ No se encontró una columna de irradiancia.")
        else:
            st.success(f"✅ Columna de irradiancia detectada: {col_irr}")

            # Convertimos de W/m² a MED/h
            df["MED/h"] = df[col_irr] / 0.0583

            # Mostrar preview
            st.subheader("📄 Vista previa:")
            st.dataframe(df.head())

            # Descargar Excel
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="MED_h")  # evitar caracteres inválidos
                writer.close()
            st.download_button(
                label="⬇️ Descargar archivo con MED/h",
                data=output.getvalue(),
                file_name="resultado_MED_h.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo: {e}")

