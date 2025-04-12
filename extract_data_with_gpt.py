from openai import OpenAI
import json
import my_config
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# client = OpenAI(api_key=my_config.OPENAI_API_KEY)

trade_function_schema = {
    "name": "parse_trade",
    "description": "Extracts trade details from a customer message",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["buy", "sell"],
                "description": "The type of trade"
            },
            "amount": {
                "type": "integer",
                "description": "The amount of currency to trade"
            },
            "currency_pair": {
                "type": "string",
                "description": "The currency pair, e.g. EUR/USD"
            },
            "price": {
                "type": "number",
                "description": "The price at which the trade should be executed"
            },
            "stop_loss": { 
                "type": "number",
                "description": "The stop loss price for the trade"
            },
            "take_profit": { 
                "type": "number",
                "description": "The take profit price for the trade"
            }
            
        },
        #"required": ["action", "amount", "currency_pair", "price"]
    }
}

def extract_trade_with_openai(user_input: str):
    try:
        response = client.chat.completions.create(
            model=my_config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a forex trading assistant. Extract trade intent from natural language."},
                {"role": "user", "content": user_input}
            ],
            tools=[{"type": "function", "function": trade_function_schema}],
            tool_choice="auto"
        )
        tool_calls = response.choices[0].message.tool_calls
        if tool_calls:
            args = tool_calls[0].function.arguments
            return json.loads(args)
    except Exception as e:
        print(f"[DEBUG] NLP extraction failed with error: {e}")
    return None
