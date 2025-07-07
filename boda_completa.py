import streamlit as st
import pandas as pd
import datetime
import base64
import requests
from io import StringIO

# ---------- CONFIGURACIÓN ----------
GITHUB_REPO = "Ozzors/boda-app"
RUTA_INVITADOS = "invitados.csv"
RUTA_PREPARATIVOS = "preparativos.csv"
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

# ---------- FUNCIONES DE GITHUB ----------
def leer_csv_desde_github(ruta):
    url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{ruta}"
    try:
        df = pd.read_csv(url)
    except:
        df = pd.DataFrame()
    return df

def guardar_en_github(nombre_archivo, contenido_csv, mensaje):
    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{nombre_archivo}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    r = requests.get(api_url, headers=headers)
    if r.status_code == 200:
        sha = r.json()["sha"]
    else:
        sha = None

    data = {
        "message": mensaje,
        "content": base64.b64encode(contenido_csv.encode("utf-8")).decode("utf-8"),
        "branch": "main"
    }
    if sha:
        data["sha"] = sha

    r = requests.put(api_url, headers=headers, json=data)
    return r.status_code == 201 or r.status_code == 200

# ---------- CARGA INICIAL ----------
if "df_invitados" not in st.session_state:
    st.session_state.df_invitados = leer_csv_desde_github(RUTA_INVITADOS)

if "df_preparativos" not in st.session_state:
    st.session_state.df_preparativos = leer_csv_desde_github(RUTA_PREPARATIVOS)

# ---------- INTERFAZ PRINCIPAL ----------
st.title("💍 Planificador de Boda")

tab1, tab2, tab3, tab4 = st.tabs(["👥 Invitados", "🎯 Preparativos", "💰 Presupuesto", "📤 Exportar"])

# ---------- TAB 1: INVITADOS ----------
with tab1:
    st.header("Invitados")
    
    df = st.session_state.df_invitados
    nombres_existentes = ["Nuevo invitado"] + df["Nombre"].tolist()

    seleccion = st.selectbox("Selecciona un invitado para editar o elige 'Nuevo invitado':", nombres_existentes)

    if seleccion == "Nuevo invitado":
        nombre = st.text_input("Nombre")
        acompanantes = st.number_input("Acompañantes", min_value=0, step=1)
        relacion = st.text_input("Relación")
        comentarios = st.text_input("Comentarios")
        confirmacion = st.selectbox("¿Confirmado?", ["Por definir", "Sí", "No"])

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

    else:
        fila = df[df["Nombre"] == seleccion].iloc[0]
        nombre = st.text_input("Nombre", value=fila["Nombre"])
        acompanantes = st.number_input("Acompañantes", value=int(fila["Acompañantes"]), min_value=0)
        relacion = st.text_input("Relación", value=fila["Relación"])
        comentarios = st.text_input("Comentarios", value=fila["Comentarios"])
        confirmacion = st.selectbox("¿Confirmado?", ["Por definir", "Sí", "No"], index=["Por definir", "Sí", "No"].index(fila["Confirmación"]))

        if st.button("Guardar cambios"):
            idx = df[df["Nombre"] == seleccion].index[0]
            st.session_state.df_invitados.loc[idx] = [nombre, acompanantes, relacion, comentarios, confirmacion]
            guardar_en_github(RUTA_INVITADOS, st.session_state.df_invitados.to_csv(index=False), "Auto-guardado: invitado editado")
            st.success("✅ Cambios guardados")
            st.experimental_rerun()

    # Contadores
    confirmados = df[df["Confirmación"] == "Sí"]["Acompañantes"].sum() + df[df["Confirmación"] == "Sí"].shape[0]
    por_definir = df[df["Confirmación"] == "Por definir"].shape[0]
    st.markdown(f"**🎉 Confirmados:** {confirmados}")
    st.markdown(f"**⏳ Por definir:** {por_definir}")
    
    st.dataframe(df)

# ---------- TAB 2: PREPARATIVOS ----------
with tab2:
    st.header("Preparativos")

    df = st.session_state.df_preparativos
    tareas_existentes = ["Nuevo preparativo"] + df["Tarea"].tolist()

    seleccion = st.selectbox("Selecciona una tarea para editar o elige 'Nuevo preparativo':", tareas_existentes)

    if seleccion == "Nuevo preparativo":
        tarea = st.text_input("Tarea")
        estado = st.selectbox("Estado", ["Por hacer", "En progreso", "Completado"])
        costo = st.number_input("Costo", min_value=0.0, step=1.0)
        notas = st.text_area("Notas")

        if st.button("Agregar tarea"):
            nueva = pd.DataFrame([{
                "Tarea": tarea,
                "Estado": estado,
                "Costo": costo,
                "Notas": notas
            }])
            st.session_state.df_preparativos = pd.concat([df, nueva], ignore_index=True)
            guardar_en_github(RUTA_PREPARATIVOS, st.session_state.df_preparativos.to_csv(index=False), "Auto-guardado: nueva tarea")
            st.success("✅ Tarea agregada")
            st.experimental_rerun()
    else:
        fila = df[df["Tarea"] == seleccion].iloc[0]
        tarea = st.text_input("Tarea", value=fila["Tarea"])
        estado = st.selectbox("Estado", ["Por hacer", "En progreso", "Completado"], index=["Por hacer", "En progreso", "Completado"].index(fila["Estado"]))
        costo = st.number_input("Costo", value=float(fila["Costo"]), min_value=0.0, step=1.0)
        notas = st.text_area("Notas", value=fila["Notas"])

        if st.button("Guardar cambios en tarea"):
            idx = df[df["Tarea"] == seleccion].index[0]
            st.session_state.df_preparativos.loc[idx] = [tarea, estado, costo, notas]
            guardar_en_github(RUTA_PREPARATIVOS, st.session_state.df_preparativos.to_csv(index=False), "Auto-guardado: tarea editada")
            st.success("✅ Cambios guardados")
            st.experimental_rerun()

    # Mostrar con colores por estado
    def colorear_estado(val):
        color = {"Por hacer": "#FFCCCC", "En progreso": "#FFF2CC", "Completado": "#CCFFCC"}.get(val, "#FFFFFF")
        return f"background-color: {color}"

    st.dataframe(df.style.applymap(colorear_estado, subset=["Estado"]))

# ---------- TAB 3: PRESUPUESTO ----------
with tab3:
    st.header("Resumen de Presupuesto")
    total = st.session_state.df_preparativos["Costo"].sum()
    st.metric("💵 Total estimado", f"${total:,.2f}")

# ---------- TAB 4: EXPORTAR ----------
with tab4:
    st.header("Exportar a CSV")
    st.download_button("⬇ Descargar invitados.csv", st.session_state.df_invitados.to_csv(index=False), "invitados.csv", "text/csv")
    st.download_button("⬇ Descargar preparativos.csv", st.session_state.df_preparativos.to_csv(index=False), "preparativos.csv", "text/csv")

# ---------- CONTADOR DE DÍAS ----------
st.sidebar.title("⏰ Cuenta Regresiva")
fecha_boda = datetime.datetime(2025, 8, 9, 15, 0, 0)
ahora = datetime.datetime.now()
restante = fecha_boda - ahora
dias, horas = restante.days, restante.seconds // 3600
st.sidebar.markdown(f"**Faltan {dias} días y {horas} horas para la boda 💒**")
