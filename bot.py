import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from config import *
from engine import run_engine

# --- USER SETTINGS ---
user_settings = {
    "coins": [],
    "timeframe": DEFAULT_TIMEFRAME,
    "interval": SCAN_INTERVAL,
    "chat_id": None
}

# --- HELPER FUNCTIONS ---
def build_coin_keyboard(coins, selected=[]):
    kb = []
    row = []
    for i, coin in enumerate(coins, 1):
        text = f"{coin} {'✅' if coin in selected else ''}"
        row.append(InlineKeyboardButton(text, callback_data=f"coin_{coin}"))
        if i % 3 == 0:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    kb.append([InlineKeyboardButton("Confirm ✅", callback_data="confirm_coins")])
    kb.append([InlineKeyboardButton("Select All ✅", callback_data="select_all")])
    return InlineKeyboardMarkup(kb)

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings["chat_id"] = update.effective_chat.id
    user_settings["coins"] = []

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
    data = q.data

    # --- MODE SELECTION ---
    if data == "halal":
        context.user_data["available_coins"] = HALAL_COINS.copy()
        context.user_data["selected_coins"] = []
        await q.edit_message_text(
            "🕌 Select Halal coins to monitor:",
            reply_markup=build_coin_keyboard(HALAL_COINS, [])
        )

    elif data == "all":
        context.user_data["available_coins"] = ALL_COINS.copy()
        context.user_data["selected_coins"] = []
        await q.edit_message_text(
            "💹 Select coins to monitor:",
            reply_markup=build_coin_keyboard(ALL_COINS, [])
        )

    # --- COIN SELECTION ---
    elif data.startswith("coin_"):
        coin = data.replace("coin_", "")
        selected = context.user_data.get("selected_coins", [])
        if coin in selected:
            selected.remove(coin)
        else:
            selected.append(coin)
        context.user_data["selected_coins"] = selected
        await q.edit_message_text(
            "Select coins to monitor:",
            reply_markup=build_coin_keyboard(context.user_data["available_coins"], selected)
        )

    elif data == "select_all":
        context.user_data["selected_coins"] = context.user_data["available_coins"].copy()
        await q.edit_message_text(
            "All coins selected ✅",
            reply_markup=build_coin_keyboard(context.user_data["available_coins"], context.user_data["selected_coins"])
        )

    elif data == "confirm_coins":
        user_settings["coins"] = context.user_data.get("selected_coins", [])
        await q.edit_message_text(f"✅ Monitoring coins: {', '.join(user_settings['coins'])}")
        asyncio.create_task(run_engine(context, user_settings))

    # --- TIMEFRAME ---
    elif data == "tf":
        kb = [
            [InlineKeyboardButton("5m", callback_data="5m"),
             InlineKeyboardButton("15m", callback_data="15m"),
             InlineKeyboardButton("1h", callback_data="1h")],
            [InlineKeyboardButton("4h", callback_data="4h"),
             InlineKeyboardButton("1d", callback_data="1d")]
        ]
        await q.edit_message_text(
            "⏱ Select Timeframe",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif data in ["5m", "15m", "1h", "4h", "1d"]:
        user_settings["timeframe"] = data
        await q.edit_message_text(f"✅ Timeframe set to {data}")

    # --- AUTO / SKIP ---
    elif data == "skip":
        await q.edit_message_text("⏩ Auto mode started")
        if not user_settings["coins"]:
            user_settings["coins"] = HALAL_COINS.copy()
        asyncio.create_task(run_engine(context, user_settings))

    # --- STATUS ---
    elif data == "status":
        msg = f"""
📡 BOT STATUS

Mode: {"Halal" if user_settings["coins"]==HALAL_COINS else "All Coins"}
Timeframe: {user_settings['timeframe']}
Coins: {len(user_settings['coins'])}
Engine: Running
"""
        await q.edit_message_text(msg)

# --- MAIN ---
def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN not found. Check Railway variables.")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    print("✅ Halal Traders Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
