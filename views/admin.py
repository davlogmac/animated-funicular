import streamlit as st
import sqlite3
import pandas as pd
from utils.auth import DB_FILE

def render_admin():
    st.title("🔐 Admin Control Panel")
    
    tab1, tab2 = st.tabs(["👥 User Management", "📋 System Logs"])
    
    # ---------------------------------------------------------
    # USER MANAGEMENT TAB
    # ---------------------------------------------------------
    with tab1:
        st.markdown("View all registered users and their system roles.")
        
        conn = sqlite3.connect(DB_FILE)
        df_users = pd.read_sql_query("SELECT email, is_admin FROM users", conn)
        conn.close()
        
        df_users['is_admin'] = df_users['is_admin'].apply(lambda x: "🟢 Admin" if x == 1 else "👤 User")
        df_users.rename(columns={"email": "Registered Email", "is_admin": "Account Role"}, inplace=True)
        
        st.dataframe(df_users, hide_index=True, use_container_width=True)

    # ---------------------------------------------------------
    # SYSTEM LOGS TAB
    # ---------------------------------------------------------
    with tab2:
        colA, colB = st.columns([4, 1])
        with colA:
            st.markdown("Audit trail of security and system events.")
        with colB:
            if st.button("🔄 Refresh Logs"):
                st.rerun()

        conn = sqlite3.connect(DB_FILE)
        # Fetch the 100 most recent events
        df_logs = pd.read_sql_query('''
            SELECT timestamp, event_type, user_email, details 
            FROM logs 
            ORDER BY timestamp DESC 
            LIMIT 100
        ''', conn)
        conn.close()
        
        if df_logs.empty:
            st.info("No system events logged yet.")
        else:
            # Format columns for readability
            df_logs.rename(columns={
                "timestamp": "UTC Time",
                "event_type": "Event Type",
                "user_email": "User Email",
                "details": "Details"
            }, inplace=True)
            
            st.dataframe(df_logs, hide_index=True, use_container_width=True)