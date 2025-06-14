import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob

st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")

# --- File loader ---
def load_file(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    if "close_time" in df.columns:
        df["close_time"] = pd.to_datetime(df["close_time"])
    return df

# --- Load backtests ---
def load_backtests(folder="backtests"):
    files = sorted(glob.glob(f"{folder}/*.csv"))
    data = {}
    for f in files:
        name = os.path.basename(f).replace(".csv", "")
        df = load_file(f)
        data[name] = df
    return data

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📊 Live", "🧪 Backtests", "📈 Compare"])

with tab1:
    st.header("📊 Live Trading Log")
    live_path = "trade_logs/trade_log.csv"
    if not os.path.exists(live_path):
        st.warning("⚠️ No live trades found (trade_log.csv missing)")
    else:
        df = load_file(live_path)
        df["equity"] = df["pnl"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
        fig.update_layout(title="Live Equity Curve", xaxis_title="Time", yaxis_title="Equity")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(20))
