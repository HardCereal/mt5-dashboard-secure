import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from dotenv import load_dotenv
load_dotenv()
Basic Auth System
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
Layout
st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")
st.title("📈 MT5 Strategy Dashboard")
Load file
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
Metrics
st.subheader("📊 Metrics")
total_pnl = df["pnl"].sum()
buy_pnl = df[df["type"] == "buy"]["pnl"].sum()
sell_pnl = df[df["type"] == "sell"]["pnl"].sum()
col1, col2, col3 = st.columns(3)
col1.metric("Total PnL", f"{total_pnl:.2f}")
col2.metric("Buy PnL", f"{buy_pnl:.2f}")
col3.metric("Sell PnL", f"{sell_pnl:.2f}")
Trailing stop hit rate
if "trailing_hit" in df.columns:
rate = df["trailing_hit"].mean() * 100
st.metric("🎯 Trailing Stop Hit Rate", f"{rate:.2f}%")
Exit reason distribution
if "exit_reason" in df.columns:
exit_counts = df["exit_reason"].value_counts()
st.subheader("📌 Exit Reason Summary")
st.dataframe(exit_counts.reset_index().rename(columns={"index": "Reason", "exit_reason": "Count"}))
Equity curve
st.subheader("📈 Equity Curve")
df["equity"] = df["pnl"].cumsum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
fig.update_layout(title="Equity Over Time", xaxis_title="Time", yaxis_title="Equity")
st.plotly_chart(fig, use_container_width=True)
Trade log
st.subheader("📄 Raw Trade Log")
df_display = df.copy()
if "exit_reason" in df_display.columns:
df_display["exit_icon"] = df_display["exit_reason"].apply(lambda x: "🏁" if x == "TP" else ("🛑" if x == "SL" else "🔁"))
df_display["trailing_icon"] = df_display["trailing_hit"].apply(lambda x: "✅" if x else "❌")
df_display["exit_summary"] = df_display["exit_icon"] + " " + df_display["exit_reason"] + " | Trailing: " + df_display["trailing_icon"]
df_display = df_display.drop(columns=["exit_icon", "trailing_icon"])
st.dataframe(df_display.sort_values("timestamp", ascending=False).reset_index(drop=True))
