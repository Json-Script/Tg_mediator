from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

# Path for the file to store user data
USER_DATA_FILE = "Telegram_bot/user_data.json"

# Function to load existing user data from the file or create an empty dictionary if it doesn't exist
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as file:
            return json.load(file)
    return {}

# Function to save user data to the file
def save_user_data(user_data):
    with open(USER_DATA_FILE, "w") as file:
        json.dump(user_data, file, indent=4)

# Function to handle the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    # Load existing user data, add the new user if not present, and save it
    user_data = load_user_data()
    if str(user_id) not in user_data:
        user_data[str(user_id)] = username
        save_user_data(user_data)

    # Send a welcome message to the user (optional)
    await update.message.reply_text("Welcome! You’ve started the bot.")

# Main function to set up and run the bot
def main():
    # Initialize the bot application with the TELEGRAM_TOKEN from environment variables
    application = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()

    # Add command handler for /start
    application.add_handler(CommandHandler("start", start))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()