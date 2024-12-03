import os
import logging
from io import BytesIO, StringIO
from pyrogram import Client
from dotenv import load_dotenv

# Load environment variables from a .env file (if exists)
if os.path.exists("/content/.env"):
    load_dotenv("/content/.env")

# Fetch environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TESTMODE = os.getenv("TESTMODE", "0") != "0"

# Parse chat lists from environment variables
EVERYONE_CHATS = list(map(int, os.getenv("EVERYONE_CHATS", "").split())) if os.getenv("EVERYONE_CHATS") else []
ADMIN_CHATS = list(map(int, os.getenv("ADMIN_CHATS", "").split())) if os.getenv("ADMIN_CHATS") else []
ALL_CHATS = EVERYONE_CHATS + ADMIN_CHATS

# Set default timeouts and update delays
PROGRESS_UPDATE_DELAY = int(os.getenv("PROGRESS_UPDATE_DELAY", 10))
MAGNET_TIMEOUT = int(os.getenv("MAGNET_TIMEOUT", 60))
LEECH_TIMEOUT = int(os.getenv("LEECH_TIMEOUT", 300))

# Source message for the bot
SOURCE_MESSAGE = '''
<a href="https://github.com/Lazy-Leecher/lazyleech">lazyleech - Telegram bot primarily to leech from torrents and upload to Telegram</a>
Copyright (c) 2021 lazyleech developers.

This program is free software under the GNU AGPL license.
'''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the Pyrogram Client
app = Client(
    "lazyleech",
    api_id=API_ID,
    api_hash=API_HASH,
    plugins={"root": "/content/plugins"},  # Adjusted for Colab's filesystem
    bot_token=BOT_TOKEN,
    test_mode=TESTMODE,
    parse_mode="html",
    sleep_threshold=30,
)

# Define custom flags
class SendAsZipFlag:
    pass

class ForceDocumentFlag:
    pass

# Function to create a memory file
def memory_file(name=None, contents=None, *, bytes=True):
    if isinstance(contents, str) and bytes:
        contents = contents.encode()
    file = BytesIO() if bytes else StringIO()
    if name:
        file.name = name
    if contents:
        file.write(contents)
        file.seek(0)
    return file

# Function to start the bot
def start_bot():
    print("Starting the bot... Make sure your environment variables are correctly set!")
    app.run()

# Keep Colab session alive
def keep_alive():
    import asyncio
    asyncio.get_event_loop().run_forever()
