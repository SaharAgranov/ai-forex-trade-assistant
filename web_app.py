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
    st.success(f"Loaded user {user_id}")

if st.sidebar.button("➕ Create New User"):
    new_id = max(user_list) + 1 if user_list else 1
    save_user_data(new_id, {"trades": []})
    st.session_state.user_id = new_id
    st.success(f"Created and loaded user {new_id}")

# Chat UI
st.title("💬 AI Forex Trade Assistant")

if st.session_state.user_id is None:
    st.warning("Please select or create a user from the sidebar.")
else:
    user_input = st.text_input("Enter your message:")
    if st.button("Send") and user_input:
        st.session_state.chat_log.append(("You", user_input))
        reply = chatbot_response(user_input, st.session_state.user_id)
        st.session_state.chat_log.append(("AI", reply))

    # Display chat
    for speaker, message in st.session_state.chat_log:
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
