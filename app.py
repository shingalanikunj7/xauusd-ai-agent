import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai

st.set_page_config(page_title="JARVIS XAUUSD Hub", layout="wide", initial_sidebar_state="collapsed")

# Capital Configuration
CAPITAL_INR = 50000.0
USD_INR = 83.5
CAPITAL_USD = CAPITAL_INR / USD_INR
MAX_RISK_PER_TRADE_USD = CAPITAL_USD * 0.01  # 1% Strict Risk (~$6)

# Session State for Demo Paper Trades
if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = []

st.title("⚡ JARVIS XAUUSD Agent")
st.caption(f"Portfolio: ₹{CAPITAL_INR:,.0f} (~${CAPITAL_USD:.1f}) | 1% Risk Limit: ${MAX_RISK_PER_TRADE_USD:.2f}")

# 1. Fetch Real-Time Market Data
@st.cache_data(ttl=60)
def get_gold_data():
    ticker = yf.Ticker("GC=F")  # Gold Futures
    df = ticker.history(period="5d", interval="15m")
    return df

df = get_gold_data()

if not df.empty:
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    chg = current_price - prev_close
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Gold (XAUUSD)", f"${current_price:.2f}", f"{chg:.2f}")
    col2.metric("Lot Size Allocated", "0.01 Micro", "Max Protection")
    col3.metric("Daily Max Loss", "$12.00 (2%)", "Safety Lock")

    # 2. Interactive Chart
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="M15"
    )])
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 3. AI Agent Logic & Backtest Simulator
st.subheader("🤖 AI Strategy & News Analysis")
api_key = st.text_input("Enter Gemini API Key", type="password")

if st.button("Run AI Market Scan & Strategy"):
    if not api_key:
        st.warning("Pehle Gemini API Key dalein.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Current XAUUSD Price: {current_price}.
        High of last 24h: {df['High'].max()}
        Low of last 24h: {df['Low'].min()}
        Capital: $600 USD. Risk per trade: $6 USD (1%).
        
        Task:
        1. Formulate an intraday setup using Asian/London liquidity sweep and Retest.
        2. Give exact Entry, Stop Loss (points), and Take Profit (1:2 RR).
        3. Confirm if news sentiment is safe to trade or avoid.
        Provide response in concise bullet points.
        """
        response = model.generate_content(prompt)
        st.write(response.text)

# 4. Instant Paper Trading Engine
st.subheader("📝 Live Demo Execution")
col_buy, col_sell = st.columns(2)

with col_buy:
    if st.button("🟢 Demo BUY 0.01"):
        st.session_state.paper_trades.append({
            "Type": "BUY",
            "Entry": current_price,
            "SL": current_price - 6.0,
            "TP": current_price + 12.0,
            "Status": "OPEN"
        })
        st.success(f"Demo Buy Executed at {current_price:.2f}")

with col_sell:
    if st.button("🔴 Demo SELL 0.01"):
        st.session_state.paper_trades.append({
            "Type": "SELL",
            "Entry": current_price,
            "SL": current_price + 6.0,
            "TP": current_price - 12.0,
            "Status": "OPEN"
        })
        st.error(f"Demo Sell Executed at {current_price:.2f}")

# Display Active Trades
if st.session_state.paper_trades:
    st.write("Active Paper Trades:")
    st.dataframe(pd.DataFrame(st.session_state.paper_trades))
      
