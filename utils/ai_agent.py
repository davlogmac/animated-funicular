import os
import streamlit as st
from google import genai
from google.genai import types
from utils.finance_tools import (
    get_stock_price, get_company_fundamentals, 
    get_recent_news, get_technical_summary, get_portfolio_holdings,
    get_watchlist
)

def initialize_agent():
    if "gemini_client" not in st.session_state:
        # Check Streamlit secrets first (Cloud), fallback to os.environ (Local .env)
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        
        if not api_key:
            st.error("API Key not found. Please set GEMINI_API_KEY in Streamlit secrets or your .env file.")
            st.stop()
            
        st.session_state.gemini_client = genai.Client(api_key=api_key)
        
    if "chat_session" not in st.session_state:
        agent_tools = [
            get_stock_price, get_company_fundamentals, 
            get_recent_news, get_technical_summary, get_portfolio_holdings,
            get_watchlist 
        ]
        
        st.session_state.chat_session = st.session_state.gemini_client.chats.create(
            model="gemini-3.5-flash",
            config=types.GenerateContentConfig(tools=agent_tools)
        )
        st.session_state.messages = []