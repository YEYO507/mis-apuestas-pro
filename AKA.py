import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración Estética
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

ARCHIVO_DATOS = "historial_apuestas.csv"

# 2. Inicializar Base de Datos Local
if not os.path.exists(ARCHIVO_DATOS):
    pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance", "Saldo_Historico"]).to_csv(ARCHIVO_DATOS, index=False)

def guardar_registro(evento, monto, cuota, resultado, balance_num):
    df_actual = pd.read_csv(ARCHIVO_DATOS)
    # Calculamos el nuevo saldo acumulado para el gráfico de líneas
    ultimo_saldo = st.session_state.capital
    
    nuevo = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%d/%m %H:%M"),
        "Evento": evento,
        "Monto": monto,
        "Cuota": cuota,
        "Resultado": resultado,
        "Balance": f"${balance_num:.2f}",
        "Saldo_Historico": ultimo_saldo
    }])
    
    df_final = pd.concat([df_actual, nuevo], ignore_index=True)
    df_final.to_csv(ARCHIVO_DATOS, index=False)

# 3. Inicializar Estados
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Mi Billetera")
    # Este campo ahora es el corazón del saldo
    st.session_state.capital = st.number_input("Saldo Manual ($):", 
                                               value=float(st.session_state.capital), 
                                               format="%.2f", key="wallet_input")
    st.metric(label="Disponible para apostar", value=f"${st.session_state.capital:.2f}")
    
    st.divider()
    if st.button("🗑️ Resetear Datos", use_container_width=True):
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance", "Saldo_Historico"]).to_csv(ARCHIVO_DATOS, index=False)
        st.rerun()

st.title("🏆 Dashboard de Rendimiento")

# --- REGISTRO ---
with st.container(border=True):
    st.subheader("1️⃣ Registrar Nueva Apuesta")
    c1, c2, c3 = st.columns(3)
    ev = c1.text_input("¿A qué apostaste?", key="f_ev")
    mo = c2.number_input("Monto ($):", min_value=0.0, format="%.2f", key="f_mo")
    cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f", key="f_cu")
    
    if st.button("🚀 Confirmar Apuesta", use_container_width=True):
        if ev and mo > 0:
            if mo <= st.session_state.capital:
                # REGLA: Al apostar, el dinero sale de la billetera inmediatamente
                st.session_state.capital -= mo
                st.session_state.pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                st.rerun()
            else:
                st.error("No tienes saldo suficiente.")

# --- PENDIENTES ---
st.subheader("2️⃣ Apuestas en Curso")
if not st.session_state.pendientes:
    st.info("No tienes apuestas pendientes.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
            col_g, col_p, col_c = st.columns(3)
            
            if col_g.button("✅ GANADA", key=f"w_{i}", use_container_width=True):
                # SUMA: Devuelve el monto apostado + la ganancia neta
                ganancia_neta = ap['mo'] * (ap['cu'] - 1)
                st.session_state.capital += (ap['mo'] + ganancia_neta)
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", ganancia_neta)
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()
            
            if col_p.button("❌ PERDIDA", key=f"l_{i}", use_container_width=True):
                # RESTA: El dinero ya se restó al registrar, así que solo documentamos la pérdida
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", -ap['mo'])
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()

            if col_c.button("🔄 Cancelar", key=f"c_{i}", use_container_width=True):
                # DEVOLUCIÓN: Regresa el dinero intacto a la billetera
                st.session_state.capital += ap['mo']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- HISTORIAL Y GRÁFICOS ---
df_hist = pd.read_csv(ARCHIVO_DATOS)

if not df_hist.empty:
    st.subheader("📈 Evolución del Capital")
    # Gráfico de Línea: muestra el historial del saldo
    st.line_chart(df_hist["Saldo_Historico"])

    st.subheader("📊 Historial Detallado")
    def color_resultado(row):
        color = '#2ecc71' if row.Resultado == 'GANADA' else '#e74c3c'
        return [f'background-color: {color}; color: white'] * len(row)

    st.dataframe(df_hist.iloc[::-1].style.apply(color_resultado, axis=1), use_container_width=True, hide_index=True)
else:
    st.write("Registra tu primera apuesta para ver las gráficas.")
