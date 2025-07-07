import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, timedelta

# -------- CONFIG --------
GITHUB_REPO = "Ozzors/boda-app"
INVITADOS_FILE = "invitados.csv"
PREPARATIVOS_FILE = "preparativos.csv"
BRANCH = "main"

# -------- FUNCION PARA SUBIR ARCHIVOS A GITHUB --------
def subir_a_github(nombre_archivo, df):
    token = st.secrets["github_token"]
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"

    # Convertir DataFrame a string CSV codificado en base64
    csv_content = df.to_csv(index=False)
    b64_content = base64.b64encode(csv_content.encode()).decode()

    # Obtener el SHA del archivo actual
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        sha = r.json()["sha"]
    else:
        sha = None

    # Preparar payload
    payload = {
        "message": f"Actualizando {nombre_archivo} desde Streamlit",
        "content": b64_content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha

    # PUT a GitHub
    r = requests.put(url, headers={"Authorization": f"token {token}"}, json=payload)
    if r.status_code in [200, 201]:
        st.success(f"'{nombre_archivo}' actualizado en GitHub ✅")
    else:
        st.error(f"Error al subir '{nombre_archivo}': {r.text}")

# --------- CARGA DE DATOS DESDE GITHUB ---------
def cargar_csv_desde_github(nombre_archivo):
    url_raw = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{nombre_archivo}"
    try:
        return pd.read_csv(url_raw)
    except Exception:
        return pd.DataFrame()

# --------- SETUP ---------
st.set_page_config(page_title="App de Boda", layout="wide")
st.title("💍 App de Planificación de Boda")

# Contador
fecha_boda = datetime(2025, 8, 9, 0, 0)
tiempo_restante = fecha_boda - datetime.now()
dias = tiempo_restante.days
horas = tiempo_restante.seconds // 3600
st.info(f"⏳ Faltan **{dias} días** y **{horas} horas** para la boda")

# --------- CARGA INICIAL A SESSION STATE ---------
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = cargar_csv_desde_github(INVITADOS_FILE)

if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = cargar_csv_desde_github(PREPARATIVOS_FILE)

# --------- INTERFAZ DE TABS ---------
tabs = st.tabs(["👥 Invitados", "🎯 Preparativos", "💰 Presupuesto", "📤 Exportar"])

# -------- TAB INVITADOS --------
with tabs[0]:
    st.header("👥 Gestión de Invitados")

    with st.form("form_invitado"):
        nombre = st.text_input("Nombre del invitado")
        acompanantes = st.number_input("Cantidad de acompañantes", min_value=0, step=1)
        relacion = st.selectbox("Relación", ["Familiar", "Amigo", "Trabajo", "Otro"])
        comentarios = st.text_input("Comentarios")
        confirmacion = st.selectbox("¿Confirmado?", ["Por definir", "Sí", "No"])
        submitted = st.form_submit_button("Agregar")

    if submitted and nombre:
        nuevo = {
            "Nombre": nombre,
            "Acompañantes": acompanantes,
            "Relación": relacion,
            "Comentarios": comentarios,
            "Confirmación": confirmacion
        }
        st.session_state.df_invitados = pd.concat([
            st.session_state.df_invitados,
            pd.DataFrame([nuevo])
        ], ignore_index=True)
        subir_a_github(INVITADOS_FILE, st.session_state.df_invitados)

    # Contadores
    confirmados = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"]["Acompañantes"].sum() + st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Sí"].shape[0]
    por_definir = st.session_state.df_invitados[st.session_state.df_invitados["Confirmación"] == "Por definir"].shape[0]
    st.metric("Invitados confirmados (con acompañantes)", confirmados)
    st.metric("Invitados por definir", por_definir)

    # Edición rápida
    edited_df = st.data_editor(st.session_state.df_invitados, use_container_width=True, num_rows="dynamic")
    if edited_df is not None:
        st.session_state.df_invitados = edited_df
        subir_a_github(INVITADOS_FILE, st.session_state.df_invitados)

# -------- TAB PREPARATIVOS --------
with tabs[1]:
    st.header("🎯 Estado de Preparativos")

    with st.form("form_preparativos"):
        elemento = st.text_input("Elemento")
        estado = st.selectbox("Estado", ["Por hacer", "En progreso", "Completado"])
        costo = st.number_input("Costo (CAD)", min_value=0.0, step=10.0)
        notas = st.text_area("Notas")
        submitted = st.form_submit_button("Agregar")

    if submitted and elemento:
        nuevo = {
            "Elemento": elemento,
            "Estado": estado,
            "Costo": costo,
            "Notas": notas
        }
        st.session_state.df_preparativos = pd.concat([
            st.session_state.df_preparativos,
            pd.DataFrame([nuevo])
        ], ignore_index=True)
        subir_a_github(PREPARATIVOS_FILE, st.session_state.df_preparativos)

    # Agregar colores por estado
    def color_estado(val):
        if val == "Completado": return "background-color: lightgreen"
        if val == "En progreso": return "background-color: #fff3cd"
        return "background-color: #f8d7da"

    st.dataframe(
        st.session_state.df_preparativos.style.applymap(color_estado, subset=["Estado"]),
        use_container_width=True
    )

# -------- TAB PRESUPUESTO --------
with tabs[2]:
    st.header("💰 Presupuesto")
    total = st.session_state.df_preparativos["Costo"].sum()
    st.success(f"Total estimado: CAD ${total:,.2f}")

# -------- TAB EXPORTAR --------
with tabs[3]:
    st.header("📤 Exportar a Excel")
    st.write("(Próximamente disponible si activas XlsxWriter)")
