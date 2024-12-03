import os
import time
import json
import shlex
import asyncio
import tempfile
import mimetypes
from decimal import Decimal
from datetime import timedelta
from pyrogram.errors import UserNotParticipant
from pyrogram.types import ChatMember
from .. import app, ADMIN_CHATS

# Helper Functions
def format_bytes(size: int) -> str:
    """Convert bytes to human-readable format."""
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

async def get_file_mimetype(filename: str) -> str:
    """Determine the MIME type of a file."""
    mimetype = mimetypes.guess_type(filename)[0]
    if not mimetype:
        proc = await asyncio.create_subprocess_exec(
            'file', '--brief', '--mime-type', filename,
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        mimetype = stdout.decode().strip()
    return mimetype or 'application/octet-stream'

async def split_files(filename: str, destination_dir: str, no_ffmpeg: bool = False) -> list[str]:
    """Split files into parts."""
    ext = os.path.splitext(filename)[1]
    if not no_ffmpeg and (await get_file_mimetype(filename)).startswith('video/'):
        video_info = (await get_video_info(filename))['format']
        if 'duration' in video_info:
            times = 1
            ss = Decimal('0.0')
            duration = Decimal(video_info['duration'])
            files = []
            while duration - ss > 1:
                filepath = os.path.join(
                    destination_dir,
                    os.path.splitext(os.path.basename(filename))[0][-(248 - len(ext)):] +
                    ('-' if ext else '.') + f'part{times}{ext}'
                )
                proc = await asyncio.create_subprocess_exec(
                    'ffmpeg', '-y', '-i', filename, '-ss', str(ss), '-c', 'copy', '-fs', '1900000000', filepath
                )
                await proc.communicate()
                video_info = (await get_video_info(filepath)).get('format')
                if not video_info or 'duration' not in video_info:
                    break
                files.append(filepath)
                times += 1
                ss += Decimal(video_info['duration'])
            return files
    args = [
        'split', '--verbose', '--numeric-suffixes=1',
        '--bytes=2097152000', '--suffix-length=2'
    ]
    if ext:
        args.append(f'--additional-suffix={ext}')
    args.append(filename)
    args.append(os.path.join(destination_dir, os.path.basename(filename)[-(248 - len(ext)):] + ('-' if ext else '.') + 'part'))
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    return shlex.split(' '.join([i[14:] for i in stdout.decode().strip().split('\n')]))

async def get_video_info(filename: str) -> dict:
    """Retrieve video metadata using ffprobe."""
    proc = await asyncio.create_subprocess_exec(
        'ffprobe', '-print_format', 'json', '-show_format', '-show_streams', filename,
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await proc.communicate()
    return json.loads(stdout.decode())

async def generate_thumbnail(videopath: str, photopath: str):
    """Generate a video thumbnail."""
    video_info = await get_video_info(videopath)
    for duration in (10, 5, 0):
        if duration < float(video_info['format'].get('duration', 0)):
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-y', '-i', videopath, '-ss', str(duration), '-frames:v', '1', photopath
            )
            await proc.communicate()
            break

async def allow_admin_cancel(chat_id: int, user_id: int) -> bool:
    """Check if a user is an admin."""
    if chat_id in ADMIN_CHATS:
        return True
    for admin_chat in ADMIN_CHATS:
        try:
            member = await app.get_chat_member(admin_chat, user_id)
            if isinstance(member, ChatMember):
                return True
        except UserNotParticipant:
            continue
    return False
