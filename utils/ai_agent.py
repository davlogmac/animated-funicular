import os
import streamlit as st
from google import genai
from google.genai import types
from utils.finance_tools import (
    get_stock_price, get_company_fundamentals, 
    get_recent_news, get_technical_summary, get_portfolio_holdings,
    get_watchlist, add_to_watchlist, remove_from_watchlist, 
    update_portfolio, remove_from_portfolio
)

def initialize_agent():
    if "gemini_client" not in st.session_state:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
        
        if not api_key:
            st.error("API Key not found. Please set GEMINI_API_KEY in Streamlit secrets or your .env file.")
            st.stop()
            
        st.session_state.gemini_client = genai.Client(api_key=api_key)
        
    if "chat_session" not in st.session_state:
        agent_tools = [
            get_stock_price, get_company_fundamentals, 
            get_recent_news, get_technical_summary, get_portfolio_holdings,
            get_watchlist, add_to_watchlist, remove_from_watchlist, 
            update_portfolio, remove_from_portfolio
        ]
        
        # 1. Define the System Instruction
        system_instruction = (
            "You are an AI market assistant integrated into a user's financial dashboard. "
            "You have direct access to tools that can view and modify the user's portfolio and watchlist. "
            "When a user asks to buy, sell, add, or remove an asset, you MUST use the provided tools to execute the action. "
            "Never tell the user to do it manually."
        )
        
        # 2. Add the instruction to the Gemini config
        st.session_state.chat_session = st.session_state.gemini_client.chats.create(
            model="gemini-3.5-flash-lite",
            config=types.GenerateContentConfig(
                tools=agent_tools,
                system_instruction=system_instruction
            )
        )
        st.session_state.messages = []