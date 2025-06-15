import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from dotenv import load_dotenv

load_dotenv()

# Basic Auth System
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
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.authenticated:
    login()
    st.stop()

# Layout
st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")
st.title("📈 MT5 Strategy Dashboard")

# Load file
st.sidebar.markdown("### 📂 Select File")
files = sorted(glob.glob("backtests/*.csv"))
selected = st.sidebar.selectbox("Select Backtest File", ["Live"] + files)

if selected != "Live":
    try:
        df = pd.read_csv(selected, parse_dates=["timestamp", "close_time"])
    except ValueError:
        df = pd.read_csv(selected, parse_dates=["timestamp"])
    st.info(f"📁 Viewing Backtest: {selected}")
else:
    path = "trade_logs/trade_log.csv"
    if not os.path.exists(path):
        st.warning("⚠️ No live trades found (trade_log.csv missing)")
        st.stop()
    try:
        df = pd.read_csv(path, parse_dates=["timestamp", "close_time"])
    except ValueError:
        df = pd.read_csv(path, parse_dates=["timestamp"])

if df.empty:
    st.warning("No data")
    st.stop()

# Metrics
st.subheader("📊 Metrics")
total_pnl = df["pnl"].sum()
buy_pnl = df[df["type"] == "buy"]["pnl"].sum()
sell_pnl = df[df["type"] == "sell"]["pnl"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total PnL", f"{total_pnl:.2f}")
col2.metric("Buy PnL", f"{buy_pnl:.2f}")
col3.metric("Sell PnL", f"{sell_pnl:.2f}")

# Trailing stop hit rate
if "trailing_hit" in df.columns:
    hit_rate = df["trailing_hit"].mean() * 100
    st.metric("🎯 Trailing Stop Hit Rate", f"{hit_rate:.2f}%")

# Equity curve
st.subheader("📈 Equity Curve")
df["equity"] = df["pnl"].cumsum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
fig.update_layout(title="Equity Over Time", xaxis_title="Time", yaxis_title="Equity")
st.plotly_chart(fig, use_container_width=True)

# Color-coded trade log
st.subheader("📄 Trade Log")
def color_row(row):
    if "exit_reason" in row and row["exit_reason"] == "TP":
        return ["background-color: #e0ffe0"] * len(row)
    elif row.get("trailing_hit"):
        return ["background-color: #ffe0e0"] * len(row)
    return [""] * len(row)

styled_df = df.sort_values("timestamp", ascending=False).reset_index(drop=True).style.apply(color_row, axis=1)
st.dataframe(styled_df, use_container_width=True)
