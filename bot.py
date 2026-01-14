import os
import time
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException

# ==========================
# ENVIRONMENT VARIABLES
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

# Binance client (SPOT ONLY)
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# ==========================
# SETTINGS
# ==========================
POLL_INTERVAL = 60  # seconds
PUMP_PRICE_THRESHOLD = 0.05   # 5%
PUMP_VOLUME_MULTIPLIER = 1.5  # 1.5x volume

# Toggle halal mode
HALAL_ONLY = True

HALAL_COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
    "ADAUSDT", "SOLUSDT", "XRPUSDT"
]

history = {}
BROADCAST_CHAT_ID = None  # auto-set on /start

# ==========================
# TELEGRAM
# ==========================
def send_message(chat_id, text):
    try:
        requests.post(
            API_URL + "sendMessage",
            json={"chat_id": chat_id, "text": text}
        )
    except Exception as e:
        print("Telegram error:", e)

def get_updates(offset=None):
    try:
        params = {"timeout": 100}
        if offset:
            params["offset"] = offset
        return requests.get(API_URL + "getUpdates", params=params).json()
    except:
        return {"ok": False, "result": []}

# ==========================
# DATA FETCH (BINANCE → COINGECKO FALLBACK)
# ==========================
def get_symbols():
    try:
        info = client.get_exchange_info()
        symbols = [
            s["symbol"] for s in info["symbols"]
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
        ]
        if HALAL_ONLY:
            symbols = [s for s in symbols if s in HALAL_COINS]
        return symbols
    except BinanceAPIException as e:
        print("Binance blocked → fallback symbols")
        return HALAL_COINS if HALAL_ONLY else []

def get_ticker(symbol):
    try:
        t = client.get_ticker_24hr(symbol=symbol)
        return {
            "price": float(t["lastPrice"]),
            "price_change": float(t["priceChangePercent"]) / 100,
            "volume": float(t["quoteVolume"])
        }
    except BinanceAPIException:
        return get_ticker_coingecko(symbol)

def get_ticker_coingecko(symbol):
    try:
        coin = symbol.replace("USDT", "").lower()
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin,
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }
        r = requests.get(url, params=params).json()
        if coin in r:
            return {
                "price": r[coin]["usd"],
                "price_change": r[coin].get("usd_24h_change", 0) / 100,
                "volume": 1
            }
    except:
        pass
    return None

# ==========================
# SIGNALS
# ==========================
def check_pump(symbol):
    data = get_ticker(symbol)
    if not data:
        return None

    prev = history.get(symbol)
    history[symbol] = data

    if not prev:
        return None

    volume_ratio = data["volume"] / max(prev["volume"], 1)

    if (
        data["price_change"] >= PUMP_PRICE_THRESHOLD
        and volume_ratio >= PUMP_VOLUME_MULTIPLIER
    ):
        return (
            f"🚀 PUMP ALERT\n"
            f"{symbol}\n"
            f"Price +{data['price_change']*100:.2f}%\n"
            f"Volume x{volume_ratio:.2f}"
        )
    return None

def check_signal(symbol):
    try:
        klines = client.get_klines(
            symbol=symbol,
            interval=Client.KLINE_INTERVAL_5MINUTE,
            limit=20
        )
        closes = [float(k[4]) for k in klines]
        short = sum(closes[-5:]) / 5
        long = sum(closes) / 20
        price = closes[-1]

        if short > long:
            return f"📈 BUY {symbol}\nPrice: {price:.4f}"
        elif short < long:
            return f"📉 SELL {symbol}\nPrice: {price:.4f}"
    except BinanceAPIException:
        pass
    return None

# ==========================
# MAIN LOOP
# ==========================
last_update_id = None
symbols = get_symbols()
print(f"Scanning {len(symbols)} symbols")

while True:
    updates = get_updates(last_update_id)
    if updates["ok"]:
        for u in updates["result"]:
            last_update_id = u["update_id"] + 1
            if "message" in u:
                chat_id = u["message"]["chat"]["id"]
                text = u["message"].get("text", "")

                if text == "/start":
                    BROADCAST_CHAT_ID = chat_id
                    send_message(
                        chat_id,
                        "✅ Halal Traders Bot Active\n\n"
                        "/pump → detect pumps\n"
                        "/signal → buy/sell signals"
                    )

                elif text == "/pump":
                    for s in symbols:
                        msg = check_pump(s)
                        if msg:
                            send_message(chat_id, msg)

                elif text == "/signal":
                    for s in symbols:
                        sig = check_signal(s)
                        if sig:
                            send_message(chat_id, sig)

    if BROADCAST_CHAT_ID:
        for s in symbols:
            msg = check_pump(s)
            if msg:
                send_message(BROADCAST_CHAT_ID, msg)

    time.sleep(POLL_INTERVAL)
