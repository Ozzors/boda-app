import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from io import StringIO

# URLs para cargar los datos
RUTA_INVITADOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/invitados.csv"
RUTA_PREPARATIVOS = "https://raw.githubusercontent.com/Ozzors/boda-app/refs/heads/main/preparativos.csv"

# Función para guardar en GitHub (requiere token configurado en secrets)
def guardar_en_github(ruta, contenido, mensaje):
    import base64
    import requests

    token = st.secrets["GITHUB_TOKEN"]
    repo = "Ozzors/boda-app"
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"

    # Obtener SHA del archivo para actualización
    headers = {"Authorization": f"token {token}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json()["sha"]
    else:
        sha = None

    data = {
        "message": mensaje,
        "content": base64.b64encode(contenido.encode()).decode(),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers=headers, json=data)
    if r.status_code not in [200, 201]:
        st.error(f"Error guardando en GitHub: {r.json().get('message')}")
    else:
        st.success("Datos guardados en GitHub correctamente")

# Cargar datos desde GitHub
@st.cache_data(ttl=600)
def cargar_datos(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        df = pd.read_csv(StringIO(r.text))
        return df
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame()

# Inicializar sesión estado
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = cargar_datos(RUTA_INVITADOS)
if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = cargar_datos(RUTA_PREPARATIVOS)

# Título y contador para la boda
st.title("📋 Planificador de Boda")

fecha_boda = datetime(2025, 8, 9, 15, 0, 0)
ahora = datetime.now()
diferencia = fecha_boda - ahora
dias = diferencia.days
horas = diferencia.seconds // 3600
st.markdown(f"### ⏳ Faltan {dias} días y {horas} horas para la boda")

# Tabs para secciones
tab1, tab2, tab3, tab4 = st.tabs(["Invitados", "Preparativos", "Presupuesto", "Exportar"])

with tab1:
    st.header("👥 Invitados")
    df = st.session_state.df_invitados.copy()

    # Contador confirmados y por definir
    confirmados = df[df["Confirmación"] == "Sí"]["Acompañantes"].sum() + df[df["Confirmación"] == "Sí"].shape[0]
    por_definir = df.shape[0] - df[df["Confirmación"] == "Sí"].shape[0]
    st.write(f"**Confirmados (incluyendo acompañantes):** {confirmados}")
    st.write(f"**Por definir:** {por_definir}")

    # Mostrar tabla editable
    editar_idx = st.selectbox("Selecciona un invitado para editar", options=["--Nuevo invitado--"] + df.index.astype(str).tolist())
    
    if editar_idx != "--Nuevo invitado--":
        idx = int(editar_idx)
        invitado = df.loc[idx]
        nombre = st.text_input("Nombre", value=invitado["Nombre"])
        acompanantes = st.number_input("Acompañantes", min_value=0, value=int(invitado["Acompañantes"]))
        relacion = st.text_input("Relación", value=invitado["Relación"])
        comentarios = st.text_area("Comentarios", value=invitado["Comentarios"])
        confirmacion = st.selectbox("Confirmación", options=["Sí", "No", "Por definir"], index=["Sí", "No", "Por definir"].index(invitado["Confirmación"]))
        
        if st.button("Guardar invitado editado"):
            st.session_state.df_invitados.at[idx, "Nombre"] = nombre
            st.session_state.df_invitados.at[idx, "Acompañantes"] = acompanantes
            st.session_state.df_invitados.at[idx, "Relación"] = relacion
            st.session_state.df_invitados.at[idx, "Comentarios"] = comentarios
            st.session_state.df_invitados.at[idx, "Confirmación"] = confirmacion
            guardar_en_github(RUTA_INVITADOS, st.session_state.df_invitados.to_csv(index=False), "Auto-guardado: invitado editado")
            st.success("Invitado editado correctamente")
            st.experimental_rerun()
            st.stop()
    else:
        st.subheader("Agregar nuevo invitado")
        nombre = st.text_input("Nombre")
        acompanantes = st.number_input("Acompañantes", min_value=0, value=0)
        relacion = st.text_input("Relación")
        comentarios = st.text_area("Comentarios")
        confirmacion = st.selectbox("Confirmación", options=["Sí", "No", "Por definir"])

        if st.button("Agregar invitado"):
            nuevo = pd.DataFrame([{
                "Nombre": nombre,
                "Acompañantes": acompanantes,
                "Relación": relacion,
                "Comentarios": comentarios,
                "Confirmación": confirmacion
            }])
            st.session_state.df_invitados = pd.concat([df, nuevo], ignore_index=True)
            guardar_en_github(RUTA_INVITADOS, st.session_state.df_invitados.to_csv(index=False), "Auto-guardado: nuevo invitado")
            st.success("✅ Invitado agregado")
            st.experimental_rerun()
            st.stop()

with tab2:
    st.header("🎀 Preparativos")
    dfp = st.session_state.df_preparativos.copy()

    estados = ["Pendiente", "En progreso", "Completado"]
    colores = {"Pendiente": "", "En progreso": "yellow", "Completado": "lightgreen"}

    editar_p_idx = st.selectbox("Selecciona un preparativo para editar", options=["--Nuevo preparativo--"] + dfp.index.astype(str).tolist())

    if editar_p_idx != "--Nuevo preparativo--":
        idxp = int(editar_p_idx)
        prep = dfp.loc[idxp]
        item = st.text_input("Elemento", value=prep["Elemento"])
        costo = st.number_input("Costo", min_value=0.0, value=float(prep["Costo"]))
        estado = st.selectbox("Estado", estados, index=estados.index(prep["Estado"]))
        notas = st.text_area("Notas", value=prep["Notas"])

        if st.button("Guardar preparativo editado"):
            st.session_state.df_preparativos.at[idxp, "Elemento"] = item
            st.session_state.df_preparativos.at[idxp, "Costo"] = costo
            st.session_state.df_preparativos.at[idxp, "Estado"] = estado
            st.session_state.df_preparativos.at[idxp, "Notas"] = notas
            guardar_en_github(RUTA_PREPARATIVOS, st.session_state.df_preparativos.to_csv(index=False), "Auto-guardado: preparativo editado")
            st.success("Preparativo editado correctamente")
            st.experimental_rerun()
            st.stop()
    else:
        st.subheader("Agregar nuevo preparativo")
        item = st.text_input("Elemento")
        costo = st.number_input("Costo", min_value=0.0, value=0.0)
        estado = st.selectbox("Estado", estados)
        notas = st.text_area("Notas")

        if st.button("Agregar preparativo"):
            nuevo_p = pd.DataFrame([{
                "Elemento": item,
                "Costo": costo,
                "Estado": estado,
                "Notas": notas
            }])
            st.session_state.df_preparativos = pd.concat([dfp, nuevo_p], ignore_index=True)
            guardar_en_github(RUTA_PREPARATIVOS, st.session_state.df_preparativos.to_csv(index=False), "Auto-guardado: nuevo preparativo")
            st.success("✅ Preparativo agregado")
            st.experimental_rerun()
            st.stop()

with tab3:
    st.header("💰 Presupuesto")
    total_costo = st.session_state.df_preparativos["Costo"].sum()
    st.write(f"**Costo total estimado: ${total_costo:,.2f}**")

with tab4:
    st.header("📥 Exportar datos")
    st.write("Actualmente la opción de exportar a Excel no está disponible para evitar dependencias externas.")

