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

# Rate limit settings
RATE_LIMIT = 5
TIME_WINDOW = 60  # in seconds
COOLDOWN_PERIODS = [60, 300, 900]  # 1 minute, 5 minutes, 15 minutes

# Dictionary to keep track of user messages, timestamps, and warnings
user_message_log = {}
user_warning_count = {}
user_block_time = {}

# List of spammy keywords
SPAM_KEYWORDS = ['buy', 'free', 'winner', 'click', 'urgent', 'lottery', 'https://', 'www.']

# Anti-spam: Check if user exceeds message limit
def is_spamming(user_id):
    current_time = time.time()

    # Block user permanently if warning count exceeds the threshold
    if user_id in user_warning_count and user_warning_count[user_id] >= len(COOLDOWN_PERIODS):
        return True  # User permanently blocked

    # Initialize user logs if not already present
    if user_id not in user_message_log:
        user_message_log[user_id] = []
    if user_id not in user_warning_count:
        user_warning_count[user_id] = 0
    if user_id not in user_block_time:
        user_block_time[user_id] = 0

    # If the user is currently blocked, ignore their messages
    if current_time < user_block_time[user_id]:
        return True  # User is still in cooldown period

    # Filter out old message timestamps outside the time window
    user_message_log[user_id] = [
        timestamp for timestamp in user_message_log[user_id]
        if current_time - timestamp < TIME_WINDOW
    ]

    # Check if the user exceeds the rate limit
    if len(user_message_log[user_id]) >= RATE_LIMIT:
        user_warning_count[user_id] += 1

        # Apply progressive blocking
        if user_warning_count[user_id] < len(COOLDOWN_PERIODS):
            block_duration = COOLDOWN_PERIODS[user_warning_count[user_id]]
        else:
            block_duration = COOLDOWN_PERIODS[-1]

        # Block the user for a period
        user_block_time[user_id] = current_time + block_duration
        logger.warning(f"User {user_id} has been blocked for {block_duration} seconds due to spam.")
        return True

    # Log the current message timestamp
    user_message_log[user_id].append(current_time)
    return False

# Anti-spam: Check for keywords in message
def contains_spam_keywords(message_text):
    return any(keyword.lower() in message_text.lower() for keyword in SPAM_KEYWORDS)

# Define message handler for text messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Check if the message contains spam keywords
    if contains_spam_keywords(user_message):
        await update.message.reply_text("Your message contains spammy content and has been ignored.")
        logger.warning(f"Message from {user_id} ({username}) ignored due to spam keywords.")
        return

    # Check for spam behavior (rate limit exceeded)
    if is_spamming(user_id):
        await update.message.reply_text(
            "You're sending messages too quickly or have violated the spam policy. Please wait before trying again."
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

# Add command handlers
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()