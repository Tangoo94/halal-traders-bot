import requests
import pandas as pd
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ================= CONFIG =================

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # optional if using env
ADMIN_ID = 123456789  # 🔴 PUT YOUR TELEGRAM ID HERE

BINANCE_BASE = "https://data.binance.vision"

SETTINGS = {
    "TP": [0.05, 0.10, 0.15, 0.20],   # percentages
    "SL": 0.04,                     # percentage
    "PUMP": 0.05,                   # 5% candle pump
}

HALAL_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
    "SOLUSDT", "ADAUSDT", "AVAXUSDT",
    "MATICUSDT", "DOTUSDT"
]

# ============== MARKET DATA ==============

def get_klines(symbol):
    url = f"{BINANCE_BASE}/data/spot/klines"
    params = {
        "symbol": symbol,
        "interval": "4h",
        "limit": 100
    }
    r = requests.get(url, params=params, timeout=10)
    if r.status_code != 200:
        return None

    df = pd.DataFrame(r.json(), columns=[
        "time","open","high","low","close","volume",
        "_","_","_","_","_"
    ])
    df["close"] = df["close"].astype(float)
    return df

def detect_pump(df):
    prev = df["close"].iloc[-2]
    curr = df["close"].iloc[-1]
    return (curr - prev) / prev >= SETTINGS["PUMP"]

def calculate_targets(entry):
    tps = [round(entry * (1 + p), 5) for p in SETTINGS["TP"]]
    sl = round(entry * (1 - SETTINGS["SL"]), 5)
    return tps, sl

# ============== TELEGRAM COMMANDS ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕌 Halal Traders Bot\n\n"
        "/signal – Market signal\n"
        "/status – Bot status"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot running\n"
        "📡 Source: Binance Spot (public)\n"
        "🕌 Mode: Halal only\n"
        "⏱ Timeframe: 4H"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = []

    for symbol in HALAL_SYMBOLS:
        df = get_klines(symbol)
        if df is None:
            continue

        entry = df["close"].iloc[-1]
        pump = detect_pump(df)
        tps, sl = calculate_targets(entry)

        msg = f"""
{'🚨 PUMP ALERT – TRADE CAREFULLY' if pump else '📈 BUY SIGNAL'}
🕌 *Halal Signal*

Currency: {symbol}
Timeframe: 4H

Entry Price:
{entry}

Take Profits:
TP1: {tps[0]}
TP2: {tps[1]}
TP3: {tps[2]}
TP4: {tps[3]}

Stop Loss:
SL: {sl}

Islamic Ruling:
Halal ✅
Spot only – No leverage
"""
        messages.append(msg)

    if not messages:
        await update.message.reply_text("😴 No clear signals")
    else:
        for m in messages[:2]:  # limit spam
            await update.message.reply_markdown(m)

# ============== ADMIN COMMANDS ==============

async def settp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    SETTINGS["TP"] = [float(x)/100 for x in context.args]
    await update.message.reply_text("✅ TP updated")

async def setsl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    SETTINGS["SL"] = float(context.args[0]) / 100
    await update.message.reply_text("✅ SL updated")

async def setpump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    SETTINGS["PUMP"] = float(context.args[0]) / 100
    await update.message.reply_text("✅ Pump sensitivity updated")

# ============== RUN BOT ==============

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("settp", settp))
app.add_handler(CommandHandler("setsl", setsl))
app.add_handler(CommandHandler("setpump", setpump))

print("✅ Halal Traders Bot started")
app.run_polling()
