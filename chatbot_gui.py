
import tkinter as tk
import json
from tkinter import ttk
from users_data import list_all_users, load_user_data, save_user_data
from chatbot_logic import chatbot_response
from extract_data_with_gpt import extract_trade_with_openai
import tkinter as tk
from tkinter import simpledialog, messagebox, scrolledtext, ttk

class TradeBotGUI:
    def __init__(self, root):

        self.root = root
        self.root.title("📊 AI Forex Trade Assistant")
        self.user_id = None
        self.user_data = load_user_data(self.user_id)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=25, state='disabled')
        self.chat_display.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # Add welcome message to chat
        self.append_chat(
            "💬 Welcome to the AI Forex Trade Assistant!\n"
            "Here's what you can do:\n"
            "• 📈 Enter trade commands like: 'Buy 1000 EUR/USD at 1.09, SL 1.08, TP 1.10'\n"
            "   - You can use 'Buy' or 'Sell'\n"
            "   - If you leave out the price, the trade will be executed immediately at market price\n"
            "   - If you include a price, the trade will be held until that price is reached\n"
            "• 👤 Switch between users using the dropdown, or create a new one\n"
            "• 📜 View your trade history on the right\n"
            "• 🤖 Talk naturally - the AI will extract and track your trades for you!\n\n"
            "Type your first command or message below to get started ⬇️"
            )


        # Entry field and buttons
        self.entry = tk.Entry(root, width=50)
        self.entry.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

        self.send_button = tk.Button(root, text="Send", command=self.send_message)
        self.send_button.grid(row=1, column=1, pady=(0, 10), sticky="w")

        # Dropdown for user selection
        self.user_selector = ttk.Combobox(root, values=list_all_users(), width=10)
        self.user_selector.set("Select User ID")
        self.user_selector.grid(row=1, column=2, padx=5)

        self.load_user_button = tk.Button(root, text="Load User", command=self.load_user)
        self.load_user_button.grid(row=1, column=3)

        # New user button
        self.new_user_button = tk.Button(root, text="➕ Create User", command=self.create_user)
        self.new_user_button.grid(row=1, column=4, padx=5)

        # Trade history box
        self.history_box = scrolledtext.ScrolledText(root, width=50, height=25, state='disabled')
        self.history_box.grid(row=0, column=5, padx=(10, 20), pady=10)

        self.refresh_trade_history()

    def send_message(self):
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self.entry.delete(0, tk.END)
        self.append_chat(f"You: {user_input}")

        reply = chatbot_response(user_input, self.user_id, self.user_data)
        self.append_chat(f"AI: {reply}")

        self.refresh_trade_history()

    def append_chat(self, text):
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, text + "\n\n")
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def load_user(self):
        uid_str = self.user_selector.get().strip()
        if not uid_str.isdigit():
            messagebox.showerror("Invalid Input", "Please select a valid numeric user ID.")
            return
        uid = int(uid_str)
        self.user_id = uid
        self.user_data = load_user_data(uid)
        self.append_chat(f"✅ Loaded user {uid}")
        self.refresh_trade_history()

    def create_user(self):
        uid = simpledialog.askinteger("Create New User", "Enter new user ID:")
        if uid is None:
            return
        try:
            save_user_data(uid, {"trades": []})
            self.user_selector['values'] = list_all_users()
            self.user_selector.set(str(uid))
            self.user_id = uid
            self.user_data = load_user_data(uid)
            self.append_chat(f"✅ Created and loaded user {uid}")
            self.refresh_trade_history()
        except Exception as e:
            messagebox.showerror("Error", f"Could not create user: {e}")

    def refresh_trade_history(self):
        self.history_box.configure(state='normal')
        self.history_box.delete(1.0, tk.END)
        trades = self.user_data.get("trades", [])
        if not trades:
            self.history_box.insert(tk.END, "No trades yet.")
        else:
            for trade in trades[-20:]:  # Show last 20 trades
                self.history_box.insert(
                    tk.END,
                    f"{trade['action'].upper()} {trade['amount']} {trade['currency_pair']} @ {trade['price']} "
                    f"(SL: {trade['stop_loss']}, TP: {trade['take_profit']})\n"
                )
        self.history_box.configure(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    gui = TradeBotGUI(root)
    root.mainloop()
