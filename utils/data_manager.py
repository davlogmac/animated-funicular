import pandas as pd
import streamlit as st
from utils.auth import get_user_data, update_user_data

def save_data():
    """Saves the current portfolio and favourites to the user's database row."""
    # Safety check: don't save if no user is logged in
    if "current_user" not in st.session_state or not st.session_state.current_user:
        return
        
    df_to_save = st.session_state.portfolio.copy()
    
    if 'Buy Date' in df_to_save.columns:
        df_to_save['Buy Date'] = df_to_save['Buy Date'].astype(str).replace('NaT', '')

    portfolio_dict = df_to_save.to_dict(orient="records")
    
    update_user_data(st.session_state.current_user["email"], portfolio_dict, st.session_state.favourites)

def initialize_session_state():
    """Sets up the application state based on the logged-in user."""
    
    # GUARDRAIL: If there is no user logged in yet, stop here. Do not crash.
    if "current_user" not in st.session_state or not st.session_state.current_user:
        return

    if "data_loaded" not in st.session_state:
        saved_data = get_user_data(st.session_state.current_user["email"])
        
        df = pd.DataFrame(saved_data["portfolio"])
        if df.empty:
            df = pd.DataFrame(columns=["Ticker", "Shares", "Buy Date", "Asset Type"])
        else:
            if 'Buy Date' not in df.columns:
                df['Buy Date'] = pd.NaT
            else:
                df['Buy Date'] = pd.to_datetime(df['Buy Date'], errors='coerce')
                
            if 'Asset Type' not in df.columns:
                df['Asset Type'] = "UNKNOWN"
                
        st.session_state.portfolio = df
        st.session_state.favourites = saved_data["favourites"]
            
        st.session_state.data_loaded = True

    if "temp_portfolio" not in st.session_state:
        st.session_state.temp_portfolio = st.session_state.portfolio.copy()