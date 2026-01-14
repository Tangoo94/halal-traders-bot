import requests
import random

BINANCE_ENDPOINTS = [
    "https://api.binance.com",
    "https://api1.binance.com",
    "https://api2.binance.com",
    "https://api3.binance.com"
]

def get_binance_24h_data():
    base = random.choice(BINANCE_ENDPOINTS)
    url = f"{base}/api/v3/ticker/24hr"

    try:
        r = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("❌ Binance fetch error:", e)
        return None
