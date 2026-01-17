import requests
import pandas as pd

# Fetch Binance klines (OHLCV data)
def get_klines(symbol, interval="4h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","quote_asset_volume","number_of_trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        # Convert numeric columns
        for col in ["open","high","low","close","volume"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None

# Simple pump detection
def detect_pump(df, threshold=0.05):
    if df is None or df.empty:
        return False
    change = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]
    return change >= threshold

# Calculate TP and SL
def calculate_targets(entry_price):
    tp1 = entry_price * 1.01
    tp2 = entry_price * 1.02
    tp3 = entry_price * 1.03
    tp4 = entry_price * 1.05
    sl = entry_price * 0.99
    return [tp1, tp2, tp3, tp4], sl
