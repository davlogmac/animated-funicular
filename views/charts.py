import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

def render_charts():
    chart_col1, chart_col2, chart_col3 = st.columns([2, 2, 1])
    with chart_col1:
        dropdown_options = ["-- Use Custom Ticker --"] + st.session_state.favourites
        selected_chart = st.selectbox("Select from Favourites:", dropdown_options)
    
    with chart_col2:
        if selected_chart == "-- Use Custom Ticker --":
            chart_ticker = st.text_input("Or Enter Ticker:", "AAPL").upper()
        else:
            chart_ticker = selected_chart
            st.text_input("Selected Ticker:", chart_ticker, disabled=True)
            
    with chart_col3:
        period = st.selectbox("Timeframe:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

    if st.button("Generate Interactive Chart"):
        with st.spinner(f"Loading data for {chart_ticker}..."):
            data = yf.Ticker(chart_ticker).history(period=period)
            
            if data.empty:
                st.error("No data found. Check the ticker symbol.")
            else:
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=data.index,
                    open=data['Open'], high=data['High'],
                    low=data['Low'], close=data['Close'],
                    name='Price'
                ))
                
                if len(data) >= 50:
                    sma_50 = data['Close'].rolling(window=50).mean()
                    fig.add_trace(go.Scatter(
                        x=data.index, y=sma_50, 
                        line=dict(color='orange', width=2), 
                        name='50-Day SMA'
                    ))
                
                fig.update_layout(
                    title=f"{chart_ticker} Price History",
                    yaxis_title="Price",
                    xaxis_rangeslider_visible=False,
                    template="plotly_dark",
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)