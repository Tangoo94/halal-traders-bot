import os
import time
import pandas as pd
from binance.client import Client
import requests

# -------------------------
# Environment Variables
# -------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Telegram Bot Token
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")  # Binance API Key
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")  # Binance API Secret

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# -------------------------
# Settings
# -------------------------
HALAL_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Add your halal coins list here
POLL_INTERVAL = 60  # seconds between updates
SHORT_MA = 5
LONG_MA = 20
PUMP_PRICE_THRESHOLD = 0.10  # 10% increase
PUMP_VOLUME_THRESHOLD = 0.5  # 50% increase
PUMP_WINDOW = 5  # minutes

# Default coin selection: all coins
use_halal_only = False

# -------------------------
# Telegram Functions
# -------------------------
def send_message(chat_id, text, buttons=None):
    data = {"chat_id": chat_id, "text": text}
    if buttons:
        data["reply_markup"] = {"inline_keyboard": buttons}
    try:
        requests.post(API_URL + "sendMessage", json=data)
    except Exception as e:
        print("Telegram send error:", e)

def send_start(chat_id):
    buttons = [
        [{"text": "📈 Buy/Sell Signal", "callback_data": "signal"}],
        [{"text": "🚀 Pump Detector", "callback_data": "pump"}],
        [{"text": "⚙️ Coins: All / Halal", "callback_data": "toggle_coins"}]
    ]
    send_message(chat_id, "🕌 Halal Trader Bot\nChoose an option:", buttons)

# -------------------------
# Binance Data Functions
# -------------------------
def get_symbols():
    info = client.get_ticker()
    symbols = [x['symbol'] for x in info if x['symbol'].endswith('USDT')]
    if use_halal_only:
        symbols = [s for s in symbols if s in HALAL_COINS]
    return symbols

def fetch_candles(symbol, interval="1m", limit=LONG_MA+5):
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "open_time","open","high","low","close","volume","close_time",
            "quote_asset_volume","trades","taker_base","taker_quote","ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df
    except Exception as e:
        print(f"Candle fetch error {symbol}:", e)
        return None

# -------------------------
# Signal Functions
# -------------------------
def generate_signal(symbol):
    df = fetch_candles(symbol)
    if df is None or len(df) < LONG_MA:
        return f"Not enough data for {symbol}."
    short_ma = df["close"].tail(SHORT_MA).mean()
    long_ma = df["close"].tail(LONG_MA).mean()
    current_price = df["close"].iloc[-1]

    if short_ma > long_ma:
        sell_target = current_price * 1.05
        return f"📈 Buy signal for {symbol}\nPrice: {current_price:.2f}\nTarget sell: {sell_target:.2f}"
    elif short_ma < long_ma:
        return f"📉 Sell signal for {symbol}\nPrice: {current_price:.2f}"
    else:
        return f"⚪ No clear signal for {symbol}\nPrice: {current_price:.2f}"

def detect_pump(symbol):
    df = fetch_candles(symbol, interval="1m", limit=PUMP_WINDOW+1)
    if df is None or len(df) < PUMP_WINDOW+1:
        return f"Not enough data for {symbol}."
    old = df["close"].iloc[0]
    recent = df["close"].iloc[-1]
    old_vol = df["volume"].iloc[0]
    recent_vol = df["volume"].iloc[-1]

    price_change = (recent - old)/old
    vol_change = (recent_vol - old_vol)/old_vol if old_vol>0 else 0

    if price_change >= PUMP_PRICE_THRESHOLD and vol_change >= PUMP_VOLUME_THRESHOLD:
        return f"🚀 Pump detected for {symbol}!\nPrice +{price_change*100:.2f}%\nVolume +{vol_change*100:.2f}%"
    else:
        return f"No pump detected for {symbol}."

# -------------------------
# Telegram Update Loop
# -------------------------
last_update_id = None
while True:
    try:
        updates = requests.get(API_URL + "getUpdates?timeout=100" + (f"&offset={last_update_id}" if last_update_id else "")).json()
        if updates.get("ok") and updates.get("result"):
            for upd in updates["result"]:
                last_update_id = upd["update_id"] + 1
                chat_id = None

                # Handle normal messages
                if "message" in upd:
                    chat_id = upd["message"]["chat"]["id"]
                    text = upd["message"].get("text","").strip()
                    if text == "/start":
                        send_start(chat_id)

                # Handle button callbacks
                elif "callback_query" in upd:
                    chat_id = upd["callback_query"]["message"]["chat"]["id"]
                    data = upd["callback_query"]["data"]

                    if data == "signal":
                        symbols = get_symbols()
                        msg = ""
                        for s in symbols[:10]:  # Scan first 10 coins to avoid overload
                            msg += generate_signal(s) + "\n\n"
                        send_message(chat_id, msg)

                    elif data == "pump":
                        symbols = get_symbols()
                        msg = ""
                        for s in symbols[:10]:  # Scan first 10 coins
                            msg += detect_pump(s) + "\n\n"
                        send_message(chat_id, msg)

                    elif data == "toggle_coins":
                        use_halal_only = not use_halal_only
                        status = "Halal coins only" if use_halal_only else "All coins"
                        send_message(chat_id, f"✅ Coin filter toggled: {status}")

        time.sleep(POLL_INTERVAL)

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
