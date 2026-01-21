import asyncio
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, HALAL_COINS, ALL_COINS, VIP_CHAT_ID, FREE_CHAT_ID, DEFAULT_TIMEFRAME, SCAN_INTERVAL
from engine import run_engine, calculate_confidence, rsi_ema_confirmation

# --- USER SETTINGS ---
user_settings = {
    "coins": HALAL_COINS,
    "timeframes": [DEFAULT_TIMEFRAME],
    "interval": SCAN_INTERVAL,
    "chat_id": None,
    "mode": "silent",  # silent / aggressive
    "vip": False
}

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings["chat_id"] = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("🕌 Halal Coins Only", callback_data="halal")],
        [InlineKeyboardButton("💹 All Coins", callback_data="all")],
        [InlineKeyboardButton("⏱ Timeframes", callback_data="tf")],
        [InlineKeyboardButton("🔇 Silent / ⚡ Aggressive", callback_data="mode")],
        [InlineKeyboardButton("👑 VIP / Free", callback_data="vip")],
        [InlineKeyboardButton("⏩ Skip (Auto Mode)", callback_data="skip")],
        [InlineKeyboardButton("📡 Status", callback_data="status")]
    ]

    await update.message.reply_text(
        "🕌 Halal Traders Bot\nSmart Spot Signals",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- BUTTON HANDLER ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # --- COINS ---
    if q.data == "halal":
        user_settings["coins"] = HALAL_COINS
        await q.edit_message_text("✅ Halal coins enabled")

    elif q.data == "all":
        user_settings["coins"] = ALL_COINS
        await q.edit_message_text("⚠️ All coins enabled")

    # --- TIMEFRAMES ---
    elif q.data == "tf":
        kb = [
            [InlineKeyboardButton("5m", callback_data="5m"), InlineKeyboardButton("15m", callback_data="15m")],
            [InlineKeyboardButton("1H", callback_data="1h"), InlineKeyboardButton("4H", callback_data="4h")],
            [InlineKeyboardButton("1D", callback_data="1d")],
            [InlineKeyboardButton("✅ Single", callback_data="single"), InlineKeyboardButton("📊 Multiple", callback_data="multiple")]
        ]
        await q.edit_message_text("⏱ Select Timeframe(s):", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data in ["5m", "15m", "1h", "4h", "1d"]:
        if "multiple_selected" in user_settings and user_settings["multiple_selected"]:
            if q.data not in user_settings["timeframes"]:
                user_settings["timeframes"].append(q.data)
        else:
            user_settings["timeframes"] = [q.data]
        await q.edit_message_text(f"✅ Timeframes selected: {', '.join(user_settings['timeframes'])}")

    elif q.data == "single":
        user_settings["multiple_selected"] = False
        await q.edit_message_text("✅ Single timeframe mode")

    elif q.data == "multiple":
        user_settings["multiple_selected"] = True
        await q.edit_message_text("✅ Multiple timeframe mode enabled")

    # --- MODE ---
    elif q.data == "mode":
        user_settings["mode"] = "aggressive" if user_settings["mode"] == "silent" else "silent"
        await q.edit_message_text(f"⚡ Mode set to {user_settings['mode'].capitalize()}")

    # --- VIP / FREE ---
    elif q.data == "vip":
        user_settings["vip"] = not user_settings["vip"]
        await q.edit_message_text(f"👑 {'VIP' if user_settings['vip'] else 'Free'} channel enabled")

    # --- SKIP / AUTO ---
    elif q.data == "skip":
        await q.edit_message_text("⏩ Auto mode started")
        asyncio.create_task(run_engine(context, user_settings))

    # --- STATUS ---
    elif q.data == "status":
        msg = f"""
📡 BOT STATUS

Mode: {user_settings['mode'].capitalize()}
Coins: {len(user_settings['coins'])} ({'Halal' if user_settings['coins']==HALAL_COINS else 'All'})
Timeframes: {', '.join(user_settings['timeframes'])}
VIP: {'Yes' if user_settings['vip'] else 'No'}
Engine: Running
"""
        await q.edit_message_text(msg)

# --- MAIN ---
def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN not found. Check your environment variables.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("✅ Halal Traders Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
