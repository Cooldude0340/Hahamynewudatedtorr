import os
import html
import time
import shutil
import logging
import asyncio
import zipfile
import tempfile
import traceback
from natsort import natsorted
from pyrogram.errors import RPCError, FloodWait
from pyrogram.parser import html as pyrogram_html
from .. import PROGRESS_UPDATE_DELAY, ADMIN_CHATS, preserved_logs, TESTMODE, SendAsZipFlag, ForceDocumentFlag
from .misc import split_files, get_file_mimetype, format_bytes, get_video_info, generate_thumbnail, return_progress_string, calculate_eta, watermark_photo

upload_queue = asyncio.Queue()
upload_statuses = {}
upload_tamper_lock = asyncio.Lock()

async def upload_worker():
    """Main worker for handling uploads."""
    while True:
        client, message, reply, torrent_info, user_id, flags = await upload_queue.get()
        try:
            message_identifier = (reply.chat.id, reply.message_id)
            if SendAsZipFlag not in flags:
                await reply.edit_text("Download successful, uploading files... 🌝")
            task = asyncio.create_task(_upload_worker(client, message, reply, torrent_info, user_id, flags))
            upload_statuses[message_identifier] = (task, user_id)
            await task
        except asyncio.CancelledError:
            await asyncio.gather(
                reply.edit_text("Your leech has been cancelled."),
                message.reply_text("Your leech has been cancelled.")
            )
        except Exception as ex:
            preserved_logs.append((message, torrent_info, ex))
            logging.exception("Error during upload: %s", ex)
            await report_error_to_admins(client, ex, message, torrent_info)
        finally:
            upload_queue.task_done()
            await clean_upload_status(reply, torrent_info, message_identifier)

async def clean_upload_status(reply, torrent_info, message_identifier):
    """Clean up after an upload task finishes."""
    to_delete = []
    async with upload_tamper_lock:
        for key, (_, worker_identifier) in upload_waits.items():
            if worker_identifier == message_identifier:
                upload_waits.pop(key)
                to_delete.append(key[1])
    if to_delete:
        await reply.chat.delete_messages(to_delete)
    upload_statuses.pop(message_identifier, None)
    if not TESTMODE:
        shutil.rmtree(torrent_info['dir'])

async def report_error_to_admins(client, error, message, torrent_info):
    """Report errors to admin chats."""
    for admin_chat in ADMIN_CHATS:
        try:
            await client.send_message(
                admin_chat,
                f"Error occurred during upload:\n{traceback.format_exc()}",
                parse_mode=None
            )
        except RPCError:
            continue

async def _upload_worker(client, message, reply, torrent_info, user_id, flags):
    """Handle the actual upload logic."""
    files_to_upload = await prepare_files(torrent_info, flags, user_id)
    sent_files = await process_upload(client, message, reply, files_to_upload, flags)
    await send_file_summary(message, reply, sent_files)

async def prepare_files(torrent_info, flags, user_id):
    """Prepare files for upload."""
    files = {}
    with tempfile.TemporaryDirectory(dir=str(user_id)) as zip_tempdir:
        if SendAsZipFlag in flags:
            filename = (torrent_info['bittorrent']['info']['name']
                        if 'bittorrent' in torrent_info else
                        os.path.basename(torrent_info['files'][0]['path']))
            filepath = os.path.join(zip_tempdir, f"{filename[:251]}.zip")
            await zip_files(filepath, torrent_info, reply)
            files[filepath] = filename
        else:
            for file in torrent_info['files']:
                filepath = file['path']
                files[filepath] = filepath.replace(os.path.join(torrent_info['dir'], ''), '', 1)
    return files

async def zip_files(filepath, torrent_info, reply):
    """Zip files for uploading."""
    def _zip_files():
        with zipfile.ZipFile(filepath, 'x') as zipf:
            for file in torrent_info['files']:
                zipf.write(file['path'], os.path.relpath(file['path'], start=torrent_info['dir']))
    await asyncio.gather(
        reply.edit_text("Download successful, zipping files... 🍀"),
        asyncio.to_thread(_zip_files)
    )

async def process_upload(client, message, reply, files_to_upload, flags):
    """Process uploading of files."""
    sent_files = []
    for filepath, filename in natsorted(files_to_upload.items()):
        try:
            result = await upload_file(client, reply, filename, filepath, ForceDocumentFlag in flags)
            sent_files.extend(result)
        except Exception as ex:
            logging.exception("Error uploading file %s: %s", filename, ex)
            await message.reply_text(f"Error uploading {filename}: {str(ex)}", parse_mode=None)
    return sent_files

async def upload_file(client, reply, filename, filepath, force_document):
    """Upload a single file."""
    if not os.path.getsize(filepath):
        return [(os.path.basename(filename), None)]
    mimetype = await get_file_mimetype(filepath)
    if not force_document and mimetype.startswith("video/"):
        return await upload_video(client, reply, filename, filepath)
    else:
        return await upload_document(client, reply, filename, filepath)

# Add updated logic for `upload_video` and `upload_document` as needed...
