import datetime
import requests
import yfinance as yf
import streamlit as st
from utils.data_manager import save_data

@st.fragment(run_every="30s")
def display_live_favourites():
    st.caption(f"⏱️ **Last market data fetch:** {datetime.datetime.now().strftime('%H:%M:%S')} (Auto-refreshes every 30s)")
    
    categories = {"📈 Equities & ETFs": [], "🪙 Crypto": [], "🛢️ Commodities & Forex": []}
    
    for fav in st.session_state.favourites:
        try:
            tkr = yf.Ticker(fav)
            info = tkr.info
            hist = tkr.history(period="6mo")
            
            if hist.empty: continue
                
            name = info.get('shortName', fav)
            q_type = info.get('quoteType', '')
            
            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            diff = current_price - prev_close
            pct_change = (diff / prev_close) * 100
            
            is_down = diff < 0
            
            if diff > 0:
                trend = f"🟢 ▲ +{pct_change:.2f}%"
            elif diff < 0:
                trend = f"🔴 ▼ {pct_change:.2f}%"
            else:
                trend = "⚪ 0.00%"
                
            avg_3m = hist['Close'].tail(63).mean()
            avg_6m = hist['Close'].mean()
            
            data_block = {
                "name": name,
                "ticker": fav,
                "price": current_price,
                "trend": trend,
                "avg_3m": avg_3m,
                "avg_6m": avg_6m,
                "is_down": is_down
            }
            
            if q_type in ['EQUITY', 'ETF', 'MUTUALFUND']:
                categories["📈 Equities & ETFs"].append(data_block)
            elif q_type == 'CRYPTOCURRENCY':
                categories["🪙 Crypto"].append(data_block)
            else:
                categories["🛢️ Commodities & Forex"].append(data_block)
        except:
            pass
            
    for cat_name, items in categories.items():
        if items:
            st.subheader(cat_name)
            cols = st.columns(3)
            for i, item in enumerate(items):
                with cols[i % 3]:
                    text_color = "#ff4b4b" if item['is_down'] else "inherit"
                    st.markdown(f"""
                    <div style="color: {text_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid rgba(128,128,128,0.3); background-color: rgba(0,0,0,0.1);">
                        <strong style="font-size: 1.1em;">{item['name']} ({item['ticker']})</strong><br>
                        <strong>Price:</strong> ${item['price']:.2f} {item['trend']}<br>
                        <span style="color: white; font-style: italic;">*3-Mo Avg:*</span> <span style="color: white;">${item['avg_3m']:.2f}</span> | 
                        <span style="color: white; font-style: italic;">*6-Mo Avg:*</span> <span style="color: white;">${item['avg_6m']:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)

def render_watchlist():
    search_col1, search_col2 = st.columns([4, 1])
    with search_col1:
        search_query = st.text_input("Type a company name or symbol (e.g., Apple, S&P, Gold):", label_visibility="collapsed")
    with search_col2:
        search_btn = st.button("🔍 Search")

    if search_btn and search_query:
        with st.spinner("Searching global markets..."):
            try:
                url = f"https://query2.finance.yahoo.com/v1/finance/search?q={search_query}"
                headers = {'User-Agent': 'Mozilla/5.0'}
                res = requests.get(url, headers=headers).json()
                quotes = res.get('quotes', [])
                if quotes:
                    options = {f"{q.get('shortname', q['symbol'])} ({q['symbol']})": q['symbol'] for q in quotes if 'symbol' in q}
                    st.session_state.search_results = options
                else:
                    st.warning("No matches found.")
            except:
                st.error("Search failed. Try again.")

    if "search_results" in st.session_state and st.session_state.search_results:
        add_col1, add_col2 = st.columns([4, 1])
        with add_col1:
            selected_name = st.selectbox("Select the exact asset to add:", list(st.session_state.search_results.keys()))
        with add_col2:
            st.write("") 
            st.write("") 
            if st.button("➕ Add to Watchlist"):
                ticker = st.session_state.search_results[selected_name]
                if ticker not in st.session_state.favourites:
                    st.session_state.favourites.append(ticker)
                    save_data()
                    st.success(f"Added {ticker}!")
                    del st.session_state.search_results
                    st.rerun()
                else:
                    st.info("Already in favourites.")

    st.markdown("---")
    
    with st.expander("Manage Watchlist (Remove Assets)"):
        for fav in st.session_state.favourites:
            c1, c2 = st.columns([1, 9])
            with c1:
                if st.button("❌ Remove", key=f"del_{fav}"):
                    st.session_state.favourites.remove(fav)
                    save_data()
                    st.rerun()
            with c2:
                st.write(f"**{fav}**")

    display_live_favourites()