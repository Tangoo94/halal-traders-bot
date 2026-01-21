import asyncio
from market import get_klines
from filters import apply_indicators, early_signal
from utils import format_signal

sent_signals = set()

async def run_engine(context, settings):
    while True:
        coins = settings["coins"]
        tf = settings["timeframe"]

        for symbol in coins:
            try:
                df = get_klines(symbol, tf)
                df = apply_indicators(df)

                signal_id = f"{symbol}_{tf}"

                if early_signal(df) and signal_id not in sent_signals:
                    msg = format_signal(symbol, tf)
                    await context.bot.send_message(
                        chat_id=settings["chat_id"],
                        text=msg
                    )
                    sent_signals.add(signal_id)

            except Exception as e:
                print("Engine error:", e)

        await asyncio.sleep(settings["interval"])
