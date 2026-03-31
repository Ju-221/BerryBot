# BerryBot

A minimal Discord bot in Python that responds to  `!fortune` commands in a specified channel.
[![Test BerryBot](https://github.com/Ju-221/BerryBot/actions/workflows/test.yml/badge.svg)](https://github.com/Ju-221/BerryBot/actions/workflows/test.yml)

## Setup
1. Clone the repo and create a virtual environment.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your Discord bot token and channel ID.
4. Enable "Message Content Intent" for your bot in the Discord Developer Portal.
5. Run the bot:
   ```
   python bot.py
   ```

## Features
- Responds to `!luck` and `!fortune` in the specified channel.
- Only sends messages to the channel set in `.env`.
