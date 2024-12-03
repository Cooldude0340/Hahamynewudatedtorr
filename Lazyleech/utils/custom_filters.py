from typing import Union, List
from pyrogram import filters
from pyrogram.types import CallbackQuery

def callback_data(data: Union[str, List[str]]):
    """
    Custom filter for handling callback queries with specific data.

    Args:
        data (Union[str, List[str]]): Single string or list of strings to match with callback query data.

    Returns:
        Filter: A Pyrogram filter that checks callback query data.
    """
    data = data if isinstance(data, list) else [data]

    def func(flt, _, callback_query: CallbackQuery):
        return callback_query.data in flt.data

    return filters.create(
        func,
        name='CustomCallbackDataFilter',
        data=data
    )

def callback_chat(chats: Union[int, List[int]]):
    """
    Custom filter for handling callback queries from specific chat IDs.

    Args:
        chats (Union[int, List[int]]): Single chat ID or list of chat IDs to match.

    Returns:
        Filter: A Pyrogram filter that checks the chat ID of callback query messages.
    """
    chats = chats if isinstance(chats, list) else [chats]

    def func(flt, _, callback_query: CallbackQuery):
        return callback_query.message.chat.id in flt.chats

    return filters.create(
        func,
        name='CustomCallbackChatsFilter',
        chats=chats
    )
