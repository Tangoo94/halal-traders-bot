import os
import time
from binance.client import Client
from binance.exceptions import BinanceAPIException
import requests

# ----------------------------
# Load keys from Railway environment
# ----------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# ----------------------------
# Settings
# ----------------------------
POLL_INTERVAL = 60  # seconds between scans
PUMP_PRICE_THRESHOLD = 0.05  # 5% price increase
PUMP_VOLUME_THRESHOLD = 0.5  # 50% volume increase
HALAL_COINS = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","ADAUSDT"]  # example halal coins

# Toggle: True = only halal, False = all coins
HALAL_ONLY = True

# Store previous prices and volumes
history = {}

# ----------------------------
# Telegram Functions
# ----------------------------
def send_message(chat_id, text, reply_markup=None):
    url = API_URL + f"sendMessage?chat_id={chat_id}&text={text}&parse_mode=Markdown"
    if reply_markup:
        url += f"&reply_markup={reply_markup}"
    try:
        requests.get(url)
    except Exception as e:
        print("Telegram send error:", e)

def get_updates(offset=None):
    url = API_URL + "getUpdates?timeout=100"
    if offset:
        url += f"&offset={offset}"
    try:
        r = requests.get(url).json()
        return r
    except:
        return {"ok": False, "result":[]}

# ----------------------------
# Binance Functions
# ----------------------------
def get_all_symbols():
    try:
        info = client.get_exchange_info()
        symbols = [s['symbol'] for s in info['symbols'] if s['quoteAsset']=="USDT"]
        if HALAL_ONLY:
            symbols = [s for s in symbols if s in HALAL_COINS]
        return symbols
    except BinanceAPIException as e:
        print("Binance API error:", e)
        return []

def check_pump(symbol):
    try:
        ticker = client.get_ticker_24hr(symbol=symbol)
        price_change = float(ticker['priceChangePercent']) / 100
        volume_change = float(ticker['quoteVolume']) / (history.get(symbol, {}).get("volume", 1))
        history[symbol] = {"price": float(ticker['lastPrice']), "volume": float(ticker['quoteVolume'])}

        if price_change >= PUMP_PRICE_THRESHOLD and volume_change >= PUMP_VOLUME_THRESHOLD:
            return True, f"🚀 PUMP ALERT\n{symbol}\nPrice +{price_change*100:.2f}%\nVolume x{volume_change:.2f}"
    except BinanceAPIException as e:
        print("Error fetching:", symbol, e)
    return False, None

def check_signal(symbol):
    try:
        klines = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=20)
        closes = [float(k[4]) for k in klines]
        short_ma = sum(closes[-5:])/5
        long_ma = sum(closes)/20
        current_price = closes[-1]

        if short_ma > long_ma:
            return f"📈 Buy signal: {symbol}\nCurrent: {current_price:.2f}\nTarget sell: {current_price*1.05:.2f}"
        elif short_ma < long_ma:
            return f"📉 Sell signal: {symbol}\nCurrent: {current_price:.2f}"
        else:
            return f"⚖️ No clear signal for {symbol}"
    except BinanceAPIException as e:
        print("Error signals:", symbol, e)
        return None

# ----------------------------
# Main Bot Loop
# ----------------------------
last_update_id = None
symbols = get_all_symbols()
print(f"Scanning {len(symbols)} coins...")

while True:
    # 1️⃣ Check Telegram messages
    updates = get_updates(last_update_id)
    if updates['ok']:
        for update in updates['result']:
            last_update_id = update['update_id'] + 1
            if 'message' in update:
                chat_id = update['message']['chat']['id']
                text = update['message'].get('text', '').strip()
                if text == "/start":
                    send_message(chat_id, "Welcome! Use /pump to detect pumps or /signal for buy/sell signals.",
                                 reply_markup='{"inline_keyboard":[[{"text":"Pump","callback_data":"/pump"},{"text":"Signal","callback_data":"/signal"}]]}')
                elif text == "/pump":
                    for sym in symbols:
                        pump, msg = check_pump(sym)
                        if pump:
                            send_message(chat_id, msg)
                elif text == "/signal":
                    for sym in symbols:
                        sig = check_signal(sym)
                        if sig:
                            send_message(chat_id, sig)

    # 2️⃣ Automatic pump detection
    for sym in symbols:
        pump, msg = check_pump(sym)
        if pump:
            # Replace with your chat id or broadcast channel
            send_message(chat_id, msg)

    time.sleep(POLL_INTERVAL)
