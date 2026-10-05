import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import google.generativeai as genai
import requests

st.set_page_config(page_title="JARVIS XAUUSD Hub v2", layout="wide", initial_sidebar_state="collapsed")

# Capital Configuration
CAPITAL_INR = 50000.0
USD_INR = 83.5
CAPITAL_USD = CAPITAL_INR / USD_INR
MAX_RISK_PER_TRADE_USD = CAPITAL_USD * 0.01  # 1% Strict Risk (~$6)

if "paper_trades" not in st.session_state:
    st.session_state.paper_trades = []

st.title("⚡ JARVIS XAUUSD Agent Pro")
st.caption(f"Portfolio: ₹{CAPITAL_INR:,.0f} (~${CAPITAL_USD:.1f}) | 1% Risk Limit: ${MAX_RISK_PER_TRADE_USD:.2f}")

# 1. Real-Time Market Data
@st.cache_data(ttl=60)
def get_gold_data():
    ticker = yf.Ticker("GC=F")
    df = ticker.history(period="1mo", interval="15m")
    return df

df = get_gold_data()

if not df.empty:
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    chg = current_price - prev_close
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Live Gold (XAUUSD)", f"${current_price:.2f}", f"{chg:.2f}")
    col2.metric("Lot Size Allocated", "0.01 Micro", "Risk: $6/Trade")
    col3.metric("Daily Max Loss", "$12.00 (2%)", "Safety Breaker")
    
    # Simple Volatility Guard Indicator
    recent_range = df['High'].iloc[-8:].max() - df['Low'].iloc[-8:].min()
    risk_level = "High Volatility (News Spike)" if recent_range > 15 else "Normal Session"
    col4.metric("Market State", risk_level)

    # Chart
    fig = go.Figure(data=[go.Candlestick(
        x=df.index[-100:],
        open=df['Open'][-100:],
        high=df['High'][-100:],
        low=df['Low'][-100:],
        close=df['Close'][-100:],
        name="M15"
    )])
    fig.update_layout(height=350, margin=dict(l=10, r=10, t=10, b=10), template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

# 2. Automated Backtesting Engine (30-Day Strategy Simulation)
st.subheader("📊 30-Day Backtest Simulator (EMA Pullback + 1:2 RR)")
if st.button("Run Instant Backtest"):
    backtest_df = df.copy()
    backtest_df['EMA20'] = backtest_df['Close'].ewm(span=20).mean()
    backtest_df['Signal'] = np.where((backtest_df['Close'] > backtest_df['EMA20']) & (backtest_df['Close'].shift(1) <= backtest_df['EMA20'].shift(1)), 1, 0)
    
    trades = []
    for i in range(len(backtest_df)-10):
        if backtest_df['Signal'].iloc[i] == 1:
            entry = backtest_df['Close'].iloc[i]
            sl = entry - 6.0  # $6 Risk
            tp = entry + 12.0 # $12 Reward (1:2)
            
            # Check outcome in next candles
            future_prices = backtest_df['Close'].iloc[i+1:i+15]
            win = any(future_prices >= tp)
            trades.append(1 if win else 0)
            
    total_trades = len(trades)
    wins = sum(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    pnl = (wins * 12.0) - ((total_trades - wins) * 6.0)
    
    b_col1, b_col2, b_col3 = st.columns(3)
    b_col1.metric("Total Simulated Trades", f"{total_trades}")
    b_col2.metric("Win Rate", f"{win_rate:.1f}%")
    b_col3.metric("Simulated Net Profit", f"${pnl:.2f}", f"₹{pnl*USD_INR:.0f}")

# 3. AI Market Scan & Strategy Formulator
st.subheader("🤖 AI Strategy Formulator")
api_key = st.text_input("Gemini API Key", type="password")

if st.button("Run AI Market Scan"):
    if not api_key:
        st.warning("Pehle Gemini API Key enter karein.")
    else:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""
        Current XAUUSD: {current_price}. High 24h: {df['High'].iloc[-96:].max()}, Low 24h: {df['Low'].iloc[-96:].min()}.
        Capital: ₹50,000 (~$600 USD). Strict risk limit: $6 per trade.
        1. Asian/London liquidity sweep analyze karo.
        2. Clean Entry, Stop Loss ($6 risk) aur Take Profit ($12 target) suggest karo.
        3. Clear verdict do: BUY, SELL ya WAIT.
        """
        response = model.generate_content(prompt)
        st.session_state.last_analysis = response.text
        st.write(response.text)

# 4. Telegram Alert Sender (Optional)
st.subheader("📲 Telegram Alerts")
tele_token = st.text_input("Telegram Bot Token (Optional)", type="password")
tele_chat_id = st.text_input("Telegram Chat ID (Optional)")

if st.button("Send Alert to Telegram"):
    if tele_token and tele_chat_id and "last_analysis" in st.session_state:
        url = f"https://api.telegram.org/bot{tele_token}/sendMessage"
        payload = {"chat_id": tele_chat_id, "text": f"🚨 XAUUSD Setup:\n{st.session_state.last_analysis}"}
        requests.post(url, json=payload)
        st.success("Alert sent to Telegram!")
    else:
        st.warning("Pehle AI Scan run karein aur Bot Token / Chat ID fill karein.")

# 5. Live Paper Trading Execution
st.subheader("📝 Live Demo Execution")
col_buy, col_sell = st.columns(2)

with col_buy:
    if st.button("🟢 Demo BUY 0.01"):
        st.session_state.paper_trades.append({
            "Type": "BUY", "Entry": current_price, "SL": current_price - 6.0, "TP": current_price + 12.0, "Status": "OPEN"
        })
        st.success(f"Demo Buy @ {current_price:.2f}")

with col_sell:
    if st.button("🔴 Demo SELL 0.01"):
        st.session_state.paper_trades.append({
            "Type": "SELL", "Entry": current_price, "SL": current_price + 6.0, "TP": current_price - 12.0, "Status": "OPEN"
        })
        st.error(f"Demo Sell @ {current_price:.2f}")

if st.session_state.paper_trades:
    st.write("Active Paper Trades:")
    st.dataframe(pd.DataFrame(st.session_state.paper_trades))
