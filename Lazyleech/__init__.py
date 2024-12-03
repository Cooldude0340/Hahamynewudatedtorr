import os
import logging
import aiohttp
from io import BytesIO, StringIO
from pyrogram import Client

# Fetch environment variables
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
TESTMODE = os.getenv('TESTMODE', '0') != '0'

# Parse chat lists from environment variables
EVERYONE_CHATS = list(map(int, os.getenv('EVERYONE_CHATS', '').split())) if os.getenv('EVERYONE_CHATS') else []
ADMIN_CHATS = list(map(int, os.getenv('ADMIN_CHATS', '').split())) if os.getenv('ADMIN_CHATS') else []
ALL_CHATS = EVERYONE_CHATS + ADMIN_CHATS

# Set default timeouts and update delays
PROGRESS_UPDATE_DELAY = int(os.getenv('PROGRESS_UPDATE_DELAY', 10))
MAGNET_TIMEOUT = int(os.getenv('MAGNET_TIMEOUT', 60))
LEECH_TIMEOUT = int(os.getenv('LEECH_TIMEOUT', 300))

# Source message for the bot
SOURCE_MESSAGE = '''
<a href="https://github.com/Lazy-Leecher/lazyleech">lazyleech - Telegram bot primarily to leech from torrents and upload to Telegram</a>
Copyright (c) 2021 lazyleech developers &lt;theblankx protonmail com, meliodas_bot protonmail com&gt;

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see &lt;https://www.gnu.org/licenses/&gt;.
'''

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize the Pyrogram Client
app = Client(
    'lazyleech',
    api_id=API_ID,
    api_hash=API_HASH,
    plugins={'root': os.path.join(os.path.dirname(__file__), 'plugins')},
    bot_token=BOT_TOKEN,
    test_mode=TESTMODE,
    parse_mode='html',
    sleep_threshold=30
)

# Initialize aiohttp session
session = aiohttp.ClientSession()
help_dict = {}
preserved_logs = []

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