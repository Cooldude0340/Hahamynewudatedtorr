import os
import time
import html
import asyncio
import tempfile
from urllib.parse import urlparse, urlunparse, unquote as urldecode
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .. import (
    ADMIN_CHATS, ALL_CHATS, PROGRESS_UPDATE_DELAY, session, help_dict,
    LEECH_TIMEOUT, MAGNET_TIMEOUT, SendAsZipFlag, ForceDocumentFlag
)
from ..utils.aria2 import (
    aria2_add_torrent, aria2_tell_status, aria2_remove, aria2_add_magnet,
    Aria2Error, aria2_tell_active, is_gid_owner, aria2_add_directdl
)
from ..utils.misc import (
    format_bytes, get_file_mimetype, return_progress_string,
    calculate_eta, allow_admin_cancel
)
from ..utils.upload_worker import (
    upload_queue, upload_statuses, progress_callback_data,
    upload_waits, stop_uploads
)

leech_statuses = {}

async def download_torrent(client, message, link, flags):
    """Download a torrent via aria2."""
    user_id = message.from_user.id
    reply = await message.reply_text("Adding torrent...")
    try:
        gid = await aria2_add_torrent(session, user_id, link, LEECH_TIMEOUT)
    except Aria2Error as ex:
        await asyncio.gather(
            message.reply_text(f"Aria2 Error Occurred!\n{ex.error_code}: {html.escape(ex.error_message)}"),
            reply.delete()
        )
        return
    finally:
        if os.path.isfile(link):
            os.remove(link)
    await manage_download(client, message, gid, reply, user_id, flags)

async def download_magnet(client, message, link, flags):
    """Download a magnet link via aria2."""
    user_id = message.from_user.id
    reply = await message.reply_text("Adding magnet...")
    try:
        gid = await asyncio.wait_for(
            aria2_add_magnet(session, user_id, link, LEECH_TIMEOUT), MAGNET_TIMEOUT
        )
    except Aria2Error as ex:
        await asyncio.gather(
            message.reply_text(f"Aria2 Error Occurred!\n{ex.error_code}: {html.escape(ex.error_message)}"),
            reply.delete()
        )
    except asyncio.TimeoutError:
        await asyncio.gather(message.reply_text("Magnet timed out"), reply.delete())
    else:
        await manage_download(client, message, gid, reply, user_id, flags)

async def manage_download(client, message, gid, reply, user_id, flags):
    """Monitor and manage active downloads."""
    torrent_info = await aria2_tell_status(session, gid)
    start_time = time.time()
    prevtext, last_edit = None, 0
    while torrent_info['status'] in ('active', 'waiting', 'paused'):
        completed = int(torrent_info.get("completedLength", 0))
        total = int(torrent_info.get("totalLength", 0))
        speed = format_bytes(int(torrent_info.get("downloadSpeed", 0))) + "/s"
        eta = calculate_eta(completed, total, start_time)
        progress = return_progress_string(completed, total)
        text = f"""<b>Downloading:</b> {html.escape(torrent_info.get('info', {}).get('name', 'unknown'))}
<b>Progress:</b> {progress}
<b>Speed:</b> {speed} | ETA: {eta}"""
        if text != prevtext and (time.time() - last_edit) > PROGRESS_UPDATE_DELAY:
            await reply.edit_text(text)
            prevtext, last_edit = text, time.time()
        torrent_info = await aria2_tell_status(session, gid)

    # Handle download completion or errors
    if torrent_info['status'] == 'error':
        await reply.edit_text(f"Error: {torrent_info['errorMessage']}")
    elif torrent_info['status'] == 'complete':
        await reply.edit_text("Download complete!")
