# bot.py
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from config import *
from engine import run_engine

user_settings = {
    "coins": HALAL_COINS,
    "selected_coins": [],
    "timeframes": [DEFAULT_TIMEFRAME],
    "interval": SCAN_INTERVAL,
    "mode": "silent",  # silent / aggressive
    "channel": "vip",  # vip / free
    "chat_id": None,
    "confidence": 50
}

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_settings["chat_id"] = update.effective_chat.id
    keyboard = [
        [InlineKeyboardButton("🕌 Halal Coins", callback_data="halal")],
        [InlineKeyboardButton("💹 All Coins", callback_data="all")],
        [InlineKeyboardButton("⏱ Timeframe", callback_data="tf")],
        [InlineKeyboardButton("🎚 Mode", callback_data="mode")],
        [InlineKeyboardButton("📡 Status", callback_data="status")],
        [InlineKeyboardButton("⏩ Auto Mode / Skip", callback_data="skip")],
        [InlineKeyboardButton("💎 Channel", callback_data="channel")]
    ]
    await update.message.reply_text("🕌 Halal Traders Bot\nSmart Spot Signals",
                                    reply_markup=InlineKeyboardMarkup(keyboard))

# --- BUTTON HANDLER ---
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # --- COINS ---
    if q.data == "halal":
        user_settings["coins"] = HALAL_COINS
        kb = [[InlineKeyboardButton(c, callback_data=f"coin_{c}")] for c in HALAL_COINS]
        kb.append([InlineKeyboardButton("✅ Confirm", callback_data="confirm_coins")])
        await q.edit_message_text("Select Halal Coins:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data == "all":
        user_settings["coins"] = ALL_COINS
        kb = [[InlineKeyboardButton(c, callback_data=f"coin_{c}")] for c in ALL_COINS]
        kb.append([InlineKeyboardButton("Select All", callback_data="select_all")])
        kb.append([InlineKeyboardButton("✅ Confirm", callback_data="confirm_coins")])
        await q.edit_message_text("Select Coins:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("coin_"):
        coin = q.data.split("_")[1]
        if coin in user_settings["selected_coins"]:
            user_settings["selected_coins"].remove(coin)
        else:
            user_settings["selected_coins"].append(coin)
        await q.answer(f"Selected: {', '.join(user_settings['selected_coins'])}")
    elif q.data == "select_all":
        user_settings["selected_coins"] = user_settings["coins"]
        await q.answer(f"All coins selected ({len(user_settings['coins'])})")
    elif q.data == "confirm_coins":
        if not user_settings["selected_coins"]:
            await q.answer("⚠️ Select at least one coin")
        else:
            await q.edit_message_text(f"✅ Coins confirmed: {', '.join(user_settings['selected_coins'])}")

    # --- TIMEFRAMES ---
    elif q.data == "tf":
        kb = [[InlineKeyboardButton(x, callback_data=x)] for x in ["5m", "15m", "1h", "4h", "1d"]]
        kb.append([InlineKeyboardButton("Confirm", callback_data="confirm_tf")])
        await q.edit_message_text("Select Timeframes:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data in ["5m", "15m", "1h", "4h", "1d"]:
        if q.data not in user_settings["timeframes"]:
            user_settings["timeframes"].append(q.data)
        else:
            user_settings["timeframes"].remove(q.data)
        await q.answer(f"Selected: {', '.join(user_settings['timeframes'])}")
    elif q.data == "confirm_tf":
        await q.edit_message_text(f"✅ Timeframes confirmed: {', '.join(user_settings['timeframes'])}")

    # --- MODE ---
    elif q.data == "mode":
        kb = [[InlineKeyboardButton("Silent", callback_data="mode_silent")],
              [InlineKeyboardButton("Aggressive", callback_data="mode_aggressive")]]
        await q.edit_message_text("Select Mode:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("mode_"):
        user_settings["mode"] = q.data.split("_")[1]
        await q.edit_message_text(f"✅ Mode set to {user_settings['mode']}")

    # --- CHANNEL ---
    elif q.data == "channel":
        kb = [[InlineKeyboardButton("VIP", callback_data="channel_vip")],
              [InlineKeyboardButton("Free", callback_data="channel_free")]]
        await q.edit_message_text("Select Channel:", reply_markup=InlineKeyboardMarkup(kb))
    elif q.data.startswith("channel_"):
        user_settings["channel"] = q.data.split("_")[1]
        await q.edit_message_text(f"✅ Channel set to {user_settings['channel']}")

    # --- AUTO MODE / SKIP ---
    elif q.data == "skip":
        await q.edit_message_text("⏩ Auto mode started")
        asyncio.create_task(run_engine(context, user_settings))

    # --- STATUS ---
    elif q.data == "status":
        msg = f"""
📡 BOT STATUS
Mode: {user_settings['mode']}
Channel: {user_settings['channel']}
Timeframes: {', '.join(user_settings['timeframes'])}
Coins: {len(user_settings['selected_coins']) if user_settings['selected_coins'] else 'None'}
Engine: Running
"""
        await q.edit_message_text(msg)

# --- MAIN ---
def main():
    if not BOT_TOKEN:
        raise RuntimeError("❌ BOT_TOKEN not found.")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("✅ Halal Traders Bot Running")
    app.run_polling()

if __name__ == "__main__":
    main()
