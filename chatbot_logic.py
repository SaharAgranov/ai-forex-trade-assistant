from openai import OpenAI
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import my_config
import pandas as pd
import re
import os
import xmltodict
from forex_data import get_forex_rate
from datetime import datetime
from users_data import list_all_users, load_user_data, save_user_data
from extract_data_with_gpt import extract_trade_with_openai

# Session state
pending_trade = None
confirmation_waiting = False

client = OpenAI(api_key=my_config.OPENAI_API_KEY)

# Session memory for trade state
trade_session = {
    'action': None,
    'amount': None,
    'currency_pair': None,
    'price': None
}

# Reset function
def reset_trade_session():
    global trade_session
    trade_session = {'action': None, 'amount': None, 'currency_pair': None, 'price': None}

def chatbot_response(user_input, user_id=1, user_data=None):
    global pending_trade, confirmation_waiting, trades_df
    user_input = user_input.lower().strip()

    if user_data is None:
        from users_data import load_user_data
        user_data = load_user_data(user_id)


    # --- Confirmation Step ---
    if confirmation_waiting:
        if user_input in ["yes", "confirm", "y", "okay", "sure"]:
            confirmation_waiting = False
            action = pending_trade['action']
            amount = pending_trade['amount']
            currency_pair = pending_trade['currency_pair']
            # price = pending_trade.get('price')
            price = pending_trade['price']
            # is_limit_order = pending_trade.get('price') is not None


            currency_pair = pending_trade.get('currency_pair', '').strip()

            # Validate and auto-correct currency pair format
            if '/' in currency_pair:
                parts = currency_pair.split('/')
            else:
                parts = currency_pair.split()

            parts = [p.upper() for p in parts if p.isalpha()]
            
            if len(parts != 2):
                return "⚠️ Invalid currency pair format. Please use 'EUR/USD'"

            currency_pair = f"{parts[0]}/{parts[1]}"
            pending_trade['currency_pair'] = currency_pair

            base, quote = parts

            # Fetch market price if not given (market order)
            if not price:
                print(f"[DEBUG] Fetching market price for {currency_pair}...")
                price = get_forex_rate(base, quote)
                if price is None:
                    confirmation_waiting = False
                    pending_trade = None
                    return (
                        "⚠️ Sorry, I couldn't fetch a valid market price right now. "
                        "Please try again in a few seconds or set a custom price manually."
                    )
                pending_trade['price'] = price



            sl = pending_trade.get('stop_loss')
            tp = pending_trade.get('take_profit')

            # SL/TP
            sl_pct, tp_pct = 0.01, 0.03
            if action == 'buy':
                sl = sl or round(price * (1 - sl_pct), 5)
                tp = tp or round(price * (1 + tp_pct), 5)
            else:
                sl = sl or round(price * (1 + sl_pct), 5)   
                tp = tp or round(price * (1 - tp_pct), 5)

            # Risk rate
            risk_rate = 0.02
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            new_trade = pd.DataFrame([{
                'user_id': user_id,
                'currency_pair': currency_pair.upper(),
                'action': action,
                'amount': amount,
                'price': price,
                'stop_loss': sl,
                'take_profit': tp,
                'risk_rate': risk_rate,
                'timestamp': timestamp
            }])


            from trade_analysis_gpt import analyze_single_trade
            analysis = analyze_single_trade(new_trade.iloc[0])
            print(f"[DEBUG] Analysis result: {analysis}")
            pending_trade = None
            
            if "trades" not in user_data:
                user_data["trades"] = []
            user_data["trades"].append(new_trade.iloc[0].to_dict())
            save_user_data(user_id, user_data)

            confirmation_waiting = False
            pending_trade = None

            # Save user data
            return (f"✅ Trade confirmed: {action.upper()} {amount} {currency_pair} at {price} "
                    f"(SL: {sl}, TP: {tp}).\n\n💡 AI Feedback:\n{analysis}")
        
        else:
            confirmation_waiting = False
            pending_trade = None
            return "❌ Trade cancelled, enter a new trade or exit."
            

    # --- NLP: Try every time to fill in missing fields ---
    try:
        required = ['action', 'amount', 'currency_pair', 'price']
        missing = [field for field in required if not pending_trade or not pending_trade.get(field)]

        # only run NLP if something is missing
        if missing:
            parsed = extract_trade_with_openai(user_input)
            print(f"[DEBUG] user input: {user_input}")
            if parsed:
                if not pending_trade:
                    pending_trade = {}
                for key, value in parsed.items():
                    if not pending_trade.get(key):
                        pending_trade[key] = value
                print(f"[DEBUG] NLP filled: {parsed}")
            else:
                print("[DEBUG] NLP could not extract anything.")
    except Exception as e:
        print(f"[DEBUG] NLP error: {e}")


    # --- Manual Fallback Parser ---
    if pending_trade and not confirmation_waiting:
        words = user_input.split()

        if not pending_trade.get('action') and ("buy" in words or "sell" in words):
            pending_trade['action'] = "buy" if "buy" in words else "sell"
            print(f"[DEBUG] Fallback action parsed: {pending_trade['action']}")

        for word in words:
            if "/" in word and not pending_trade.get('currency_pair'):
                pending_trade['currency_pair'] = word.upper()
            elif word.replace('.', '', 1).isdigit():
                value = float(word)
                if not pending_trade.get('amount'):
                    pending_trade['amount'] = int(value)
                elif not pending_trade.get('price') and 0.5 <= value <= 2.0:
                    pending_trade['price'] = value

    market_price = None
        # Try to fetch price if it's missing (market order fallback)
    if pending_trade and not pending_trade.get('price'):
          # Ensure 'currency_pair' exists
        if not pending_trade.get('currency_pair'):
            return "⚠️ Missing currency pair. Please specify a valid currency pair (e.g., 'EUR/USD')."

        base, quote = pending_trade['currency_pair'].split('/')
        market_price = get_forex_rate(base, quote)
        print(f"[DEBUG] Fallback market price fetched: {market_price}")

        if market_price is None:
            pending_trade = None
            return (
                "⚠️ I couldn't fetch a valid market price right now. "
                "Please try again in a few seconds or provide a custom price."
            )

        pending_trade['price'] = market_price
        pending_trade['auto_price'] = True
        print(f"[DEBUG] Market price used: {market_price}")


    # --- Check what’s still missing ---
    required = ['action', 'amount', 'currency_pair', 'price']
    if not pending_trade:
        pending_trade = {}
        print(pending_trade)

    missing = [field for field in required if not pending_trade.get(field)]

    if missing:
        example = {
            'action': '**buy/sell**',
            'amount': '**10000**',
            'currency_pair': '**EUR/USD**',
            'price': '**1.0850**'
        }
        for k in pending_trade:
            if pending_trade[k]:
                example[k] = str(pending_trade[k])

        message = f"📝 I still need: {', '.join(f'**{m}**' for m in missing)}.\n"
        message += f"💡 Example: `{example['action']} {example['amount']} {example['currency_pair']} at {example['price']} (or leave empty for stock price)`"
        return message



    # --- Everything ready → Ask for confirmation ---
    confirmation_waiting = True
    is_limit_order = not pending_trade.get('auto_price', False)

    if is_limit_order:
        price_msg = f"at custom price {pending_trade['price']} (this is a limit order and will be held until the market reaches this price)"
    else:
        price_msg = f"**at the current market price {market_price}** (this is a market order and will be executed immediately)"

    return (
    f"You asked to **{pending_trade['action'].upper()} {pending_trade['amount']} "
    f"{pending_trade['currency_pair']} {price_msg}**.\n\n"
    f"Stop Loss: {pending_trade.get('stop_loss')} | Take Profit: {pending_trade.get('take_profit')}.\n"
    f"(If SL/TP not set, I will set them automatically)\n\n"
    f"📩 Should I proceed? (yes/no)"
)

# Test CLI loop
if __name__ == "__main__":
    user_data = load_user_data()
    print("💬 Hello user number 1, I'm your AI Trade Assistant. Type 'exit' to stop.")
    while True:
        user_input = input("You: ")
        reply = chatbot_response(user_input)
        print("AI Agent:", reply)
        if user_input.lower() in ['exit', 'quit']:
            print("Exiting...")
            break
