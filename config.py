# config.py

# --- TELEGRAM ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your Telegram bot token

# --- COINS ---
HALAL_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Halal coins example
ALL_COINS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "DOGEUSDT", "ADAUSDT", "XRPUSDT"]  # All coins

# --- TIMEFRAMES & SCAN ---
DEFAULT_TIMEFRAME = "4h"
SCAN_INTERVAL = 60  # seconds between scans

# --- ALERT SETTINGS ---
ALERT_CHAT_ID = None  # will be set dynamically per user
