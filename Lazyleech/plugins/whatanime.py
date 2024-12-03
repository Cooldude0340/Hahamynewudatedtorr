import os
import time
import html
import aiohttp
import asyncio
import datetime
import tempfile
from urllib.parse import quote as urlencode
from decimal import Decimal
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message

from .. import ALL_CHATS, help_dict

# Ensure session management is proper
session = aiohttp.ClientSession()
progress_callback_data = {}


def format_bytes(size):
    size = int(size)
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'B'}"


def return_progress_string(current, total):
    filled_length = int(30 * current // total)
    return '[' + '=' * filled_length + ' ' * (30 - filled_length) + ']'


def calculate_eta(current, total, start_time):
    if not current:
        return '00:00:00'
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = (elapsed_time * (total / current)) - elapsed_time
    time_str = str(timedelta(seconds=seconds)).split('.', 1)[0]
    return time_str


@Client.on_message(filters.command('whatanime') & filters.chat(ALL_CHATS))
async def whatanime(c: Client, m: Message):
    media = m.photo or m.animation or m.video or m.document
    if not media:
        reply = m.reply_to_message
        if reply and not getattr(reply, 'empty', True):
            media = reply.photo or reply.animation or reply.video or reply.document
    if not media:
        await m.reply_text('Photo, GIF, or Video required.')
        return

    async with tempfile.TemporaryDirectory() as tempdir:
        reply = await m.reply_text('Downloading...')
        try:
            path = await c.download_media(
                media, file_name=os.path.join(tempdir, 'media'), 
                progress=progress_callback, progress_args=(reply,)
            )
        except Exception as e:
            await reply.edit_text(f"Error downloading media: {e}")
            return

        new_path = os.path.join(tempdir, 'frame.png')
        proc = await asyncio.create_subprocess_exec('ffmpeg', '-i', path, '-frames:v', '1', new_path)
        await proc.communicate()

        if not os.path.exists(new_path):
            await reply.edit_text("Error extracting frame using ffmpeg.")
            return

        await reply.edit_text('Uploading for search...')
        try:
            async with session.post(
                'https://api.trace.moe/search?cutBorders&anilistInfo', 
                data={'image': open(new_path, 'rb')}
            ) as resp:
                response_data = await resp.json()
        except Exception as e:
            await reply.edit_text(f"Error querying Trace.moe API: {e}")
            return

        if response_data.get('error'):
            await reply.edit_text(response_data['error'])
        else:
            await process_trace_response(reply, response_data)


async def process_trace_response(reply, response_data):
    try:
        match = response_data['result'][0]
    except IndexError:
        await reply.edit_text('No match found.')
        return

    nsfw = match['anilist']['isAdult']
    title_native = match['anilist']['title']['native']
    title_english = match['anilist']['title']['english']
    title_romaji = match['anilist']['title']['romaji']
    synonyms = ', '.join(match['anilist']['synonyms'])
    anilist_id = match['anilist']['id']
    episode = match.get('episode')
    similarity = Decimal(match['similarity']) * 100
    from_time = str(timedelta(seconds=match['from'])).split('.', 1)[0]
    to_time = str(timedelta(seconds=match['to'])).split('.', 1)[0]

    text = f'<a href="https://anilist.co/anime/{anilist_id}">{title_romaji}</a>'
    if title_english:
        text += f' ({title_english})'
    if title_native:
        text += f' ({title_native})'
    if synonyms:
        text += f'\n<b>Synonyms:</b> {synonyms}'
    text += f'\n<b>Similarity:</b> {similarity:.2f}%\n'
    if episode:
        text += f'<b>Episode:</b> {episode}\n'
    if nsfw:
        text += '<b>Hentai/NSFW:</b> Yes'

    await reply.edit_text(text, disable_web_page_preview=True)


async def progress_callback(current, total, reply):
    identifier = (reply.chat.id, reply.message_id)
    last_edit_time, prev_text, start_time = progress_callback_data.get(
        identifier, (0, None, time.time())
    )

    if current == total:
        progress_callback_data.pop(identifier, None)
    elif time.time() - last_edit_time > 1:
        download_speed = format_bytes((current - total) / (time.time() - start_time)) if last_edit_time else '0 B'
        text = (f"Downloading...\n"
                f"<code>{return_progress_string(current, total)}</code>\n"
                f"<b>Total Size:</b> {format_bytes(total)}\n"
                f"<b>Downloaded:</b> {format_bytes(current)}\n"
                f"<b>Speed:</b> {download_speed}/s\n"
                f"<b>ETA:</b> {calculate_eta(current, total, start_time)}")
        if text != prev_text:
            await reply.edit_text(text)
            progress_callback_data[identifier] = (time.time(), text, start_time)


help_dict['extras'] = ('Extras',
'''/mediainfo <i>[replied media]</i> 
/whatanime <i>[replied media]</i>
<b>Credits</b>
- @TheKneesocks for /whatanime
- @deleteduser420 for /mediainfo''')
