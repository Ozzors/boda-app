import streamlit as st
import pandas as pd
from datetime import datetime

# Configurar la página
st.set_page_config(page_title="Planificador de Boda", layout="wide")

# Inicializar los DataFrames en la sesión si no existen
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = pd.DataFrame(columns=["Nombre", "Acompañantes", "Relación", "Comentarios", "Confirmado"])

if "df_preparativos" not in st.session_state:
    elementos = [
        "Bouquet de la novia", "Vestido de la novia", "Maquillaje y peinado", "Traje del novio",
        "Corbata", "Pin", "Medias", "Torta", "Fotógrafo", "Notario", "Anillos",
        "Pre-invitaciones", "Invitaciones con detalle", "Locación del evento", "Decoración",
        "Cuchillo de torta", "Bolígrafo para la firma", "Habitación de hotel"
    ]
    st.session_state.df_preparativos = pd.DataFrame({
        "Elemento": elementos,
        "Estado": ["Pendiente"] * len(elementos),
        "Costo ($)": [0] * len(elementos),
        "Notas": [""] * len(elementos)
    })

# Calcular contador regresivo
boda_fecha = datetime(2025, 8, 9, 15, 0, 0)  # 9 agosto 2025, 3:00 PM
ahora = datetime.now()
faltan = boda_fecha - ahora
dias = faltan.days
horas = faltan.seconds // 3600

# Mostrar título y contador
st.title("💒 Planificador de Boda")
st.subheader(f"⏳ Faltan **{dias} días y {horas} horas** para la boda")

# Crear pestañas
tab_invitados, tab_preparativos, tab_presupuesto, tab_exportar = st.tabs([
    "👥 Invitados", "📋 Preparativos", "💰 Presupuesto", "⬇️ Exportar"
])

# Sección: Invitados
with tab_invitados:
    st.header("👥 Lista de Invitados")

    with st.form("form_invitado"):
        col1, col2, col3 = st.columns(3)
        nombre = col1.text_input("Nombre del invitado")
        acompanantes = col2.number_input("Acompañantes", min_value=0, value=0)
        relacion = col3.text_input("Relación")

        comentarios = st.text_input("Comentarios")
        confirmado = st.checkbox("¿Confirmado?")
        submitted = st.form_submit_button("Agregar invitado")

        if submitted and nombre:
            nuevo = {
                "Nombre": nombre,
                "Acompañantes": acompanantes,
                "Relación": relacion,
                "Comentarios": comentarios,
                "Confirmado": confirmado
            }
            st.session_state.df_invitados = pd.concat([st.session_state.df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
            st.success("Invitado agregado correctamente ✅")

    # Mostrar tabla editable
    st.markdown("### Editar invitados")
    st.session_state.df_invitados = st.data_editor(
        st.session_state.df_invitados,
        num_rows="dynamic",
        use_container_width=True
    )

# Sección: Preparativos
with tab_preparativos:
    st.header("📋 Estado de Preparativos")

    estado_opciones = ["Pendiente", "En progreso", "Completo"]

    for i, row in st.session_state.df_preparativos.iterrows():
        with st.expander(f"📌 {row['Elemento']}"):
            col1, col2 = st.columns(2)
            estado = col1.selectbox("Estado", estado_opciones, index=estado_opciones.index(row["Estado"]), key=f"estado_{i}")
            costo = col2.number_input("Costo ($)", min_value=0, value=int(row["Costo ($)"]), key=f"costo_{i}")
            notas = st.text_area("Notas", value=row["Notas"], key=f"notas_{i}")

            st.session_state.df_preparativos.at[i, "Estado"] = estado
            st.session_state.df_preparativos.at[i, "Costo ($)"] = costo
            st.session_state.df_preparativos.at[i, "Notas"] = notas

# Sección: Presupuesto
with tab_presupuesto:
    st.header("💰 Presupuesto total")

    total = st.session_state.df_preparativos["Costo ($)"].sum()
    st.metric(label="Costo total estimado de la boda", value=f"${total:,.2f}")

    st.dataframe(
        st.session_state.df_preparativos[["Elemento", "Costo ($)", "Estado"]],
        use_container_width=True
    )

# Sección: Exportar
with tab_exportar:
    st.header("⬇️ Exportar datos (formato .CSV)")

    st.markdown("Puedes descargar por separado las tablas en archivos `.csv`:")

    # Invitados
    csv_invitados = st.session_state.df_invitados.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar invitados (.csv)",
        data=csv_invitados,
        file_name="invitados.csv",
        mime='text/csv'
    )

    # Preparativos
    csv_preparativos = st.session_state.df_preparativos.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar preparativos (.csv)",
        data=csv_preparativos,
        file_name="preparativos.csv",
        mime='text/csv'
    )
