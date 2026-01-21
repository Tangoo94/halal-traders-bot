import asyncio
import logging
import os
import requests
import pandas as pd

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ================== CONFIG ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # ✅ Railway Variable
SCAN_INTERVAL = 60  # seconds

HALAL_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
]

ALL_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOGEUSDT",
]

DEFAULT_TIMEFRAME = "4h"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# ================== GLOBAL STATE ==================

user_settings = {
    "coins": HALAL_COINS,
    "timeframe": DEFAULT_TIMEFRAME,
    "chat_id": None,
    "running": False,
}

# ================== MARKET DATA ==================

def get_klines(symbol: str, interval: str, limit: int = 50):
    url = (
        f"https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    try:
        data = requests.get(url, timeout=10).json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","qav","trades","tbb","tbq","ignore"
        ])
        df["close"] = pd.to_numeric(df["close"])
        df["volume"] = pd.to_numeric(df["volume"])
        return df
    except Exception as e:
        logging.error(f"Klines error {symbol}: {e}")
        return None

# ================== SIMPLE EARLY SIGNAL LOGIC ==================
# (NO TP / SL — engine only flags opportunities)

def early_signal(df: pd.DataFrame):
    if df is None or len(df) < 20:
        return False

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price_change = (last["close"] - prev["close"]) / prev["close"]
    volume_spike = last["volume"] > df["volume"].rolling(20).mean().iloc[-1] * 1.8

    return price_change > 0.01 and volume_spike

# ================== ENGINE ==================

async def run_engine(context: ContextTypes.DEFAULT_TYPE):
    if user_settings["running"]:
        return

    user_settings["running"] = True
    chat_id = user_settings["chat_id"]

    await context.bot.send_message(
        chat_id=chat_id,
        text="🚀 Auto scan started"
    )

    while True:
        try:
            for symbol in user_settings["coins"]:
                df = get_klines(symbol, user_settings["timeframe"])
                if early_signal(df):
                    price = df["close"].iloc[-1]
                    msg = (
                        "🚨 EARLY SIGNAL DETECTED\n\n"
                        f"🪙 Coin: {symbol}\n"
                        f"⏱ Timeframe: {user_settings['timeframe']}\n"
                        f"💰 Price: {price}\n\n"
                        "🕌 Spot only\n"
                        "📌 No leverage\n"
                        "⚠️ Not financial advice"
                    )
                    await context.bot.send_message(chat_id=chat_id, text=msg)

            await asyncio.sleep(SCAN_INTERVAL)

        except Exception as e:
            logging.error(f"Engine error: {e}")
            await asyncio.sleep(10)

# ================== TELEGRAM HANDLERS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings["chat_id"] = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("🕌 Halal Coins Only", callback_data="halal")],
        [InlineKeyboardButton("💹 All Coins", callback_data="all")],
        [InlineKeyboardButton("⏱ Timeframe", callback_data="tf")],
        [InlineKeyboardButton("⏩ Skip (Auto Mode)", callback_data="skip")],
        [InlineKeyboardButton("📡 Status", callback_data="status")],
    ]

    await update.message.reply_text(
        "🕌 Halal Traders Bot\nSmart Spot Signals",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "halal":
        user_settings["coins"] = HALAL_COINS
        await q.edit_message_text("✅ Halal coins enabled")

    elif q.data == "all":
        user_settings["coins"] = ALL_COINS
        await q.edit_message_text("⚠️ All coins enabled")

    elif q.data == "tf":
        kb = [
            [InlineKeyboardButton("1H", callback_data="1h")],
            [InlineKeyboardButton("4H", callback_data="4h")],
            [InlineKeyboardButton("1D", callback_data="1d")],
        ]
        await q.edit_message_text(
            "⏱ Select Timeframe",
            reply_markup=InlineKeyboardMarkup(kb),
        )

    elif q.data in ["1h", "4h", "1d"]:
        user_settings["timeframe"] = q.data
        await q.edit_message_text(f"✅ Timeframe set to {q.data}")

    elif q.data == "skip":
        await q.edit_message_text("⏩ Auto mode started")
        asyncio.create_task(run_engine(context))

    elif q.data == "status":
        msg = (
            "📡 BOT STATUS\n\n"
            f"Mode: {'Halal' if user_settings['coins']==HALAL_COINS else 'All'}\n"
            f"Timeframe: {user_settings['timeframe']}\n"
            f"Coins: {len(user_settings['coins'])}\n"
            f"Engine: {'Running' if user_settings['running'] else 'Idle'}"
        )
        await q.edit_message_text(msg)

# ================== MAIN ==================

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "❌ BOT_TOKEN not found. "
            "Add BOT_TOKEN in Railway → Variables"
        )

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("✅ Halal Traders Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
