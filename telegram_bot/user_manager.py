import os
import json
from telegram.ext import ContextTypes

# Path to the user IDs file
USER_IDS_FILE = "Telegram_bot/user_ids.json"

# Ensure the file exists initially
if not os.path.exists(USER_IDS_FILE):
    with open(USER_IDS_FILE, "w") as f:
        json.dump([], f)

# Load saved user IDs from file
def load_user_ids():
    with open(USER_IDS_FILE, "r") as f:
        return json.load(f)

# Save a new user ID if it's not already saved
def save_user_id(user_id):
    user_ids = load_user_ids()
    if user_id not in user_ids:
        user_ids.append(user_id)
        with open(USER_IDS_FILE, "w") as f:
            json.dump(user_ids, f)

# Send a message to all saved user IDs
async def send_to_all(context: ContextTypes.DEFAULT_TYPE, message):
    user_ids = load_user_ids()
    for user_id in user_ids:
        await context.bot.send_message(chat_id=user_id, text=message)