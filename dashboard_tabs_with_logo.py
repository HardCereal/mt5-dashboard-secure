
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from PIL import Image

st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")

# === AUTH ===
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

# === HEADER WITH LOGO ===
col1, col2 = st.columns([1, 5])
with col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/0/0b/MT5_Logo.png", width=90)
with col2:
    st.title("📈 MT5 Strategy Dashboard")
    st.caption("🚀 Powered by **Bandile's MT5 AI Bot**")

# === TAB LAYOUT ===
tabs = st.tabs(["📊 Live", "🧪 Backtests", "📈 Compare"])

# === BACKTEST/LOGIC LOADER (shared) ===
def load_file(path):
    return pd.read_csv(path, parse_dates=["timestamp", "close_time"])

def load_files_from_folder(folder="backtests"):
    files = sorted(glob.glob(f"{folder}/*.csv"))
    data = {}
    for f in files:
        name = os.path.basename(f).replace(".csv", "")
        data[name] = load_file(f)
    return data

# === TAB 1: LIVE ===
with tabs[0]:
    st.subheader("📊 Live Trading Log")
    live_file = "trade_logs/trade_log.csv"
    if os.path.exists(live_file):
        df = load_file(live_file)
        df["equity"] = df["pnl"].cumsum()
        st.line_chart(df.set_index("timestamp")["equity"])
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.warning("⚠️ No live trades found (trade_log.csv missing)")

# === TAB 2: BACKTESTS ===
with tabs[1]:
    st.subheader("🧪 Explore Uploaded Backtests")
    files = sorted(glob.glob("backtests/*.csv"))
    selected = st.selectbox("📂 Choose a backtest file", files)
    df = load_file(selected)
    df["equity"] = df["pnl"].cumsum()
    st.line_chart(df.set_index("timestamp")["equity"])
    st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

# === TAB 3: COMPARE STRATEGIES ===
with tabs[2]:
    st.subheader("📈 Strategy Equity Curve Comparison")
    dfs = load_files_from_folder("backtests")
    for name, df in dfs.items():
        df["equity"] = df["pnl"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["equity"],
            mode="lines+markers", name=name.upper()
        ))
        fig.update_layout(title=f"{name.upper()} Equity Curve", height=400)
        st.plotly_chart(fig, use_container_width=True)
