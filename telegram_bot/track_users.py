import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# File to store user IDs
USER_FILE = 'users.json'

# Ensure the users file exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as f:
        json.dump([], f)

# Function to load user IDs from the file
def load_users():
    with open(USER_FILE, 'r') as f:
        return json.load(f)

# Function to save user IDs to the file
def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

# Command handler to track users who start the bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    users = load_users()
    
    # Add user ID if not already present
    if user_id not in users:
        users.append(user_id)
        save_users(users)
    
    # Send a welcome message
    await update.message.reply_text("Hello! You're now registered to receive messages from the owner.")