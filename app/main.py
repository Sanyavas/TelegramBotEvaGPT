import os
import logging
import dotenv
from datetime import datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from open_ai import question_to_ai
from mongo_db import get_chat_history, clear_chat_history, DB_MONGO
from enemy_losses import scheduler_enemy

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

TG_TOKEN = os.getenv('TG_TOKEN')

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
BUTTONS = ["/history", "/info_user", "/clear_history", "/my_projects", "/vote"]
KEYBOARD.add(*[KeyboardButton(button) for button in BUTTONS])


@dp.message_handler(commands=["start"])
async def start_message(message: types.Message):
    await bot.send_photo(message.from_user.id,
                         photo='https://i.pinimg.com/564x/c6/b9/1d/c6b91d47538de8534d5302bdb6135eb0.jpg')
    await message.answer(f"Вітаю {message.from_user.first_name}! Мене звати EVA, я ваш AI-помічник.",
                         reply_markup=KEYBOARD)


@dp.message_handler(commands=["info_user"])
async def info_message(message: types.Message):
    await message.answer(f"Інформація про користувача:\n {message}")


@dp.message_handler(commands=['history'])
async def show_history(message: types.Message):
    user_id = message.from_user.id
    history_records = get_chat_history(user_id)

    formatted_history = ''
    for record in history_records:
        formatted_history += f"Ти: {record['text']}\nEVA: {record['response']}\n\n"

    if formatted_history:
        await message.answer(formatted_history)
    else:
        await message.answer("Історія чату порожня.")


@dp.message_handler(commands=['clear_history'])
async def handle_clear_history(message: types.Message):
    user_id = message.from_user.id
    clear_chat_history(user_id)
    await message.answer("Ваша історія чату була видалена.")


@dp.message_handler(commands=["my_projects"])
async def info_my_projects(message: types.Message):
    ikm = InlineKeyboardMarkup(row_width=2)
    ikb1 = InlineKeyboardButton(text='Personal project Quotes', url='https://sanyavas-django.fly.dev/')
    ikb2 = InlineKeyboardButton(text='Team project Xmara', url='https://xmara.fly.dev/')
    ikm.add(ikb1, ikb2)
    photo_url = "https://i.pinimg.com/564x/33/65/29/3365296afc98e3178c45e6b76dd525fc.jpg"
    await bot.send_photo(chat_id=message.from_user.id, photo=photo_url, caption="My projects on Django:",
                         reply_markup=ikm)


@dp.message_handler(commands=["vote"])
async def vote_command(message: types.Message):
    ikm = InlineKeyboardMarkup(row_width=2)
    ikb1 = InlineKeyboardButton(text='👍', callback_data="like")
    ikb2 = InlineKeyboardButton(text='👎', callback_data="dislike")
    ikm.add(ikb1, ikb2)
    photo_url = "https://i.pinimg.com/564x/05/da/c9/05dac9b5ba156a2ad78eb09f3fa65795.jpg"
    await bot.send_photo(chat_id=message.from_user.id, photo=photo_url, caption="Тобі подобається цей персонаж?",
                         reply_markup=ikm)


@dp.message_handler(content_types=['text'])
async def handle_text_messages(message: types.Message):
    hello_msg = ['hello', 'hi', 'привіт', 'вітаю']

    if message.text.lower() in hello_msg:
        await message.answer(f"Привіт {message.from_user.first_name}!\nЧим я можу тобі допомогти?")
        return

    try:
        response_text = question_to_ai(message.from_user.id, message.text)
        await message.answer(response_text)

        chat_record = {
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'text': message.text,
            'response': response_text
        }
        DB_MONGO.insert_one(chat_record)
    except Exception as e:
        logging.error(f"Error while processing the message: {e}")
        await message.answer("Вибачте, виникла помилка під час обробки вашого повідомлення.")


@dp.callback_query_handler()
async def vote_callback(callback: types.CallbackQuery):
    if callback.data == 'like':
        await callback.answer(text='так, цей робот має милий погляд!')
    await callback.answer(text='у тебе нема серця...')


async def on_startup(_):
    logging.info(f"Start telegram bot. {datetime.now()}")
    scheduler_enemy()


async def on_shutdown(_):
    logging.warning('Shutting down..')


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
