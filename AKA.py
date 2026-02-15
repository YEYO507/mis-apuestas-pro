import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de archivos
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

ARCHIVO_DATOS = "historial_apuestas.csv"
ARCHIVO_PENDIENTES = "pendientes.csv"

# Crear archivos si no existen
for archivo, columnas in {
    ARCHIVO_DATOS: ["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"],
    ARCHIVO_PENDIENTES: ["ev", "mo", "cu"]
}.items():
    if not os.path.exists(archivo):
        pd.DataFrame(columns=columnas).to_csv(archivo, index=False)

# --- FUNCIONES DE PERSISTENCIA ---
def guardar_registro(evento, monto, cuota, resultado, balance_num, tipo="Apuesta"):
    df_actual = pd.read_csv(ARCHIVO_DATOS)
    nuevo = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%d/%m %H:%M"),
        "Evento": evento, 
        "Monto": round(float(monto), 2), 
        "Cuota": round(float(cuota), 2),
        "Resultado": resultado, 
        "Balance_Num": round(float(balance_num), 2), 
        "Tipo": tipo
    }])
    pd.concat([df_actual, nuevo], ignore_index=True).to_csv(ARCHIVO_DATOS, index=False)

def actualizar_pendientes(lista_pendientes):
    # Guardamos asegurando que los valores numéricos vayan redondeados
    df_p = pd.DataFrame(lista_pendientes)
    if not df_p.empty:
        df_p["mo"] = df_p["mo"].round(2)
        df_p["cu"] = df_p["cu"].round(2)
    df_p.to_csv(ARCHIVO_PENDIENTES, index=False)

# --- CARGA DE DATOS ---
df_hist_lectura = pd.read_csv(ARCHIVO_DATOS)
saldo_calculado = round(df_hist_lectura["Balance_Num"].sum(), 2)
pendientes_guardados = pd.read_csv(ARCHIVO_PENDIENTES).to_dict('records')

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_ingreso = st.number_input("Monto a Ingresar ($):", min_value=0.0, step=10.0, format="%.2f")
    
    if st.button("➕ Ingresar Capital", use_container_width=True):
        if monto_ingreso > 0:
            guardar_registro("Depósito Manual", monto_ingreso, 0, "DEPÓSITO", monto_ingreso, tipo="Ingreso")
            st.rerun()
            
    st.divider()
    st.metric("Saldo Disponible", f"${saldo_calculado:.2f}")
    
    if st.button("🗑️ Resetear Todo", use_container_width=True):
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)
        pd.DataFrame(columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)
        st.rerun()

st.title("🏆 Mi Control de Apuestas")

# --- PASO 1: NUEVA APUESTA ---
with st.container(border=True):
    st.subheader("1️⃣ Nueva Apuesta")
    with st.form("mi_formulario", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ev = c1.text_input("Evento:")
        mo = c2.number_input("Monto ($):", min_value=0.0, format="%.2f")
        cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f")
        enviar = st.form_submit_button("🚀 Registrar Jugada", use_container_width=True)
        
        if enviar:
            if ev and mo > 0:
                if mo <= saldo_calculado:
                    # Registrar la salida (negativo)
                    guardar_registro(ev, mo, cu, "PENDIENTE", -mo)
                    # Añadir a pendientes
                    pendientes_guardados.append({"ev": ev, "mo": round(mo, 2), "cu": round(cu, 2)})
                    actualizar_pendientes(pendientes_guardados)
                    st.rerun()
                else:
                    st.error("No tienes suficiente capital.")

# --- PASO 2: EN CURSO ---
st.subheader("2️⃣ Apuestas Pendientes")
if not pendientes_guardados:
    st.info("No hay apuestas activas.")
else:
    # Usamos una copia para iterar y poder eliminar por índice real
    for i, ap in enumerate(pendientes_guardados):
        with st.expander(f"⏳ {ap['ev']} | Apostado: ${ap['mo']:.2f} | Cuota: {ap['cu']:.2f}", expanded=True):
            g, p, can = st.columns(3)
            
            if g.button("✅ GANADA", key=f"win_{i}"):
                premio_total = round(ap['mo'] * ap['cu'], 2)
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", premio_total)
                pendientes_guardados.pop(i) # Elimina de la lista en memoria
                actualizar_pendientes(pendientes_guardados) # Sobrescribe el CSV sin esta apuesta
                st.balloons()
                st.rerun()
            
            if p.button("❌ PERDIDA", key=f"loss_{i}"):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", 0)
                pendientes_guardados.pop(i)
                actualizar_pendientes(pendientes_guardados)
                st.snow()
                st.rerun()

            if can.button("🔄 Cancelar", key=f"cancel_{i}"):
                # Se devuelve el monto original
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "CANCELADA", ap['mo'])
                pendientes_guardados.pop(i)
                actualizar_pendientes(pendientes_guardados)
                st.rerun()

# --- PASO 3: RESUMEN ---
st.divider()
df_hist = pd.read_csv(ARCHIVO_DATOS)
if not df_hist.empty:
    st.subheader("📊 Resumen de Rendimiento")
    ganadas = len(df_hist[df_hist['Resultado'] == 'GANADA'])
    perdidas = len(df_hist[df_hist['Resultado'] == 'PERDIDA'])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Ganadas", ganadas)
    m2.metric("❌ Perdidas", perdidas)
    m3.metric("💰 Saldo Real", f"${saldo_calculado:.2f}")

    def color_rows(row):
        if row.Resultado == 'GANADA': return ['background-color: #2ecc71; color: white'] * len(row)
        if row.Resultado == 'PERDIDA': return ['background-color: #e74c3c; color: white'] * len(row)
        if row.Resultado == 'PENDIENTE': return ['background-color: #f39c12; color: white'] * len(row)
        if row.Resultado == 'DEPÓSITO': return ['background-color: #3498db; color: white'] * len(row)
        return [''] * len(row)

    # Formatear el dataframe para mostrar 2 decimales en la tabla
    df_mostrar = df_hist.iloc[::-1].copy()
    st.dataframe(
        df_mostrar.style.apply(color_rows, axis=1).format({
            "Monto": "{:.2f}",
            "Cuota": "{:.2f}",
            "Balance_Num": "{:.2f}"
        }), 
        use_container_width=True, 
        hide_index=True
    )
