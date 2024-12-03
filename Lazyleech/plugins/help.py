import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .. import ALL_CHATS, help_dict
from ..utils import custom_filters

# Tracks callback information
callback_info = {}
callback_lock = asyncio.Lock()

@Client.on_message(filters.command('help') & filters.chat(ALL_CHATS))
async def help_cmd(client: Client, message):
    """Handles the /help command to provide module-specific help."""
    # Extract module name from the command
    module_name = (message.text.split(' ', 1)[1:] or [None])[0]
    module_name = module_name.lower().strip() if module_name else None

    text = None
    buttons = []
    # Look for the requested module
    for internal_name, (external_name, module_text) in help_dict.items():
        if module_name in (internal_name.lower(), external_name.lower()):
            text = module_text
            buttons = [[InlineKeyboardButton('Back', 'help_back')]]
            break
    else:
        # Default help menu if no specific module is requested or found
        text = 'Select the module you want help with 👀'
        buttons = generate_help_menu_buttons(help_dict)

    reply = await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    callback_info[(reply.chat.id, reply.message_id)] = (message.from_user.id, module_name)


@Client.on_callback_query(custom_filters.callback_data('help_back') & custom_filters.callback_chat(ALL_CHATS))
async def help_back(client: Client, callback_query):
    """Handles the 'Back' button in the help menu."""
    message = callback_query.message
    message_id = (message.chat.id, message.message_id)

    # Validate callback info
    if message_id not in callback_info:
        await callback_query.answer('This help message is too old.', show_alert=True, cache_time=3600)
        return

    async with callback_lock:
        user_id, _ = callback_info[message_id]
        if callback_query.from_user.id != user_id:
            await callback_query.answer('You cannot perform this action.', cache_time=3600)
            return

        buttons = generate_help_menu_buttons(help_dict)
        await message.edit_text('Select the module you want help with 👀', reply_markup=InlineKeyboardMarkup(buttons))
        callback_info[message_id] = (user_id, None)
    await callback_query.answer()


@Client.on_callback_query(filters.regex(r'^help_m.+') & custom_filters.callback_chat(ALL_CHATS))
async def help_module(client: Client, callback_query):
    """Handles module-specific help requests from the menu."""
    message = callback_query.message
    message_id = (message.chat.id, message.message_id)

    # Validate callback info
    if message_id not in callback_info:
        await callback_query.answer('This help message is too old.', show_alert=True, cache_time=3600)
        return

    async with callback_lock:
        user_id, _ = callback_info[message_id]
        if callback_query.from_user.id != user_id:
            await callback_query.answer('You cannot perform this action.', cache_time=3600)
            return

        module_key = callback_query.data[6:]
        if module_key not in help_dict:
            await callback_query.answer('Module not found.')
            return

        module_name, module_text = help_dict[module_key]
        await message.edit_text(module_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('Back', 'help_back')]
        ]))
        callback_info[message_id] = (user_id, module_key)
    await callback_query.answer()


def generate_help_menu_buttons(help_data):
    """Generates the inline keyboard buttons for the help menu."""
    buttons = []
    row = []
    for internal_name, (external_name, _) in help_data.items():
        row.append(InlineKeyboardButton(external_name.strip(), f'help_m{internal_name}'))
        if len(row) >= 3:  # Adjust number of buttons per row if necessary
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons
