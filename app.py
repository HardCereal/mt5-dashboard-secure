import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os

st.set_page_config(page_title="📊 MT5 Dashboard", layout="wide")

# Load trade log
log_path = "trade_logs/trade_log.csv"
if not os.path.exists(log_path):
    st.warning("⚠️ trade_log.csv not found in trade_logs/")
    st.stop()

df = pd.read_csv(log_path, parse_dates=["timestamp"])
if df.empty:
    st.warning("No trades found in log.")
    st.stop()

# Coerce PnL column to numeric in case of string issues
df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)

st.title("📈 MT5 Strategy Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "📄 Full Log", "📍 Exit Analysis", "📈 Strategy Compare"])

with tab1:
    total_trades = len(df)
    total_pnl = df["pnl"].sum()
    win_rate = (df["pnl"] > 0).mean() * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total Trades", total_trades)
    col2.metric("💰 Total PnL", f"{total_pnl:.2f}")
    col3.metric("✅ Win Rate", f"{win_rate:.2f}%")

    df["equity"] = df["pnl"].cumsum()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers", name="Equity"))
    fig.update_layout(title="📈 Equity Curve", xaxis_title="Time", yaxis_title="Equity")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("📄 Trade Log")
    st.dataframe(df.sort_values("timestamp", ascending=False).reset_index(drop=True))

with tab3:
    if "exit_reason" in df.columns:
        st.subheader("📍 Exit Reason Counts")
        st.dataframe(df["exit_reason"].value_counts())

    if "exit_emoji" in df.columns:
        st.subheader("🎯 Exit Emoji Counts")
        st.dataframe(df["exit_emoji"].value_counts())

with tab4:
    if "strategy" in df.columns:
        st.subheader("📈 PnL by Strategy")
        strategy_stats = df.groupby("strategy").agg(
            Trades=("pnl", "count"),
            Total_PnL=("pnl", "sum"),
            Avg_PnL=("pnl", "mean"),
            Win_Rate=("pnl", lambda x: (x > 0).mean() * 100)
        ).reset_index()
        st.dataframe(strategy_stats.sort_values("Total_PnL", ascending=False))
