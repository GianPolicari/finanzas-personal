import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Inicializamos la conexión usando los secretos
# Streamlit cachea la conexión para que sea veloz
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase: Client = init_connection()

def load_transactions():
    """Descarga todos los movimientos desde la nube."""
    response = supabase.table("transactions").select("*").order("date", desc=True).execute()
    # Convertimos la respuesta JSON a DataFrame de Pandas
    df = pd.DataFrame(response.data)
    return df

def add_transaction(date, description, amount, currency, category, type_):
    """Sube un nuevo movimiento a la nube."""
    data = {
        "date": str(date),
        "description": description,
        "amount": amount,
        "currency": currency,
        "category": category,
        "type": type_
    }
    supabase.table("transactions").insert(data).execute()

def delete_transaction(tx_id):
    """Borra un movimiento de la nube por su ID."""
    supabase.table("transactions").delete().eq("id", tx_id).execute()