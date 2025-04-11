import os
import json

USER_FOLDER = "users"

def load_user_data(user_id):
    path = os.path.join(USER_FOLDER, f"user_{user_id}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_user_data(user_id, data):
    os.makedirs(USER_FOLDER, exist_ok=True)
    path = os.path.join(USER_FOLDER, f"user_{user_id}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def list_all_users():
    os.makedirs(USER_FOLDER, exist_ok=True)
    return [
        f.replace("user_", "").replace(".json", "")
        for f in os.listdir(USER_FOLDER)
        if f.startswith("user_") and f.endswith(".json")
    ]
