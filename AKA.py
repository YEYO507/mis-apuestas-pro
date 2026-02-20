import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de página
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

ARCHIVO_DATOS = "historial_apuestas.csv"
ARCHIVO_PENDIENTES = "pendientes.csv"

# --- FUNCIONES DE PERSISTENCIA ---
def inicializar_archivos():
    if not os.path.exists(ARCHIVO_DATOS) or os.path.getsize(ARCHIVO_DATOS) == 0:
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)
    if not os.path.exists(ARCHIVO_PENDIENTES) or os.path.getsize(ARCHIVO_PENDIENTES) == 0:
        pd.DataFrame(columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)

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
    df_final = pd.concat([df_actual, nuevo], ignore_index=True)
    df_final.to_csv(ARCHIVO_DATOS, index=False)

def actualizar_pendientes(lista_pendientes):
    df_p = pd.DataFrame(lista_pendientes) if lista_pendientes else pd.DataFrame(columns=["ev", "mo", "cu"])
    df_p.to_csv(ARCHIVO_PENDIENTES, index=False)

# Ejecución inicial
inicializar_archivos()

# --- LECTURA DE DATOS (IMPORTANTE: Leer siempre lo más reciente) ---
try:
    df_hist = pd.read_csv(ARCHIVO_DATOS)
except:
    df_hist = pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"])

saldo_actual = round(df_hist["Balance_Num"].sum(), 2) if not df_hist.empty else 0.0

try:
    pendientes = pd.read_csv(ARCHIVO_PENDIENTES).to_dict('records')
except:
    pendientes = []

# --- INTERFAZ: BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_ingreso = st.number_input("Monto a Ingresar ($):", min_value=0.0, step=10.0)
    if st.button("➕ Ingresar Capital", use_container_width=True):
        if monto_ingreso > 0:
            guardar_registro("Depósito Manual", monto_ingreso, 0, "DEPÓSITO", monto_ingreso, tipo="Ingreso")
            st.rerun()
    
    st.divider()
    st.metric("Saldo Disponible", f"${saldo_actual:.2f}")
    
    if st.button("🗑️ Resetear Todo"):
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)
        pd.DataFrame(columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)
        st.rerun()

st.title("🏆 Mi Control de Apuestas")

# --- PASO 1: NUEVA APUESTA ---
with st.container(border=True):
    st.subheader("1️⃣ Registrar Nueva Apuesta")
    with st.form("form_apuesta", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        ev = col1.text_input("Evento:")
        mo = col2.number_input("Monto ($):", min_value=0.0)
        cu = col3.number_input("Cuota:", min_value=1.0)
        btn = st.form_submit_button("🚀 Apostar Ahora", use_container_width=True)
        
        if btn and ev and mo > 0:
            if mo <= saldo_actual:
                guardar_registro(ev, mo, cu, "PENDIENTE", -mo)
                pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                actualizar_pendientes(pendientes)
                st.rerun()
            else:
                st.error("Saldo insuficiente.")

# --- PASO 2: APUESTAS PENDIENTES ---
st.subheader("2️⃣ Apuestas en Curso")
if not pendientes:
    st.info("No hay apuestas pendientes.")
else:
    for i, ap in enumerate(pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']} (Cuota: {ap['cu']})", expanded=True):
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ GANADA", key=f"g_{i}"):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", round(ap['mo'] * ap['cu'], 2))
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()
            if c2.button("❌ PERDIDA", key=f"p_{i}"):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", 0)
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()
            if c3.button("🔄 Cancelar", key=f"c_{i}"):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "CANCELADA", ap['mo'])
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()

# --- PASO 3: GRÁFICO Y TABLA ---
st.divider()
if not df_hist.empty:
    st.subheader("📊 Evolución del Saldo")
    # Crear los datos del gráfico: suma acumulada del balance
    df_grafico = df_hist.copy()
    df_grafico['Saldo_Acumulado'] = df_grafico['Balance_Num'].cumsum()
    
    # Gráfico Lineal Estático
    st.line_chart(df_grafico, x="Fecha", y="Saldo_Acumulado")

    st.subheader("📝 Historial de Movimientos")
    def color_rows(row):
        colores = {'GANADA': '#2ecc71', 'PERDIDA': '#e74c3c', 'PENDIENTE': '#f39c12', 'DEPÓSITO': '#3498db'}
        return [f'background-color: {colores.get(row.Resultado, "")}; color: white'] * len(row)

    st.dataframe(
        df_hist.iloc[::-1].style.apply(color_rows, axis=1),
        use_container_width=True,
        hide_index=True
    )
