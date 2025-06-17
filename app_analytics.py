
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from dotenv import load_dotenv

load_dotenv()

# 🔐 Login system
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    st.title("🔐 Login")
    user = st.text_input("Username")
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == st.secrets["LOGIN_USERNAME"] and pw == st.secrets["LOGIN_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid credentials")

if not st.session_state.authenticated:
    login()
    st.stop()

st.set_page_config(page_title="📊 MT5 Analytics Dashboard", layout="wide")
st.title("📈 MT5 Strategy Analysis Dashboard")

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
    st.warning("No trade data found.")
    st.stop()

df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce")
df["win"] = df["pnl"] > 0
df["month"] = df["timestamp"].dt.to_period("M").dt.to_timestamp()
df["day"] = df["timestamp"].dt.date
df["hour"] = df["timestamp"].dt.hour
df["weekday"] = df["timestamp"].dt.day_name()

if "close_time" in df.columns:
    df["holding_time"] = (df["close_time"] - df["timestamp"]).dt.total_seconds() / 60
    df["holding_bucket"] = pd.cut(df["holding_time"], bins=[0, 5, 15, 30, 60, 180, 720, float("inf")],
                                  labels=["<5m", "5-15m", "15-30m", "30-60m", "1-3h", "3-12h", "12h+"])

st.subheader("📊 Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Trades", len(df))
col2.metric("Total PnL", f"{df['pnl'].sum():.2f}")
col3.metric("Win Rate", f"{df['win'].mean() * 100:.2f}%")

# Win Rate Trend
st.subheader("📈 Monthly Win Rate")
monthly_win = df.groupby("month")["win"].mean() * 100
fig = go.Figure([go.Scatter(x=monthly_win.index, y=monthly_win.values, mode="lines+markers")])
fig.update_layout(yaxis_title="Win %")
st.plotly_chart(fig, use_container_width=True)

# Daily PnL
st.subheader("💵 Daily PnL")
daily_pnl = df.groupby("day")["pnl"].sum()
fig = go.Figure([go.Bar(x=daily_pnl.index, y=daily_pnl.values)])
st.plotly_chart(fig, use_container_width=True)

# Weekday Performance
st.subheader("📆 PnL by Weekday")
weekday_pnl = df.groupby("weekday")["pnl"].mean().reindex([
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
])
fig = go.Figure([go.Bar(x=weekday_pnl.index, y=weekday_pnl.values)])
st.plotly_chart(fig, use_container_width=True)

# Hour of Day
st.subheader("🕒 Hour of Day Performance")
hour_pnl = df.groupby("hour")["pnl"].mean()
fig = go.Figure([go.Bar(x=hour_pnl.index, y=hour_pnl.values)])
st.plotly_chart(fig, use_container_width=True)

# Holding Time PnL
if "holding_bucket" in df.columns:
    st.subheader("⏱️ PnL by Holding Time")
    hold_pnl = df.groupby("holding_bucket")["pnl"].mean()
    fig = go.Figure([go.Bar(x=hold_pnl.index.astype(str), y=hold_pnl.values)])
    st.plotly_chart(fig, use_container_width=True)

# Multi-symbol overlay
if "symbol" in df.columns:
    st.subheader("📊 Multi-Symbol Equity Overlay")
    fig_multi = go.Figure()
    for sym in df["symbol"].unique():
        temp = df[df["symbol"] == sym].copy()
        temp["equity"] = temp["pnl"].cumsum()
        fig_multi.add_trace(go.Scatter(x=temp["timestamp"], y=temp["equity"], mode="lines", name=sym))
    fig_multi.update_layout(xaxis_title="Time", yaxis_title="Equity")
    st.plotly_chart(fig_multi, use_container_width=True)

# Full Log
st.subheader("📄 Trade Log")
st.dataframe(df.sort_values("timestamp", ascending=False).reset_index(drop=True))
