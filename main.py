from io import BytesIO
import re

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from decouple import Config, RepositoryEnv


env = Config(RepositoryEnv('.env'))
bot = Bot(token=env.get('TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

messages_buffer = []
title = False
file_title = ''


def slugify(s):
  s = s.lower().strip()
  s = re.sub(r'[^\w\s-]', '', s)
  s = re.sub(r'[\s_-]+', '-', s)
  s = re.sub(r'^-+|-+$', '', s)
  return s


@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Hello! I am your message formatter bot. Send me your messages and I will create .doc file "
                        "for you.")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Send me your messages and I will create .doc file for you. Use \get_file command when you"
                        "send everything you wanted")


@dp.message_handler(commands=['clear'])
async def clear_buffer(message: types.Message):
    messages_buffer.clear()
    await message.reply("Buffer successfully cleared. YOu can send me messages again")


@dp.message_handler(commands=['next'])
async def get_title(message: types.Message):
    global title
    title = True
    await message.reply("Enter your file title.")


@dp.message_handler(commands=['get_file'])
async def get_file(message: types.Message):
    if not messages_buffer:
        await message.reply("Message buffer is empty!")
        return
    elif len(file_title) == 0:
        global title
        title = True
        await message.reply('Enter your file title first.')
        return

    file_data = BytesIO('\n\n'.join(messages_buffer).encode('utf8'))

    await bot.send_document(message.chat.id, (f'{file_title}.doc', file_data), caption="Here is your file:")
    messages_buffer.clear()


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def collect_messages(message: types.Message):
    global title
    if not title:
        text = message.text
        messages_buffer.append(text)
        await message.reply("Message saved! Press /next if you want to move to the next step.")
    else:
        global file_title
        file_title = slugify(message.text)
        await message.reply("File title saved! Now press /get_file to get your file.")
        title = False

if __name__ == '__main__':
    executor.start_polling(dp)