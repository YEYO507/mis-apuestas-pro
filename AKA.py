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

# --- CARGA Y LIMPIEZA DE DATOS ---
try:
    df_hist = pd.read_csv(ARCHIVO_DATOS)
    # FILTRO CLAVE: Quitar las filas 'PENDIENTE' que ya tienen un resultado final (Ganada/Perdida/Cancelada)
    # Buscamos eventos que ya no estén pendientes para limpiar el historial visual
    eventos_finalizados = df_hist[df_hist['Resultado'].isin(['GANADA', 'PERDIDA', 'CANCELADA'])]['Evento'].unique()
    # Solo mantenemos las filas PENDIENTE si su evento NO está en la lista de finalizados
    df_hist_limpio = df_hist[~((df_hist['Resultado'] == 'PENDIENTE') & (df_hist['Evento'].isin(eventos_finalizados)))]
except:
    df_hist_limpio = pd.DataFrame(columns=["Fecha", "Evento", "Monto", "Cuota", "Resultado", "Balance_Num", "Tipo"])

saldo_actual = round(df_hist_limpio["Balance_Num"].sum(), 2)

try:
    pendientes = pd.read_csv(ARCHIVO_PENDIENTES).to_dict('records')
except:
    pendientes = []

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    monto_ingreso = st.number_input("Monto a Ingresar ($):", min_value=0.0, step=10.0, format="%.2f")
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

# --- NUEVA APUESTA ---
with st.container(border=True):
    st.subheader("1️⃣ Registrar Nueva Apuesta")
    with st.form("form_apuesta", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        ev = col1.text_input("Evento:")
        mo = col2.number_input("Monto ($):", min_value=0.0, format="%.2f")
        cu = col3.number_input("Cuota:", min_value=1.0, format="%.2f")
        if st.form_submit_button("🚀 Apostar Ahora", use_container_width=True):
            if ev and mo > 0 and mo <= saldo_actual:
                guardar_registro(ev, mo, cu, "PENDIENTE", -mo)
                pendientes.append({"ev": ev, "mo": mo, "cu": cu})
                actualizar_pendientes(pendientes)
                st.rerun()
            elif mo > saldo_actual:
                st.error("Saldo insuficiente.")

# --- APUESTAS PENDIENTES (TARJETAS) ---
st.subheader("2️⃣ Apuestas en Curso")
if not pendientes:
    st.info("No hay apuestas pendientes.")
else:
    for i, ap in enumerate(pendientes):
        with st.expander(f"⏳ {ap['ev']} | ${ap['mo']:.2f}", expanded=True):
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

# --- ESTADÍSTICAS Y GRÁFICO ---
st.divider()
if not df_hist_limpio.empty:
    # Métricas de conteo
    ganadas = len(df_hist_limpio[df_hist_limpio['Resultado'] == 'GANADA'])
    perdidas = len(df_hist_limpio[df_hist_limpio['Resultado'] == 'PERDIDA'])
    
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("✅ Ganadas", ganadas)
    col_m2.metric("❌ Perdidas", perdidas)
    col_m3.metric("📈 Rendimiento", f"{((ganadas/(ganadas+perdidas))*100 if (ganadas+perdidas)>0 else 0):.1f}%")

    st.subheader("📊 Evolución del Saldo")
    df_grafico = df_hist_limpio.copy()
    df_grafico['Saldo_Acumulado'] = df_grafico['Balance_Num'].cumsum()
    st.line_chart(df_grafico, x="Fecha", y="Saldo_Acumulado")

    st.subheader("📝 Historial de Movimientos")
    
    # Formateo visual de la tabla
    def color_rows(row):
        colores = {'GANADA': '#2ecc71', 'PERDIDA': '#e74c3c', 'PENDIENTE': '#f39c12', 'DEPÓSITO': '#3498db'}
        return [f'background-color: {colores.get(row.Resultado, "")}; color: white'] * len(row)

    # Mostrar tabla con 2 decimales y sin duplicados de pendientes finalizados
    st.dataframe(
        df_hist_limpio.iloc[::-1].style.apply(color_rows, axis=1).format({
            "Monto": "{:.2f}",
            "Cuota": "{:.2f}",
            "Balance_Num": "{:.2f}"
        }),
        use_container_width=True,
        hide_index=True
    )
