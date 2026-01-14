import requests

BINANCE_24H_URL = "https://api.binance.com/api/v3/ticker/24hr"

def get_binance_24h_data():
    try:
        r = requests.get(BINANCE_24H_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("❌ Binance fetch error:", e)
        return None
