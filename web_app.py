import streamlit as st
from chatbot_logic import chatbot_response
from users_data import list_all_users, load_user_data, save_user_data

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'chat_log' not in st.session_state:
    st.session_state.chat_log = []

# Sidebar: User management
st.sidebar.header("User Management")
user_list = list_all_users()
user_id = st.sidebar.selectbox("Select User ID", user_list)
if st.sidebar.button("Load User"):
    st.session_state.user_id = int(user_id)
    st.session_state.chat_log = []  # Reset chat log for new user
    st.success(f"Loaded user {user_id}")

if st.sidebar.button("➕ Create New User"):
    numeric_ids = [int(uid) for uid in user_list]
    new_id = max(numeric_ids) + 1 if numeric_ids else 1
    save_user_data(new_id, {"trades": []})
    st.session_state.user_id = new_id
    st.session_state.chat_log = []  # 👈 Clear chat log for new user
    st.success(f"Created and loaded user {new_id}")


# Chat UI
st.title("💬 AI Forex Trade Assistant")

if st.session_state.user_id is None:
    st.warning("Please select or create a user from the sidebar.")
else:
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


import os
import streamlit as st

USER_DATA_FOLDER = "user_data"  # adjust this to your real folder

st.subheader("🗑️ Delete a User")

# List all users
users = [f.replace(".json", "") for f in os.listdir(USER_DATA_FOLDER) if f.endswith(".json")]

if users:
    user_to_delete = st.selectbox("Select a user to delete:", users)

    if st.button("Delete User"):
        file_path = os.path.join(USER_DATA_FOLDER, f"{user_to_delete}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            st.success(f"✅ User '{user_to_delete}' deleted.")
        else:
            st.error("❌ File not found.")
else:
    st.info("No users found.")

