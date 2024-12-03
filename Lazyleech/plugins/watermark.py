import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message
from .. import ALL_CHATS, help_dict
from ..utils.misc import get_file_mimetype, watermark_photo


@Client.on_message(filters.command(['watermark', 'savewatermark', 'setwatermark']) & filters.chat(ALL_CHATS))
async def savewatermark(client: Client, message: Message):
    reply = message.reply_to_message
    document = message.document
    photo = message.photo
    thumbset = False
    user_id = str(message.from_user.id)
    watermark_path = os.path.join(user_id, 'watermark.jpg')
    os.makedirs(user_id, exist_ok=True)

    async def process_file(file_message):
        nonlocal thumbset
        with tempfile.NamedTemporaryFile(delete=False, dir=user_id) as temp_file:
            try:
                await file_message.download(temp_file.name)
                mimetype = await get_file_mimetype(temp_file.name)
                if mimetype and mimetype.startswith('image/'):
                    thumbset = True
                    os.rename(temp_file.name, watermark_path)
            finally:
                if os.path.exists(temp_file.name):
                    os.remove(temp_file.name)

    if photo or (document and document.file_size < 10 * 1024 * 1024 and document.mime_type.startswith('image/')):
        await process_file(message)

    if not thumbset and reply:
        document = reply.document
        photo = reply.photo
        if photo or (document and document.file_size < 10 * 1024 * 1024 and document.mime_type.startswith('image/')):
            await process_file(reply)

    if thumbset:
        thumbnail = os.path.join(user_id, 'thumbnail.jpg')
        watermarked_thumbnail = os.path.join(user_id, 'watermarked_thumbnail.jpg')
        if os.path.isfile(thumbnail):
            await watermark_photo(thumbnail, watermark_path, watermarked_thumbnail)
        await message.reply_text('Watermark set')
    else:
        await message.reply_text('Cannot find a valid watermark image')


@Client.on_message(filters.command(['clearwatermark', 'rmwatermark', 'delwatermark', 'removewatermark', 'deletewatermark']) & filters.chat(ALL_CHATS))
async def rmwatermark(client: Client, message: Message):
    user_id = str(message.from_user.id)
    for filename in ['watermark.jpg', 'watermarked_thumbnail.jpg']:
        path = os.path.join(user_id, filename)
        if os.path.isfile(path):
            os.remove(path)
    await message.reply_text('Watermark cleared')


@Client.on_message(filters.command('testwatermark') & filters.chat(ALL_CHATS))
async def testwatermark(client: Client, message: Message):
    user_id = str(message.from_user.id)
    watermark_path = os.path.join(user_id, 'watermark.jpg')
    if not os.path.isfile(watermark_path):
        await message.reply_text('Cannot find watermark')
        return

    watermarked_thumbnail = os.path.join(user_id, 'watermarked_thumbnail.jpg')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        try:
            if not os.path.isfile(watermarked_thumbnail):
                await watermark_photo('testwatermark.jpg', watermark_path, temp_file.name)
                await message.reply_photo(temp_file.name)
            else:
                await message.reply_photo(watermarked_thumbnail)
        finally:
            if os.path.exists(temp_file.name):
                os.remove(temp_file.name)


help_dict['watermark'] = ('Watermark',
    '''/watermark <i>&lt;as reply to image or as a caption&gt;</i>
/setwatermark <i>&lt;as reply to image or as a caption&gt;</i>
/savewatermark <i>&lt;as reply to image or as a caption&gt;</i>

/clearwatermark
/rmwatermark
/removewatermark
/delwatermark
/deletewatermark

/testwatermark''')
