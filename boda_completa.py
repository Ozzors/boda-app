import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Planificador de Boda", layout="wide")

# ---------- FUNCIONES DE CARGA Y GUARDADO ----------
def cargar_csv(nombre_archivo, columnas):
    try:
        return pd.read_csv(nombre_archivo)
    except FileNotFoundError:
        return pd.DataFrame(columns=columnas)

def guardar_csv(df, nombre_archivo):
    df.to_csv(nombre_archivo, index=False)

# ---------- CARGA DE DATOS EXISTENTES ----------
df_invitados = cargar_csv("invitados.csv", ["Nombre", "Acompañantes", "Relación", "Confirmación", "Comentarios"])
df_preparativos = cargar_csv("preparativos.csv", ["Elemento", "Estado", "Costo", "Notas"])

# ---------- INTERFAZ ----------
st.title("💒 Planificador de Boda")
col1, col2 = st.columns([2, 1])

with col2:
    fecha_boda = datetime(2025, 8, 9, 15, 0)
    ahora = datetime.now()
    tiempo_restante = fecha_boda - ahora
    dias = tiempo_restante.days
    horas = tiempo_restante.seconds // 3600
    st.metric("⏳ Días para la boda", f"{dias} días, {horas} horas")

# ---------- INVITADOS ----------
st.header("👥 Lista de invitados")

with st.expander("➕ Agregar nuevo invitado"):
    with st.form("form_invitado", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        acompanantes = st.number_input("Cantidad de acompañantes", min_value=0, step=1)
        relacion = st.selectbox("Relación", ["Familia", "Amigo", "Trabajo", "Otro"])
        confirmacion = st.selectbox("Confirmación", ["Pendiente", "Confirmado", "No asistirá"])
        comentario = st.text_input("Comentario")
        submitted = st.form_submit_button("Agregar")
        if submitted and nombre:
            nuevo = {
                "Nombre": nombre,
                "Acompañantes": acompanantes,
                "Relación": relacion,
                "Confirmación": confirmacion,
                "Comentarios": comentario
            }
            df_invitados = pd.concat([df_invitados, pd.DataFrame([nuevo])], ignore_index=True)
            guardar_csv(df_invitados, "invitados.csv")
            st.success(f"Invitado {nombre} agregado")

# Modificar o eliminar invitados
if not df_invitados.empty:
    st.subheader("✏️ Editar invitados existentes")
    index = st.selectbox("Selecciona un invitado para editar", df_invitados.index, format_func=lambda i: df_invitados.at[i, "Nombre"])
    with st.form("edit_invitado"):
        df_row = df_invitados.loc[index]
        nuevo_nombre = st.text_input("Nombre", value=df_row["Nombre"])
        nuevo_acomp = st.number_input("Acompañantes", min_value=0, value=int(df_row["Acompañantes"]))
        nueva_relacion = st.selectbox("Relación", ["Familia", "Amigo", "Trabajo", "Otro"], index=["Familia", "Amigo", "Trabajo", "Otro"].index(df_row["Relación"]))
        nueva_confirm = st.selectbox("Confirmación", ["Pendiente", "Confirmado", "No asistirá"], index=["Pendiente", "Confirmado", "No asistirá"].index(df_row["Confirmación"]))
        nuevo_coment = st.text_input("Comentario", value=df_row["Comentarios"])
        guardar_cambios = st.form_submit_button("Guardar cambios")
        eliminar = st.form_submit_button("Eliminar invitado")
        if guardar_cambios:
            df_invitados.loc[index] = [nuevo_nombre, nuevo_acomp, nueva_relacion, nueva_confirm, nuevo_coment]
            guardar_csv(df_invitados, "invitados.csv")
            st.success("Cambios guardados")
        elif eliminar:
            df_invitados = df_invitados.drop(index).reset_index(drop=True)
            guardar_csv(df_invitados, "invitados.csv")
            st.success("Invitado eliminado")

st.dataframe(df_invitados, use_container_width=True)

# ---------- PREPARATIVOS ----------
st.header("📋 Seguimiento de preparativos")

with st.expander("➕ Agregar nuevo elemento"):
    with st.form("form_preparativo", clear_on_submit=True):
        elemento = st.text_input("Elemento")
        estado = st.selectbox("Estado", ["Pendiente", "En progreso", "Completado"])
        costo = st.number_input("Costo estimado ($)", min_value=0.0, step=1.0)
        nota = st.text_area("Notas")
        submitted = st.form_submit_button("Agregar")
        if submitted and elemento:
            nuevo = {"Elemento": elemento, "Estado": estado, "Costo": costo, "Notas": nota}
            df_preparativos = pd.concat([df_preparativos, pd.DataFrame([nuevo])], ignore_index=True)
            guardar_csv(df_preparativos, "preparativos.csv")
            st.success(f"Elemento '{elemento}' agregado")

if not df_preparativos.empty:
    st.subheader("✏️ Editar elementos existentes")
    idx = st.selectbox("Selecciona un elemento", df_preparativos.index, format_func=lambda i: df_preparativos.at[i, "Elemento"])
    with st.form("edit_preparativo"):
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
            st.success("Elemento eliminado")

st.dataframe(df_preparativos, use_container_width=True)

# ---------- PRESUPUESTO TOTAL ----------
total = df_preparativos["Costo"].sum()
st.subheader("💰 Presupuesto estimado")
st.metric("Total estimado", f"${total:,.2f}")


