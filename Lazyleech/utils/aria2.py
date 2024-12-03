import os
import json
import time
import base64
import random
import asyncio
import tempfile
from aiohttp import ClientSession  # Explicitly specify the async HTTP client

HEX_CHARACTERS = 'abcdef'
HEXNUMERIC_CHARACTERS = HEX_CHARACTERS + '0123456789'

class Aria2Error(Exception):
    def __init__(self, message):
        self.error_code = message.get('code')
        self.error_message = message.get('message')
        super().__init__(str(message))

def _raise_or_return(data):
    if 'error' in data:
        raise Aria2Error(data['error'])
    return data.get('result')

async def aria2_request(session: ClientSession, method: str, params: list = None):
    if params is None:
        params = []
    data = {
        'jsonrpc': '2.0',
        'id': str(time.time()),
        'method': method,
        'params': params
    }
    async with session.post('http://127.0.0.1:6800/jsonrpc', json=data) as resp:
        resp.raise_for_status()  # Ensure HTTP errors are raised
        return await resp.json()

async def aria2_tell_active(session: ClientSession):
    return _raise_or_return(await aria2_request(session, 'aria2.tellActive'))

async def aria2_tell_status(session: ClientSession, gid: str):
    return _raise_or_return(await aria2_request(session, 'aria2.tellStatus', [gid]))

async def aria2_change_option(session: ClientSession, gid: str, options: dict):
    return _raise_or_return(await aria2_request(session, 'aria2.changeOption', [gid, options]))

async def aria2_remove(session: ClientSession, gid: str):
    return _raise_or_return(await aria2_request(session, 'aria2.remove', [gid]))

async def generate_gid(session: ClientSession, user_id: int):
    def _generate_gid():
        gid = str(user_id) + random.choice(HEX_CHARACTERS)
        while len(gid) < 16:
            gid += random.choice(HEXNUMERIC_CHARACTERS)
        return gid

    while True:
        gid = _generate_gid()
        try:
            await aria2_tell_status(session, gid)
        except Aria2Error as ex:
            if ex.error_code == 1 and ex.error_message == f'GID {gid} is not found':
                return gid

def is_gid_owner(user_id: int, gid: str):
    return gid.split(str(user_id), 1)[-1][0] in HEX_CHARACTERS

async def aria2_add_torrent(session: ClientSession, user_id: int, link: str, timeout: int = 0):
    if os.path.isfile(link):
        with open(link, 'rb') as file:
            torrent = file.read()
    else:
        async with session.get(link) as resp:
            resp.raise_for_status()
            torrent = await resp.read()

    torrent = base64.b64encode(torrent).decode()
    dir_path = os.path.join(os.getcwd(), str(user_id), str(time.time()))
    return _raise_or_return(await aria2_request(session, 'aria2.addTorrent', [torrent, [], {
        'gid': await generate_gid(session, user_id),
        'dir': dir_path,
        'seed-time': 0,
        'bt-stop-timeout': str(timeout)
    }]))

async def aria2_add_magnet(session: ClientSession, user_id: int, link: str, timeout: int = 0):
    with tempfile.TemporaryDirectory() as tempdir:
        gid = _raise_or_return(await aria2_request(session, 'aria2.addUri', [[link], {
            'dir': tempdir,
            'bt-save-metadata': 'true',
            'bt-metadata-only': 'true',
            'follow-torrent': 'false'
        }]))
        try:
            while True:
                info = await aria2_tell_status(session, gid)
                if info['status'] != 'active':
                    break
                await asyncio.sleep(0.5)
            filename = os.path.join(tempdir, info['infoHash'] + '.torrent')
            return await aria2_add_torrent(session, user_id, filename, timeout)
        finally:
            try:
                await aria2_remove(session, gid)
            except Aria2Error as ex:
                if ex.error_code != 1 or ex.error_message != f'Active Download not found for GID#{gid}':
                    raise

async def aria2_add_directdl(session: ClientSession, user_id: int, link: str, filename: str = None, timeout: int = 60):
    dir_path = os.path.join(os.getcwd(), str(user_id), str(time.time()))
    options = {
        'gid': await generate_gid(session, user_id),
        'dir': dir_path,
        'timeout': str(timeout),
        'follow-torrent': 'false',
        'header': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
    }
    if filename:
        options['out'] = filename
    return _raise_or_return(await aria2_request(session, 'aria2.addUri', [[link], options]))
