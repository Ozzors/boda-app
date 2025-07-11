import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import requests
from github import Github

# URLs para leer desde GitHub
URL_INVITADOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/invitados.csv"
URL_PREPARATIVOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/preparativos.csv"

# Función para cargar CSV desde URL
@st.cache_data(ttl=3600)
def cargar_csv(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return pd.read_csv(BytesIO(resp.content))
    except Exception as e:
        st.error(f"No se pudo cargar el archivo desde {url}.\nError: {e}")
        return pd.DataFrame()

# Inicializar dataframes en session_state
def inicializar_dfs():
    if "df_invitados" not in st.session_state:
        df_invitados = cargar_csv(URL_INVITADOS)
        if df_invitados.empty:
            df_invitados = pd.DataFrame(columns=["Nombre", "Acompañantes", "Relación", "Comentarios", "Confirmación"])
        st.session_state.df_invitados = df_invitados

    if "df_preparativos" not in st.session_state:
        df_preparativos = cargar_csv(URL_PREPARATIVOS)
        if df_preparativos.empty:
            df_preparativos = pd.DataFrame(columns=["Tarea", "Costo", "Estado", "Notas"])
        st.session_state.df_preparativos = df_preparativos

inicializar_dfs()

# Función para exportar a Excel
def to_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# Función para guardar en GitHub
def guardar_en_github(nombre_archivo, contenido_csv, mensaje_commit):
    try:
        token = st.secrets["GITHUB_TOKEN"]
    except KeyError:
        st.warning("No está configurado el token de GitHub en st.secrets. No se guardarán los cambios automáticamente.")
        return False

    repo_name = "Ozzors/boda-app"
    g = Github(token)
    repo = g.get_repo(repo_name)

    try:
        archivo = repo.get_contents(nombre_archivo)
        repo.update_file(archivo.path, mensaje_commit, contenido_csv, archivo.sha)
    except Exception:
        repo.create_file(nombre_archivo, mensaje_commit, contenido_csv)
    return True

# Función para recargar desde GitHub y actualizar session_state
def recargar_desde_github():
    df_inv = cargar_csv(URL_INVITADOS)
    df_prep = cargar_csv(URL_PREPARATIVOS)
    if not df_inv.empty:
        st.session_state.df_invitados = df_inv
    if not df_prep.empty:
        st.session_state.df_preparativos = df_prep

# --- App ---

st.title("Planificador de Boda")

# Botones globales para guardar y actualizar
col1, col2 = st.columns(2)
with col1:
    if st.button("💾 Guardar cambios en GitHub", key="guardar_todo"):
        ok_inv = guardar_en_github("invitados.csv", st.session_state.df_invitados.to_csv(index=False), "Guardado manual desde app")
        ok_prep = guardar_en_github("preparativos.csv", st.session_state.df_preparativos.to_csv(index=False), "Guardado manual desde app")
        if ok_inv and ok_prep:
            st.success("Cambios guardados correctamente en GitHub.")
        else:
            st.error("Error al guardar en GitHub.")
with col2:
    if st.button("🔄 Actualizar datos desde GitHub", key="actualizar_todo"):
        recargar_desde_github()
        st.session_state["recargar"] = True

fecha_boda = datetime(2025, 8, 9, 15, 0, 0)
ahora = datetime.now()
diferencia = fecha_boda - ahora
dias = diferencia.days
horas = diferencia.seconds // 3600
st.markdown(f"### Faltan {dias} días y {horas} horas para la boda 🎉")

tab1, tab2, tab3, tab4 = st.tabs(["Invitados", "Preparativos", "Presupuesto", "Exportar"])

with tab1:
    st.header("Invitados")
    with st.expander("Agregar nuevo invitado"):
        nombre_nuevo = st.text_input("Nombre", key="nombre_nuevo")
        acompañantes_nuevo = st.number_input("Acompañantes (0 si va solo)", min_value=0, step=1, key="acompañantes_nuevo")
        relacion_nuevo = st.text_input("Relación", key="relacion_nuevo")
        comentarios_nuevo = st.text_area("Comentarios", key="comentarios_nuevo")
        confirmacion_nuevo = st.selectbox("Confirmación", ["Sí", "No", "Por definir"], key="confirmacion_nuevo")

        if st.button("Agregar invitado", key="btn_agregar_inv"):
            nuevo = {
                "Nombre": nombre_nuevo,
                "Acompañantes": acompañantes_nuevo,
                "Relación": relacion_nuevo,
                "Comentarios": comentarios_nuevo,
                "Confirmación": confirmacion_nuevo
            }
            st.session_state.df_invitados = pd.concat([st.session_state.df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
            st.success(f"Invitado {nombre_nuevo} agregado.")
            st.session_state["recargar"] = True

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

            opciones_confirmacion = ["Sí", "No", "Por definir"]
            try:
                idx_confirmacion = opciones_confirmacion.index(invitado["Confirmación"])
            except ValueError:
                idx_confirmacion = 0  # Valor por defecto si no encuentra

            confirmacion_edit = st.selectbox(
                "Confirmación",
                options=opciones_confirmacion,
                index=idx_confirmacion,
                key="confirmacion_edit"
            )

            if st.button("Guardar cambios", key="guardar_inv"):
                st.session_state.df_invitados.loc[idx] = [nombre_edit, acompañantes_edit, relacion_edit, comentarios_edit, confirmacion_edit]
                st.success("Invitado actualizado.")
                st.session_state["recargar"] = True

        st.subheader("Lista completa de invitados")
        st.dataframe(st.session_state.df_invitados)

        # Opción para borrar invitados
        invitados_para_borrar = st.multiselect(
            "Selecciona invitados para borrar",
            options=st.session_state.df_invitados["Nombre"].tolist(),
            key="invitados_para_borrar"
        )
        if st.button("Borrar seleccionado(s)", key="borrar_invitados_btn"):
            if invitados_para_borrar:
                st.session_state.df_invitados = st.session_state.df_invitados[~st.session_state.df_invitados["Nombre"].isin(invitados_para_borrar)].reset_index(drop=True)
                st.success(f"Invitado(s) {', '.join(invitados_para_borrar)} borrado(s).")
                st.session_state["recargar"] = True
            else:
                st.warning("No seleccionaste ningún invitado para borrar.")
    else:
        st.info("No hay invitados registrados aún.")

    confirmados = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"]
    num_confirmados = confirmados["Acompañantes"].sum() + len(confirmados)
    por_definir = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Por definir"].shape[0]
    st.markdown(f"**Confirmados (incluyendo acompañantes):** {num_confirmados}")
    st.markdown(f"**Por definir:** {por_definir}")

with tab2:
    st.header("Preparativos")
    with st.expander("Agregar nueva tarea"):
        tarea_nueva = st.text_input("Tarea", key="tarea_nueva")
        costo_nuevo = st.number_input("Costo (CAD)", min_value=0.0, step=0.01, format="%.2f", key="costo_nuevo")
        estado_nuevo = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"], key="estado_nuevo")
        notas_nuevo = st.text_area("Notas", key="notas_nuevo")

        if st.button("Agregar tarea", key="btn_agregar_prep"):
            nueva_tarea = {
                "Tarea": tarea_nueva,
                "Costo": costo_nuevo,
                "Estado": estado_nuevo,
                "Notas": notas_nuevo
            }
            st.session_state.df_preparativos = pd.concat([st.session_state.df_preparativos, pd.DataFrame([nueva_tarea])], ignore_index=True)
            st.success(f"Tarea '{tarea_nueva}' agregada.")
            st.session_state["recargar"] = True

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
                st.session_state["recargar"] = True

        def color_estado(val):
            if val == "En progreso":
                color = "yellow"
            elif val == "Completado":
                color = "lightgreen"
            else:
                color = ""
            return f"background-color: {color}"

        st.subheader("Lista completa de preparativos")
        st.dataframe(st.session_state.df_preparativos.style.applymap(color_estado, subset=["Estado"]))

        # Opción para borrar tareas
        tareas_para_borrar = st.multiselect(
            "Selecciona tareas para borrar",
            options=st.session_state.df_preparativos["Tarea"].tolist(),
            key="tareas_para_borrar"
        )
        if st.button("Borrar seleccionado(s)", key="borrar_preparativos_btn"):
            if tareas_para_borrar:
                st.session_state.df_preparativos = st.session_state.df_preparativos[~st.session_state.df_preparativos["Tarea"].isin(tareas_para_borrar)].reset_index(drop=True)
                st.success(f"Tarea(s) {', '.join(tareas_para_borrar)} borrada(s).")
                st.session_state["recargar"] = True
            else:
                st.warning("No seleccionaste ninguna tarea para borrar.")
    else:
        st.info("No hay tareas registradas aún.")

with tab3:
    st.header("Presupuesto")
    if not st.session_state.df_preparativos.empty:
        total = st.session_state.df_preparativos["Costo"].sum()
        st.metric("Costo total estimado (CAD)", f"${total:,.2f}")
    else:
        st.info("No hay costos registrados aún.")

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

# Controlar rerun solo cuando la variable recargar esté en True
if st.session_state.get("recargar", False):
    st.session_state["recargar"] = False
    st.experimental_rerun()
