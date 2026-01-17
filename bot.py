# ================= CONFIG =================
BOT_TOKEN = "8235549857:AAHX_dJUl-Ve8qK5XzJVlPhqhuiEE76kS_Q"  # your new token
ADMIN_ID = 8497827576  # 🔴 PUT YOUR TELEGRAM ID HERE
BINANCE_BASE = "https://data.binance.vision"

HALAL_SYMBOLS = ["BTCUSDT", "ETHUSDT"]  # add your halal symbols here
SETTINGS = {
    "TP": [0.01, 0.02, 0.03, 0.05],  # default take profits
    "SL": 0.01,                       # default stop loss
    "PUMP": 0.05                       # default pump sensitivity
}

# ================= IMPORTS =================
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from utils import get_klines, detect_pump, calculate_targets  # make sure utils.py exists

# ================= BOT COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🕌 Halal Traders Bot Started\nUse /status to check bot status.")

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

# ================= ADMIN COMMANDS =================
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

# ================= RUN BOT =================
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("status", status))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("settp", settp))
app.add_handler(CommandHandler("setsl", setsl))
app.add_handler(CommandHandler("setpump", setpump))

print("✅ Halal Traders Bot starting...")

try:
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )
except Exception as e:
    print("\n"*2)
    print("═"*70)
    print("      BOT CRASHED !")
    print(f"      {type(e).__name__}: {e}")
    print("═"*70)
    import traceback
    traceback.print_exc()
    print("═"*70)
