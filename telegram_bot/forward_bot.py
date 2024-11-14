import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from datetime import datetime

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

# Define message handler
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    phone_number = update.message.contact.phone_number if update.message.contact else "No phone number provided"
    date_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Skip forwarding if the message is from the owner's chat ID
    if user_id == CHAT_ID:
        logger.debug("Message from owner's chat ID. Skipping forwarding.")
        return

    # Format message as a quote
    message_to_owner = (
        f"> {user_message}\n\n"
        f"User ID: {user_id}\n"
        f"Username: @{username}\n"
        f"Phone Number: {phone_number}\n"
        f"Date: {date_sent}"
    )

    # Send the message to the owner's chat ID with Markdown
    await context.bot.send_message(chat_id=CHAT_ID, text=message_to_owner, parse_mode="MarkdownV2")
    await update.message.reply_text("Your message has been sent to the owner.")

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
        "For sending your message to the owner, just write it and send it without commands.\n\n"
        "/send <number_id> <message> - Sends a message to a specific user ID (Owner Only)\n"
        "/help - Displays this help message\n\n"
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

# Add handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("start", start_command))

# Start polling
app.run_polling()