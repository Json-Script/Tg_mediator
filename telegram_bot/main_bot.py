import json
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Environment variables (ensure they are set properly in GitHub Actions)
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

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

# Command handler for /all
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure only the owner can send to all
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    # Get the message to send to all users
    message = " ".join(context.args)
    if not message:
        await update.message.reply_text("Please provide a message to send to all users.")
        return

    # Load users from the file
    users = load_users()
    
    # Send the message to all users
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            # If there is an error (e.g., user blocked the bot), log it
            print(f"Failed to send message to {user_id}: {e}")

    await update.message.reply_text(f"Message sent to {len(users)} users.")

# Function to track users who start the bot
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    users = load_users()
    
    # Add user ID if not already present
    if user_id not in users:
        users.append(user_id)
        save_users(users)
    
    # Send a welcome message
    await update.message.reply_text("Hello! You're now registered to receive messages from the owner.")

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Add handlers for commands
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("all", all_command))

# Run the bot
app.run_polling()