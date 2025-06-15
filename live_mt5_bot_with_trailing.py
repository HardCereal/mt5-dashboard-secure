import MetaTrader5 as mt5
import time, os, subprocess
from datetime import datetime
import pandas as pd
from email.message import EmailMessage
import smtplib, requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
EMAIL = os.getenv("EMAIL_SENDER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
REPO_PATH = os.getenv("GIT_REPO_PATH") or "C:/Users/bandi/Documents/mt5-dashboard-secure"

# Parameters
SYMBOLS = ["EURUSD", "GBPUSD", "BTCUSD"]
VOLUME = 0.1
SL_PIPS = 10
TP_PIPS = 10
RSI_PERIOD = 14
RSI_THRESHOLD = 30
TRAIL_TRIGGER_PIPS = 5
TRAIL_OFFSET_PIPS = 3

log_dir = os.path.join(REPO_PATH, "trade_logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "trade_log.csv")

if not os.path.exists(log_file):
    pd.DataFrame(columns=[
        "timestamp", "close_time", "symbol", "type", "volume", "price", "sl", "tp",
        "pnl", "holding_time", "comment", "strategy", "trailing_hit", "adjusted_sl"
    ]).to_csv(log_file, index=False)

def send_alert(subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASS)
            server.send_message(msg)
    except Exception as e:
        print("Email failed:", e)
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={
            "chat_id": TELEGRAM_CHAT_ID, "text": body
        })
    except Exception as e:
        print("Telegram failed:", e)

def sync_to_github():
    try:
        os.chdir(REPO_PATH)
        subprocess.run(["git", "add", "trade_logs/trade_log.csv"], check=True)
        subprocess.run(["git", "commit", "-m", "Auto: update trade log"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Trade log pushed to GitHub.")
    except Exception as e:
        print("❌ Git push failed:", e)

def get_rsi(symbol, period=14):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, period + 1)
    if rates is None or len(rates) < period + 1:
        return None
    df = pd.DataFrame(rates)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def trade(symbol):
    rsi = get_rsi(symbol, RSI_PERIOD)
    if rsi is None:
        print(f"⚠️ Not enough data for {symbol}")
        return
    print(f"📊 {symbol} RSI: {rsi:.2f}")
    if rsi > RSI_THRESHOLD:
        print(f"⏸️ Skipping {symbol} (RSI too high)")
        return

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"❌ Symbol not found: {symbol}")
        return

    price = tick.ask
    sl = price - SL_PIPS * 0.0001
    tp = price + TP_PIPS * 0.0001

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": VOLUME,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "RSI entry",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ {symbol} BUY trade placed")
        entry_time = datetime.now()
        trailing_hit = False
        adjusted_sl = sl

        time.sleep(5)
        new_price = mt5.symbol_info_tick(symbol).bid
        diff = (new_price - price) * 10000

        if diff >= TRAIL_TRIGGER_PIPS:
            adjusted_sl = price + (diff - TRAIL_OFFSET_PIPS) * 0.0001
            trailing_hit = True

        pnl = (new_price - price) * 100000 * VOLUME
        hold_secs = (datetime.now() - entry_time).total_seconds()

        log = {
            "timestamp": entry_time,
            "close_time": datetime.now(),
            "symbol": symbol,
            "type": "buy",
            "volume": VOLUME,
            "price": price,
            "sl": sl,
            "tp": tp,
            "pnl": pnl,
            "holding_time": hold_secs,
            "comment": "RSI < 30",
            "strategy": "rsi",
            "trailing_hit": trailing_hit,
            "adjusted_sl": adjusted_sl
        }

        df = pd.read_csv(log_file)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
        df.to_csv(log_file, index=False)

        send_alert(f"{symbol} Trade Executed", f"BUY @ {price:.5f} | PnL: {pnl:.2f} | Trailing SL: {'✅' if trailing_hit else '❌'}")
        sync_to_github()
    else:
        print(f"❌ {symbol} trade failed: {result.retcode}")

# 🔁 Main Loop
if __name__ == "__main__":
    if not mt5.initialize():
        print("❌ Failed to connect to MT5")
        quit()
    try:
        while True:
            print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking signals")
            for sym in SYMBOLS:
                trade(sym)
            print("💤 Sleeping for 10 mins...\n")
            time.sleep(600)
    except KeyboardInterrupt:
        print("👋 Stopped")
    finally:
        mt5.shutdown()
