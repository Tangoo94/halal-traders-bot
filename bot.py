import logging
import requests
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# ================= CONFIG =================
BOT_TOKEN = "8235549857:AAHX_dJUl-Ve8qK5XzJVlPhqhuiEE76kS_Q"
ADMIN_ID = 8497827576  # 🔴 Your Telegram ID
HALAL_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Example halal coins
ALL_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT"]  # Example all coins

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# ============== UTILITIES =================
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

# ============== BUTTON HANDLER =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🕌 Halal Coins", callback_data="halal")],
        [InlineKeyboardButton("💰 All Coins", callback_data="all")],
        [InlineKeyboardButton("⏱ 1h", callback_data="1h"),
         InlineKeyboardButton("⏱ 4h", callback_data="4h"),
         InlineKeyboardButton("⏱ 1d", callback_data="1d")],
        [InlineKeyboardButton("⏩ Skip", callback_data="skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to Halal Traders Bot! 🕌\nChoose options below:", reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "halal":
        context.user_data["symbols"] = HALAL_SYMBOLS
        await query.edit_message_text("✅ Halal coins selected. Bot will send signals for these coins.")
    elif data == "all":
        context.user_data["symbols"] = ALL_SYMBOLS
        await query.edit_message_text("✅ All coins selected. Bot will send signals for all coins.")
    elif data in ["1h","4h","1d"]:
        context.user_data["interval"] = data
        await query.edit_message_text(f"✅ Timeframe set to {data}.")
    elif data == "skip":
        await query.edit_message_text("⏩ Skipping manual selection. Bot will continue automatically.")
    else:
        await query.edit_message_text("❌ Unknown option.")

# ============== STATUS & SIGNALS =================
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ Bot running\n"
        "📡 Source: Binance Spot (public)\n"
        f"🕌 Mode: {'Halal only' if context.user_data.get('symbols', HALAL_SYMBOLS) == HALAL_SYMBOLS else 'All coins'}\n"
        f"⏱ Timeframe: {context.user_data.get('interval', '4H')}"
    )

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = []
    symbols = context.user_data.get("symbols", HALAL_SYMBOLS)
    interval = context.user_data.get("interval", "4h")
    for symbol in symbols:
        df = get_klines(symbol, interval=interval)
        if df is None:
            continue
        entry = df["close"].iloc[-1]
        pump = detect_pump(df)
        tps, sl = calculate_targets(entry)
        msg = f"""
{'🚨 PUMP ALERT – TRADE CAREFULLY' if pump else '📈 BUY SIGNAL'}
🕌 *Halal Signal*
Currency: {symbol}
Timeframe: {interval}
Entry Price: {entry}
Take Profits:
TP1: {tps[0]:.4f}
TP2: {tps[1]:.4f}
TP3: {tps[2]:.4f}
TP4: {tps[3]:.4f}
Stop Loss: {sl:.4f}
Islamic Ruling: Halal ✅
Spot only – No leverage
"""
        messages.append(msg)
    if not messages:
        await update.message.reply_text("😴 No clear signals")
    else:
        for m in messages[:5]:  # limit spam
            await update.message.reply_markdown(m)

# ============== RUN BOT =================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CallbackQueryHandler(button))

print("✅ Halal Traders Bot starting...")

try:
    app.run_polling(drop_pending_updates=True)
except Exception as e:
    import traceback
    print("\n"*2, "═"*70)
    print("      BOT CRASHED !")
    print(f"      {type(e).__name__}: {e}")
    traceback.print_exc()
    print("═"*70)
