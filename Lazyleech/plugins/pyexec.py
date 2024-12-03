import ast
import sys
import html
import inspect
import traceback
from io import BytesIO, StringIO
from pyrogram import Client, filters
from .. import ADMIN_CHATS

@Client.on_message(filters.command('exec') & filters.chat(ADMIN_CHATS))
async def run_code(client, message):
    class UniqueExecReturnIdentifier:
        pass

    code = message.text[5:].strip()
    if not code:
        await message.reply_text('Code block is empty.')
        return

    try:
        tree = ast.parse(code)
        original_body = tree.body
        modified_body = original_body.copy()
        modified_body.append(ast.Return(ast.Name('_ueri', ast.Load())))

        def generate_function(body):
            # Define arguments: m, message, c, client, _ueri
            func = ast.AsyncFunctionDef(
                'ex',
                ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg=i) for i in ['m', 'message', 'c', 'client', '_ueri']],
                    kwonlyargs=[], kw_defaults=[], defaults=[]
                ),
                body=body,
                decorator_list=[]
            )
            ast.fix_missing_locations(func)
            module = ast.Module(body=[func], type_ignores=[])
            compiled_code = compile(module, '<ast>', 'exec')
            local_scope = {}
            exec(compiled_code, globals(), local_scope)
            return local_scope['ex']

        ex_function = generate_function(modified_body)

    except SyntaxError as e:
        if e.msg != "'return' with value in async generator":
            await message.reply_text(f"Syntax Error:\n<code>{html.escape(e.msg)}</code>", parse_mode="HTML")
            return
        ex_function = generate_function(original_body)

    escaped_code = html.escape(code)
    async_obj = ex_function(message, message, client, client, UniqueExecReturnIdentifier)
    reply = await message.reply_text(f"Type[py]\n<code>{escaped_code}</code>\nState[Executing]", parse_mode="HTML")

    stdout_backup = sys.stdout
    stderr_backup = sys.stderr
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    sys.stdout = stdout_buffer
    sys.stderr = stderr_buffer

    try:
        result = []
        if inspect.isasyncgen(async_obj):
            async for output in async_obj:
                result.append(output)
        else:
            output = await async_obj
            if output != UniqueExecReturnIdentifier:
                result.append(output)

    except Exception as e:
        traceback_message = traceback.format_exc()
        await message.reply_text(f"Exception occurred:\n<code>{html.escape(traceback_message)}</code>", parse_mode="HTML")
        return
    finally:
        sys.stdout = stdout_backup
        sys.stderr = stderr_backup

    stdout_content = stdout_buffer.getvalue().strip()
    stderr_content = stderr_buffer.getvalue().strip()
    output_message = "\n".join(filter(None, [stdout_content, stderr_content, *map(str, result)]))
    output_message = html.escape(output_message) or 'undefined'

    await reply.edit_text(f"Type[py]\n<code>{escaped_code}</code>\nState[Executed]\nOutput:\n<code>{output_message}</code>", parse_mode="HTML")
