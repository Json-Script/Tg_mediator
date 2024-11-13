import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

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

# Function to handle media files (photo, video, voice)
async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check that the message was sent by the owner (CHAT_ID)
    if update.message.from_user.id != CHAT_ID:
        logger.debug("Message from unauthorized user, ignoring.")
        return

    # Extract the file type and handle appropriately
    file = None
    file_type = None

    # Handle photo
    if update.message.photo:
        file = update.message.photo[-1].get_file()  # Get the highest resolution photo
        file_type = "photo"
        logger.debug(f"Received photo with file_id: {file.file_id}")

    # Handle video
    elif update.message.video:
        file = update.message.video.get_file()
        file_type = "video"
        logger.debug(f"Received video with file_id: {file.file_id}")

    # Handle voice message
    elif update.message.voice:
        file = update.message.voice.get_file()
        file_type = "voice"
        logger.debug(f"Received voice message with file_id: {file.file_id}")

    # Send the file to the target chat if a valid file is received
    if file:
        try:
            # Send the file to the CHAT_ID (your user ID)
            if file_type == "photo":
                await context.bot.send_photo(chat_id=CHAT_ID, photo=file.file_id)
                await update.message.reply_text(f"Photo sent to {CHAT_ID}.")
            elif file_type == "video":
                await context.bot.send_video(chat_id=CHAT_ID, video=file.file_id)
                await update.message.reply_text(f"Video sent to {CHAT_ID}.")
            elif file_type == "voice":
                await context.bot.send_voice(chat_id=CHAT_ID, voice=file.file_id)
                await update.message.reply_text(f"Voice message sent to {CHAT_ID}.")
        except Exception as e:
            await update.message.reply_text(f"Failed to send {file_type}: {e}")
    else:
        await update.message.reply_text("No valid media file detected.")

# Add media handler
app.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO | filters.VOICE, handle_media))

# Start polling
app.run_polling()