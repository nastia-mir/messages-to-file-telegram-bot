import re
import os
import asyncio

from io import BytesIO
from aiogram import Bot, Dispatcher
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage

from background import keep_alive


bot = Bot(token=os.getenv("TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

messages_buffers = {}
buffer_timeout = 600


def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s


async def clear_buffer(chat_id):
    await asyncio.sleep(messages_buffers[chat_id]['buffer_timeout'])
    if chat_id in messages_buffers:
        del messages_buffers[chat_id]


@dp.message(Command("start"))
async def process_start_command(message: Message):
    chat_id = message.chat.id
    if chat_id in messages_buffers.keys():
        del messages_buffers[chat_id]
    messages_buffers[chat_id] = {'messages': [],
                                 'title': '',
                                 'title_flag': False,
                                 'buffer_timeout': buffer_timeout}
    asyncio.create_task(clear_buffer(chat_id))
    await message.answer("Hello! I am your message formatter bot. Send me your messages and I will create .doc file "
                        "for you.")


@dp.message(Command("help"))
async def process_help_command(message: Message):
    await message.answer("Send me your messages and I will create .doc file for you. Click /start to begin."
                        "\n\nPlease note that message buffer expires after 10 minutes. If you need more time, "
                        "you will have to resend messages once again.")


@dp.message(Command("clear"))
async def clear_buffer_command(message: Message):
    try:
        chat_id = message.chat.id
        messages_buffers[chat_id]['messages'].clear()
        messages_buffers[chat_id]['title'] = ""
        messages_buffers[chat_id]['title_flag'] = False
        await message.answer("Buffer successfully cleared. You can send me messages again")
    except:
        messages_buffers[chat_id] = {'messages': [],
                                     'title': '',
                                     'title_flag': False,
                                     'buffer_timeout': 300}
        await message.answer("Send me your messages and I will create .txt file for you.")


@dp.message(Command("next"))
async def get_title(message: Message):
    try:
        chat_id = message.chat.id
        messages_buffers[chat_id]['title_flag'] = True
        await message.answer("Enter your file title.")
    except:
        await message.answer("I can't remember where we stopped last time. Please click /start to begin.")


@dp.message(Command("get_file"))
async def get_file(message: Message):
    chat_id = message.chat.id
    if len(messages_buffers[chat_id]['messages']) == 0:
        await message.answer("Message buffer is empty.")
        return
    elif len(messages_buffers[chat_id]['title']) == 0:
        messages_buffers[chat_id]['title_flag'] = True
        await message.answer('Enter your file title first.')
        return
    elif not messages_buffers[chat_id]:
        await message.answer("I can't remember where we stopped last time. Please click /start to begin.")

    file_data = BytesIO('\n\n'.join(messages_buffers[chat_id]['messages']).encode('utf8'))

    document = BufferedInputFile(
        file_data.getvalue(),
        filename=f"{messages_buffers[chat_id]['title']}.txt"
    )

    await bot.send_document(
        chat_id,
        document=document,
        caption="Here is your file:"
    )

    messages_buffers[chat_id]['messages'].clear()
    messages_buffers[chat_id]['title'] = ""
    messages_buffers[chat_id]['title_flag'] = False


@dp.message()
async def collect_messages(message: Message):
    chat_id = message.chat.id
    try:
        if not messages_buffers[chat_id]['title_flag']:
            text = message.text
            messages_buffers[chat_id]['messages'].append(text)
            await message.answer("Message saved! Press /next if you want to move to the next step.")
        else:
            messages_buffers[chat_id]['title'] = slugify(message.text)
            await message.answer("File title saved! Now press /get_file to get your file.")
            messages_buffers[chat_id]['title_flag'] = False
    except:
        await message.answer("I can't remember where we stopped last time. Please click /start to begin.")

async def main():
    keep_alive()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
