from pyrogram import Client, filters
from pyrogram.types import Message  # Explicitly import types for better clarity

@Client.on_message(filters.command('start'))
async def start_cmd(client: Client, message: Message):
    await message.reply_text(
        "<b>Hi, I am Torrent Lazyleech.</b>\n\n"
        "I can leech direct/torrent links. Currently unavailable in private 😅.\n\n"
        "For More Info, use /help.",
        parse_mode="HTML"  # Explicitly specify the parsing mode
    )
