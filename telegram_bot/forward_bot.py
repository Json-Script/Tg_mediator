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

# Define the file size limit (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Define message handler
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

# Command handler for /send
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # Parse command arguments
    try:
        target_id = int(context.args[0])  # Ensure the target ID is an integer
        message = " ".join(context.args[1:]) if len(context.args) > 1 else None

        # Send the text message if provided
        if message:
            await context.bot.send_message(chat_id=target_id, text=message)
            await update.message.reply_text("Text message sent successfully.")

    except (IndexError, ValueError):
        await update.message.reply_text("Invalid format. Use /send <number_id> <message> or send media files.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send message: {e}")

# Function to handle media files
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check that the message was sent by the owner
    if update.message.from_user.id != CHAT_ID:
        return

    # Extract the file type and file size
    file_type = None
    file_size = None
    file = None

    # Check for photo
    if update.message.photo:
        file = update.message.photo[-1].get_file()  # Get the highest resolution photo
        file_type = "photo"
        file_size = file.file_size

    # Check for video
    elif update.message.video:
        file = update.message.video.get_file()
        file_type = "video"
        file_size = file.file_size

    # Check for voice message
    elif update.message.voice:
        file = update.message.voice.get_file()
        file_type = "voice"
        file_size = file.file_size

    # Limit file size to 10MB
    if file and file_size <= MAX_FILE_SIZE:
        # Send the file to the target chat
        try:
            target_id = int(context.user_data.get('target_id'))
            if file_type == "photo":
                await context.bot.send_photo(chat_id=target_id, photo=file.file_id)
            elif file_type == "video":
                await context.bot.send_video(chat_id=target_id, video=file.file_id)
            elif file_type == "voice":
                await context.bot.send_voice(chat_id=target_id, voice=file.file_id)

            await update.message.reply_text(f"{file_type.capitalize()} sent successfully.")
        except Exception as e:
            await update.message.reply_text(f"Failed to send {file_type}: {e}")
    else:
        await update.message.reply_text("File is too large. Please send a file smaller than 10MB.")

# Add handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, handle_media))

# Start polling
app.run_polling()