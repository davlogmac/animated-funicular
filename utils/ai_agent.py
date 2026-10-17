import streamlit as st
from google import genai
from google.genai import types
from utils.finance_tools import (
    get_stock_price, get_company_fundamentals, 
    get_recent_news, get_technical_summary, get_portfolio_holdings,
    get_watchlist # <-- Import the new tool
)

def initialize_agent():
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = genai.Client()
        
    if "chat_session" not in st.session_state:
        # Add get_watchlist to the tools array so Gemini can use it
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