from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from trade_history import fetch_forex_history, simulate_trade_outcome
import my_config
from datetime import datetime, timedelta

llm = ChatOpenAI(api_key=my_config.OPENAI_API_KEY, model=my_config.OPENAI_MODEL)

def analyze_single_trade(trade):
    print("[DEBUG] Analyzing trade:", trade)
    
    base, quote = trade['currency_pair'].split('/')
    df = fetch_forex_history(base, quote)
    if df is None:
        return "❌ Could not fetch historical data."

    
    trade['timestamp'] = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    print("[DEBUG] Trade timestamp set to:", trade['timestamp'])
    outcome, future_candles = simulate_trade_outcome(trade, df)
    print("[DEBUG] Outcome:", outcome)
    print("[DEBUG] Future Candles Length:", len(future_candles))
    if not future_candles:
        return "⚠️ Could not simulate trade outcome — no future data available."



    # ✅ FORMAT the future_candles clearly for GPT
    formatted_candles = "\n".join(
        f"{row['timestamp'].strftime('%y-%m-%d')} | O:{row['open']:.4f} H:{row['high']:.4f} L:{row['low']:.4f} C:{row['close']:.4f}"
        for row in future_candles
    )
    print("[DEBUG] Formatted candles:\n" + formatted_candles)




    # ✅ GPT Prompt Template
    prompt = ChatPromptTemplate.from_template("""
    You are a Forex trade coach. Analyze this trade using recent market data and give direct, practical advice.

    📄 Trade Info:
    - User ID: {user_id}
    - Action: {action}
    - Entry Price: {price}
    - Stop Loss: {stop_loss}
    - Take Profit: {take_profit}
    - Outcome: {outcome}

    📉 Market Data (next 12 trading days):
    {formatted_candles}

    Respond with:
    1. 📈 Rating (Good, Average, Poor)
    2. 🧠 One improvement tip (Up to 10 words)
    3. 📊 Detailed analysis (1-2 paragraphs with clear reasoning)
    4. 📅 Suggested next steps (Up to 10 words)
                                              
    """)

    # ✅ Fill prompt
    formatted_prompt = prompt.format(
        user_id=trade['user_id'],
        action=trade['action'],
        price=trade['price'],
        stop_loss=trade['stop_loss'],
        take_profit=trade['take_profit'],
        outcome=outcome,
        formatted_candles=formatted_candles
    )

    # ✅ Send to GPT
    response = llm.invoke(formatted_prompt)
    return response.content
