import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import database as db

# --- CONFIGURACIÓN MINIMALISTA ---
st.set_page_config(
    page_title="Finanzas",
    page_icon="💳",
    layout="centered", # Centrado es más elegante para móvil
    initial_sidebar_state="collapsed" # Ocultamos sidebar para más limpieza
)

# Estilo CSS para forzar look limpio y tarjetas
st.markdown("""
<style>
    .stMetric {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #41444e;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("Finanzas G&C")
st.caption(f"📅 {datetime.now().strftime('%B %Y').capitalize()}")

# --- CARGAR DATOS ---
try:
    df = db.load_transactions()
except Exception as e:
    st.error("Error conectando a Supabase. Revisa tus secrets.toml")
    df = pd.DataFrame()

# --- INPUT RÁPIDO (Top de la página para móvil) ---
with st.expander("➕ Nuevo Movimiento", expanded=False):
    with st.form("entry_form", clear_on_submit=True):
        col_date, col_type = st.columns([1, 1])
        date = col_date.date_input("Fecha", datetime.today())
        tx_type = col_type.selectbox("Tipo", ["Gasto", "Ingreso"])
        
        desc = st.text_input("Descripción", placeholder="Ej: Supermercado")
        
        col_monto, col_divisa = st.columns([2, 1])
        amount = col_monto.number_input("Monto", min_value=0.0, step=100.0, format="%.2f")
        currency = col_divisa.selectbox("Moneda", ["ARS", "USD"])
        
        # Categorías inteligentes
        categories = [
            "Galicia Visa", "Galicia Master", 
            "Gastos Fijos", "Supermercado", 
            "Salidas", "Sueldo", "Varios"
        ]
        category = st.selectbox("Categoría", categories)
        
        submitted = st.form_submit_button("Guardar Movimiento", use_container_width=True)
        
        if submitted:
            if amount > 0:
                # Convertimos 'Gasto'/'Ingreso' a 'Expense'/'Income' para la DB
                db_type = 'Income' if tx_type == "Ingreso" else 'Expense'
                db.add_transaction(date, desc, amount, currency, category, db_type)
                st.toast("✅ Guardado en la nube")
                st.rerun()
            else:
                st.warning("Ingresa un monto válido.")

st.divider()

# --- DASHBOARD ---
if not df.empty:
    # Conversiones
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'])
    
    # Filtro de Mes
    current_month = datetime.now().strftime('%Y-%m')
    df['month'] = df['date'].dt.strftime('%Y-%m')
    
    # --- LOGICA DE TU EXCEL (SEPARACION) ---
    mask_month = df['month'] == current_month
    df_mes = df[mask_month]
    
    # 1. Saldos y Totales
    ingresos = df_mes[df_mes['type'] == 'Income']['amount'].sum()
    
    # Gastos Tarjetas
    visa = df_mes[(df_mes['category'] == 'Galicia Visa') & (df_mes['type'] == 'Expense')]['amount'].sum()
    master = df_mes[(df_mes['category'] == 'Galicia Master') & (df_mes['type'] == 'Expense')]['amount'].sum()
    
    # Gastos Fijos
    fijos = df_mes[df_mes['category'] == 'Gastos Fijos']['amount'].sum()
    
    # Otros Gastos (Resto)
    otros = df_mes[
        (~df_mes['category'].isin(['Galicia Visa', 'Galicia Master', 'Gastos Fijos'])) & 
        (df_mes['type'] == 'Expense')
    ]['amount'].sum()
    
    total_gastos = visa + master + fijos + otros
    saldo = ingresos - total_gastos

    # --- VISUALIZACIÓN DE MÉTRICAS ---
    # Fila 1: El número más importante
    st.metric("Saldo Disponible", f"${saldo:,.2f}", delta=saldo)
    
    # Fila 2: Tarjetas (Tu dolor de cabeza principal)
    c1, c2 = st.columns(2)
    c1.metric("💳 Visa", f"${visa:,.2f}", delta=-visa, delta_color="inverse")
    c2.metric("💳 Master", f"${master:,.2f}", delta=-master, delta_color="inverse")
    
    # Fila 3: Fijos y Otros
    c3, c4 = st.columns(2)
    c3.metric("🏠 Fijos", f"${fijos:,.2f}", delta=-fijos, delta_color="inverse")
    c4.metric("💸 Varios", f"${otros:,.2f}", delta=-otros, delta_color="inverse")

    st.divider()

    # --- GRÁFICO DONA (Más minimalista que barras) ---
    st.subheader("Distribución")
    gastos_df = df_mes[df_mes['type'] == 'Expense']
    
    if not gastos_df.empty:
        # Agrupamos por categoría para el gráfico
        chart_data = gastos_df.groupby('category')['amount'].sum().reset_index()
        
        fig = px.pie(chart_data, values='amount', names='category', hole=0.6, 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=False)
        # Texto en el centro
        fig.add_annotation(text=f"${total_gastos:,.0f}", x=0.5, y=0.5, font_size=20, showarrow=False)
        
        st.plotly_chart(fig, use_container_width=True)

    # --- LISTA RECIENTE (Compacta) ---
    st.subheader("Historial")
    
    for index, row in df.head(10).iterrows():
        # Icono según tipo
        icon = "💰" if row['type'] == 'Income' else "💸"
        if "Visa" in row['category']: icon = "💳"
        if "Master" in row['category']: icon = "💳"
        
        # Color del monto
        color = "green" if row['type'] == 'Income' else "red"
        sign = "+" if row['type'] == 'Income' else "-"
        
        # Layout de fila customizado
        cols = st.columns([0.15, 0.55, 0.3])
        cols[0].write(f"## {icon}")
        cols[1].markdown(f"**{row['description']}**\n\n<span style='color:gray; font-size:0.8em'>{row['date'].strftime('%d/%m')} • {row['category']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<div style='text-align:right; color:{color}; font-weight:bold'>{sign}${row['amount']:,.0f}</div>", unsafe_allow_html=True)
        
        # Botón borrar discreto
        if cols[2].button("🗑", key=f"del_{row['id']}"):
            db.delete_transaction(row['id'])
            st.rerun()
        
        st.markdown("---")

else:
    st.info("👋 ¡Bienvenido! Agrega tu primer movimiento arriba.")