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
    await context.bot.send_photo(chat_id=CHAT_ID, photo=photo.file_id, caption=f"Photo from {username} (ID: {user_id})")
    await update.message.reply_text("Your photo has been sent to the owner.")

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
    await context.bot.send_video(chat_id=CHAT_ID, video=video.file_id, caption=f"Video from {username} (ID: {user_id})")
    await update.message.reply_text("Your video has been sent to the owner.")

# Define handler for .7z files
async def forward_7z(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Check if the file is a .7z file
    if update.message.document and update.message.document.file_name.endswith('.7z'):
        # Forward the 7zip file to the owner
        file = update.message.document
        await context.bot.send_document(chat_id=CHAT_ID, document=file.file_id, caption=f"7zip file from {username} (ID: {user_id})")
        await update.message.reply_text("Your 7zip file has been sent to the owner.")
    else:
        await update.message.reply_text("Please send a .7z file.")

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

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here’s how you can interact with the bot:\n\n"
        "for sending your message to the owner just write it and send it without commands.\n\n"
        "/send <number_id> <message> - Sends a message to a specific user ID (Owner Only)\n"
        "/help - Displays this help message\n\n"
        "The bot also supports the following media:\n\n"
        "- Photos: Send photos and they will be forwarded to the owner.\n"
        "- Videos: Send videos and they will be forwarded to the owner.\n"
        "- 7zip files: Send .7z files and they will be forwarded to the owner.\n\n"
        "For any issues or questions, feel free to reach out!"
    )
    await update.message.reply_text(help_text)

# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "Hello and welcome! 🫂\n\n"
        "I’m your forwarder bot. I am the intermediary between you and the senior manager. I will personally forward your messages to the owner.\n\n"
        "How can I assist you today? You can type /help to see the available commands."
    )
    await update.message.reply_text(start_text)

# Add handlers for text, photos, videos, and .7z files
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
app.add_handler(MessageHandler(filters.VIDEO, forward_video))
app.add_handler(MessageHandler(filters.DOCUMENT & filters.Regex(r'.*\.7z$'), forward_7z))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()