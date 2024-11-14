name: Deploy

on:
  push:
    branches:
      - main  # Automatically runs on push to main
  workflow_dispatch:  # Allows manual run from GitHub Actions

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install Telegram bot dependencies
        run: |
          python -m pip install --upgrade pip
          pip install python-telegram-bot==20.0  # Install the required dependencies directly

      - name: Run the Telegram Bot with restart every 50 minutes
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
        run: |
          while true; do
            echo "Starting Telegram bot..."
            python telegram_bot/forward_bot.py &
            BOT_PID=$!
            sleep 3000  # Wait 50 minutes (3000 seconds)
            echo "Restarting Telegram bot..."
            kill $BOT_PID
          done