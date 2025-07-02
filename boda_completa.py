import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Planificador de Boda", layout="wide")

# ---------- FUNCIONES ----------
def cargar_csv(nombre_archivo, columnas, datos_iniciales=None):
    try:
        return pd.read_csv(nombre_archivo)
    except FileNotFoundError:
        if datos_iniciales is not None:
            return pd.DataFrame(datos_iniciales, columns=columnas)
        else:
            return pd.DataFrame(columns=columnas)

def guardar_csv(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False)

# ---------- DATOS INICIALES ----------
preparativos_iniciales = [
    {"Elemento": "Bouquet de la novia", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Vestido de la novia", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Maquillaje y peinado", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Traje de novio", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Corbata, pin y medias", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Torta", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Fotógrafo", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Notario", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Anillos", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Estado de envío de pre-invitaciones", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Invitaciones con detalle", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Locación del evento", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Decoración", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Compra de cuchillo de torta", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Bolígrafo de la firma", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
    {"Elemento": "Habitación del hotel", "Estado": "Pendiente", "Costo": 0.0, "Notas": ""},
]

# ---------- CARGA DE DATOS ----------
df_invitados = cargar_csv("invitados.csv", ["Nombre", "Acompañantes", "Relación", "Confirmación", "Comentarios"])
df_preparativos = cargar_csv("preparativos.csv", ["Elemento", "Estado", "Costo", "Notas"], preparativos_iniciales)

# ---------- UI: CONTADOR DE BODA ----------
st.title("💒 Planificador de Boda")

col1, col2 = st.columns([3, 1])
with col2:
    fecha_boda = datetime(2025, 8, 9, 15, 0)
    ahora = datetime.now()
    tiempo = fecha_boda - ahora
    dias = tiempo.days
    horas = tiempo.seconds // 3600
    st.metric("⏳ Faltan:", f"{dias} días, {horas} horas")

# ---------- TABS ----------
tabs = st.tabs(["👥 Invitados", "📋 Preparativos", "💰 Presupuesto", "📝 Notas"])

# ---------- TAB 1: INVITADOS ----------
with tabs[0]:
    st.subheader("Invitados")

    with st.expander("➕ Agregar nuevo invitado"):
        with st.form("form_invitado", clear_on_submit=True):
            nombre = st.text_input("Nombre")
            acompanantes = st.number_input("Acompañantes", min_value=0, step=1)
            relacion = st.selectbox("Relación", ["Familia", "Amigo", "Trabajo", "Otro"])
            confirmacion = st.selectbox("Confirmación", ["Pendiente", "Confirmado", "No asistirá"])
            comentario = st.text_input("Comentario")
            submit = st.form_submit_button("Agregar")
            if submit and nombre:
                nuevo = {
                    "Nombre": nombre,
                    "Acompañantes": acompanantes,
                    "Relación": relacion,
                    "Confirmación": confirmacion,
                    "Comentarios": comentario
                }
                df_invitados = pd.concat([df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
                guardar_csv(df_invitados, "invitados.csv")
                st.success(f"{nombre} agregado")

    if not df_invitados.empty:
        index = st.selectbox("Editar invitado", df_invitados.index, format_func=lambda i: df_invitados.at[i, "Nombre"])
        with st.form("edit_invitado"):
            row = df_invitados.loc[index]
            nuevo_nombre = st.text_input("Nombre", value=row["Nombre"])
            nuevo_acomp = st.number_input("Acompañantes", min_value=0, value=int(row["Acompañantes"]))
            nueva_relacion = st.selectbox("Relación", ["Familia", "Amigo", "Trabajo", "Otro"], index=["Familia", "Amigo", "Trabajo", "Otro"].index(row["Relación"]))
            nueva_confirm = st.selectbox("Confirmación", ["Pendiente", "Confirmado", "No asistirá"], index=["Pendiente", "Confirmado", "No asistirá"].index(row["Confirmación"]))
            nuevo_coment = st.text_input("Comentario", value=row["Comentarios"])
            guardar = st.form_submit_button("Guardar cambios")
            eliminar = st.form_submit_button("Eliminar")
            if guardar:
                df_invitados.loc[index] = [nuevo_nombre, nuevo_acomp, nueva_relacion, nueva_confirm, nuevo_coment]
                guardar_csv(df_invitados, "invitados.csv")
                st.success("Cambios guardados")
            elif eliminar:
                df_invitados = df_invitados.drop(index).reset_index(drop=True)
                guardar_csv(df_invitados, "invitados.csv")
                st.success("Eliminado")

    st.dataframe(df_invitados, use_container_width=True)

# ---------- TAB 2: PREPARATIVOS ----------
with tabs[1]:
    st.subheader("Preparativos")

    with st.expander("➕ Agregar nuevo elemento"):
        with st.form("form_prep", clear_on_submit=True):
            elem = st.text_input("Elemento")
            estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"])
            costo = st.number_input("Costo ($)", min_value=0.0, step=1.0)
            notas = st.text_area("Notas")
            agregar = st.form_submit_button("Agregar")
            if agregar and elem:
                nuevo = {"Elemento": elem, "Estado": estado, "Costo": costo, "Notas": notas}
                df_preparativos = pd.concat([df_preparativos, pd.DataFrame([nuevo])], ignore_index=True)
                guardar_csv(df_preparativos, "preparativos.csv")
                st.success("Elemento agregado")

    if not df_preparativos.empty:
        idx = st.selectbox("Editar elemento", df_preparativos.index, format_func=lambda i: df_preparativos.at[i, "Elemento"])
        with st.form("edit_prep"):
            fila = df_preparativos.loc[idx]
            nuevo_elem = st.text_input("Elemento", value=fila["Elemento"])
            nuevo_estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"], index=["Pendiente", "En progreso", "Completado"].index(fila["Estado"]))
            nuevo_costo = st.number_input("Costo", value=float(fila["Costo"]))
            nueva_nota = st.text_area("Notas", value=fila["Notas"])
            guardar = st.form_submit_button("Guardar cambios")
            eliminar = st.form_submit_button("Eliminar")
            if guardar:
                df_preparativos.loc[idx] = [nuevo_elem, nuevo_estado, nuevo_costo, nueva_nota]
                guardar_csv(df_preparativos, "preparativos.csv")
                st.success("Cambios guardados")
            elif eliminar:
                df_preparativos = df_preparativos.drop(idx).reset_index(drop=True)
                guardar_csv(df_preparativos, "preparativos.csv")
                st.success("Eliminado")

    # Mostrar tabla con colores por estado
    st.markdown("### Estado de Preparativos (con colores)")

    def color_estado(estado):
        colores = {
            "Pendiente": "#FFCDD2",     # Rojo claro
            "En progreso": "#FFF9C4",   # Amarillo claro
            "Completado": "#C8E6C9"     # Verde claro
        }
        return f"background-color: {colores.get(estado, 'white')}"

    df_estilo = df_preparativos.style.applymap(color_estado, subset=["Estado"])
    st.dataframe(df_estilo, use_container_width=True)

# ---------- TAB 3: PRESUPUESTO ----------
with tabs[2]:
    st.subheader("Presupuesto estimado")
    total = df_preparativos["Costo"].sum()
    st.metric("💰 Total", f"${total:,.2f}")
    st.dataframe(df_preparativos[["Elemento", "Costo"]], use_container_width=True)

# ---------- TAB 4: NOTAS PERSONALES ----------
with tabs[3]:
    st.subheader("Notas personales")
    notas = st.text_area("Escribe tus notas aquí...")
