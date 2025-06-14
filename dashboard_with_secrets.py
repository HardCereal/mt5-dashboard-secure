import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import os, glob

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

st.set_page_config(page_title="📊 Dashboard", layout="wide")
st.title("📈 MT5 Dashboard")

files = sorted(glob.glob("backtests/*.csv"))
selected = st.sidebar.selectbox("📂 Backtest", ["Live"] + files)

if selected != "Live":
    df = pd.read_csv(selected, parse_dates=["timestamp", "close_time"])
    st.info(f"Backtest: {selected}")
else:
    df = pd.DataFrame(columns=["timestamp","close_time","symbol","type","volume","price","sl","tp","comment","strategy","pnl"])

if df.empty:
    st.warning("No data")
    st.stop()

df["equity"] = df["pnl"].cumsum()
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["timestamp"], y=df["equity"], mode="lines+markers"))
fig.update_layout(title="Equity Curve", xaxis_title="Time", yaxis_title="Equity")
st.plotly_chart(fig, use_container_width=True)