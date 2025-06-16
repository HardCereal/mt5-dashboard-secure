import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────
# 🔐 Login
# ─────────────────────────────────────
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

# ─────────────────────────────────────
# 📊 Dashboard Layout
# ─────────────────────────────────────
st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")
st.title("📈 MT5 Strategy Dashboard")

# ─────────────────────────────────────
# 📁 Load File
# ─────────────────────────────────────
st.sidebar.markdown("### 📂 Select File")
files = sorted(glob.glob("backtests/*.csv"))
selected = st.sidebar.selectbox("Backtest File", ["Live"] + files)

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

# ─────────────────────────────────────
# 📌 Summary Metrics
# ─────────────────────────────────────
st.subheader("📊 Summary Metrics")
total_pnl = df["pnl"].sum()
buy_pnl = df[df["type"] == "buy"]["pnl"].sum()
sell_pnl = df[df["type"] == "sell"]["pnl"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total PnL", f"{total_pnl:.2f}")
col2.metric("Buy PnL", f"{buy_pnl:.2f}")
col3.metric("Sell PnL", f"{sell_pnl:.2f}")

if "trailing_hit" in df.columns:
    trail_rate = df["trailing_hit"].mean() * 100
    st.metric("🎯 Trailing Stop Hit %", f"{trail_rate:.2f}%")

# ─────────────────────────────────────
# 📈 Equity Curve
# ─────────────────────────────────────
st.subheader("📈 Equity Curve")
df["equity"] = df["pnl"].cumsum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
fig.update_layout(title="Equity Over Time", xaxis_title="Time", yaxis_title="Equity")
st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────
# 🧠 Exit Analysis
# ─────────────────────────────────────
if "exit_reason" in df.columns:
    exit_summary = df.groupby("exit_reason")["pnl"].agg(["count", "sum"]).reset_index()
    st.subheader("🧠 Exit Reason Summary")
    st.dataframe(exit_summary)

# ─────────────────────────────────────
# 📄 Trade Log (With Emoji & Highlights)
# ─────────────────────────────────────
st.subheader("📄 Raw Trade Log")

def highlight_exit(row):
    if row.get("exit_reason") == "TP":
        return ["background-color: #d4edda"] * len(row)
    elif row.get("exit_reason") == "SL":
        return ["background-color: #f8d7da"] * len(row)
    elif row.get("exit_reason") == "Trailing":
        return ["background-color: #ffeeba"] * len(row)
    return [""] * len(row)

st.dataframe(df.sort_values("timestamp", ascending=False).style.apply(highlight_exit, axis=1))
