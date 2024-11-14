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

# Dictionary to store target IDs for forwarding media
target_ids = {}

# Define message handler for text messages
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # If message is from the owner and contains a /send command, set the target ID for forwarding
    if user_id == CHAT_ID and user_message.startswith("/send"):
        # Parse the target ID from the command
        try:
            parts = user_message.split()
            target_id = int(parts[1])  # Extract the target ID
            target_ids[target_id] = True  # Mark this ID for receiving forwarded media
            await update.message.reply_text(f"Media will be sent to ID: {target_id}.")
        except IndexError:
            await update.message.reply_text("Please provide a valid user ID after /send.")
        except ValueError:
            await update.message.reply_text("The user ID must be a valid number.")
        return

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Send message with username and ID of the sender to the target user ID
    for target_id in target_ids:
        await context.bot.send_message(chat_id=target_id, text=f"Message from {username} (ID: {user_id}): {user_message}")
    
    await update.message.reply_text("Your message has been sent to the target user.")

# Define handler for photos
async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Forward photo to target user ID(s)
    for target_id in target_ids:
        photo = update.message.photo[-1]  # Get the highest quality photo
        await context.bot.send_photo(chat_id=target_id, photo=photo.file_id, caption=f"Photo from {username} (ID: {user_id})")
    
    await update.message.reply_text("Your photo has been sent to the target user.")

# Define handler for videos
async def forward_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Forward video to target user ID(s)
    for target_id in target_ids:
        video = update.message.video
        await context.bot.send_video(chat_id=target_id, video=video.file_id, caption=f"Video from {username} (ID: {user_id})")
    
    await update.message.reply_text("Your video has been sent to the target user.")

# Command handler for /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here’s how you can interact with the bot:\n\n"
        "for sending your message to the owner just write it and send it without commands.\n\n"
        "/send <number_id> - Set the user ID to receive forwarded media (Owner Only)\n"
        "/help - Displays this help message\n\n"
        "For any issues or questions, feel free to reach out!"
    )
    await update.message.reply_text(help_text)

# Command handler for /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "Hello and welcome! 🫂\n\n"
        "I’m your forwarder bot. I will forward any media you send to the target user specified using /send.\n\n"
        "How can I assist you today? You can type /help to see the available commands."
    )
    await update.message.reply_text(start_text)

# Add handlers for text, photos, and videos
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
app.add_handler(MessageHandler(filters.VIDEO, forward_video))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()