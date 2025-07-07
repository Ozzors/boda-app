import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import requests

# URLs crudas de GitHub para leer los CSV
URL_INVITADOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/invitados.csv"
URL_PREPARATIVOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/preparativos.csv"

# Función para cargar CSV desde URL
@st.cache_data(ttl=3600)
def cargar_csv(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        df = pd.read_csv(BytesIO(resp.content))
        return df
    except Exception as e:
        st.error(f"No se pudo cargar el archivo desde {url}.\nError: {e}")
        return pd.DataFrame()

# Inicializar dataframes en session_state si no existen (carga desde GitHub)
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = cargar_csv(URL_INVITADOS)
    # Si CSV vacío, inicializa con columnas
    if st.session_state.df_invitados.empty:
        st.session_state.df_invitados = pd.DataFrame(columns=["Nombre", "Acompañantes", "Relación", "Comentarios", "Confirmación"])

if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = cargar_csv(URL_PREPARATIVOS)
    if st.session_state.df_preparativos.empty:
        st.session_state.df_preparativos = pd.DataFrame(columns=["Tarea", "Costo", "Estado", "Notas"])

# --- Función para exportar a Excel ---
def to_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        writer.save()
    processed_data = output.getvalue()
    return processed_data

# --- Título ---
st.title("Planificador de Boda")

# --- Contador de días ---
fecha_boda = datetime(2025, 8, 9, 15, 0, 0)  # 9 de agosto 2025 a las 3pm
ahora = datetime.now()
diferencia = fecha_boda - ahora
dias = diferencia.days
horas = diferencia.seconds // 3600
st.markdown(f"### Faltan {dias} días y {horas} horas para la boda 🎉")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["Invitados", "Preparativos", "Presupuesto", "Exportar"])

# --- TAB 1: Invitados ---
with tab1:
    st.header("Invitados")

    # Agregar invitado nuevo
    with st.expander("Agregar nuevo invitado"):
        nombre_nuevo = st.text_input("Nombre")
        acompañantes_nuevo = st.number_input("Acompañantes (0 si va solo)", min_value=0, step=1)
        relacion_nuevo = st.text_input("Relación")
        comentarios_nuevo = st.text_area("Comentarios")
        confirmacion_nuevo = st.selectbox("Confirmación", ["Sí", "No", "Por definir"])

        if st.button("Agregar invitado"):
            nuevo = {
                "Nombre": nombre_nuevo,
                "Acompañantes": acompañantes_nuevo,
                "Relación": relacion_nuevo,
                "Comentarios": comentarios_nuevo,
                "Confirmación": confirmacion_nuevo
            }
            st.session_state.df_invitados = pd.concat([st.session_state.df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
            st.success(f"Invitado {nombre_nuevo} agregado.")
            st.experimental_rerun()

    # Editar invitado existente
    if not st.session_state.df_invitados.empty:
        st.subheader("Editar invitado existente")
        invitado_sel = st.selectbox("Selecciona un invitado para editar", st.session_state.df_invitados["Nombre"].tolist())

        if invitado_sel:
            idx = st.session_state.df_invitados[st.session_state.df_invitados["Nombre"] == invitado_sel].index[0]
            invitado = st.session_state.df_invitados.loc[idx]

            nombre_edit = st.text_input("Nombre", value=invitado["Nombre"], key="nombre_edit")
            acompañantes_edit = st.number_input("Acompañantes", min_value=0, step=1, value=int(invitado["Acompañantes"]), key="acompañantes_edit")
            relacion_edit = st.text_input("Relación", value=invitado["Relación"], key="relacion_edit")
            comentarios_edit = st.text_area("Comentarios", value=invitado["Comentarios"], key="comentarios_edit")
            confirmacion_edit = st.selectbox("Confirmación", options=["Sí", "No", "Por definir"], index=["Sí", "No", "Por definir"].index(invitado["Confirmación"]), key="confirmacion_edit")

            if st.button("Guardar cambios", key="guardar_inv"):
                st.session_state.df_invitados.loc[idx] = [nombre_edit, acompañantes_edit, relacion_edit, comentarios_edit, confirmacion_edit]
                st.success("Invitado actualizado.")
                st.experimental_rerun()

        # Mostrar tabla actual de invitados
        st.subheader("Lista completa de invitados")
        st.dataframe(st.session_state.df_invitados)

    else:
        st.info("No hay invitados registrados aún.")

    # Contador confirmados y por definir
    confirmados = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"]
    num_confirmados = confirmados["Acompañantes"].sum() + len(confirmados)
    por_definir = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Por definir"].shape[0]
    st.markdown(f"**Confirmados (incluyendo acompañantes):** {num_confirmados}")
    st.markdown(f"**Por definir:** {por_definir}")

# --- TAB 2: Preparativos ---
with tab2:
    st.header("Preparativos")

    # Agregar tarea nueva
    with st.expander("Agregar nueva tarea"):
        tarea_nueva = st.text_input("Tarea")
        costo_nuevo = st.number_input("Costo (CAD)", min_value=0.0, step=0.01, format="%.2f")
        estado_nuevo = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"])
        notas_nuevo = st.text_area("Notas")

        if st.button("Agregar tarea"):
            nueva_tarea = {
                "Tarea": tarea_nueva,
                "Costo": costo_nuevo,
                "Estado": estado_nuevo,
                "Notas": notas_nuevo
            }
            st.session_state.df_preparativos = pd.concat([st.session_state.df_preparativos, pd.DataFrame([nueva_tarea])], ignore_index=True)
            st.success(f"Tarea '{tarea_nueva}' agregada.")
            st.experimental_rerun()

    # Editar tarea existente
    if not st.session_state.df_preparativos.empty:
        st.subheader("Editar tarea existente")
        tarea_sel = st.selectbox("Selecciona una tarea para editar", st.session_state.df_preparativos["Tarea"].tolist())

        if tarea_sel:
            idx_p = st.session_state.df_preparativos[st.session_state.df_preparativos["Tarea"] == tarea_sel].index[0]
            tarea = st.session_state.df_preparativos.loc[idx_p]

            tarea_edit = st.text_input("Tarea", value=tarea["Tarea"], key="tarea_edit")
            costo_edit = st.number_input("Costo (CAD)", min_value=0.0, step=0.01, format="%.2f", value=float(tarea["Costo"]), key="costo_edit")
            estado_edit = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"], index=["Pendiente", "En progreso", "Completado"].index(tarea["Estado"]), key="estado_edit")
            notas_edit = st.text_area("Notas", value=tarea["Notas"], key="notas_edit")

            if st.button("Guardar cambios", key="guardar_prep"):
                st.session_state.df_preparativos.loc[idx_p] = [tarea_edit, costo_edit, estado_edit, notas_edit]
                st.success("Tarea actualizada.")
                st.experimental_rerun()

        # Mostrar tabla actual de preparativos con colores de estado
        st.subheader("Lista completa de preparativos")

        def color_estado(val):
            if val == "En progreso":
                color = "yellow"
            elif val == "Completado":
                color = "lightgreen"
            else:
                color = ""
            return f"background-color: {color}"

        st.dataframe(st.session_state.df_preparativos.style.applymap(color_estado, subset=["Estado"]))

    else:
        st.info("No hay tareas registradas aún.")

# --- TAB 3: Presupuesto ---
with tab3:
    st.header("Presupuesto")

    if not st.session_state.df_preparativos.empty:
        total = st.session_state.df_preparativos["Costo"].sum()
        st.metric("Costo total estimado (CAD)", f"${total:,.2f}")
    else:
        st.info("No hay costos registrados aún.")

# --- TAB 4: Exportar ---
with tab4:
    st.header("Exportar datos")

    data_frames = {
        "Invitados": st.session_state.df_invitados,
        "Preparativos": st.session_state.df_preparativos,
    }

    excel_data = to_excel(data_frames)

    st.download_button(
        label="📥 Descargar Excel con datos de boda",
        data=excel_data,
        file_name="boda_datos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# --- Función para guardar en GitHub (opcional, requiere token) ---
"""
import base64
from github import Github

def guardar_en_github(nombre_archivo, contenido_csv, mensaje_commit):
    # Esto solo funciona si configuras el token en st.secrets
    github_token = st.secrets["GITHUB_TOKEN"]
    repo_name = "Ozzors/boda-app"
    g = Github(github_token)
    repo = g.get_repo(repo_name)

    try:
        archivo = repo.get_contents(nombre_archivo)
        repo.update_file(archivo.path, mensaje_commit, contenido_csv, archivo.sha)
    except Exception:
        repo.create_file(nombre_archivo, mensaje_commit, contenido_csv)
"""

