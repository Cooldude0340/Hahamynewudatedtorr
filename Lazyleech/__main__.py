# lazyleech - Telegram bot primarily to leech from torrents and upload to Telegram
# Copyright (c) 2021 lazyleech developers
# Licensed under the GNU Affero General Public License, version 3 or later.

import asyncio
import logging
import traceback
from pyrogram import idle
from . import app, ADMIN_CHATS, preserved_logs
from .utils.upload_worker import upload_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logging.getLogger('pyrogram.syncer').setLevel(logging.WARNING)

async def autorestart_worker():
    """
    Continuously runs the upload worker, restarting it on failure.
    """
    while True:
        try:
            await upload_worker()
        except Exception as ex:
            preserved_logs.append(ex)
            logging.exception('Upload worker encountered an error and will restart.')
            tb = traceback.format_exc()
            for chat_id in ADMIN_CHATS:
                try:
                    await app.send_message(chat_id, 'Upload worker encountered an error and restarted.')
                    await app.send_message(chat_id, f"Traceback:\n{tb}", parse_mode=None)
                except Exception as inner_ex:
                    logging.exception('Failed to notify admin chat %s due to: %s', chat_id, inner_ex)

async def main():
    """
    Main entry point for the application.
    """
    # Start the autorestart worker
    asyncio.create_task(autorestart_worker())

    # Start the Pyrogram client
    await app.start()

    # Keep the bot running until interrupted
    logging.info("Bot is running. Press Ctrl+C to stop.")
    await idle()

    # Stop the Pyrogram client
    await app.stop()
    logging.info("Bot stopped.")

if __name__ == "__main__":
    try:
        # Run the event loop
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot interrupted and is shutting down.")
    except Exception as e:
        logging.exception("Unexpected error occurred: %s", e)
