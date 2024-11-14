import os
import time
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

# Set the rate limit (e.g., 5 messages per 60 seconds)
RATE_LIMIT = 5
TIME_WINDOW = 60  # in seconds

# Dictionary to keep track of user messages and timestamps
user_message_log = {}

# Anti-spam check
def is_spamming(user_id):
    current_time = time.time()

    # Initialize user message log if not present
    if user_id not in user_message_log:
        user_message_log[user_id] = []

    # Filter out messages outside the time window
    user_message_log[user_id] = [
        timestamp for timestamp in user_message_log[user_id]
        if current_time - timestamp < TIME_WINDOW
    ]

    # Check if the user exceeds the rate limit
    if len(user_message_log[user_id]) >= RATE_LIMIT:
        return True

    # Log the current message timestamp
    user_message_log[user_id].append(current_time)
    return False

# Define message handler for text messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check for spam
    if is_spamming(user_id):
        await update.message.reply_text(
            "You're sending messages too quickly. Please wait a moment before sending more."
        )
        logger.warning(f"User {user_id} ({username}) is spamming.")
        return

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Send message with username and ID of the sender
    await context.bot.send_message(
        chat_id=CHAT_ID, 
        text=f"@{username} ID: {user_id}\n\n"
             f"{user_message}"
    )
    await update.message.reply_text(
        "Thank you for your message. It has been successfully forwarded to the owner."
    )

# Define handler for photos
async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Forward photo to the owner
    photo = update.message.photo[-1]  # Get the highest quality photo
    await context.bot.send_photo(
        chat_id=CHAT_ID, 
        photo=photo.file_id, 
        caption=f"Photo from {username} (ID: {user_id})"
    )
    await update.message.reply_text(
        "Your photo has been successfully sent to the owner. Thank you for sharing."
    )

# Define handler for videos
async def forward_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Forward video to the owner
    video = update.message.video
    await context.bot.send_video(
        chat_id=CHAT_ID, 
        video=video.file_id, 
        caption=f"Video from {username} (ID: {user_id})"
    )
    await update.message.reply_text(
        "Your video has been successfully sent to the owner. Thank you for your submission."
    )

# Command handler for /send
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text(
            "I’m afraid you do not have permission to use this command. Please contact the owner for assistance."
        )
        return

    # Parse command arguments
    try:
        target_id = context.args[0]
        message = " ".join(context.args[1:])

        # Ensure the target ID is an integer
        target_id = int(target_id)

        # Send the message to the specified target ID
        await context.bot.send_message(chat_id=target_id, text=message)
        await update.message.reply_text("Your message has been successfully sent.")
    except (IndexError, ValueError):
        await update.message.reply_text(
            "It seems there was an issue with the format. Please use /send <number_id> <message>."
        )
    except Exception as e:
        await update.message.reply_text(f"Something went wrong: {e}. Please try again later.")

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Hello! Here’s how you can interact with me:\n\n"
        "• To send a message to the owner, simply write it and send it, no commands necessary.\n\n"
        "• /send <number_id> <message> – Sends a message to a specific user (Owner Only)\n"
        "• /help – Displays this helpful guide\n\n"
        "If you have any questions, don’t hesitate to reach out. I’m here to assist you!"
    )
    await update.message.reply_text(help_text)

# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "Welcome! 🌟\n\n"
        "I’m your assistant bot, here to relay your messages to the senior manager. "
        "Feel free to send me a message, and I'll make sure it reaches the owner promptly.\n\n"
        "If you're unsure about something, type /help to learn how to use the available features."
    )
    await update.message.reply_text(start_text)

# Add handlers for text, photos, and videos
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
app.add_handler(MessageHandler(filters.VIDEO, forward_video))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()