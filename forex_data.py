import requests
import my_config

API_KEY = 'ALPHA_VANTAGE_API_KEY'

def get_forex_rate(from_currency='USD', to_currency='EUR'):
    url = (
        f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE"
        f"&from_currency={from_currency}&to_currency={to_currency}"
        f"&apikey={API_KEY}"
    )
    response = requests.get(url)
    data = response.json()

    try:
        return float(data['Realtime Currency Exchange Rate']['5. Exchange Rate'])
    except KeyError:
        return None
