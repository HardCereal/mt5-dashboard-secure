import MetaTrader5 as mt5
import pandas as pd
import time, os
from datetime import datetime
from email.message import EmailMessage
import smtplib, requests
from dotenv import load_dotenv
load_dotenv()
EMAIL = os.getenv("EMAIL_SENDER")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GIT_REPO_PATH = os.getenv("GIT_REPO_PATH")
GIT_USERNAME = os.getenv("GIT_USERNAME")
GIT_EMAIL = os.getenv("GIT_EMAIL")
last_trade_time = {}
trade_cooldown_minutes = 30
equity = 10000  # Example starting equity
max_drawdown_pct = 0.1  # 10%
lowest_equity = equity
symbol_rsi_threshold = {
"EURUSD": 40,
"GBPUSD": 42
}
──────────────────────────────
📤 Alert function (Email + Telegram)
──────────────────────────────
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
requests.post(
f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
data={"chat_id": TELEGRAM_CHAT_ID, "text": body},
)
except Exception as e:
print("Telegram failed:", e)
──────────────────────────────
💾 Log trade to CSV
──────────────────────────────
def log_trade(trade):
os.makedirs("trade_logs", exist_ok=True)
path = "trade_logs/trade_log.csv"
df = pd.DataFrame([trade])
df.to_csv(path, mode="a", index=False, header=not os.path.exists(path))
def log_skipped(symbol, rsi):
os.makedirs("logs", exist_ok=True)
path = "logs/skipped_signals.csv"
record = pd.DataFrame([{"timestamp": datetime.now(), "symbol": symbol, "reason": f"RSI too high: {rsi:.2f}"}])
record.to_csv(path, mode="a", index=False, header=not os.path.exists(path))
──────────────────────────────
🔁 Git Auto-Push Function
──────────────────────────────
def git_push_log():
os.chdir(GIT_REPO_PATH)
os.system(f"git config user.email "{GIT_EMAIL}"")
os.system(f"git config user.name "{GIT_USERNAME}"")
os.system("git add trade_logs/trade_log.csv")
msg = f"Auto-log trade at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
os.system(f"git commit -m "{msg}"")
os.system("git push")
──────────────────────────────
🤖 RSI + MACD + SMA Strategy Trading Loop
──────────────────────────────
def trade():
global equity, lowest_equity
if not mt5.initialize():
    print("MT5 failed")
    return

for symbol in ["EURUSD", "GBPUSD"]:
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None or len(rates) < 50:
        print(f"⚠️ Not enough data for {symbol}")
        continue

    df = pd.DataFrame(rates)
    df['rsi'] = pd.Series(df['close']).rolling(window=14).apply(
        lambda x: 100 - 100 / (1 + (x.diff().clip(lower=0).sum() / (-x.diff().clip(upper=0).sum() + 1e-10)))
    )
    df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()

    rsi = df['rsi'].iloc[-1]
    macd = df['macd'].iloc[-1]
    macd_prev = df['macd'].iloc[-2]
    signal = df['signal'].iloc[-1]
    signal_prev = df['signal'].iloc[-2]
    price = df['close'].iloc[-1]
    sma50 = df['sma50'].iloc[-1]

    print(f"📊 {symbol} RSI: {rsi:.2f}, MACD: {macd:.5f}, Signal: {signal:.5f}, SMA50: {sma50:.5f}")

    if symbol in last_trade_time:
        delta = (datetime.now() - last_trade_time[symbol]).total_seconds() / 60
        if delta < trade_cooldown_minutes:
            print(f"🕒 Skipping {symbol} - cooldown {delta:.1f} mins")
            continue

    rsi_threshold = symbol_rsi_threshold.get(symbol, 40)

    action = None
    if rsi < rsi_threshold and macd > signal and macd_prev < signal_prev and price > sma50:
        action = mt5.ORDER_TYPE_BUY
    elif rsi > 70 and macd < signal and macd_prev > signal_prev and price < sma50:
        action = mt5.ORDER_TYPE_SELL

    if action is not None:
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask if action == mt5.ORDER_TYPE_BUY else tick.bid
        sl = price - 0.001 if action == mt5.ORDER_TYPE_BUY else price + 0.001
        tp = price + 0.002 if action == mt5.ORDER_TYPE_BUY else price - 0.002

        result = mt5.order_send({
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": 0.1,
            "type": action,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,
            "magic": 123456,
            "comment": "RSI+MACD+SMA entry",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        })

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Trade executed on {symbol} @ {price}")
            last_trade_time[symbol] = datetime.now()
            close_price = tp  # Simulated
            pnl = tp - price if action == mt5.ORDER_TYPE_BUY else price - tp
            exit_reason = "TP"
            trailing_hit = False

            icon = "🏁" if exit_reason == "TP" else "🛑" if exit_reason == "SL" else "🔁"

            trade = {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "type": "buy" if action == mt5.ORDER_TYPE_BUY else "sell",
                "volume": 0.1,
                "price": price,
                "sl": sl,
                "tp": tp,
                "comment": "RSI+MACD+SMA",
                "strategy": "rsi_macd_sma",
                "close_price": close_price,
                "pnl": pnl,
                "exit_reason": exit_reason,
                "trailing_hit": trailing_hit,
                "exit_icon": icon
            }
            log_trade(trade)
            git_push_log()
            send_alert("Trade Executed", f"{symbol} {'BUY' if action == 0 else 'SELL'} @ {price:.5f} | PnL: {pnl:.2f} | Exit: {exit_reason} | Trailing SL: {'✅' if trailing_hit else '❌'}")
        else:
            print(f"❌ Trade failed for {symbol}. Error: {result.retcode}")
    else:
        print(f"⏸️ Skipping {symbol} (no trade setup)")
        log_skipped(symbol, rsi)

    lowest_equity = min(lowest_equity, equity)
    drawdown = 1 - (lowest_equity / equity if equity != 0 else 1)
    if drawdown > max_drawdown_pct:
        send_alert("⚠️ Max Drawdown Alert", f"Drawdown exceeded: {drawdown*100:.2f}%")

mt5.shutdown()

if name == "main":
try:
while True:
print(f"\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking signals")
trade()
time.sleep(600)
except KeyboardInterrupt:
print("👋 Bot stopped by user")
