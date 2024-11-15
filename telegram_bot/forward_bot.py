import os
import time
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from Telegram_bot.user_manager import save_user_id, send_to_all  # Import from user_manager

# Set up logging for debugging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get environment variables
BOT_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

# Log the environment variables for debugging
logger.debug(f"Telegram Token: {BOT_TOKEN}")
logger.debug(f"Chat ID (CHAT_ID): {CHAT_ID}")

# Create the bot application
app = Application.builder().token(BOT_TOKEN).build()

# Anti-spam settings
RATE_LIMIT = 5
TIME_WINDOW = 60
COOLDOWN_PERIODS = [60, 300, 900]
SPAM_KEYWORDS = ['buy', 'free', 'winner', 'click', 'urgent', 'lottery', 'https://', 'www.']
user_message_log = {}
user_warning_count = {}
user_block_time = {}

# Anti-spam functions
def is_spamming(user_id):
    current_time = time.time()
    if user_id in user_warning_count and user_warning_count[user_id] >= len(COOLDOWN_PERIODS):
        return True
    if user_id not in user_message_log:
        user_message_log[user_id] = []
    if user_id not in user_warning_count:
        user_warning_count[user_id] = 0
    if user_id not in user_block_time:
        user_block_time[user_id] = 0
    if current_time < user_block_time[user_id]:
        return True
    user_message_log[user_id] = [
        timestamp for timestamp in user_message_log[user_id] if current_time - timestamp < TIME_WINDOW
    ]
    if len(user_message_log[user_id]) >= RATE_LIMIT:
        user_warning_count[user_id] += 1
        block_duration = COOLDOWN_PERIODS[min(user_warning_count[user_id], len(COOLDOWN_PERIODS) - 1)]
        user_block_time[user_id] = current_time + block_duration
        logger.warning(f"User {user_id} has been blocked for {block_duration} seconds due to spam.")
        return True
    user_message_log[user_id].append(current_time)
    return False

def contains_spam_keywords(message_text):
    return any(keyword.lower() in message_text.lower() for keyword in SPAM_KEYWORDS)

# Handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    save_user_id(user_id)
    await update.message.reply_text("Welcome! You've been registered for updates from the owner.")

async def send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != CHAT_ID:
        await update.message.reply_text("Unauthorized to use this command.")
        return
    if context.args[0].lower() == "all":
        message = " ".join(context.args[1:])
        await send_to_all(context, message)
        await update.message.reply_text("Message sent to all users.")
    else:
        try:
            target_id = int(context.args[0])
            message = " ".join(context.args[1:])
            await context.bot.send_message(chat_id=target_id, text=message)
            await update.message.reply_text("Message sent successfully.")
        except (IndexError, ValueError):
            await update.message.reply_text("Use /send <user_id> <message> or /send all <message>.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Here’s how you can interact with me:\n"
        "• /send <user_id> <message> or /send all <message> – Send message (Owner Only)\n"
        "• /help – Displays this guide"
    )
    await update.message.reply_text(help_text)

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if contains_spam_keywords(user_message):
        await update.message.reply_text("Your message contains spammy content and has been ignored.")
        logger.warning(f"Message from {user_id} ignored due to spam keywords.")
        return
    if is_spamming(user_id):
        await update.message.reply_text("Please wait before sending more messages.")
        logger.warning(f"User {user_id} is spamming.")
        return
    if user_id != CHAT_ID:
        await context.bot.send_message(chat_id=CHAT_ID, text=f"@{username} (ID: {user_id}):\n{user_message}")
        await update.message.reply_text("Message forwarded to the owner.")

async def forward_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if user_id != CHAT_ID:
        photo = update.message.photo[-1]
        await context.bot.send_photo(chat_id=CHAT_ID, photo=photo.file_id, caption=f"Photo from {username} (ID: {user_id})")
        await update.message.reply_text("Your photo has been sent to the owner.")

async def forward_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    if user_id != CHAT_ID:
        video = update.message.video
        await context.bot.send_video(chat_id=CHAT_ID, video=video.file_id, caption=f"Video from {username} (ID: {user_id})")
        await update.message.reply_text("Your video has been sent to the owner.")

# Add handlers
app.add_handler(CommandHandler("start", start_command))
app.add_handler(CommandHandler("send", send_command))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))
app.add_handler(MessageHandler(filters.PHOTO, forward_photo))
app.add_handler(MessageHandler(filters.VIDEO, forward_video))

# Start polling
app.run_polling()