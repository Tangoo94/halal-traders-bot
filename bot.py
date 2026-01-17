import requests
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

# --- SETTINGS ---
BOT_TOKEN = "8235549857:AAHX_dJUl-Ve8qK5XzJVlPhqhuiEE76kS_Q"
ALERT_CHAT_ID = "YOUR_TELEGRAM_ID"  # replace with your Telegram ID
SYMBOLS_HALAL = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # example halal coins
SYMBOLS_ALL = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT"]
DEFAULT_INTERVAL = "4h"
DEFAULT_PUMP_THRESHOLD = 0.05

# --- GLOBAL STATE ---
user_settings = {
    "mode": "halal",
    "symbol": None,
    "interval": DEFAULT_INTERVAL,
    "pump_threshold": DEFAULT_PUMP_THRESHOLD,
    "alerts_on": True
}

# --- FUNCTIONS ---
def get_klines(symbol, interval="4h", limit=50):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=[
            "open_time","open","high","low","close","volume",
            "close_time","quote_asset_volume","number_of_trades",
            "taker_buy_base","taker_buy_quote","ignore"
        ])
        for col in ["open","high","low","close","volume"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        print(f"Error fetching klines for {symbol}: {e}")
        return None

def detect_pump(df, threshold=0.05):
    if df is None or df.empty:
        return False
    change = (df["close"].iloc[-1] - df["close"].iloc[-2]) / df["close"].iloc[-2]
    return change >= threshold

def calculate_targets(entry_price):
    tp1 = entry_price * 1.01
    tp2 = entry_price * 1.02
    tp3 = entry_price * 1.03
    tp4 = entry_price * 1.05
    sl = entry_price * 0.99
    return [tp1, tp2, tp3, tp4], sl

async def send_alert(context, symbol, price):
    if user_settings["alerts_on"]:
        tps, sl = calculate_targets(price)
        message = f"🚨 Pump Detected!\nSymbol: {symbol}\nPrice: {price}\nTPs: {tps}\nSL: {sl}"
        await context.bot.send_message(chat_id=ALERT_CHAT_ID, text=message)

# --- TELEGRAM HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Halal Coins 🕌", callback_data="mode_halal"),
         InlineKeyboardButton("All Coins 💹", callback_data="mode_all")],
        [InlineKeyboardButton("Skip ⏩", callback_data="skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🕌 Halal Traders Bot Started!\nChoose mode:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("mode_"):
        user_settings["mode"] = "halal" if data == "mode_halal" else "all"
        symbols = SYMBOLS_HALAL if user_settings["mode"] == "halal" else SYMBOLS_ALL
        keyboard = [[InlineKeyboardButton(s, callback_data=f"symbol_{s}")] for s in symbols]
        keyboard.append([InlineKeyboardButton("Skip ⏩", callback_data="skip")])
        await query.edit_message_text("Select coin:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("symbol_"):
        user_settings["symbol"] = data.replace("symbol_", "")
        keyboard = [
            [InlineKeyboardButton("1m", callback_data="interval_1m"),
             InlineKeyboardButton("5m", callback_data="interval_5m"),
             InlineKeyboardButton("15m", callback_data="interval_15m")],
            [InlineKeyboardButton("1h", callback_data="interval_1h"),
             InlineKeyboardButton("4h", callback_data="interval_4h"),
             InlineKeyboardButton("1d", callback_data="interval_1d")],
            [InlineKeyboardButton("Skip ⏩", callback_data="skip")]
        ]
        await query.edit_message_text("Select interval:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("interval_"):
        user_settings["interval"] = data.replace("interval_", "")
        await query.edit_message_text(f"✅ Monitoring started for {user_settings['symbol']} at {user_settings['interval']} interval.")
        asyncio.create_task(monitor(context))

    elif data == "skip":
        await query.edit_message_text("⏩ Skipping menu, bot will continue automatically.")
        asyncio.create_task(monitor(context))

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"✅ Bot running\nMode: {user_settings['mode']}\nSymbol: {user_settings['symbol']}\nInterval: {user_settings['interval']}\nAlerts: {'ON' if user_settings['alerts_on'] else 'OFF'}"
    await update.message.reply_text(msg)

async def monitor(context: ContextTypes.DEFAULT_TYPE):
    while True:
        symbol = user_settings.get("symbol")
        if not symbol:
            # pick first symbol automatically
            symbols = SYMBOLS_HALAL if user_settings["mode"] == "halal" else SYMBOLS_ALL
            symbol = symbols[0]
            user_settings["symbol"] = symbol

        df = get_klines(symbol, user_settings["interval"])
        if detect_pump(df, user_settings["pump_threshold"]):
            price = df["close"].iloc[-1]
            await send_alert(context, symbol, price)
        await asyncio.sleep(60)  # check every 1 minute

# --- TELEGRAM SETUP ---
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CallbackQueryHandler(button))

print("✅ Halal Traders Bot starting...")
app.run_polling()
