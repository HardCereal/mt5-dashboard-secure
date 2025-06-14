import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob

# 🛡️ Simple login check
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

# 📊 Dashboard starts here
st.set_page_config(page_title="📊 Strategy Comparison", layout="wide")
st.title("📈 Strategy Equity Curve Comparison")

# 📁 Load latest or backtest file
files = sorted(glob.glob("backtests/*.csv"))
selected_file = st.sidebar.selectbox("📂 Choose Backtest File", ["Live"] + files)

if selected_file != "Live":
    df = pd.read_csv(selected_file, parse_dates=["timestamp", "close_time"])
    st.info(f"📁 Viewing Backtest: {selected_file}")
else:
    df = pd.DataFrame(columns=[
        "timestamp", "close_time", "symbol", "type", "volume",
        "price", "sl", "tp", "comment", "strategy", "pnl"
    ])

if df.empty:
    st.warning("⚠️ No trade data available.")
    st.stop()

# 🔎 Sidebar filters
strategies = df['strategy'].unique().tolist()
symbols = df['symbol'].unique().tolist()

selected_strategies = st.sidebar.multiselect("📈 Strategy", options=strategies, default=strategies)
selected_symbols = st.sidebar.multiselect("🪙 Symbol", options=symbols, default=symbols)

# 🧹 Filter data
df = df[df['strategy'].isin(selected_strategies) & df['symbol'].isin(selected_symbols)]

if df.empty:
    st.warning("No data after filtering.")
    st.stop()

# 📊 Equity Curve per Strategy
st.subheader("📈 Equity Curves by Strategy")
tabs = st.tabs(selected_strategies)

for i, strategy in enumerate(selected_strategies):
    strat_df = df[df["strategy"] == strategy].copy()
    strat_df["equity"] = strat_df["pnl"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=strat_df["timestamp"],
        y=strat_df["equity"],
        mode="lines+markers",
        name=strategy.upper()
    ))
    fig.update_layout(
        title=f"{strategy.upper()} Equity Curve",
        xaxis_title="Time",
        yaxis_title="Equity",
        height=400
    )
    with tabs[i]:
        st.plotly_chart(fig, use_container_width=True)