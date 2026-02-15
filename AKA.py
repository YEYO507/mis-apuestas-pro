import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

ARCHIVO_DATOS = "historial_apuestas.csv"

if not os.path.exists(ARCHIVO_DATOS):
    pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)

def guardar_registro(evento, monto, cuota, resultado, balance_num, tipo="Apuesta"):
    df_actual = pd.read_csv(ARCHIVO_DATOS)
    nuevo = pd.DataFrame([{
        "Fecha": datetime.now().strftime("%d/%m %H:%M"),
        "Evento": evento,
        "Monto": monto,
        "Cuota": cuota,
        "Resultado": resultado,
        "Balance_Num": balance_num,
        "Tipo": tipo
    }])
    df_final = pd.concat([df_actual, nuevo], ignore_index=True)
    df_final.to_csv(ARCHIVO_DATOS, index=False)

# 2. Inicializar Billetera
if 'capital' not in st.session_state:
    st.session_state.capital = 0.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_ingreso = st.number_input("Monto a Ingresar ($):", min_value=0.0, step=10.0, key="monto_deposito")
    
    # BOTÓN INGRESAR CAPITAL
    if st.button("➕ Ingresar Capital", use_container_width=True):
        if monto_ingreso > 0:
            st.session_state.capital += monto_ingreso
            # El ingreso suma al Balance Total
            guardar_registro("Depósito Manual", monto_ingreso, 0, "DEPÓSITO", monto_ingreso, tipo="Ingreso")
            st.rerun()
            
    st.divider()
    st.metric("Saldo Disponible", f"${st.session_state.capital:.2f}")
    
    if st.button("🗑️ Resetear Todo", use_container_width=True):
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)
        st.session_state.capital = 0.00
        st.session_state.pendientes = []
        st.rerun()

st.title("🏆 Mi Control de Apuestas")

# --- PASO 1: REGISTRO CON LIMPIEZA CORREGIDA ---
with st.container(border=True):
    st.subheader("1️⃣ Nueva Apuesta")
    
    # Creamos un formulario para que se limpie solo al enviar
    with st.form("mi_formulario", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ev = c1.text_input("Evento:")
        mo = c2.number_input("Monto ($):", min_value=0.0, format="%.2f")
        cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f")
        
        enviar = st.form_submit_button("🚀 Registrar Jugada", use_container_width=True)
        
        if enviar:
            if ev and mo > 0:
                if mo <= st.session_state.capital:
                    # RESTAR: Dinero sale de la billetera
                    st.session_state.capital -= mo
                    st.session_state.pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                    st.rerun()
                else:
                    st.error("No tienes suficiente capital.")
            else:
                st.warning("Completa los campos.")

# --- PASO 2: EN CURSO ---
st.subheader("2️⃣ Apuestas Pendientes")
if not st.session_state.pendientes:
    st.info("No hay apuestas activas.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['ev']} | Apostado: ${ap['mo']:.2f}", expanded=True):
            g, p, can = st.columns(3)
            
            if g.button("✅ GANADA", key=f"win_{i}", use_container_width=True):
                premio_total = ap['mo'] * ap['cu']
                st.session_state.capital += premio_total # SUMA capital + ganancia
                
                ganancia_neta = premio_total - ap['mo']
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", ganancia_neta)
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()
            
            if p.button("❌ PERDIDA", key=f"loss_{i}", use_container_width=True):
                # RESTAR: El dinero ya se restó del saldo, aquí resta del Balance Total
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", -ap['mo'])
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()

            if can.button("🔄 Cancelar", key=f"cancel_{i}", use_container_width=True):
                st.session_state.capital += ap['mo']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- PASO 3: RESUMEN DE RENDIMIENTO ---
st.divider()
df_hist = pd.read_csv(ARCHIVO_DATOS)

if not df_hist.empty:
    st.subheader("📊 Resumen de Rendimiento")
    ganadas = len(df_hist[df_hist['Resultado'] == 'GANADA'])
    perdidas = len(df_hist[df_hist['Resultado'] == 'PERDIDA'])
    # El Balance Total suma ingresos y ganancias, resta pérdidas
    balance_total = df_hist['Balance_Num'].sum()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Ganadas", ganadas)
    m2.metric("❌ Perdidas", perdidas)
    m3.metric("💰 Balance Neto Total", f"${balance_total:.2f}")

    def color_rows(row):
        if row.Resultado == 'GANADA': color = '#2ecc71'
        elif row.Resultado == 'PERDIDA': color = '#e74c3c'
        else: color = '#3498db'
        return [f'background-color: {color}; color: white'] * len(row)

    st.dataframe(df_hist.iloc[::-1].style.apply(color_rows, axis=1), use_container_width=True, hide_index=True)
