import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the bot and owner ID from environment variables
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Your bot's token
OWNER_ID = os.getenv("CHAT_ID")  # Your personal chat ID

# Create the bot instance
app = Application.builder().token(BOT_TOKEN).build()

# Define message handler function
async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    # Send the user's message to the owner (your personal chat)
    await context.bot.send_message(chat_id=OWNER_ID, text=f"**{user_message}** /// Message from @{update.message.from_user.username}")
    # Acknowledge the user that their message was sent
    await update.message.reply_text("Your message has been sent to the owner.")

# Add a message handler
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

# Start the bot
app.run_polling()
