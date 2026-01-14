import os
import time
import requests
from market_data import get_binance_24h_data

# =========================
# ENV
# =========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# =========================
# SETTINGS
# =========================
POLL_INTERVAL = 60  # seconds

HALAL_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
    "SOLUSDT", "ADAUSDT", "XRPUSDT",
    "MATICUSDT", "DOTUSDT", "LINKUSDT"
]

# Pump conditions
MIN_PRICE_CHANGE = 3.0      # %
MIN_VOLUME_USDT = 5_000_000 # USDT

last_update_id = 0

# =========================
# TELEGRAM
# =========================
def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

def get_updates():
    global last_update_id
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 30, "offset": last_update_id + 1}

    try:
        r = requests.get(url, params=params, timeout=35).json()
        if r["ok"]:
            return r["result"]
    except:
        pass
    return []

# =========================
# SIGNAL LOGIC
# =========================
def scan_pumps():
    data = get_binance_24h_data()
    if not data:
        return []

    signals = []

    for coin in data:
        symbol = coin["symbol"]
        if symbol not in HALAL_COINS:
            continue

        price_change = float(coin["priceChangePercent"])
        volume = float(coin["quoteVolume"])
        price = float(coin["lastPrice"])

        if price_change >= MIN_PRICE_CHANGE and volume >= MIN_VOLUME_USDT:
            confidence = min(100, int((price_change * volume) / 1_000_000))

            signals.append(
                f"🚀 *HALAL PUMP ALERT*\n"
                f"🪙 *{symbol}*\n"
                f"💵 Price: `{price}`\n"
                f"📈 Change: `{price_change:.2f}%`\n"
                f"💰 Volume: `{volume:,.0f} USDT`\n"
                f"🧠 Confidence: `{confidence}%`"
            )

    return signals

def scan_signals():
    data = get_binance_24h_data()
    if not data:
        return []

    messages = []

    for coin in data:
        symbol = coin["symbol"]
        if symbol not in HALAL_COINS:
            continue

        price_change = float(coin["priceChangePercent"])
        price = float(coin["lastPrice"])

        if price_change > 1:
            messages.append(
                f"📈 *BUY SIGNAL*\n"
                f"{symbol}\n"
                f"Price: `{price}`\n"
                f"Trend: Bullish"
            )
        elif price_change < -1:
            messages.append(
                f"📉 *SELL SIGNAL*\n"
                f"{symbol}\n"
                f"Price: `{price}`\n"
                f"Trend: Bearish"
            )

    return messages

# =========================
# MAIN LOOP
# =========================
print("✅ Halal Traders Bot started")

while True:
    updates = get_updates()

    for update in updates:
        last_update_id = update["update_id"]

        if "message" not in update:
            continue

        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        if text == "/start":
            send_message(
                chat_id,
                "🕌 *Halal Traders Bot*\n\n"
                "/pump – Detect halal pumps\n"
                "/signal – Buy/Sell signals\n"
                "/status – Bot status"
            )

        elif text == "/pump":
            results = scan_pumps()
            if not results:
                send_message(chat_id, "😴 No pumps detected")
            else:
                for msg in results:
                    send_message(chat_id, msg)

        elif text == "/signal":
            results = scan_signals()
            if not results:
                send_message(chat_id, "⚖️ No clear signals")
            else:
                for msg in results:
                    send_message(chat_id, msg)

        elif text == "/status":
            send_message(
                chat_id,
                "✅ Bot running\n"
                "📡 Source: Binance Spot (public)\n"
                "🕌 Mode: Halal only"
            )

    time.sleep(POLL_INTERVAL)
