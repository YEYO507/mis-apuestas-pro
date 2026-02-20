import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuración
st.set_page_config(page_title="Gestor de Apuestas Pro", layout="wide")

ARCHIVO_DATOS = "historial_apuestas.csv"
ARCHIVO_PENDIENTES = "pendientes.csv"

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
    pd.concat([df_actual, nuevo], ignore_index=True).to_csv(ARCHIVO_DATOS, index=False)

inicializar_archivos()

# --- CARGA DE DATOS ---
try:
    df_base = pd.read_csv(ARCHIVO_DATOS)
    # Identificar eventos que ya se cerraron
    cerrados = df_base[df_base['Resultado'].isin(['GANADA', 'PERDIDA', 'CANCELADA'])]['Evento'].unique()
    # Filtrar: No mostrar el 'PENDIENTE' original si el evento ya se cerró
    df_hist = df_base[~((df_base['Resultado'] == 'PENDIENTE') & (df_base['Evento'].isin(cerrados)))]
except:
    df_hist = pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"])

saldo_actual = round(df_hist["Balance_Num"].sum(), 2)

try:
    pendientes = pd.read_csv(ARCHIVO_PENDIENTES).to_dict('records')
except:
    pendientes = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_in = st.number_input("Monto ($):", min_value=0.0, format="%.2f")
    if st.button("➕ Ingresar Capital", use_container_width=True):
        if monto_in > 0:
            guardar_registro("Depósito Manual", monto_in, 0, "DEPÓSITO", monto_in, "Ingreso")
            st.rerun()
    
    st.divider()
    st.metric("Saldo Disponible", f"${saldo_actual:.2f}")
    
    # ESTO LIMPIARÁ TU CSV PARA EMPEZAR DE CERO CON LA LÓGICA NUEVA
    if st.button("🗑️ Resetear Todo (Limpiar CSV)"):
        pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"]).to_csv(ARCHIVO_DATOS, index=False)
        pd.DataFrame(columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)
        st.rerun()

st.title("🏆 Mi Control de Apuestas")

# --- NUEVA APUESTA ---
with st.container(border=True):
    with st.form("apuesta_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ev = c1.text_input("Evento:")
        mo = c2.number_input("Monto:", min_value=0.0, format="%.2f")
        cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f")
        if st.form_submit_button("🚀 Registrar Apuesta"):
            if ev and mo > 0 and mo <= saldo_actual:
                guardar_registro(ev, mo, cu, "PENDIENTE", -mo)
                pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                pd.DataFrame(pendientes).to_csv(ARCHIVO_PENDIENTES, index=False)
                st.rerun()

# --- GESTIÓN DE PENDIENTES ---
st.subheader("2️⃣ Apuestas Pendientes")
if not pendientes:
    st.info("No hay apuestas activas.")
else:
    for i, ap in enumerate(pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
            g, p, c = st.columns(3)
            if g.button("✅ GANADA", key=f"g{i}"):
                # LÓGICA SOLICITADA:
                # El balance es el PREMIO TOTAL (Capital + Ganancia)
                # Como ya restamos el capital al inicio, al sumarlo aquí, 
                # el "Balance Neto" total de la app queda solo en la ganancia.
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", ap['mo'] * ap['cu'])
                pendientes.pop(i)
                pd.DataFrame(pendientes if pendientes else columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)
                st.rerun()
            if p.button("❌ PERDIDA", key=f"p{i}"):
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", 0)
                pendientes.pop(i)
                pd.DataFrame(pendientes if pendientes else columns=["ev", "mo", "cu"]).to_csv(ARCHIVO_PENDIENTES, index=False)
                st.rerun()

# --- HISTORIAL Y GRÁFICO ---
st.divider()
if not df_hist.empty:
    st.subheader("📊 Evolución de Capital")
    df_grafico = df_hist.copy()
    df_grafico['Capital_Total'] = df_grafico['Balance_Num'].cumsum()
    st.line_chart(df_grafico, x="Fecha", y="Capital_Total")

    st.subheader("📝 Historial Detallado")
    st.dataframe(
        df_hist.iloc[::-1].style.format({"Monto": "{:.2f}", "Cuota": "{:.2f}", "Balance_Num": "{:.2f}"}),
        use_container_width=True, hide_index=True
    )
