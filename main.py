from io import BytesIO
import re

import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from decouple import Config, RepositoryEnv

from background import keep_alive


env = Config(RepositoryEnv('.env'))
bot = Bot(token=env.get('TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    chat_id = message.chat.id
    if chat_id in messages_buffers.keys():
        del messages_buffers[chat_id]
    messages_buffers[chat_id] = {'messages': [],
                                 'title': '',
                                 'title_flag': False,
                                 'buffer_timeout': buffer_timeout}
    asyncio.create_task(clear_buffer(chat_id))
    await message.reply("Hello! I am your message formatter bot. Send me your messages and I will create .doc file "
                        "for you.")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Send me your messages and I will create .doc file for you. Click /start to begin."
                        "\n\nPlease note that message buffer expires after 10 minutes. If you need more time, "
                        "you will have to resend messages once again.")


@dp.message_handler(commands=['clear'])
async def clear_buffer_command(message: types.Message):
    try:
        chat_id = message.chat.id
        messages_buffers[chat_id]['messages'].clear()
        messages_buffers[chat_id]['title'] = ""
        messages_buffers[chat_id]['title_flag'] = False
        await message.reply("Buffer successfully cleared. You can send me messages again")
    except:
        messages_buffers[chat_id] = {'messages': [],
                                     'title': '',
                                     'title_flag': False,
                                     'buffer_timeout': 300}
        await message.reply("Send me your messages and I will create .doc file for you.")


@dp.message_handler(commands=['next'])
async def get_title(message: types.Message):
    try:
        chat_id = message.chat.id
        messages_buffers[chat_id]['title_flag'] = True
        await message.reply("Enter your file title.")
    except:
        await message.reply("I can't remember where we stopped last time. Please click /start to begin.")


@dp.message_handler(commands=['get_file'])
async def get_file(message: types.Message):
    chat_id = message.chat.id
    if len(messages_buffers[chat_id]['messages']) == 0:
        await message.reply("Message buffer is empty.")
        return
    elif len(messages_buffers[chat_id]['title']) == 0:
        messages_buffers[chat_id]['title_flag'] = True
        await message.reply('Enter your file title first.')
        return
    elif not messages_buffers[chat_id]:
        await message.reply("I can't remember where we stopped last time. Please click /start to begin.")

    file_data = BytesIO('\n\n'.join(messages_buffers[chat_id]['messages']).encode('utf8'))

    await bot.send_document(message.chat.id, (f"'{messages_buffers[chat_id]['title']}.doc'", file_data),
                            caption="Here is your file:")
    messages_buffers[chat_id]['messages'].clear()
    messages_buffers[chat_id]['title'] = ""
    messages_buffers[chat_id]['title_flag'] = False


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def collect_messages(message: types.Message):
    chat_id = message.chat.id
    try:
        if not messages_buffers[chat_id]['title_flag']:
            text = message.text
            messages_buffers[chat_id]['messages'].append(text)
            await message.reply("Message saved! Press /next if you want to move to the next step.")
        else:
            messages_buffers[chat_id]['title'] = slugify(message.text)
            await message.reply("File title saved! Now press /get_file to get your file.")
            messages_buffers[chat_id]['title_flag'] = False
    except:
        await message.reply("I can't remember where we stopped last time. Please click /start to begin.")

keep_alive()
if __name__ == '__main__':
    asyncio.run(executor.start_polling(dp))
