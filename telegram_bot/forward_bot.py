import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

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

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Define the path for storing user IDs
USER_LIST_FILE = "users_list.txt"

# Load user IDs from the file if it exists, otherwise create an empty list
def load_user_ids():
    if os.path.exists(USER_LIST_FILE):
        with open(USER_LIST_FILE, "r") as f:
            return [int(line.strip()) for line in f.readlines()]
    return []

# Save a new user ID to the list file
def save_user_id(user_id):
    with open(USER_LIST_FILE, "a") as f:
        f.write(f"{user_id}\n")

# Define message handler for text messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Send message with username and ID of the sender
    await context.bot.send_message(chat_id=CHAT_ID, text=f"Message from {username} (ID: {user_id}): {user_message}")
    await update.message.reply_text("Your message has been sent to the owner.")

# Define handler for the /all command
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Get the message to send to all users
    message = " ".join(context.args)

    if not message:
        await update.message.reply_text("Please provide a message to send to all users.")
        return

    # Load user IDs and send the message to all users
    user_ids = load_user_ids()
    for user_id in user_ids:
        try:
            await context.bot.send_message(chat_id=user_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send message to {user_id}: {e}")

    await update.message.reply_text(f"Message sent to {len(user_ids)} users.")

# Define handler for /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Save user ID if it's not already in the list
    user_ids = load_user_ids()
    if user_id not in user_ids:
        save_user_id(user_id)
        logger.debug(f"Added {username} ({user_id}) to the user list.")

    start_text = (
        "Hello and welcome! 🫂\n\n"
        "I’m your forwarder bot. I am the intermediary between you and the senior manager. I will personally forward your messages to the owner.\n\n"
        "How can I assist you today? You can type /help to see the available commands."
    )
    await update.message.reply_text(start_text)

# Add handlers for text, photos, and videos
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(CommandHandler("all", all_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()