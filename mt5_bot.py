
import MetaTrader5 as mt5
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
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={"chat_id": TELEGRAM_CHAT_ID, "text": body})
    except Exception as e:
        print("Telegram failed:", e)

def trade():
    if not mt5.initialize():
        print("MT5 failed")
        return
    price = mt5.symbol_info_tick("EURUSD").ask
    req = {
        "action": mt5.TRADE_ACTION_DEAL, "symbol": "EURUSD", "volume": 0.1,
        "type": mt5.ORDER_TYPE_BUY, "price": price, "sl": price - 0.001, "tp": price + 0.001,
        "deviation": 10, "magic": 123456, "comment": "Live trade",
        "type_time": mt5.ORDER_TIME_GTC, "type_filling": mt5.ORDER_FILLING_IOC
    }
    result = mt5.order_send(req)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print("✅ Trade placed")
        send_alert("Live Trade Executed", f"BUY @ {price}")
    else:
        print("❌ Trade failed", result.retcode)
    mt5.shutdown()

if __name__ == "__main__":
    try:
        while True:
            trade()
            time.sleep(600)
    except KeyboardInterrupt:
        print("Stopped by user")
