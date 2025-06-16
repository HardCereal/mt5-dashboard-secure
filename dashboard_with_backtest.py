import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from dotenv import load_dotenv

load_dotenv()

# ───────────🔐 AUTH ────────────
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

# ──────────📂 LOAD CSV ──────────
st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")
st.title("📈 MT5 Strategy Dashboard")

st.sidebar.markdown("### 📂 Select File")
files = sorted(glob.glob("backtests/*.csv"))
selected = st.sidebar.selectbox("Select Backtest File", ["Live"] + files)

def load_file(path):
    try:
        return pd.read_csv(path, parse_dates=["timestamp", "close_time"])
    except:
        return pd.read_csv(path, parse_dates=["timestamp"])

if selected != "Live":
    df = load_file(selected)
    st.info(f"📁 Viewing Backtest: {selected}")
else:
    path = "trade_logs/trade_log.csv"
    if not os.path.exists(path):
        st.warning("⚠️ No live trades found (trade_log.csv missing)")
        st.stop()
    df = load_file(path)

if df.empty:
    st.warning("No data")
    st.stop()

# ──────────📊 METRICS ──────────
st.subheader("📊 Performance Metrics")
total_pnl = df["pnl"].sum()
buy_pnl = df[df["type"] == "buy"]["pnl"].sum()
sell_pnl = df[df["type"] == "sell"]["pnl"].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Total PnL", f"{total_pnl:.2f}")
col2.metric("Buy PnL", f"{buy_pnl:.2f}")
col3.metric("Sell PnL", f"{sell_pnl:.2f}")

# 🧠 Exit reason tracking
if "exit_reason" in df.columns:
    reason_counts = df["exit_reason"].value_counts()
    with st.expander("📌 Exit Reason Summary"):
        st.dataframe(reason_counts)

# 🎯 Trailing stop stats
if "trailing_hit" in df.columns:
    hit_rate = df["trailing_hit"].mean() * 100
    st.metric("🎯 Trailing Stop Hit Rate", f"{hit_rate:.1f}%")

# 📈 Equity curve
st.subheader("📈 Equity Curve")
df["equity"] = df["pnl"].cumsum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
fig.update_layout(title="Equity Over Time", xaxis_title="Time", yaxis_title="Equity")
st.plotly_chart(fig, use_container_width=True)

# 🎯 Exit emoji table
if "exit_emoji" in df.columns:
    df["exit_display"] = df["exit_emoji"] + " " + df["exit_reason"]

# 📄 Raw log
st.subheader("📄 Raw Trade Log")
color_map = {
    "TP": "#d4edda",
    "SL": "#f8d7da",
    "Trailing": "#fff3cd"
}

def highlight_row(row):
    reason = row.get("exit_reason", "")
    color = color_map.get(reason, "")
    return ["background-color: " + color] * len(row)

styled = df.sort_values("timestamp", ascending=False).style.apply(highlight_row, axis=1)
st.dataframe(styled, use_container_width=True)
