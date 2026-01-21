import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes
)

from config import *
from engine import run_engine

user_settings = {
    "coins": HALAL_COINS,
    "timeframe": DEFAULT_TIMEFRAME,
    "interval": SCAN_INTERVAL,
    "chat_id": None
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings["chat_id"] = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("🕌 Halal Coins Only", callback_data="halal")],
        [InlineKeyboardButton("💹 All Coins", callback_data="all")],
        [InlineKeyboardButton("⏱ Timeframe", callback_data="tf")],
        [InlineKeyboardButton("⏩ Skip (Auto Mode)", callback_data="skip")],
        [InlineKeyboardButton("📡 Status", callback_data="status")]
    ]

    await update.message.reply_text(
        "🕌 Halal Traders Bot\nSmart Spot Signals",
        reply_markup=InlineKeyboardMarkup(keyboard)
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
            [InlineKeyboardButton("1D", callback_data="1d")]
        ]
        await q.edit_message_text(
            "⏱ Select Timeframe",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif q.data in ["1h","4h","1d"]:
        user_settings["timeframe"] = q.data
        await q.edit_message_text(f"✅ Timeframe set to {q.data}")

    elif q.data == "skip":
        await q.edit_message_text("⏩ Auto mode started")
        asyncio.create_task(run_engine(context, user_settings))

    elif q.data == "status":
        msg = f"""
📡 BOT STATUS

Mode: {"Halal" if user_settings["coins"]==HALAL_COINS else "All Coins"}
Timeframe: {user_settings["timeframe"]}
Coins: {len(user_settings["coins"])}
Engine: Running
"""
        await q.edit_message_text(msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("✅ Halal Traders Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
