import os
import streamlit as st
from chatbot_logic import chatbot_response
from users_data import list_all_users, load_user_data, save_user_data

# USER_DATA_FOLDER = "user_data"
# os.makedirs(USER_DATA_FOLDER, exist_ok=True)

USER_FOLDER = "users"
os.makedirs(USER_FOLDER, exist_ok=True)


# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'chat_log' not in st.session_state:
    st.session_state.chat_log = []

# Sidebar: User management
st.sidebar.header("User Management")
user_list = list_all_users()
user_id = st.sidebar.selectbox("Select User ID", user_list)

# Load User Button
if st.sidebar.button("✅ Load User"):
    st.session_state.user_id = int(user_id)
    st.session_state.chat_log = []
    st.success(f"Loaded user {user_id}")

# Create New User Button
if st.sidebar.button("➕ Create New User"):
    numeric_ids = [int(uid) for uid in user_list]
    new_id = max(numeric_ids) + 1 if numeric_ids else 1
    save_user_data(new_id, {"trades": []})
    st.session_state.user_id = new_id
    st.session_state.chat_log = []
    st.success(f"Created and loaded user {new_id}")
    st.rerun()  # Refresh the user list

# Delete User Button
if st.sidebar.button("🗑️ Delete User"):
    file_path = os.path.join(USER_FOLDER, f"user_{user_id}.json")

    st.sidebar.write(f"🔍 Looking for: `{file_path}`")  # Debug info

    if os.path.isfile(file_path):
        os.remove(file_path)
        st.success(f"User {user_id} deleted successfully.")
        if st.session_state.user_id == int(user_id):
            st.session_state.user_id = None
            st.session_state.chat_log = []
        st.rerun()
    else:
        st.sidebar.error("❌ User file not found.")


# Main Chat UI
st.title("💬 AI Forex Trade Assistant")

if st.session_state.user_id is None:
    st.warning("Please select or create a user from the sidebar.")
else:
    # Show welcome message at the beginning of a new session
    if not st.session_state.chat_log:
        welcome_msg = (
            "👋 Welcome to the AI Forex Trade Assistant!\n\n"
            "- Type something like **buy 1000 EUR/USD** to open a trade.\n"
            "- You can leave the price blank to buy/sell at the market rate.\n"
            "- You’ll be asked to choose SL/TP methods or enter them manually.\n\n"
            "📌 Type your first message below to begin!"
        )
        st.session_state.chat_log.append(("AI", welcome_msg))
        
    user_input = st.chat_input("Enter your message:")
    if user_input:
        st.session_state.chat_log.append(("You", user_input))
        reply = chatbot_response(user_input, st.session_state.user_id)
        st.session_state.chat_log.append(("AI", reply))

    # Display chat
    for speaker, message in st.session_state.chat_log:
        icon = "🤖" if speaker == "AI" else "🧑"
        st.markdown(f"**{speaker}:** {message}")

    # Trade History
    st.subheader("Trade History")
    user_data = load_user_data(st.session_state.user_id)
    trades = user_data.get("trades", [])
    if not trades:
        st.info("No trades yet.")
    else:
        for trade in trades[-10:]:
            st.markdown(
                f"- **{trade['action'].upper()} {trade['amount']} {trade['currency_pair']}** @ {trade['price']} "
                f"(SL: {trade['stop_loss']}, TP: {trade['take_profit']})"
            )
