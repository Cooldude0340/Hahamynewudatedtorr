import os
import re
import asyncio
import tempfile
from urllib.parse import urlsplit
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .. import ALL_CHATS, SendAsZipFlag, ForceDocumentFlag
from ..utils.misc import get_file_mimetype
from ..utils import custom_filters
from .leech import initiate_torrent, initiate_magnet

# Use updated regex patterns or libraries as needed
NYAA_REGEX = re.compile(r'^(?:https?://)?(?P<base>(?:www\.|sukebei\.)?nyaa\.si|nyaa\.squid\.workers\.dev)/(?:view|download)/(?P<sauce>\d+)(?:[\./]torrent)?$')

# Dictionary to track autodetections
auto_detects = {}

@Client.on_message(filters.chat(ALL_CHATS), group=1)
async def autodetect(client: Client, message):
    """Autodetect torrents or magnet links from messages."""
    text = message.text
    document = message.document
    link = None
    is_torrent = False

    if document:
        if (
            document.file_size < 1_048_576 and
            document.file_name.endswith('.torrent') and
            (not document.mime_type or document.mime_type == 'application/x-bittorrent')
        ):
            os.makedirs(str(message.from_user.id), exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=str(message.from_user.id), suffix='.torrent', delete=False) as temp_file:
                link = temp_file.name
            await message.download(link)
            mimetype = await get_file_mimetype(link)
            is_torrent = True if mimetype == 'application/x-bittorrent' else False
            if not is_torrent:
                os.remove(link)
                link = None

    if not link and text:
        match = NYAA_REGEX.match(text)
        if match:
            link = f'https://{match.group("base")}/download/{match.group("sauce")}.torrent'
            is_torrent = True
        elif text.startswith('magnet:'):
            link = text

    if link:
        reply = await message.reply_text(
            f'{"Torrent" if is_torrent else "Magnet"} detected. Select upload method.',
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton('📂 Individual Files', 'autodetect_individual'),
                    InlineKeyboardButton('🤐 Zip', 'autodetect_zip'),
                    InlineKeyboardButton('💾 Force Document', 'autodetect_file')
                ],
                [InlineKeyboardButton('Delete 🗑', 'autodetect_delete')]
            ])
        )
        auto_detects[(reply.chat.id, reply.message_id)] = (link, message.from_user.id, initiate_torrent if is_torrent else initiate_magnet)

answered = set()
answer_lock = asyncio.Lock()

@Client.on_callback_query(
    custom_filters.callback_data(['autodetect_individual', 'autodetect_zip', 'autodetect_file', 'autodetect_delete']) &
    custom_filters.callback_chat(ALL_CHATS)
)
async def autodetect_callback(client: Client, callback_query):
    """Handle callback queries for autodetected content."""
    message = callback_query.message
    identifier = (message.chat.id, message.message_id)
    result = auto_detects.get(identifier)

    if not result:
        await callback_query.answer('I can\'t get your message, please try again.', show_alert=True, cache_time=3600)
        return

    link, user_id, init_func = result

    if callback_query.from_user.id != user_id:
        await callback_query.answer('You cannot interact with this action.', cache_time=3600)
        return

    async with answer_lock:
        if identifier in answered:
            await callback_query.answer('Action already taken.', cache_time=3600)
            return
        answered.add(identifier)

    await message.delete()

    if callback_query.data in ('autodetect_individual', 'autodetect_zip', 'autodetect_file'):
        if getattr(message.reply_to_message, 'empty', True):
            await callback_query.answer('Original message deleted. Cannot proceed.', show_alert=True)
            return

        flags = ()
        if callback_query.data == 'autodetect_zip':
            flags = (SendAsZipFlag,)
        elif callback_query.data == 'autodetect_file':
            flags = (ForceDocumentFlag,)

        await asyncio.gather(
            callback_query.answer(),
            init_func(client, message.reply_to_message, link, flags)
        )
