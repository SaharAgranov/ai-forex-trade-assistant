import pandas as pd
import datetime
import requests
import os
import my_config

API_KEY = my_config.ALPHA_VANTAGE_API_KEY
HISTORY_FOLDER = "data/history"
os.makedirs(HISTORY_FOLDER, exist_ok=True)

def fetch_forex_history(base: str, quote: str):
    file_path = f"{HISTORY_FOLDER}/{base}_{quote}_1y.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path, parse_dates=['timestamp'])

    url = f"https://www.alphavantage.co/query?function=FX_DAILY&from_symbol={base}&to_symbol={quote}&outputsize=full&apikey={API_KEY}"
    r = requests.get(url).json()

    if "Time Series FX (Daily)" not in r:
        return None

    df = pd.DataFrame.from_dict(r["Time Series FX (Daily)"], orient="index")
    df.columns = ['open', 'high', 'low', 'close']
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df[df.index >= (datetime.datetime.now() - datetime.timedelta(days=365))]
    df.reset_index(inplace=True)
    df.rename(columns={"index": "timestamp"}, inplace=True)
    df.to_csv(file_path, index=False)

    return df

def simulate_trade_outcome(trade, df):
    print("[DEBUG] Simulating trade outcome...")
    trade_time = pd.to_datetime(trade['timestamp'])
    future_data = df[df['timestamp'] > trade_time].head(12)
    print("[DEBUG] Future data length:", len(future_data), "Future data:", future_data)
    sl, tp, action = trade['stop_loss'], trade['take_profit'], trade['action']

    outcome = "open"
    for _, row in future_data.iterrows():
        high, low = row['high'], row['low']
        if action == "buy":
            if low <= sl:
                outcome = "loss"
                break
            elif high >= tp:
                outcome = "profit"
                break
        else:
            if high >= sl:
                outcome = "loss"
                break
            elif low <= tp:
                outcome = "profit"
                break

    return outcome, future_data[['timestamp', 'open', 'high', 'low', 'close']].to_dict(orient='records')


# in trade_history.py

import pandas as pd
from datetime import datetime


def get_dynamic_sl_tp(
    action,
    entry_price,
    currency_pair,
    timestamp=None,
    lookback=20,
    method="volatility"  # options: 'volatility', 'bollinger'
):
    """
    Dynamically compute SL/TP using selected logic:
    - 'volatility': uses recent high/low and avg candle range
    - 'bollinger': uses Bollinger Bands to define SL/TP
    """
    base, quote = currency_pair.split('/')
    df = fetch_forex_history(base, quote)
    if df is None or len(df) < lookback:
        return None, None

    # Preprocess time
    if isinstance(timestamp, str):
        timestamp = pd.to_datetime(timestamp)
    if timestamp:
        df = df[df['timestamp'] < timestamp]

    recent = df.tail(lookback)
    if recent.empty:
        return None, None

    if method == "volatility":
        recent_high = recent['high'].max()
        recent_low = recent['low'].min()
        avg_range = (recent['high'] - recent['low']).mean()

        if action == 'buy':
            sl = round(recent_low - avg_range * 0.2, 5)
            tp = round(recent_high + avg_range * 0.5, 5)
        else:  # sell
            sl = round(recent_high + avg_range * 0.2, 5)
            tp = round(recent_low - avg_range * 0.5, 5)

    elif method == "bollinger":
        close = recent['close']
        sma = close.rolling(window=lookback).mean().iloc[-1]
        std = close.rolling(window=lookback).std().iloc[-1]
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std

        if action == 'buy':
            sl = round(lower_band - std * 0.5, 5)
            tp = round(upper_band + std * 0.5, 5)
        else:
            sl = round(upper_band + std * 0.5, 5)
            tp = round(lower_band - std * 0.5, 5)

    else:
        raise ValueError("Invalid method. Use 'volatility' or 'bollinger'.")

    return sl, tp
