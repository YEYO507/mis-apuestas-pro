import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuración de página
st.set_page_config(page_title="Control de Apuestas", layout="wide")

# Inicializar estados de memoria
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00
if 'pendientes' not in st.session_state:
    st.session_state.pendientes = []
if 'historial' not in st.session_state:
    st.session_state.historial = []

st.title("🏆 Mi Gestor de Apuestas")

# --- SIDEBAR: BILLETERA EDITABLE ---
with st.sidebar:
    st.header("💰 Gestión de Fondos")
    
    # Aquí es donde puedes editar el saldo manualmente
    nuevo_saldo = st.number_input("Editar Saldo Disponible ($):", 
                                   value=float(st.session_state.capital), 
                                   step=1.0, 
                                   format="%.2f")
    
    # Actualizamos el estado con lo que escribas
    st.session_state.capital = nuevo_saldo
    
    st.write("---")
    if st.button("Reiniciar App (Borra Todo)"):
        st.session_state.pendientes = []
        st.session_state.historial = []
        st.session_state.capital = 100.00
        st.rerun()

# --- 1. REGISTRO ---
st.subheader("1️⃣ Registrar Apuesta")
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1: evento = st.text_input("Evento:")
    with c2: monto = st.number_input("Monto a Apostar ($):", min_value=0.0, format="%.2f", key="input_monto")
    with c3: cuota = st.number_input("Cuota:", min_value=1.0, format="%.2f", key="input_cuota")
    
    if st.button("🚀 Guardar Apuesta Pendiente", use_container_width=True):
        if evento and monto > 0:
            if monto <= st.session_state.capital:
                st.session_state.capital -= monto 
                st.session_state.pendientes.append({"Evento": evento, "Monto": monto, "Cuota": cuota})
                st.success(f"Apuesta por {evento} guardada.")
                st.rerun()
            else:
                st.error("No tienes saldo suficiente en la billetera.")

# --- 2. RESOLVER ---
st.subheader("2️⃣ Resolver Apuestas en Curso")
if not st.session_state.pendientes:
    st.info("No hay apuestas pendientes.")
else:
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['Evento']} | Apostado: ${ap['Monto']:.2f}", expanded=True):
            col_gane, col_perdi, col_can = st.columns(3)
            
            # GANÉ: Devuelve el monto + ganancia neta
            if col_gane.button(f"✅ GANÉ (${(ap['Monto']*ap['Cuota']):.2f})", key=f"win_{i}", use_container_width=True):
                premio_total = ap['Monto'] * ap['Cuota']
                st.session_state.capital += premio_total 
                
                registro = {
                    "Evento": ap['Evento'],
                    "Monto": ap['Monto'],
                    "Resultado": "✅ GANADA",
                    "Balance": f"+${(premio_total - ap['Monto']):.2f}"
                }
                st.session_state.historial.append(registro)
                st.session_state.pendientes.pop(i)
                st.balloons()
                st.rerun()

            # PERDÍ: El dinero ya se restó al registrar, así que solo documentamos
            if col_perdi.button(f"❌ PERDÍ", key=f"loss_{i}", use_container_width=True):
                registro = {
                    "Evento": ap['Evento'],
                    "Monto": ap['Monto'],
                    "Resultado": "❌ PERDIDA",
                    "Balance": f"-${ap['Monto']:.2f}"
                }
                st.session_state.historial.append(registro)
                st.session_state.pendientes.pop(i)
                st.snow()
                st.rerun()
            
            # CANCELAR: Devuelve el dinero intacto
            if col_can.button(f"🔄 Cancelar", key=f"can_{i}", use_container_width=True):
                st.session_state.capital += ap['Monto']
                st.session_state.pendientes.pop(i)
                st.rerun()

# --- 3. HISTORIAL ---
st.subheader("📊 Historial de Resultados")
if st.session_state.historial:
    # Mostramos la tabla. Nota: Se invierte para ver la más reciente arriba
    df_historial = pd.DataFrame(st.session_state.historial)
    st.table(df_historial.iloc[::-1])
    # Configuración
st.set_page_config(page_title="Control de Apuestas Pro", layout="wide")

# Conexión a Google Sheets
url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTOhb-TqvYp4VbtGOWMdABdShujR2lzL7d2GtvJPs4ni7rSlVE9Sp5NU4o3UmynnVWsH8hXRbsp45ZK/pubhtml" # <--- PEGA TU LINK AQUÍ
conn = st.connection("gsheets", type=GSheetsConnection)

# Cargar datos existentes
df_historico = conn.read(spreadsheet=url)

# --- BILLETERA ---
if 'capital' not in st.session_state:
    st.session_state.capital = 100.00

with st.sidebar:
    st.header("💰 Billetera")
    st.session_state.capital = st.number_input("Saldo ($):", value=float(st.session_state.capital), step=1.0, format="%.2f")

# --- REGISTRO ---
st.subheader("1️⃣ Registrar Apuesta")
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1: evento = st.text_input("Evento:")
    with c2: monto = st.number_input("Monto ($):", min_value=0.0, format="%.2f")
    with c3: cuota = st.number_input("Cuota:", min_value=1.0, format="%.2f")
    
    if st.button("🚀 Guardar Pendiente", use_container_width=True):
        if evento and monto > 0:
            st.session_state.pendientes = st.session_state.get('pendientes', [])
            st.session_state.pendientes.append({"Evento": evento, "Monto": monto, "Cuota": cuota})
            st.rerun()

# --- RESOLVER Y GUARDAR ---
if st.session_state.get('pendientes'):
    for i, ap in enumerate(st.session_state.pendientes):
        with st.expander(f"⏳ {ap['Evento']}"):
            col1, col2 = st.columns(2)
            if col1.button(f"✅ GANÉ", key=f"w_{i}"):
                # Lógica de guardado en Google Sheets
                nueva_fila = pd.DataFrame([{
                    "Evento": ap['Evento'],
                    "Monto": ap['Monto'],
                    "Resultado": "✅ GANADA",
                    "Balance": f"+${(ap['Monto']*ap['Cuota'] - ap['Monto']):.2f}"
                }])
                df_final = pd.concat([df_historico, nueva_fila], ignore_index=True)
                conn.update(spreadsheet=url, data=df_final)
                st.session_state.pendientes.pop(i)
                st.success("¡Guardado en la nube!")
                st.rerun()
            # (Aquí iría el de perder, similar al de ganar)
