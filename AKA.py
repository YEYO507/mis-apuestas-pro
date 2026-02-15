import streamlit as st
import pandas as pd
import os

# 1. Configuración de Estética
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

# Archivo de almacenamiento local (Más estable que Sheets para empezar)
ARCHIVO_DATOS = "historial_apuestas.csv"

if not os.path.exists(ARCHIVO_DATOS):
    pd.DataFrame(columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"]).to_csv(ARCHIVO_DATOS, index=False)

def guardar_registro(evento, monto, cuota, resultado, balance):
    nuevo = pd.DataFrame([[evento, monto, cuota, resultado, balance]], 
                         columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"])
    nuevo.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)

# 2. Inicializar Billetera
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []

# --- MENU LATERAL ---
with st.sidebar:
    st.header("💰 Mi Billetera")
    st.session_state.capital = st.number_input("Saldo Actual ($):", 
                                               value=float(st.session_state.capital), 
                                               format="%.2f", key="wallet_fixed")
    st.divider()
    if st.button("🗑️ Resetear Todo", use_container_width=True):
        pd.DataFrame(columns=["Evento", "Monto", "Cuota", "Resultado", "Balance"]).to_csv(ARCHIVO_DATOS, index=False)
        st.session_state.pendientes = []
        st.rerun()

st.title("🏆 Dashboard de Apuestas")

# --- PASO 1: REGISTRO ---
with st.container(border=True):
    st.subheader("1️⃣ Nueva Apuesta")
    c1, c2, c3 = st.columns(3)
    ev = c1.text_input("Evento:", key="input_evento")
    mo = c2.number_input("Monto ($):", min_value=0.0, format="%.2f", key="input_monto")
    cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f", key="input_cuota")
    
    if st.button("🚀 Registrar Jugada", use_container_width=True):
        if ev and mo > 0:
            if mo <= st.session_state.capital:
                st.session_state.capital -= mo
                st.session_state.pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                st.rerun()
            else:
                st.error("Saldo insuficiente.")

# --- PASO 2: EN CURSO ---
st.subheader("2️⃣ Apuestas Pendientes")
if not st.session_state.pendientes:
    st.info("No hay apuestas activas.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
            g, p, can = st.columns(3)
            if g.button("✅ GANADA", key=f"win_{i}", use_container_width=True):
                premio = ap['mo'] * ap['cu']
                st.session_state.capital += premio
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", f"+${premio-ap['mo']:.2f}")
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()
            
            if p.button("❌ PERDIDA", key=f"loss_{i}", use_container_width=True):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", f"-${ap['mo']:.2f}")
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()

            if can.button("🔄 Cancelar", key=f"cancel_{i}", use_container_width=True):
                st.session_state.capital += ap['mo']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- PASO 3: HISTORIAL CON COLORES ---
st.subheader("📊 Resumen de Resultados")
df_hist = pd.read_csv(ARCHIVO_DATOS)

if not df_hist.empty:
    def color_rows(row):
        return ['background-color: #2ecc71; color: white' if row.Resultado == 'GANADA' else 'background-color: #e74c3c; color: white'] * len(row)

    st.dataframe(df_hist.iloc[::-1].style.apply(color_rows, axis=1), use_container_width=True)
    
    # Gráfico rápido de efectividad
    st.divider()
    conteo = df_hist['Resultado'].value_counts()
    st.write("### 📈 Tu Efectividad")
    st.bar_chart(conteo)
else:
    st.write("Historial vacío.")
