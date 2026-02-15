import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. Configuración de página
st.set_page_config(page_title="Control de Apuestas Pro", layout="wide")

# 2. Conexión a Google Sheets (Asegúrate de haber configurado tu link)
# Si aún no tienes el link, puedes probar la app localmente comentando las líneas de Sheets
url = "TU_LINK_DE_GOOGLE_SHEETS_AQUI" 

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_historico = conn.read(spreadsheet=url)
except:
    st.warning("⚠️ Nota: No se pudo conectar a Google Sheets. Los datos se guardarán solo temporalmente.")
    df_historico = pd.DataFrame(columns=["Evento", "Monto", "Resultado", "Balance"])

# 3. Inicializar estados de memoria
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []

# --- SIDEBAR: BILLETERA EDITABLE ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    st.session_state.capital = st.number_input("Editar Saldo ($):", 
                                               value=float(st.session_state.capital), 
                                               step=1.0, format="%.2f", key="wallet_input")
    st.divider()
    if st.button("Limpiar Pendientes"):
        st.session_state.pendientes = []
        st.rerun()

st.title("🏆 Mi Gestor de Apuestas")

# --- 1. REGISTRO (Aquí corregimos el error de ID duplicado) ---
st.subheader("1️⃣ Registrar Apuesta")
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        # Agregamos key="reg_evento" para evitar el error de tu imagen
        evento = st.text_input("Evento:", placeholder="Ej. Madrid vs Barca", key="reg_evento")
    with c2:
        monto = st.number_input("Monto ($):", min_value=0.0, format="%.2f", key="reg_monto")
    with c3:
        cuota = st.number_input("Cuota:", min_value=1.0, format="%.2f", key="reg_cuota")
    
    if st.button("🚀 Guardar Apuesta Pendiente", use_container_width=True):
        if evento and monto > 0:
            if monto <= st.session_state.capital:
                st.session_state.capital -= monto
                st.session_state.pendientes.append({"Evento": evento, "Monto": monto, "Cuota": cuota})
                st.rerun()
            else:
                st.error("Saldo insuficiente.")

# --- 2. RESOLVER ---
st.subheader("2️⃣ Resolver Apuestas en Curso")
if not st.session_state.pendientes:
    st.info("No hay apuestas pendientes.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['Evento']} | ${ap['Monto']:.2f}", expanded=True):
            col_g, col_p, col_c = st.columns(3)
            
            # BOTÓN GANAR
            if col_g.button(f"✅ GANÉ", key=f"btn_win_{i}", use_container_width=True):
                premio = ap['Monto'] * ap['Cuota']
                st.session_state.capital += premio
                nueva_fila = pd.DataFrame([{
                    "Evento": ap['Evento'], "Monto": ap['Monto'], 
                    "Resultado": "✅ GANADA", "Balance": f"+${(premio - ap['Monto']):.2f}"
                }])
                # Actualizar Sheets
                try:
                    df_final = pd.concat([df_historico, nueva_fila], ignore_index=True)
                    conn.update(spreadsheet=url, data=df_final)
                except: pass
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()

            # BOTÓN PERDER
            if col_p.button(f"❌ PERDÍ", key=f"btn_loss_{i}", use_container_width=True):
                nueva_fila = pd.DataFrame([{
                    "Evento": ap['Evento'], "Monto": ap['Monto'], 
                    "Resultado": "❌ PERDIDA", "Balance": f"-${ap['Monto']:.2f}"
                }])
                try:
                    df_final = pd.concat([df_historico, nueva_fila], ignore_index=True)
                    conn.update(spreadsheet=url, data=df_final)
                except: pass
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()

            if col_c.button(f"🔄 Cancelar", key=f"btn_can_{i}", use_container_width=True):
                st.session_state.capital += ap['Monto']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- 3. HISTORIAL ---
st.subheader("📊 Historial de Resultados")
st.dataframe(df_historico.iloc[::-1], use_container_width=True)
