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

# Store the target user ID in a variable
target_user_id = None

# Define message handler for text messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global target_user_id
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Ensure that the target user ID is set
    if target_user_id is not None:
        # Send message with username and ID of the sender
        await context.bot.send_message(chat_id=target_user_id, text=f"Message from {username} (ID: {user_id}): {user_message}")
        await update.message.reply_text("Your message has been sent to the user.")
    else:
        await update.message.reply_text("No target user set. Please use /send <number_id> to set a target user.")

# Define handler for photos
async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global target_user_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Ensure that the target user ID is set
    if target_user_id is not None:
        # Forward photo to the target user
        photo = update.message.photo[-1]  # Get the highest quality photo
        await context.bot.send_photo(chat_id=target_user_id, photo=photo.file_id, caption=f"Photo from {username} (ID: {user_id})")
        await update.message.reply_text("Your photo has been sent to the user.")
    else:
        await update.message.reply_text("No target user set. Please use /send <number_id> to set a target user.")

# Define handler for videos
async def forward_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global target_user_id
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Ensure that the target user ID is set
    if target_user_id is not None:
        # Forward video to the target user
        video = update.message.video
        await context.bot.send_video(chat_id=target_user_id, video=video.file_id, caption=f"Video from {username} (ID: {user_id})")
        await update.message.reply_text("Your video has been sent to the user.")
    else:
        await update.message.reply_text("No target user set. Please use /send <number_id> to set a target user.")

# Command handler for /send
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global target_user_id
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Parse command arguments
    try:
        target_user_id = int(context.args[0])  # Set the target user ID
        await update.message.reply_text(f"Target user ID set to {target_user_id}. Now all messages will be forwarded to this ID.")
    except (IndexError, ValueError):
        await update.message.reply_text("Invalid format. Use /send <number_id> to set a target user ID.")

# Command handler for /nsend (reset target ID)
async def nsend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global target_user_id
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    target_user_id = None
    await update.message.reply_text("Target user ID has been reset. You can set a new ID with /send.")

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here’s how you can interact with the bot:\n\n"
        "for sending your message to the target user, just write it and send it without commands.\n\n"
        "/send <number_id> - Sets the target user ID to which messages, photos, and videos will be forwarded (Owner Only)\n"
        "/nsend - Resets the target user ID (Owner Only)\n"
        "/help - Displays this help message\n\n"
        "For any issues or questions, feel free to reach out!"
    )
    await update.message.reply_text(help_text)

# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "Hello and welcome! 🫂\n\n"
        "I’m your forwarder bot. I will forward your messages to the designated user (set via /send command).\n\n"
        "How can I assist you today? You can type /help to see the available commands."
    )
    await update.message.reply_text(start_text)

# Add handlers for text, photos, and videos
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
app.add_handler(MessageHandler(filters.VIDEO, forward_video))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("nsend", nsend_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()