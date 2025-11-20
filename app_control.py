import re
import io

import pandas as pd
import streamlit as st
import pdfplumber


# ----------------------------
# Función para extraer SKU y Cantidad desde el PDF
# ----------------------------
def extraer_sku_cantidades(pdf_file) -> pd.DataFrame:
    texto_completo = ""

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto_completo += (page.extract_text() or "") + "\n"

    patron = r"SKU:\s*(\d+)[^\n]*\nCantidad:\s*(\d+)"

    resultados = re.findall(patron, texto_completo)

    filas = []
    for sku, cantidad in resultados:
        filas.append({
            "sku": sku.strip(),
            "cantidad": int(cantidad.strip())
        })

    return pd.DataFrame(filas)


# ----------------------------
# Función para cargar la base de productos
# ----------------------------
def cargar_base_datos(archivo):
    nombre = archivo.name.lower()

    if nombre.endswith(".csv"):
        df = pd.read_csv(archivo, dtype={"sku": str})
    else:
        df = pd.read_excel(archivo, dtype={"sku": str})

    df.columns = [c.lower().strip() for c in df.columns]

    necesarias = {"sku", "descripcion", "area"}
    if not necesarias.issubset(df.columns):
        raise ValueError("La base debe tener columnas: sku, descripcion, area")

    df["sku"] = df["sku"].astype(str)

    return df


# ----------------------------
# INTERFAZ STREAMLIT
# ----------------------------
def main():

    st.title("📦 Control de Productos desde PDF (Ferretería Aurora)")

    st.write("""
    Sube un archivo PDF de Mercado Libre + una base de productos (CSV o Excel)
    y la app generará una tabla con:

    **Cantidad | SKU | Descripción | Área**, ordenada por SKU.
    """)

    pdf_file = st.file_uploader("Sube el PDF", type=["pdf"])
    base_file = st.file_uploader("Sube la base de datos", type=["csv", "xlsx", "xls"])

    if pdf_file and base_file:
        if st.button("Procesar Archivos"):
            try:
                st.write("🔍 Extrayendo datos del PDF...")
                df_pdf = extraer_sku_cantidades(pdf_file)

                st.write("📂 Cargando base de productos...")
                df_base = cargar_base_datos(base_file)

                st.write("🔗 Cruzando información...")
                df_final = df_pdf.merge(df_base, on="sku", how="left")

                df_final = df_final[["cantidad", "sku", "descripcion", "area"]]
                df_final = df_final.sort_values("sku")

                st.success("Tabla generada correctamente")
                st.dataframe(df_final)

                # Exportar CSV
                csv_buffer = io.StringIO()
                df_final.to_csv(csv_buffer, index=False, encoding="utf-8-sig")

                st.download_button(
                    "⬇️ Descargar como CSV",
                    csv_buffer.getvalue(),
                    "resultado_control.csv",
                    "text/csv"
                )

            except Exception as e:
                st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
