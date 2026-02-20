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
    pd.concat([df_actual, nuevo], ignore_index=True).to_csv(ARCHIVO_DATOS, index=False)

def actualizar_pendientes(lista_pendientes):
    df_p = pd.DataFrame(lista_pendientes) if lista_pendientes else pd.DataFrame(columns=["ev", "mo", "cu"])
    df_p.to_csv(ARCHIVO_PENDIENTES, index=False)

inicializar_archivos()

# --- CARGA Y FILTRADO DE DATOS ---
try:
    df_hist_base = pd.read_csv(ARCHIVO_DATOS)
    
    # IMPORTANTE: Para el saldo y el historial, eliminamos la fila "PENDIENTE" 
    # de un evento si ese mismo evento ya tiene un resultado (GANADA/PERDIDA/CANCELADA)
    eventos_resueltos = df_hist_base[df_hist_base['Resultado'].isin(['GANADA', 'PERDIDA', 'CANCELADA'])]['Evento'].tolist()
    
    # Creamos el dataframe limpio: no incluimos 'PENDIENTE' si el evento ya se resolvió
    df_hist = df_hist_base[~((df_hist_base['Resultado'] == 'PENDIENTE') & (df_hist_base['Evento'].isin(eventos_resueltos)))]
except:
    df_hist = pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"])

# El saldo se calcula sobre el historial limpio
saldo_actual = round(df_hist["Balance_Num"].sum(), 2) if not df_hist.empty else 0.0

try:
    pendientes = pd.read_csv(ARCHIVO_PENDIENTES).to_dict('records')
except:
    pendientes = []

# --- INTERFAZ LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_ingreso = st.number_input("Monto a Ingresar ($):", min_value=0.0, format="%.2f")
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

# --- 1. REGISTRO ---
with st.container(border=True):
    st.subheader("1️⃣ Nueva Apuesta")
    with st.form("f_apuesta", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        ev = c1.text_input("Evento:")
        mo = c2.number_input("Monto ($):", min_value=0.0, format="%.2f")
        cu = c3.number_input("Cuota:", min_value=1.0, format="%.2f")
        if st.form_submit_button("🚀 Registrar", use_container_width=True):
            if ev and mo > 0 and mo <= saldo_actual:
                guardar_registro(ev, mo, cu, "PENDIENTE", -mo)
                pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                actualizar_pendientes(pendientes)
                st.rerun()
            elif mo > saldo_actual:
                st.error("Saldo insuficiente.")

# --- 2. EN CURSO ---
st.subheader("2️⃣ Apuestas Pendientes")
if not pendientes:
    st.info("No hay apuestas activas.")
else:
    for i, ap in enumerate(pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
            col_g, col_p, col_c = st.columns(3)
            
            if col_g.button("✅ GANADA", key=f"win_{i}"):
                # LÓGICA DE DIFERENCIAL (GANANCIA NETA)
                # Si apostaste 5 a cuota 2, el premio es 10. 
                # Como ya restamos 5 al inicio, para que el saldo suba a 25, 
                # sumamos los 10 (Premio Bruto). 
                # El historial mostrará el Balance_Num de la ganancia total recuperada.
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "GANADA", ap['mo'] * ap['cu'])
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()
                
            if col_p.button("❌ PERDIDA", key=f"loss_{i}"):
                # No sumamos nada porque el monto ya se restó al inicio
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "PERDIDA", 0)
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()
                
            if col_c.button("🔄 Cancelar", key=f"can_{i}"):
                # Devolvemos el monto apostado
                guardar_registro(ap['ev'], ap['mo'], ap['cu'], "CANCELADA", ap['mo'])
                pendientes.pop(i)
                actualizar_pendientes(pendientes)
                st.rerun()

# --- 3. ESTADÍSTICAS Y TABLA ---
st.divider()
if not df_hist.empty:
    # Métricas
    g = len(df_hist[df_hist['Resultado'] == 'GANADA'])
    p = len(df_hist[df_hist['Resultado'] == 'PERDIDA'])
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("✅ Ganadas", g)
    col_b.metric("❌ Perdidas", p)
    col_c.metric("💰 Balance Total", f"${saldo_actual:.2f}")

    st.subheader("📊 Gráfico de Rendimiento")
    df_graf = df_hist.copy()
    df_graf['Saldo_Evolucion'] = df_graf['Balance_Num'].cumsum()
    st.line_chart(df_graf, x="Fecha", y="Saldo_Evolucion")

    st.subheader("📝 Historial Final (Limpio)")
    
    def color_filas(row):
        color = {'GANADA': '#2ecc71', 'PERDIDA': '#e74c3c', 'PENDIENTE': '#f39c12', 'DEPÓSITO': '#3498db'}
        return [f'background-color: {color.get(row.Resultado, "")}; color: white'] * len(row)

    st.dataframe(
        df_hist.iloc[::-1].style.apply(color_filas, axis=1).format({
            "Monto": "{:.2f}", "Cuota": "{:.2f}", "Balance_Num": "{:.2f}"
        }),
        use_container_width=True, hide_index=True
    )
