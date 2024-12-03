import time
from pyrogram import Client, filters
from .. import ALL_CHATS

@Client.on_message(filters.command("ping") & filters.chat(ALL_CHATS))
async def ping_pong(client: Client, message):
    """Responds to the /ping command with a Pong message and response time."""
    start_time = time.time()
    reply = await message.reply_text("🏓 Pong!")
    end_time = time.time()
    response_time = (end_time - start_time) * 1000  # Convert to milliseconds
    await reply.edit_text(f"🏓 Pong! ({response_time:.2f} ms)")
