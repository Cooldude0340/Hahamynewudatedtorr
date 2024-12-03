import os
import tempfile
from pyrogram import Client, filters
from pyrogram.types import Message  # Explicit typing for better clarity
from .. import ALL_CHATS, help_dict
from ..utils.misc import convert_to_jpg, get_file_mimetype, watermark_photo


@Client.on_message(
    filters.command(['thumbnail', 'savethumbnail', 'setthumbnail']) & filters.chat(ALL_CHATS)
)
async def savethumbnail(client: Client, message: Message):
    reply = message.reply_to_message
    user_id = str(message.from_user.id)
    thumbnail_path = os.path.join(user_id, 'thumbnail.jpg')
    os.makedirs(user_id, exist_ok=True)

    thumbset = False

    async def process_media(media):
        nonlocal thumbset
        if media:
            # Check if the file is valid and small enough
            if getattr(media, "photo", None) or (
                media.file_size < 10 * 1024 * 1024
                and os.path.splitext(media.file_name or "")[1]
                and (not media.mime_type or media.mime_type.startswith('image/'))
            ):
                with tempfile.NamedTemporaryFile(dir=user_id, suffix=".tmp") as temp_file:
                    await media.download(temp_file.name)
                    mimetype = await get_file_mimetype(temp_file.name)
                    if mimetype.startswith('image/'):
                        await convert_to_jpg(temp_file.name, thumbnail_path)
                        thumbset = True

    # Process the current message
    await process_media(message.document or message.photo)

    # If no thumbnail is set, process the reply message
    if not thumbset and reply:
        await process_media(reply.document or reply.photo)

    if thumbset:
        watermark_path = os.path.join(user_id, 'watermark.jpg')
        watermarked_thumbnail_path = os.path.join(user_id, 'watermarked_thumbnail.jpg')
        if os.path.isfile(watermark_path):
            await watermark_photo(thumbnail_path, watermark_path, watermarked_thumbnail_path)
        await message.reply_text('Thumbnail set ☑️')
    else:
        await message.reply_text('Cannot find thumbnail ¯\\_(ツ)_/¯')


@Client.on_message(
    filters.command(['clearthumbnail', 'rmthumbnail', 'delthumbnail', 'removethumbnail', 'deletethumbnail']) & filters.chat(ALL_CHATS)
)
async def rmthumbnail(client: Client, message: Message):
    user_id = str(message.from_user.id)
    for file_name in ['thumbnail.jpg', 'watermarked_thumbnail.jpg']:
        file_path = os.path.join(user_id, file_name)
        if os.path.isfile(file_path):
            os.remove(file_path)
    await message.reply_text('Thumbnail cleared 🗑')


help_dict['thumbnail'] = (
    'Thumbnail',
    '''/thumbnail <i>&lt;as reply to image or as a caption&gt;</i>
/setthumbnail <i>&lt;as reply to image or as a caption&gt;</i>
/savethumbnail <i>&lt;as reply to image or as a caption&gt;</i>

/clearthumbnail
/rmthumbnail
/removethumbnail
/delthumbnail
/deletethumbnail'''
)
