import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes, ConversationHandler

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

# Conversation states for /send command
ASK_TARGET_ID, ASK_MESSAGE = range(2)

# Define message handler
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Send message with username and ID of the sender
    await context.bot.send_message(chat_id=CHAT_ID, text=f"Message from {username} (ID: {user_id}): {user_message}")
    await update.message.reply_text("Your message has been sent to the owner.")

# Start the /send command
async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only allow the command for the owner
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return ConversationHandler.END

    await update.message.reply_text("Please send me the contact ID to deliver the message to:")
    return ASK_TARGET_ID

# Handle target ID input
async def ask_target_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['target_id'] = update.message.text
    await update.message.reply_text("Send me the message you want to deliver:")
    return ASK_MESSAGE

# Handle message input for target ID
async def ask_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = context.user_data['target_id']
    message = update.message.text
    try:
        await context.bot.send_message(chat_id=target_id, text=message)
        await update.message.reply_text("Message sent successfully.")
    except Exception as e:
        await update.message.reply_text(f"Failed to send message: {e}")
    return ConversationHandler.END

# Cancel command handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Command cancelled.")
    return ConversationHandler.END

# Add handlers
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

# Set up conversation handler for /send command
send_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("send", send_command)],
    states={
        ASK_TARGET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_target_id)],
        ASK_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_message)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

app.add_handler(send_conv_handler)

# Start polling
app.run_polling()