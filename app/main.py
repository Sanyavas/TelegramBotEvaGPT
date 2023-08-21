import os
import logging
import dotenv
from datetime import datetime

import telebot.types
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from flask import Flask, request, Response

from open_ai import question_to_ai
from mongo_db import get_chat_history, clear_chat_history, DB_MONGO_HISTORY
from enemy_losses import scheduler_enemy

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)

OTHER_TG_TOKEN = os.getenv('OTHER_TG_TOKEN')  # !!!

TG_TOKEN = os.getenv('TG_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = "/"
WEBHOOK_HOST = "0.0.0.0"
WEBHOOK_PORT = 8080  # !! 8080

bot = Bot(token=OTHER_TG_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

app = Flask(__name__)

KEYBOARD = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
BUTTONS = ["/history_user", "/info_user", "/clear_history", "/my_projects", "/vote"]
KEYBOARD.add(*[KeyboardButton(button) for button in BUTTONS])

TIME_NOW = datetime.now().strftime('%d-%m-%Y %H:%M:%S')

flag_false = False
like = 0
dislike = 0


@app.route('/', methods=["POST", "GET"])
def webhook_handle():
    return '<h1>Hello World</h1>'


@dp.message_handler(commands=["start"])
async def start_message(message: types.Message):
    await bot.send_photo(message.from_user.id,
                         photo='https://i.pinimg.com/564x/c6/b9/1d/c6b91d47538de8534d5302bdb6135eb0.jpg')
    await message.answer(f"Вітаю {message.from_user.first_name}! Мене звати EVA, я ваш AI-помічник.",
                         reply_markup=KEYBOARD)


@dp.message_handler(commands=["info_user"])
async def info_message(message: types.Message):
    await message.answer(f"Інформація про користувача:\n {message}")


@dp.message_handler(commands=['history_user'])
async def show_history(message: types.Message):
    user_id = message.from_user.id
    history_records = get_chat_history(user_id)

    formatted_history = ''
    for record in history_records:
        formatted_history += f"Date: {record['date']}\nYou: {record['text']}\nEVA: {record['response']}\n\n"

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
    ikm = InlineKeyboardMarkup(row_width=1)
    ikb1 = InlineKeyboardButton(text='Personal project Quotes', url='https://sanyavas-django.fly.dev/')
    ikb2 = InlineKeyboardButton(text='Team project Xmara', url='https://xmara.fly.dev/')
    ikm.add(ikb1, ikb2)
    photo_url = "https://i.pinimg.com/564x/33/65/29/3365296afc98e3178c45e6b76dd525fc.jpg"
    await bot.send_photo(chat_id=message.from_user.id, photo=photo_url, caption="My projects on Django:",
                         reply_markup=ikm)


@dp.message_handler(commands=["vote"])
async def vote_command(message: types.Message):
    ikm = InlineKeyboardMarkup(row_width=2)
    ikb1 = InlineKeyboardButton(text=f'👍{like}', callback_data="like")
    ikb2 = InlineKeyboardButton(text=f'👎{dislike}', callback_data="dislike")
    ikb3 = InlineKeyboardButton(text='Close', callback_data="close")
    ikm.add(ikb1, ikb2, ikb3)
    photo_url = "https://i.pinimg.com/564x/05/da/c9/05dac9b5ba156a2ad78eb09f3fa65795.jpg"
    await bot.send_photo(chat_id=message.from_user.id, photo=photo_url, caption="Тобі подобається цей персонаж?",
                         reply_markup=ikm)
    await message.delete()


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
            'date': TIME_NOW,
            'response': response_text
        }
        DB_MONGO_HISTORY.insert_one(chat_record)
    except Exception as e:
        logging.error(f"Error while processing the message: {e}")
        await message.answer("Вибачте, виникла помилка під час обробки вашого повідомлення.")


@dp.callback_query_handler(text='close')
async def vote_close_handler(callback: types.CallbackQuery):
    await callback.message.delete()


# @dp.callback_query_handler()
# async def vote_callback(callback: types.CallbackQuery):
#     # print(callback)
#     global flag_false, like, dislike
#     if not flag_false:
#         if callback.data == 'like':
#             await callback.answer(show_alert=False, text='так, цей робот має милий погляд!')
#             like += 1
#             flag_false = True
#         await callback.answer(show_alert=False, text='у тебе нема серця...')
#         dislike += 1
#         flag_false = True
#     await callback.answer(text='ти вже зробив свій вибір', show_alert=True)


@dp.callback_query_handler()
async def vote_callback(callback: types.CallbackQuery):
    global flag_false, like, dislike

    if flag_false:
        return await callback.answer(text='ти вже зробив свій вибір', show_alert=True)

    if callback.data == 'like':
        await callback.answer(show_alert=False, text='так, цей робот має милий погляд!')
        like += 1
    elif callback.data == 'dislike':
        await callback.answer(show_alert=False, text='у тебе нема серця...')
        dislike += 1
    flag_false = True

    ikm = InlineKeyboardMarkup(row_width=2)
    ikb1 = InlineKeyboardButton(text=f'👍{like}', callback_data="like")
    ikb2 = InlineKeyboardButton(text=f'👎{dislike}', callback_data="dislike")
    ikb3 = InlineKeyboardButton(text='Close', callback_data="close")
    ikm.add(ikb1, ikb2, ikb3)

    # Редагування повідомлення з оновленими даними
    await bot.edit_message_caption(caption="Тобі подобається цей персонаж?",
                                   chat_id=callback.message.chat.id,
                                   message_id=callback.message.message_id,
                                   reply_markup=ikm)


async def on_startup(_):
    logging.info(f"Start telegram bot. {datetime.now()}")
    scheduler_enemy()


async def on_shutdown(_):
    logging.warning('Shutting down..')


# async def on_startup(dp):
#     # await bot.send_message(chat_id=ADMIN_ID, text="бот запущено")
#     logging.info(f"Start telegram bot. {TIME_NOW}")
#     scheduler_enemy()
#     await bot.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)
#
#
# async def on_shutdown(dp):
#     # await bot.send_message(chat_id=ADMIN_ID, text="бот вимкнено")
#     logging.warning(f'Shutting down.. {TIME_NOW}')
#     await bot.delete_webhook()


if __name__ == '__main__':
    # dp.middleware.setup(TestMiddleware())  # add middleware
    executor.start_polling(dp,
                           on_startup=on_startup,
                           on_shutdown=on_shutdown,
                           skip_updates=True)

# if __name__ == '__main__':
#     # app.run()
#     executor.start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH,
#                            on_startup=on_startup, on_shutdown=on_shutdown,
#                            host=WEBHOOK_HOST, port=WEBHOOK_PORT, skip_updates=True)
