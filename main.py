import asyncio
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import mongo
import parcer

storage = MemoryStorage()


load_dotenv()

telegram_key = os.getenv('TELEGRAM_API_KEY')
ADMIN_ID = os.getenv('TELEGRAM_ADMIN_ID')

bot = Bot(token=telegram_key)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


class LinkState(StatesGroup):
    waiting_for_link = State()


@dp.message_handler(commands=['start'])
async def start_bot(message):
    if await mongo.user_exist(message.from_user.id):
        first_mess = f"<b>{message.from_user.first_name}</b>, привет!"
        await bot.send_message(message.chat.id, first_mess, parse_mode='html')
    else:
        markup = types.InlineKeyboardMarkup()
        item = types.InlineKeyboardButton("Введите ссылку", callback_data="input_link")
        markup.add(item)
        first_mess = f"<b>{message.from_user.first_name}</b>, привет!\nЯ бот, который упростит твою жизнь! Я помогаю просматривать расписание СГТУ им.Гагарина прямо в телеграмме!\n"
        await bot.send_message(message.chat.id, first_mess, parse_mode='html', reply_markup=markup)


@dp.message_handler(commands=['today'])
async def today_timetable(message):
    screenshotName = f"screenshots/{message.from_user.id}.png"
    day_num = 0
    print(day_num)
    if await parcer.getDayScreenshot(await mongo.get_url(message.from_user.id), day_num, 'day-current', screenshotName):
        await bot.send_photo(message.chat.id, photo=open(screenshotName, 'rb'),
                             caption='Расписание на сегодня')
        await asyncio.sleep(20)
        os.remove(screenshotName)
    else:
        await bot.send_message(message.chat.id, f'У вас сегодня выходной, расслабьтесь :)')


@dp.message_handler(commands=['tomorrow'])
async def tomorrow_timetable(message):
    day_num = (datetime.now().weekday() + 2) % 7
    print(day_num)
    screenshot_name = f"screenshots/{message.from_user.id}.png"
    if await parcer.getDayScreenshot(await mongo.get_url(message.from_user.id), day_num, 'day', screenshot_name):
        await bot.send_photo(message.chat.id, photo=open(screenshot_name, 'rb'),
                             caption='Расписание на завтра')
        await asyncio.sleep(20)
        os.remove(screenshot_name)
    else:
        await bot.send_message(message.chat.id, f'У вас завтра выходной, расслабьтесь :)')


@dp.message_handler(commands=['current_week'])
async def current_week_timetable(message):
    screenshot_name = f"screenshots/{message.from_user.id}.png"
    await parcer.getWeekScreenshot(await mongo.get_url(message.from_user.id), 0, 'week', screenshot_name)
    await bot.send_photo(message.chat.id, photo=open(screenshot_name, 'rb'),
                         caption='Расписание на текущую неделю')
    time.sleep(20)
    os.remove(screenshot_name)


@dp.message_handler(commands=['next_week'])
async def next_week_timetable(message):
    screenshot_name = f"screenshots/{message.from_user.id}.png"
    await parcer.getWeekScreenshot(await mongo.get_url(message.from_user.id), 1, 'week', screenshot_name)
    await bot.send_photo(message.chat.id, photo=open(screenshot_name, 'rb'),
                         caption='Расписание на следующую неделю')
    time.sleep(5)
    os.remove(screenshot_name)


@dp.message_handler(commands=['schedule'])
async def set_schedule(message):
    await mongo.update_schedule(message.from_user.id)
    if await mongo.is_schedule(message.from_user.id):
        await bot.send_message(message.chat.id, f'Теперь вы будете получать расписание по времени')
    else:
        await bot.send_message(message.chat.id, f'Теперь вы не будете  получать расписание по времени')


@dp.message_handler(commands=['help'])
async def help_message(message):
    await bot.send_message(message.chat.id,
                           f'🚀 Добро пожаловать в бота расписания СГТУ им. Гагарина! 🚀\nЭтот бот поможет вам всегда быть в курсе вашего расписания занятий. Просто отправьте ему ссылку на ваше расписание формата «rasp.sstu» и используйте следующие команды:\n📅 /today - получить расписание на сегодня \n🔜 /tomorrow - узнать расписание на завтра\n📆 /current_week - расписание на текущую неделю\n🔍 /next_week - расписание на следующую неделю\n⏰ /schedule - настроить автоматическую отправку расписания по времени\n🔄 /update_link - обновить ссылку на ваше расписание\n❓ /help - показать это справочное сообщение\n\nНе забудьте начать с отправки ссылки на ваше расписание! Если возникнут вопросы или предложения, не стесняйтесь обращаться. Удачного использования! 🎓📚')


@dp.message_handler(commands=['update_link'])
async def update_link(message):
    markup = types.InlineKeyboardMarkup()
    item = types.InlineKeyboardButton("Введите ссылку", callback_data="input_link")
    markup.add(item)
    update_message = f"<b>{message.from_user.first_name}</b>, Давайте поменяем ссылку\n"
    await bot.send_message(message.chat.id, update_message, parse_mode='html', reply_markup=markup)


@dp.callback_query_handler(lambda c: c.data and c.data == "input_link")
async def callback_query(call: types.CallbackQuery):
    await call.message.answer("Пожалуйста, введите ссылку:")
    await LinkState.waiting_for_link.set()


@dp.message_handler(state=LinkState.waiting_for_link)
async def process_add_user(message: types.Message, state: FSMContext):
    if await mongo.user_exist(message.from_user.id):
        if await mongo.update_url(message.from_user.id, message.text):
            await bot.send_message(message.chat.id, f'Ваша ссылка обновлена!')
            await state.finish()
        else:
            await bot.send_message(message.chat.id, f'Возникла ошибка, повторите попытку позже')
            await state.finish()
    else:
        await mongo.add_one(message.from_user.first_name, message.from_user.id, message.text)
        await bot.send_message(message.chat.id, f'Спасибо, ваша ссылка сохранена!')
        await state.finish()


async def on_startup(dp):
    await bot.send_message(chat_id=ADMIN_ID, text='Bot has been started')


async def on_shutdown(dp):
    await bot.send_message(chat_id=ADMIN_ID, text='Bot has been stopped')


if __name__ == '__main__':
    from aiogram import executor

    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
