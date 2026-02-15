import streamlit as st
import pandas as pd
import os

# 1. Configuración de Estética y Título
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

# Archivo de almacenamiento local
ARCHIVO_DATOS = "historial_apuestas.csv"

# 2. Base de Datos Local (CSV)
if not os.path.exists(ARCHIVO_DATOS):
    pd.DataFrame(columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"]).to_csv(ARCHIVO_DATOS, index=False)

def guardar_registro(evento, monto, cuota, resultado, balance):
    nuevo = pd.DataFrame([[evento, monto, cuota, resultado, balance]], 
                         columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"])
    nuevo.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)

# 3. Inicializar Estados
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []

# --- BARRA LATERAL (BILLETERA) ---
with st.sidebar:
    st.header("💰 Mi Billetera")
    st.session_state.capital = st.number_input("Saldo Actual ($):", 
                                               value=float(st.session_state.capital), 
                                               format="%.2f", key="wallet_fixed")
    st.divider()
    if st.button("🗑️ Resetear Historial", use_container_width=True):
        pd.DataFrame(columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"]).to_csv(ARCHIVO_DATOS, index=False)
        st.rerun()

st.title("🏆 Dashboard de Control")

# --- PASO 1: REGISTRO (SIN ERRORES DE ID) ---
with st.container(border=True):
    st.subheader("1️⃣ Nueva Apuesta")
    c1, c2, c3 = st.columns(3)
    ev = c1.text_input("Evento / Equipo:", key="f_ev", placeholder="Ej: Real Madrid")
    mo = c2.number_input("Monto a Invertir ($):", min_value=0.0, format="%.2f", key="f_mo")
    cu = c3.number_input("Cuota Final:", min_value=1.0, format="%.2f", key="f_cu")
    
    if st.button("🚀 Registrar Jugada", use_container_width=True):
        if ev and mo > 0:
            if mo <= st.session_state.capital:
                st.session_state.capital -= mo
                st.session_state.pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                st.rerun()
            else:
                st.error("No tienes suficiente saldo.")

# --- PASO 2: APUESTAS ACTIVAS ---
st.subheader("2️⃣ En Curso")
if not st.session_state.pendientes:
    st.info("No hay apuestas activas en este momento.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
            g, p, can = st.columns(3)
            if g.button("✅ GANADA", key=f"w_{i}", use_container_width=True):
                premio = ap['mo'] * ap['cu']
                st.session_state.capital += premio
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", f"+${premio-ap['mo']:.2f}")
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()
            
            if p.button("❌ PERDIDA", key=f"l_{i}", use_container_width=True):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", f"-${ap['mo']:.2f}")
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()

            if can.button("🔄 Cancelar", key=f"c_{i}", use_container_width=True):
                st.session_state.capital += ap['mo']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- PASO 3: HISTORIAL CON COLORES ---
st.subheader("📊 Resumen de Rendimiento")

df_hist = pd.read_csv(ARCHIVO_DATOS)

if not df_hist.empty:
    # Función para aplicar colores a las filas
    def color_resultado(val):
        color = '#2ecc71' if val == 'GANADA' else '#e74c3c' # Verde vs Rojo
        return f'background-color: {color}; color: white; font-weight: bold'

    # Aplicamos el estilo solo a la columna 'Resultado'
    styled_df = df_hist.iloc[::-1].style.map(color_resultado, subset=['Resultado'])
    
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.write("
