import streamlit as st
import pandas as pd
import datetime
import requests
import base64
import json

# CONFIGURACIÓN INICIAL
st.set_page_config(page_title="App Boda", layout="wide")
st.title("👰🤵 Planificador de Boda")

# FECHA DE LA BODA Y CONTADOR
fecha_boda = datetime.datetime(2025, 8, 9, 15, 0, 0)
tiempo_restante = fecha_boda - datetime.datetime.now()
st.info(f"⏳ Faltan {tiempo_restante.days} días y {tiempo_restante.seconds // 3600} horas para la boda")

# FUNCIONES PARA GOOGLE SHEETS O GITHUB
@st.cache_data(ttl=60)
def cargar_csv_desde_github(url):
    return pd.read_csv(url)

def guardar_en_github(archivo, contenido, mensaje):
    github_token = st.secrets["GITHUB_TOKEN"]
    repo = "Ozzors/boda-app"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json"
    }
    url_api = f"https://api.github.com/repos/{repo}/contents/{archivo}"
    r_get = requests.get(url_api, headers=headers)
    if r_get.status_code == 200:
        sha = r_get.json()["sha"]
    else:
        sha = None

    data = {
        "message": mensaje,
        "content": base64.b64encode(contenido.encode()).decode(),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    r_put = requests.put(url_api, headers=headers, data=json.dumps(data))
    if r_put.status_code in [200, 201]:
        st.toast(f"'{archivo}' actualizado en GitHub", icon="✅")
    else:
        st.error(f"Error al subir '{archivo}': {r_put.text}")

# CARGA INICIAL DE DATOS
url_invitados = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/invitados.csv"
url_preparativos = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/preparativos.csv"

df_invitados = cargar_csv_desde_github(url_invitados)
df_preparativos = cargar_csv_desde_github(url_preparativos)

if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = df_invitados.copy()

if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = df_preparativos.copy()

# PESTAÑAS
tabs = st.tabs(["📋 Invitados", "🎯 Preparativos", "💰 Presupuesto"])

# TAB INVITADOS
with tabs[0]:
    st.header("📋 Lista de Invitados")

    with st.form("Agregar/Editar invitado"):
        col1, col2, col3 = st.columns(3)
        nombre = col1.text_input("Nombre completo")
        acompanantes = col2.number_input("Acompañantes", min_value=0, step=1)
        relacion = col3.text_input("Relación")

        comentarios = st.text_input("Comentarios")
        confirmacion = st.selectbox("¿Confirmó?", ["Por definir", "Sí", "No"])

        editar = st.checkbox("Editar invitado existente (por nombre)")

        if st.form_submit_button("Guardar"):
            nuevo = {
                "Nombre": nombre,
                "Acompañantes": acompanantes,
                "Relación": relacion,
                "Comentarios": comentarios,
                "Confirmación": confirmacion
            }
            df = st.session_state.df_invitados
            if editar and nombre in df["Nombre"].values:
                st.session_state.df_invitados.loc[df["Nombre"] == nombre] = nuevo
            else:
                st.session_state.df_invitados = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)

            # Guardar en GitHub automáticamente
            invitados_csv = st.session_state.df_invitados.to_csv(index=False)
            guardar_en_github("invitados.csv", invitados_csv, "Auto-guardado: invitados actualizados")

    # Mostrar tabla y estadísticas
    df = st.session_state.df_invitados
    confirmados = df[df["Confirmación"] == "Sí"]["Acompañantes"].sum() + df[df["Confirmación"] == "Sí"].shape[0]
    por_definir = df[df["Confirmación"] == "Por definir"].shape[0]

    st.markdown(f"✅ Confirmados: **{confirmados}** personas")
    st.markdown(f"❔ Por definir: **{por_definir}** invitados")
    st.dataframe(df, use_container_width=True)

# TAB PREPARATIVOS
with tabs[1]:
    st.header("🎯 Preparativos")

    with st.form("Agregar/Editar tarea"):
        col1, col2 = st.columns([3, 1])
        tarea = col1.text_input("Tarea")
        costo = col2.number_input("Costo ($)", min_value=0.0, step=10.0)

        estado = st.selectbox("Estado", ["Por definir", "En progreso", "Completado"])
        notas = st.text_area("Notas")

        editar_tarea = st.checkbox("Editar tarea existente (por nombre)")

        if st.form_submit_button("Guardar tarea"):
            nuevo = {
                "Tarea": tarea,
                "Costo": costo,
                "Estado": estado,
                "Notas": notas
            }
            df = st.session_state.df_preparativos
            if editar_tarea and tarea in df["Tarea"].values:
                st.session_state.df_preparativos.loc[df["Tarea"] == tarea] = nuevo
            else:
                st.session_state.df_preparativos = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)

            # Guardar en GitHub automáticamente
            preparativos_csv = st.session_state.df_preparativos.to_csv(index=False)
            guardar_en_github("preparativos.csv", preparativos_csv, "Auto-guardado: preparativos actualizados")

    df = st.session_state.df_preparativos.copy()

    # Colorear por estado
    def color_estado(val):
        color = ""
        if val == "Completado":
            color = "background-color: lightgreen"
        elif val == "En progreso":
            color = "background-color: khaki"
        elif val == "Por definir":
            color = "background-color: lightcoral"
        return color

    st.dataframe(df.style.applymap(color_estado, subset=["Estado"]), use_container_width=True)

# TAB PRESUPUESTO
with tabs[2]:
    st.header("💰 Presupuesto total")
    total = st.session_state.df_preparativos["Costo"].sum()
    st.metric("Total estimado ($)", f"${total:,.2f}")
