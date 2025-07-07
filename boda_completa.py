import streamlit as st
import pandas as pd
import datetime
import base64
from io import BytesIO

# --- Datos iniciales (puedes reemplazar con carga desde GitHub o Google Sheets) ---

# Inicializar sesión para invitados
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = pd.DataFrame(columns=["Nombre", "Acompañantes", "Relación", "Comentarios", "Confirmación"])

# Inicializar sesión para preparativos
if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = pd.DataFrame(columns=["Tarea", "Costo", "Estado", "Notas"])

# Función para convertir dataframes a Excel para descargar
def to_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# Fecha de la boda
fecha_boda = datetime.datetime(2025, 8, 9, 0, 0, 0)

# --- Contador de días y horas ---
ahora = datetime.datetime.now()
diferencia = fecha_boda - ahora
dias_faltan = diferencia.days
horas_faltan = diferencia.seconds // 3600

st.title("App de Planificación de Boda")
st.markdown(f"### Faltan {dias_faltan} días y {horas_faltan} horas para la boda 🎉")

# --- Tabs principales ---
tabs = st.tabs(["Invitados", "Preparativos", "Presupuesto", "Exportar"])

# --- TAB INVITADOS ---
with tabs[0]:
    st.header("Invitados")
    
    # Contadores
    df_inv = st.session_state.df_invitados
    confirmados = df_inv[df_inv["Confirmación"] == "Sí"]["Acompañantes"].sum() + df_inv[df_inv["Confirmación"] == "Sí"].shape[0]
    por_definir = df_inv[df_inv["Confirmación"] == "Por definir"].shape[0]
    st.write(f"Confirmados (incluyendo acompañantes): {confirmados}")
    st.write(f"Por definir: {por_definir}")

    st.subheader("Agregar nuevo invitado")
    nombre_nuevo = st.text_input("Nombre del invitado", key="nuevo_nombre")
    acompanantes_nuevo = st.number_input("Número de acompañantes", min_value=0, max_value=20, step=1, key="nuevo_acompanantes")
    relacion_nuevo = st.text_input("Relación", key="nuevo_relacion")
    comentarios_nuevo = st.text_area("Comentarios", key="nuevo_comentarios")
    confirmacion_nuevo = st.selectbox("Confirmación", ["Sí", "No", "Por definir"], key="nuevo_confirmacion")

    if st.button("Agregar invitado"):
        nuevo = {
            "Nombre": nombre_nuevo,
            "Acompañantes": acompanantes_nuevo,
            "Relación": relacion_nuevo,
            "Comentarios": comentarios_nuevo,
            "Confirmación": confirmacion_nuevo
        }
        st.session_state.df_invitados = pd.concat([st.session_state.df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
        st.experimental_rerun()

    st.subheader("Editar invitados existentes")
    for i, invitado in st.session_state.df_invitados.iterrows():
        with st.expander(f"{invitado['Nombre']}"):
            nombre_edit = st.text_input("Nombre", value=invitado["Nombre"], key=f"nombre_{i}")
            acompanantes_edit = st.number_input("Acompañantes", min_value=0, max_value=20, step=1, value=invitado["Acompañantes"], key=f"acompanantes_{i}")
            relacion_edit = st.text_input("Relación", value=invitado["Relación"], key=f"relacion_{i}")
            comentarios_edit = st.text_area("Comentarios", value=invitado["Comentarios"], key=f"comentarios_{i}")
            confirmacion_edit = st.selectbox(
                "Confirmación",
                options=["Sí", "No", "Por definir"],
                index=["Sí", "No", "Por definir"].index(invitado["Confirmación"]) if invitado["Confirmación"] in ["Sí", "No", "Por definir"] else 2,
                key=f"confirmacion_{i}"
            )
            if st.button(f"Guardar cambios {invitado['Nombre']}", key=f"guardar_invitado_{i}"):
                st.session_state.df_invitados.at[i, "Nombre"] = nombre_edit
                st.session_state.df_invitados.at[i, "Acompañantes"] = acompanantes_edit
                st.session_state.df_invitados.at[i, "Relación"] = relacion_edit
                st.session_state.df_invitados.at[i, "Comentarios"] = comentarios_edit
                st.session_state.df_invitados.at[i, "Confirmación"] = confirmacion_edit
                st.experimental_rerun()

    st.subheader("Lista completa de invitados")
    st.dataframe(st.session_state.df_invitados)

# --- TAB PREPARATIVOS ---
with tabs[1]:
    st.header("Preparativos")
    estados_color = {
        "Pendiente": "⚪",  # Blanco
        "En progreso": "🟡",  # Amarillo
        "Completado": "🟢"  # Verde
    }

    st.subheader("Agregar nuevo preparativo")
    tarea_nueva = st.text_input("Tarea", key="nuevo_tarea")
    costo_nuevo = st.number_input("Costo", min_value=0, value=0, step=1, key="nuevo_costo")
    estado_nuevo = st.selectbox("Estado", options=list(estados_color.keys()), key="nuevo_estado")
    notas_nuevo = st.text_area("Notas", key="nuevo_notas")

    if st.button("Agregar preparativo"):
        nuevo_prep = {
            "Tarea": tarea_nueva,
            "Costo": costo_nuevo,
            "Estado": estado_nuevo,
            "Notas": notas_nuevo
        }
        st.session_state.df_preparativos = pd.concat([st.session_state.df_preparativos, pd.DataFrame([nuevo_prep])], ignore_index=True)
        st.experimental_rerun()

    st.subheader("Editar preparativos existentes")
    for i, prep in st.session_state.df_preparativos.iterrows():
        with st.expander(f"{prep['Tarea']}"):
            tarea_edit = st.text_input("Tarea", value=prep["Tarea"], key=f"tarea_{i}")
            costo_edit = st.number_input("Costo", min_value=0, value=prep["Costo"], step=1, key=f"costo_{i}")
            estado_edit = st.selectbox(
                "Estado",
                options=list(estados_color.keys()),
                index=list(estados_color.keys()).index(prep["Estado"]) if prep["Estado"] in estados_color else 0,
                key=f"estado_{i}"
            )
            notas_edit = st.text_area("Notas", value=prep["Notas"], key=f"notas_{i}")
            if st.button(f"Guardar cambios {prep['Tarea']}", key=f"guardar_prep_{i}"):
                st.session_state.df_preparativos.at[i, "Tarea"] = tarea_edit
                st.session_state.df_preparativos.at[i, "Costo"] = costo_edit
                st.session_state.df_preparativos.at[i, "Estado"] = estado_edit
                st.session_state.df_preparativos.at[i, "Notas"] = notas_edit
                st.experimental_rerun()

    st.subheader("Lista completa de preparativos")
    # Mostrar con iconos de estado
    df_mostrar = st.session_state.df_preparativos.copy()
    df_mostrar["Estado"] = df_mostrar["Estado"].map(estados_color).fillna("⚪")
    st.dataframe(df_mostrar)

# --- TAB PRESUPUESTO ---
with tabs[2]:
    st.header("Presupuesto")
    total_costo = st.session_state.df_preparativos["Costo"].sum()
    st.write(f"Costo total de preparativos: ${total_costo}")

# --- TAB EXPORTAR ---
with tabs[3]:
    st.header("Exportar datos")
    data_frames = {
        "Invitados": st.session_state.df_invitados,
        "Preparativos": st.session_state.df_preparativos
    }
    excel_data = to_excel(data_frames)

    st.download_button(
        label="📥 Descargar Excel con datos de boda",
        data=excel_data,
        file_name="datos_boda.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
