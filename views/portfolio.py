import requests
import pandas as pd
import streamlit as st
from utils.data_manager import save_data
from utils.finance_tools import get_asset_type

def highlight_unsaved(row):
    saved = st.session_state.portfolio
    is_saved = False
    if not saved.empty and row['Ticker'] in saved['Ticker'].values:
        saved_shares = saved.loc[saved['Ticker'] == row['Ticker'], 'Shares'].values
        if row['Shares'] in saved_shares:
            is_saved = True
    
    color = 'background-color: rgba(212, 175, 55, 0.2)' if not is_saved else ''
    return [color] * len(row)

def render_portfolio():
    # 1. SMART LOOKUP ADDER
    st.markdown("### Search & Add Asset")
    p_search_col1, p_search_col2 = st.columns([4, 1])
    with p_search_col1:
        p_search_query = st.text_input("Search for an asset to add (e.g. Nvidia, Gold):", key="port_search", label_visibility="collapsed")
    with p_search_col2:
        p_search_btn = st.button("🔍 Search", key="port_search_btn")

    if p_search_btn and p_search_query:
        with st.spinner("Searching..."):
            try:
                res = requests.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={p_search_query}", headers={'User-Agent': 'Mozilla/5.0'}).json()
                quotes = res.get('quotes', [])
                if quotes:
                    st.session_state.port_search_results = {f"{q.get('shortname', q['symbol'])} ({q['symbol']})": q['symbol'] for q in quotes if 'symbol' in q}
                else:
                    st.warning("No matches found.")
            except:
                st.error("Search failed.")

    if "port_search_results" in st.session_state and st.session_state.port_search_results:
        p_add_col1, p_add_col2, p_add_col3 = st.columns([3, 1, 1])
        with p_add_col1:
            p_selected_name = st.selectbox("Select exact asset:", list(st.session_state.port_search_results.keys()), key="port_sel")
        with p_add_col2:
            p_shares = st.number_input("Shares", min_value=0.0, step=1.0)
        with p_add_col3:
            st.write("")
            st.write("")
            if st.button("➕ Add to Staging", key="port_add_btn"):
                ticker = st.session_state.port_search_results[p_selected_name]
                with st.spinner("Fetching Asset Type..."):
                    asset_type = get_asset_type(ticker)
                
                new_row = {"Ticker": ticker, "Shares": p_shares, "Buy Date": pd.NaT, "Asset Type": asset_type}
                st.session_state.temp_portfolio = pd.concat([st.session_state.temp_portfolio, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"{ticker} staged! Remember to click Save below.")
                del st.session_state.port_search_results
                st.rerun()

    st.markdown("---")
    
    # 2. ROBUST PORTFOLIO EDITOR
    st.markdown("### Edit Holdings")
    st.markdown("Rows highlighted in <span style='color: #d4af37;'>**Amber**</span> have unsaved changes. They won't apply to the Agent until you hit **Save**.", unsafe_allow_html=True)
    
    # 🔴 THE BUG FIX: Force 'Buy Date' to proper datetime format before rendering the editor
    st.session_state.temp_portfolio['Buy Date'] = pd.to_datetime(st.session_state.temp_portfolio['Buy Date'], errors='coerce')
    
    styled_portfolio = st.session_state.temp_portfolio.style.apply(highlight_unsaved, axis=1)

    st.session_state.temp_portfolio = st.data_editor(
        styled_portfolio,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker Symbol", required=True),
            "Shares": st.column_config.NumberColumn("Total Shares", min_value=0.0, format="%.4f"),
            "Buy Date": st.column_config.DatetimeColumn("Buy Date & Time (Optional)"),
            "Asset Type": st.column_config.TextColumn("Asset Type", disabled=True)
        }
    )
    
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 3])
    with ctrl_col1:
        if st.button("💾 Save Changes", type="primary"):
            for idx, row in st.session_state.temp_portfolio.iterrows():
                if pd.isna(row.get('Asset Type')) or str(row.get('Asset Type')).strip() == "":
                    st.session_state.temp_portfolio.at[idx, 'Asset Type'] = get_asset_type(row['Ticker'])
                
                tkr = row['Ticker']
                if pd.notna(tkr) and str(tkr).strip() != "":
                    if tkr not in st.session_state.favourites:
                        st.session_state.favourites.append(tkr)
            
            st.session_state.portfolio = st.session_state.temp_portfolio.copy()
            save_data()
            st.success("Portfolio saved & Watchlist updated!")
            st.rerun()
    with ctrl_col2:
        if st.button("🔄 Revert to Saved"):
            st.session_state.temp_portfolio = st.session_state.portfolio.copy()
            st.rerun()
            
    st.markdown("---")
    
    # 3. BREAKDOWN BY TYPE
    st.markdown("### Portfolio Breakdown by Asset Type")
    if not st.session_state.portfolio.empty:
        types = st.session_state.portfolio['Asset Type'].unique()
        for t in types:
            if pd.notna(t) and t != "UNKNOWN":
                st.markdown(f"**{t}**")
                subset = st.session_state.portfolio[st.session_state.portfolio['Asset Type'] == t]
                st.dataframe(subset[['Ticker', 'Shares', 'Buy Date']], hide_index=True, use_container_width=True)