import pandas as pd
import numpy as np

def calculate_sl_tp(entry_price, market_data, risk_reward_ratio=2):
    """
    Calculate dynamic stop loss (SL) and take profit (TP) based on market data.
    
    Args:
        entry_price (float): The trade entry price.
        market_data (pd.DataFrame): DataFrame with market data (columns: 'high', 'low', 'close').
        risk_reward_ratio (float): Desired risk-to-reward ratio.
    
    Returns:
        tuple: (stop_loss, take_profit)
    """
    # Calculate recent volatility using ATR (Average True Range)
    market_data['tr'] = np.maximum(
        market_data['high'] - market_data['low'],
        np.maximum(
            abs(market_data['high'] - market_data['close'].shift(1)),
            abs(market_data['low'] - market_data['close'].shift(1))
        )
    )
    atr = market_data['tr'].rolling(window=14).mean().iloc[-1]  # 14-period ATR

    # Determine stop loss and take profit
    stop_loss = entry_price - atr if entry_price > market_data['close'].iloc[-1] else entry_price + atr
    take_profit = entry_price + (atr * risk_reward_ratio) if entry_price > market_data['close'].iloc[-1] else entry_price - (atr * risk_reward_ratio)

    return round(stop_loss, 5), round(take_profit, 5)