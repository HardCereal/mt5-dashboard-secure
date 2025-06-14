import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔐 Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == st.secrets["LOGIN_USERNAME"] and pw == st.secrets["LOGIN_PASSWORD"]:
            st.session_state.authenticated = True
            st.success("✅ Login successful.")
            st.stop()
        else:
            st.error("Invalid credentials")

if not st.session_state.authenticated:
    login()
    st.stop()

st.set_page_config(page_title="📊 Dashboard", layout="wide")
st.title("📈 MT5 Strategy Dashboard with Multi-Symbol Support")

# Load CSV files
files = sorted(glob.glob("backtests/*.csv"))
selected = st.sidebar.selectbox("📂 Backtest", ["Live"] + files)

if selected != "Live":
    df = pd.read_csv(selected, parse_dates=["timestamp", "close_time"])
    st.info(f"📁 Backtest file: {selected}")
else:
    df = pd.DataFrame(columns=["timestamp","close_time","symbol","type","volume","price","sl","tp","comment","strategy","pnl"])

if df.empty:
    st.warning("No data found.")
    st.stop()

# Sidebar filters
symbols = df['symbol'].unique().tolist()
strategies = df['strategy'].unique().tolist()
types = df['type'].unique().tolist()

selected_symbols = st.sidebar.multiselect("🪙 Symbols", symbols, default=symbols)
selected_strategies = st.sidebar.multiselect("📈 Strategies", strategies, default=strategies)
selected_types = st.sidebar.multiselect("🧾 Trade Types", types, default=types)

df = df[df['symbol'].isin(selected_symbols)]
df = df[df['strategy'].isin(selected_strategies)]
df = df[df['type'].isin(selected_types)]

if df.empty:
    st.warning("No trades after filtering.")
    st.stop()

# Equity curves per symbol
st.subheader("📊 Equity Curves by Symbol")
tabs = st.tabs(selected_symbols)

for i, symbol in enumerate(selected_symbols):
    sym_df = df[df["symbol"] == symbol].copy()
    sym_df["equity"] = sym_df["pnl"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sym_df["timestamp"], y=sym_df["equity"], mode="lines+markers"))
    fig.update_layout(title=f"{symbol} Equity Curve", xaxis_title="Time", yaxis_title="Equity")
    with tabs[i]:
        st.plotly_chart(fig, use_container_width=True)