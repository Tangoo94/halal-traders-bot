import asyncio
import pandas as pd
import requests
import talib  # For RSI and EMA calculations
from config import VIP_CHAT_ID, FREE_CHAT_ID

# --- Get candlestick data from Binance ---
def get_klines(symbol, interval="4h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume","close_time",
            "quote_asset_volume","trades","taker_buy_base","taker_buy_quote","ignore"
        ])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching klines: {e}")
        return None

# --- Calculate confidence score ---
def calculate_confidence(df):
    # Confidence based on last 3 candles trend
    try:
        recent = df["close"].iloc[-3:]
        if recent.is_monotonic_increasing:
            return 90
        elif recent.iloc[-1] > recent.iloc[0]:
            return 70
        else:
            return 40
    except:
        return 50

# --- RSI + EMA confirmation ---
def rsi_ema_confirmation(df):
    close = df["close"].values
    rsi = talib.RSI(close, timeperiod=14)
    ema50 = talib.EMA(close, timeperiod=50)
    ema200 = talib.EMA(close, timeperiod=200)
    
    latest_rsi = rsi[-1]
    latest_close = close[-1]
    signal = False

    # Example bullish confirmation
    if latest_rsi < 70 and latest_close > ema50[-1] and ema50[-1] > ema200[-1]:
        signal = True

    return signal, latest_rsi, ema50[-1], ema200[-1]

# --- Main engine ---
async def run_engine(context, user_settings):
    while True:
        coins = user_settings["coins"]
        timeframes = user_settings["timeframes"]
        vip = user_settings["vip"]
        mode = user_settings["mode"]

        for coin in coins:
            for tf in timeframes:
                df = get_klines(coin, interval=tf)
                if df is None or df.empty:
                    continue

                confirmed, rsi, ema50, ema200 = rsi_ema_confirmation(df)
                confidence = calculate_confidence(df)

                if confirmed:
                    msg = f"""
🚨 Signal Detected!

Coin: {coin}
Timeframe: {tf}
Confidence: {confidence}%
RSI: {rsi:.2f}
EMA50: {ema50:.2f}
EMA200: {ema200:.2f}

Mode: {mode.capitalize()}
Halal Spot Only ✅
"""
                    chat_id = VIP_CHAT_ID if vip else FREE_CHAT_ID
                    await context.bot.send_message(chat_id=chat_id, text=msg)

        await asyncio.sleep(user_settings.get("interval", 60))
