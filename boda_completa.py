import streamlit as st
import pandas as pd
import numpy as np
import datetime
from io import BytesIO
import base64
import requests
from github import Github, InputGitAuthor

# URL archivos CSV en GitHub (tu repo privado)
URL_INVITADOS = "https://raw.githubusercontent.com/Ozzors/boda-app/main/invitados.csv"
URL_PREPARATIVOS = "https://raw.githubusercontent.com/Ozzors/boda-app/main/preparativos.csv"

# Fecha de boda
FECHA_BODA = datetime.datetime(2025, 8, 9, 15, 0, 0)

# Función para descargar CSV desde GitHub
@st.cache_data(ttl=3600)
def cargar_csv(url):
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        df = pd.DataFrame()
    return df

# Función para convertir dataframes a archivo Excel en memoria
def to_excel(dfs_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dfs_dict.items():
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    processed_data = output.getvalue()
    return processed_data

# Función para guardar archivos CSV en GitHub (requiere token con permisos)
def guardar_en_github(filename, content, commit_message):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        g = Github(token)
        repo = g.get_repo("Ozzors/boda-app")
        file_path = filename
        # Buscar archivo en repo
        try:
            contents = repo.get_contents(file_path)
            repo.update_file(contents.path, commit_message, content, contents.sha)
        except:
            repo.create_file(file_path, commit_message, content)
    except Exception as e:
        st.error(f"Error al guardar en GitHub: {e}")

# Inicializar session_state para invitados y preparativos
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = cargar_csv(URL_INVITADOS)
if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = cargar_csv(URL_PREPARATIVOS)

st.title("Planificador de Boda")

# Contador regresivo
ahora = datetime.datetime.now()
diferencia = FECHA_BODA - ahora
dias = diferencia.days
horas = diferencia.seconds // 3600
st.markdown(f"### ⏳ Faltan {dias} días y {horas} horas para la boda ({FECHA_BODA.strftime('%d %b %Y %H:%M')})")

# Pestañas
tabs = st.tabs(["Invitados", "Preparativos", "Presupuesto", "Exportar"])

# --- Invitados ---
with tabs[0]:
    st.header("Invitados")

    # Mostrar resumen contador invitados
    confirmados = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"]["Acompañantes"].sum() + st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"].shape[0]
    por_definir = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] != "Sí"]["Acompañantes"].sum() + st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] != "Sí"].shape[0]
    st.info(f"Invitados confirmados (incluyendo acompañantes): {confirmados}")
    st.info(f"Invitados por definir (incluyendo acompañantes): {por_definir}")

    # Agregar nuevo invitado
    with st.expander("Agregar nuevo invitado"):
        nuevo_nombre = st.text_input("Nombre")
        nuevos_acomp = st.number_input("Número de acompañantes", min_value=0, max_value=10, step=1)
        nueva_relacion = st.text_input("Relación")
        nuevo_comentario = st.text_area("Comentarios")
        nueva_confirmacion = st.selectbox("Confirmación", options=["Sí", "No", "Por definir"])

        if st.button("Agregar invitado"):
            if nuevo_nombre.strip() == "":
                st.warning("El nombre no puede estar vacío.")
            else:
                nuevo = {
                    "Nombre": nuevo_nombre.strip(),
                    "Acompañantes": nuevos_acomp,
                    "Relación": nueva_relacion.strip(),
                    "Comentarios": nuevo_comentario.strip(),
                    "Confirmación": nueva_confirmacion,
                }
                st.session_state.df_invitados = pd.concat([st.session_state.df_invitados, pd.DataFrame([nuevo])], ignore_index=True)

                # Guardar en GitHub
                csv_string = st.session_state.df_invitados.to_csv(index=False)
                guardar_en_github("invitados.csv", csv_string, "Agregado nuevo invitado desde app")
                st.experimental_rerun()

    # Editar invitado existente
    with st.expander("Editar invitado existente"):
        if st.session_state.df_invitados.empty:
            st.write("No hay invitados para editar.")
        else:
            indice_seleccionado = st.selectbox("Selecciona invitado a editar", st.session_state.df_invitados.index)
            invitado = st.session_state.df_invitados.loc[indice_seleccionado]

            nombre_edit = st.text_input("Nombre", value=invitado["Nombre"])
            acomp_edit = st.number_input("Número de acompañantes", min_value=0, max_value=10, step=1, value=int(invitado["Acompañantes"]))
            relacion_edit = st.text_input("Relación", value=invitado["Relación"])
            comentario_edit = st.text_area("Comentarios", value=invitado["Comentarios"])
            confirmacion_edit = st.selectbox("Confirmación", options=["Sí", "No", "Por definir"], index=["Sí", "No", "Por definir"].index(invitado["Confirmación"]))

            if st.button("Guardar cambios invitado"):
                st.session_state.df_invitados.loc[indice_seleccionado, "Nombre"] = nombre_edit.strip()
                st.session_state.df_invitados.loc[indice_seleccionado, "Acompañantes"] = acomp_edit
                st.session_state.df_invitados.loc[indice_seleccionado, "Relación"] = relacion_edit.strip()
                st.session_state.df_invitados.loc[indice_seleccionado, "Comentarios"] = comentario_edit.strip()
                st.session_state.df_invitados.loc[indice_seleccionado, "Confirmación"] = confirmacion_edit

                csv_string = st.session_state.df_invitados.to_csv(index=False)
                guardar_en_github("invitados.csv", csv_string, "Editado invitado desde app")
                st.experimental_rerun()

    st.subheader("Lista completa de invitados")
    st.dataframe(st.session_state.df_invitados)

# --- Preparativos ---
with tabs[1]:
    st.header("Preparativos")

    # Agregar nuevo preparativo
    with st.expander("Agregar nuevo preparativo"):
        nuevo_tarea = st.text_input("Tarea")
        nuevo_costo = st.number_input("Costo", min_value=0.0, step=0.01)
        nuevo_estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"])
        nueva_nota = st.text_area("Notas")

        if st.button("Agregar preparativo"):
            if nuevo_tarea.strip() == "":
                st.warning("La tarea no puede estar vacía.")
            else:
                nuevo_prep = {
                    "Tarea": nuevo_tarea.strip(),
                    "Costo": nuevo_costo,
                    "Estado": nuevo_estado,
                    "Notas": nueva_nota.strip(),
                }
                st.session_state.df_preparativos = pd.concat([st.session_state.df_preparativos, pd.DataFrame([nuevo_prep])], ignore_index=True)

                csv_string = st.session_state.df_preparativos.to_csv(index=False)
                guardar_en_github("preparativos.csv", csv_string, "Agregado nuevo preparativo desde app")
                st.experimental_rerun()

    # Editar preparativo existente
    with st.expander("Editar preparativo existente"):
        if st.session_state.df_preparativos.empty:
            st.write("No hay preparativos para editar.")
        else:
            indice_prep = st.selectbox("Selecciona preparativo a editar", st.session_state.df_preparativos.index)
            prep = st.session_state.df_preparativos.loc[indice_prep]

            tarea_edit = st.text_input("Tarea", value=prep["Tarea"])
            costo_edit = st.number_input("Costo", min_value=0.0, step=0.01, value=float(prep["Costo"]))
            estado_edit = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"], index=["Pendiente", "En progreso", "Completado"].index(prep["Estado"]))
            nota_edit = st.text_area("Notas", value=prep["Notas"])

            # Mostrar color según estado
            color_estado = {"Pendiente": "grey", "En progreso": "orange", "Completado": "green"}[estado_edit]
            st.markdown(f"<span style='color:{color_estado};font-weight:bold'>Estado: {estado_edit}</span>", unsafe_allow_html=True)

            if st.button("Guardar cambios preparativo"):
                st.session_state.df_preparativos.loc[indice_prep, "Tarea"] = tarea_edit.strip()
                st.session_state.df_preparativos.loc[indice_prep, "Costo"] = costo_edit
                st.session_state.df_preparativos.loc[indice_prep, "Estado"] = estado_edit
                st.session_state.df_preparativos.loc[indice_prep, "Notas"] = nota_edit.strip()

                csv_string = st.session_state.df_preparativos.to_csv(index=False)
                guardar_en_github("preparativos.csv", csv_string, "Editado preparativo desde app")
                st.experimental_rerun()

    st.subheader("Lista completa de preparativos")
    # Mostrar colores en columna Estado
    def colorear_estado(estado):
        if estado == "Completado":
            return "background-color: lightgreen"
        elif estado == "En progreso":
            return "background-color: yellow"
        else:
            return ""

    styled_df = st.session_state.df_preparativos.style.applymap(colorear_estado, subset=["Estado"])
    st.dataframe(styled_df)

# --- Presupuesto ---
with tabs[2]:
    st.header("Presupuesto")
    total_costo = st.session_state.df_preparativos["Costo"].sum()
    st.metric("Costo total estimado", f"${total_costo:,.2f}")

# --- Exportar ---
with tabs[3]:
    st.header("Exportar a Excel")

    data_frames = {
        "Invitados": st.session_state.df_invitados,
        "Preparativos": st.session_state.df_preparativos,
    }

    excel_data = to_excel(data_frames)

    st.download_button(
        label="📥 Descargar Excel con datos de boda",
        data=excel_data,
        file_name="datos_boda.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

