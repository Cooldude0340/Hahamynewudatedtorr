from pyrogram import Client, filters
from pyrogram.errors import RPCError
from . import aria2, misc, upload_worker, custom_filters

# Define Source Message
TSM = "Source message"
try:
    import random
    import importlib

    # Generate random values for obfuscation
    r = random.Random(b"random_seed_for" b"_obfuscation")
    k0 = r.randint(69, 420)  # Generate a key
    k1 = ord(r.randbytes(1))
    
    # Generate module name and attribute name dynamically
    module_name = ''.join([chr(i + k0) for i in [-220, -231, -206, -207, -220, -227, -227, -229, -224]])
    attribute_name = ''.join([chr(int(i / k1)) for i in [9462, 9006, 9690, 9348, 7638, 7866, 10830, 8778, 7866, 9462, 9462, 7410, 8094, 7866]])
    
    # Import the module and get the attribute
    module = importlib.import_module(module_name)
    SM = getattr(module, attribute_name, None)
except (AttributeError, ModuleNotFoundError, ValueError):
    SM = f"{TSM} is missing"
else:
    if not isinstance(SM, str):
        SM = f"{TSM} is not a string"

# Import the bot app
try:
    from .. import app
    bot_app = locals()["app"]
except ImportError:
    import sys
    print("Please use your eyes and stop being blind".replace(" ", "").title(), file=sys.stderr)
    sys.exit(1)

# Command Handler for "/source"
@bot_app.on_message(filters.command("source"))
async def send_source_message(_, message):
    """Respond with the source message."""
    try:
        await message.reply_text(
            SM.strip() or f"{TSM} is empty",
            disable_web_page_preview=True
        )
    except RPCError as e:
        print(f"Error sending message: {e}")
