# engine.py
import asyncio
import pandas as pd
import requests
from telegram import InlineKeyboardMarkup

from config import ALERT_CHAT_ID

# === HELPER FUNCTIONS ===

def get_klines(symbol, interval="4h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume","close_time",
            "quote_asset_volume","num_trades","taker_buy_base","taker_buy_quote","ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["open"] = df["open"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None

def detect_pump(df, threshold=0.05):
    """Simple pump detection based on close price vs previous close"""
    if df is None or len(df) < 2:
        return False
    prev = df["close"].iloc[-2]
    last = df["close"].iloc[-1]
    change = (last - prev) / prev
    return change >= threshold

def calculate_targets(entry_price):
    """Calculate TP1-4 and SL"""
    tp1 = entry_price * 1.15
    tp2 = entry_price * 1.30
    tp3 = entry_price * 1.45
    tp4 = entry_price * 1.65
    sl = entry_price * 0.90
    return [tp1, tp2, tp3, tp4], sl

async def send_signal(context, chat_id, symbol, interval, entry):
    tps, sl = calculate_targets(entry)
    msg = f"""
🚨 PUMP ALERT – TRADE CAREFULLY

🕌 Halal Signal
Currency: {symbol}
Timeframe: {interval}
Entry Price: {entry:.6f}

Take Profits:
TP1: {tps[0]:.6f} (+15%)
TP2: {tps[1]:.6f} (+30%)
TP3: {tps[2]:.6f} (+45%)
TP4: {tps[3]:.6f} (+65%)

Stop Loss: {sl:.6f} (-10%)
Islamic Ruling: Halal ✅
Spot only – No leverage
"""
    await context.bot.send_message(chat_id=chat_id, text=msg)

# === MAIN ENGINE ===
async def run_engine(context, user_settings):
    chat_id = user_settings.get("chat_id")
    coins = user_settings.get("coins", [])
    timeframe = user_settings.get("timeframe", "4h")

    print(f"Engine started for coins: {coins}, timeframe: {timeframe}")

    while True:
        for symbol in coins:
            df = get_klines(symbol, interval=timeframe)
            if df is None:
                continue
            last_price = df["close"].iloc[-1]
            if detect_pump(df):
                await send_signal(context, chat_id, symbol, timeframe, last_price)
        await asyncio.sleep(user_settings.get("interval", 60))
