import os
import logging
from datetime import datetime
import subprocess  # To get the Git commit hash
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes

# Set up logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))  # Ensure CHAT_ID is an integer

# Get the current git commit hash
def get_git_commit():
    try:
        commit_hash = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode('utf-8')
    except Exception as e:
        logger.error(f"Could not get git commit hash: {e}")
        commit_hash = "Unknown"
    return commit_hash

COMMIT_HASH = get_git_commit()

# Log the environment variables for debugging
logger.debug(f"Telegram Token: {BOT_TOKEN}")
logger.debug(f"Chat ID (CHAT_ID): {CHAT_ID}")

if not CHAT_ID:
    logger.error("Error: CHAT_ID is empty. Please set the CHAT_ID environment variable.")

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Define message handler
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    load_time = round(context.application.startup_duration, 2) if context.application.startup_duration else "N/A"

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Construct the forwarded message
    forwarded_text = (
        f"{user_message}\n\n\n"
        f"User: @{username} (ID: {user_id})\n"
        f"Sent on: {timestamp}\n"
        f"Commit Hash: {COMMIT_HASH}\n"
        f"Load Time: {load_time} seconds"
    )

    # Send the constructed message to the owner
    await context.bot.send_message(chat_id=CHAT_ID, text=forwarded_text)
    await update.message.reply_text("Your message has been sent to the owner.")

# Other handler functions remain the same
# (send_command, help_command, start_command)

# Add handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()