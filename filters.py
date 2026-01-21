import ta

def apply_indicators(df):
    df["ema20"] = ta.trend.EMAIndicator(df["close"], 20).ema_indicator()
    df["ema50"] = ta.trend.EMAIndicator(df["close"], 50).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], 14).rsi()
    df["vol_avg"] = df["volume"].rolling(20).mean()
    return df

def early_signal(df):
    last = df.iloc[-1]

    conditions = [
        last["volume"] > last["vol_avg"] * 1.8,
        last["ema20"] > last["ema50"],
        45 <= last["rsi"] <= 60,
        last["close"] > df["high"].rolling(20).max().iloc[-2]
    ]

    return sum(conditions) >= 3
