import yfinance as yf
import pandas as pd
import streamlit as st
from utils.data_manager import save_data

def get_asset_type(ticker: str) -> str:
    try:
        return yf.Ticker(ticker).info.get('quoteType', 'UNKNOWN')
    except:
        return 'UNKNOWN'

def get_stock_price(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'].iloc[-1]
        return f"Current price of {ticker.upper()}: ${price:.2f}"
    except Exception as e:
        return f"Error fetching price for {ticker}: {e}"

def get_company_fundamentals(ticker: str) -> str:
    try:
        info = yf.Ticker(ticker).info
        market_cap = info.get('marketCap', 'N/A')
        pe_ratio = info.get('trailingPE', 'N/A')
        high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
        low_52 = info.get('fiftyTwoWeekLow', 'N/A')
        sector = info.get('sector', 'N/A')

        if isinstance(market_cap, (int, float)):
            market_cap = f"${market_cap / 1e9:.2f} Billion"

        return (
            f"Fundamentals for {ticker.upper()} ({sector}):\n"
            f"• Market Cap: {market_cap}\n"
            f"• P/E Ratio: {pe_ratio}\n"
            f"• 52-Week Range: ${low_52} - ${high_52}"
        )
    except Exception as e:
        return f"Error fetching fundamentals for {ticker}: {e}"

def get_recent_news(ticker: str) -> str:
    try:
        stock = yf.Ticker(ticker)
        news_items = stock.news[:3]
        if not news_items:
            return f"No recent news found for {ticker}."
        headlines = [f"Latest headlines for {ticker.upper()}:"]
        for item in news_items:
            headlines.append(f"• {item.get('title', 'No Title')}")
        return "\n".join(headlines)
    except Exception as e:
        return f"Error fetching news for {ticker}: {e}"

def get_technical_summary(ticker: str) -> str:
    try:
        history = yf.Ticker(ticker).history(period="1y")
        if len(history) < 200:
            return f"Not enough history to calculate 200-day SMA for {ticker}."
        
        sma_50 = history['Close'].rolling(window=50).mean().iloc[-1]
        sma_200 = history['Close'].rolling(window=200).mean().iloc[-1]
        current_price = history['Close'].iloc[-1]
        signal = "Bullish Uptrend" if sma_50 > sma_200 else "Bearish Downtrend"

        return (
            f"Technical Indicators for {ticker.upper()}:\n"
            f"• Current Price: ${current_price:.2f}\n"
            f"• 50-Day SMA: ${sma_50:.2f}\n"
            f"• 200-Day SMA: ${sma_200:.2f}\n"
            f"• Trend Signal: {signal}"
        )
    except Exception as e:
        return f"Error calculating technicals for {ticker}: {e}"

def get_portfolio_holdings() -> str:
    df = st.session_state.portfolio
    if df.empty:
        return "The user's portfolio is currently empty."
        
    holdings_str = "User's Portfolio:\n"
    for index, row in df.iterrows():
        ticker = row.get('Ticker', '')
        shares = row.get('Shares', 0)
        buy_date = row.get('Buy Date', '')
        
        if pd.notna(ticker) and str(ticker).strip() != "":
            date_str = f" (Bought: {buy_date.strftime('%Y-%m-%d %H:%M')})" if pd.notna(buy_date) else ""
            holdings_str += f"• {ticker}: {shares} shares{date_str}\n"
    return holdings_str

def get_watchlist() -> str:
    """Returns the user's current Smart Watchlist (Favourites) tickers."""
    favs = st.session_state.get('favourites', [])
    if not favs:
        return "The user's watchlist is currently empty."
        
    return "User's Watchlist (Favourites):\n" + "\n".join([f"• {tkr}" for tkr in favs])

def add_to_watchlist(ticker: str) -> str:
    """Adds a stock ticker to the user's Smart Watchlist."""
    ticker = ticker.upper().strip()
    if ticker not in st.session_state.favourites:
        st.session_state.favourites.append(ticker)
        save_data()
        return f"Successfully added {ticker} to your watchlist."
    return f"{ticker} is already in your watchlist."

def remove_from_watchlist(ticker: str) -> str:
    """Removes a stock ticker from the user's Smart Watchlist."""
    ticker = ticker.upper().strip()
    if ticker in st.session_state.favourites:
        st.session_state.favourites.remove(ticker)
        save_data()
        return f"Successfully removed {ticker} from your watchlist."
    return f"{ticker} was not found in your watchlist."

def update_portfolio(ticker: str, shares: float, buy_date: str = "") -> str:
    """Adds a new stock or updates the share count of an existing stock in the user's portfolio. buy_date is optional (YYYY-MM-DD)."""
    ticker = ticker.upper().strip()
    df = st.session_state.portfolio
    
    asset_type = get_asset_type(ticker)
    parsed_date = pd.to_datetime(buy_date, errors='coerce') if buy_date else pd.NaT

    if ticker in df['Ticker'].values:
        df.loc[df['Ticker'] == ticker, ['Shares', 'Buy Date']] = [shares, parsed_date]
        action = "updated"
    else:
        new_row = pd.DataFrame([{"Ticker": ticker, "Shares": shares, "Buy Date": parsed_date, "Asset Type": asset_type}])
        df = pd.concat([df, new_row], ignore_index=True)
        action = "added"
        
    st.session_state.portfolio = df
    st.session_state.temp_portfolio = df.copy() # Sync the staging editor so the UI doesn't overwrite it
    save_data()
    
    return f"Successfully {action} {ticker} in your portfolio ({shares} shares)."

def remove_from_portfolio(ticker: str) -> str:
    """Removes a stock entirely from the user's portfolio."""
    ticker = ticker.upper().strip()
    df = st.session_state.portfolio
    
    if ticker in df['Ticker'].values:
        st.session_state.portfolio = df[df['Ticker'] != ticker].reset_index(drop=True)
        st.session_state.temp_portfolio = st.session_state.portfolio.copy()
        save_data()
        return f"Successfully removed {ticker} from your portfolio."
    return f"{ticker} was not found in your portfolio."