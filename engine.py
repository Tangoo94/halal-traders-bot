# engine.py
import asyncio
import random
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

# Placeholder: replace with actual trading library / API
def calculate_signal(coin, timeframe):
    """
    Fake signal generator.
    Real implementation should:
      - Fetch candle data
      - Calculate RSI + EMA
      - Decide BUY / SELL
      - Return confidence 0-100%
    """
    signal = random.choice(["BUY", "SELL", "HOLD"])
    confidence = random.randint(50, 100)
    return signal, confidence

async def run_engine(context, settings):
    """
    Main engine loop to scan selected coins and send signals.
    """
    chat_id = settings["chat_id"]
    if settings["channel"] == "vip":
        chat_id = settings.get("vip_chat_id") or chat_id
    else:
        chat_id = settings.get("free_chat_id") or chat_id

    coins = settings.get("selected_coins") or settings["coins"]
    timeframes = settings.get("timeframes") or [settings["timeframe"]]

    while True:
        for coin in coins:
            for tf in timeframes:
                signal, confidence = calculate_signal(coin, tf)
                
                if signal != "HOLD":
                    mode = settings.get("mode", "silent")
                    # Silent mode: only high confidence
                    if mode == "silent" and confidence < 70:
                        continue

                    text = f"📊 {coin} ({tf})\nSignal: {signal}\nConfidence: {confidence}%\nMode: {mode.upper()}"
                    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Details", callback_data="details")]])

                    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
        await asyncio.sleep(settings.get("interval", 60))
