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
with tab2:
    st.header("🧪 Backtest Explorer")
    backtest_files = sorted(glob.glob("backtests/*.csv"))
    selected = st.selectbox("Choose a backtest", backtest_files)
    if selected:
        df = load_file(selected)
        df["equity"] = df["pnl"].cumsum()
        st.subheader(f"Equity Curve: {os.path.basename(selected)}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines"))
        fig.update_layout(title="Backtest Equity", xaxis_title="Time", yaxis_title="Equity")
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df.tail(20))

with tab3:
    st.header("📈 Strategy Comparison Dashboard")
    dfs = load_backtests()
    if not dfs:
        st.warning("No backtest data found.")
        st.stop()

    combined = pd.concat(dfs.values(), keys=dfs.keys(), names=["strategy"])
    combined = combined.reset_index(level=0)
    combined["win"] = combined["pnl"] > 0
    combined["month"] = combined["timestamp"].dt.to_period("M").astype(str)
    combined["date"] = combined["timestamp"].dt.date

    # 📉 Win Rate Trend
    st.subheader("📉 Win Rate Trend (Monthly)")
    win_rate = combined.groupby(["strategy", "month"])["win"].mean().reset_index()
    win_rate["win"] = (win_rate["win"] * 100).round(1)

    for strat in win_rate["strategy"].unique():
        subset = win_rate[win_rate["strategy"] == strat]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=subset["month"], y=subset["win"], mode="lines+markers", name=strat))
        fig.update_layout(title=f"{strat.upper()} Win Rate", yaxis_title="% Wins", height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 📊 Daily PnL
    st.subheader("📊 Daily PnL (Bar Chart)")
    daily_pnl = combined.groupby(["strategy", "date"])["pnl"].sum().reset_index()
    for strat in daily_pnl["strategy"].unique():
        dfp = daily_pnl[daily_pnl["strategy"] == strat]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=dfp["date"], y=dfp["pnl"], name=strat))
        fig.update_layout(title=f"{strat.upper()} Daily PnL", yaxis_title="PnL", height=300)
        st.plotly_chart(fig, use_container_width=True)

    # 📍 Equity Curve Overlay
    st.subheader("📍 Multi-Strategy Equity Overlay")
    fig = go.Figure()
    for strat, df in dfs.items():
        df = df.sort_values("timestamp")
        df["equity"] = df["pnl"].cumsum()
        fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines", name=strat))
    fig.update_layout(title="Equity Comparison", xaxis_title="Time", yaxis_title="Equity")
    st.plotly_chart(fig, use_container_width=True)
