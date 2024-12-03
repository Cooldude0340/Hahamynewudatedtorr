import asyncio
import os
import shlex
from typing import Tuple
from html_telegraph_poster import TelegraphPoster


def post_to_telegraph(a_title: str, content: str) -> str:
    """
    Create a Telegram Post using HTML content.
    
    Args:
        a_title (str): The title of the post.
        content (str): HTML-formatted content for the post.
    
    Returns:
        str: URL of the created Telegraph post.
    """
    post_client = TelegraphPoster(use_api=True)
    auth_name = "Weeb Zone"
    post_client.create_api_token(auth_name)
    post_page = post_client.post(
        title=a_title,
        author=auth_name,
        author_url="https://t.me/Torrent_leech_zone_x",
        text=content,
    )
    return post_page["url"]


async def runcmd(cmd: str) -> Tuple[str, str, int, int]:
    """
    Run a command in the terminal asynchronously.
    
    Args:
        cmd (str): Command to run.
    
    Returns:
        Tuple[str, str, int, int]: stdout, stderr, return code, and process PID.
    """
    args = shlex.split(cmd)
    process = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return (
        stdout.decode("utf-8", errors="replace").strip(),
        stderr.decode("utf-8", errors="replace").strip(),
        process.returncode,
        process.pid,
    )


def safe_filename(path_: str) -> str:
    """
    Make the filename safe by removing problematic characters.
    
    Args:
        path_ (str): Path to the file.
    
    Returns:
        str: Safened file path.
    """
    if not path_:
        return path_
    
    safename = path_.replace("'", "").replace('"', "")
    if safename != path_:
        os.rename(path_, safename)
    return safename
