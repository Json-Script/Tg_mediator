import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes, CallbackQueryHandler
import signal

# Set up logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))  # Ensure CHAT_ID is an integer

# Log the environment variables for debugging
logger.debug(f"Telegram Token: {BOT_TOKEN}")
logger.debug(f"Chat ID (CHAT_ID): {CHAT_ID}")

if not CHAT_ID:
    logger.error("Error: CHAT_ID is empty. Please set the CHAT_ID environment variable.")

# Store message history for all users with timestamps
user_message_history = {}
unsent_messages = []

# File paths for persistence
HISTORY_FILE = 'message_history.json'
UNSENT_FILE = 'unsent_messages.json'

# Load persisted data if files exist
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'r') as f:
        user_message_history = json.load(f)

if os.path.exists(UNSENT_FILE):
    with open(UNSENT_FILE, 'r') as f:
        unsent_messages = json.load(f)

# Save data to file (history and unsent messages)
def save_data():
    with open(HISTORY_FILE, 'w') as f:
        json.dump(user_message_history, f)
    with open(UNSENT_FILE, 'w') as f:
        json.dump(unsent_messages, f)

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Define message handler
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    timestamp = datetime.now()

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Store the message with timestamp in the history for the user
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    user_message_history[user_id].append({"username": username, "message": user_message, "timestamp": timestamp.isoformat()})

    # Send message with username and ID of the sender
    await context.bot.send_message(chat_id=CHAT_ID, text=f"Message from {username} (ID: {user_id}): {user_message}")
    
    # Send the confirmation message to the user with buttons
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Delete Message", callback_data=f"delete_{user_id}_{timestamp.isoformat()}"),
         InlineKeyboardButton("Resend Message", callback_data=f"resend_{user_id}_{timestamp.isoformat()}")]
    ])
    await update.message.reply_text("Your message has been sent to the owner.", reply_markup=reply_markup)

    # Save unsent messages for later
    unsent_messages.append({"user_id": user_id, "message": user_message, "timestamp": timestamp.isoformat()})
    save_data()

# Command handler for /send
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Parse command arguments
    try:
        target_id = context.args[0]
        message = " ".join(context.args[1:])

        # Ensure the target ID is an integer
        target_id = int(target_id)

        # Send the message to the specified target ID
        await context.bot.send_message(chat_id=target_id, text=message)
        await update.message.reply_text("Message sent successfully.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid format. Use /send <number_id> <message>.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send message: {e}")

# Command handler for /history (last 6 hours)
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Get the cutoff time for messages within the last 6 hours
    cutoff_time = datetime.now() - timedelta(hours=6)

    # Compile the recent chat history from all users
    history_text = ""
    for user_id, messages in user_message_history.items():
        for msg in messages:
            # Check if the message timestamp is within the last 6 hours
            message_time = datetime.fromisoformat(msg["timestamp"])
            if message_time >= cutoff_time:
                history_text += f"{msg['username']} (ID: {user_id}) at {message_time}:\n{msg['message']}\n\n"

    # Send history or indicate no recent history if none found
    if history_text:
        await update.message.reply_text(f"Chat history from the last 6 hours:\n{history_text}")
    else:
        await update.message.reply_text("No chat history from the last 6 hours.")

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here are the available commands:\n"
        "/send <number_id> <message> - Send a message to the specified user ID.\n"
        "/history - View the chat history from the last 6 hours (owner only).\n"
        "/help - Display this help message."
    )
    await update.message.reply_text(help_text)

# Callback handler for delete/resend actions
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action_data = query.data
    user_id, timestamp_str = action_data.split("_")[1:]

    # Retrieve the message from the unsent messages list
    timestamp = datetime.fromisoformat(timestamp_str)
    user_message = next((msg["message"] for msg in unsent_messages if msg["user_id"] == int(user_id) and msg["timestamp"] == timestamp_str), None)

    if action_data.startswith("delete"):
        # Remove message
        unsent_messages[:] = [msg for msg in unsent_messages if not (msg["user_id"] == int(user_id) and msg["timestamp"] == timestamp_str)]
        save_data()
        await query.answer("Message deleted successfully.")
        await query.edit_message_text("Your message has been deleted.")
    
    elif action_data.startswith("resend"):
        # Resend message to owner
        await query.answer("Message resent to the owner.")
        await query.edit_message_text(f"Message from {user_id}: {user_message}")
        await app.bot.send_message(chat_id=CHAT_ID, text=f"Resent message from {user_id}: {user_message}")

# Add handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("history", history_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CallbackQueryHandler(button_callback))

# Notify that the bot is turned on
async def notify_turn_on():
    await app.bot.send_message(CHAT_ID, "Bot turned on...")

# Start polling
app.run_polling(on_shutdown=notify_turn_on)

# Notify that the bot is turned off
def notify_turn_off(signum, frame):
    app.bot.send_message(CHAT_ID, "Bot turned off...")

# Set up shutdown handler (for bot shutdown notifications)
signal.signal(signal.SIGTERM, notify_turn_off)