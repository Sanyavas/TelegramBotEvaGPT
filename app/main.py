import os
import logging
import dotenv
from datetime import datetime

import telebot
from telebot.types import ReplyKeyboardMarkup

from open_ai import question_to_ai
from mongo_db import get_chat_history, clear_chat_history, DB_MONGO
from enemy_losses import scheduler_enemy

# Завантажте змінні середовища з .env файлу
dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TG_TOKEN = os.getenv('TG_TOKEN')


def telegram_bot():
    logger.info(f"Start telegram bot. {datetime.now()}")
    bot = telebot.TeleBot(TG_TOKEN)

    @bot.message_handler(commands=["start"])
    def start_message(message):
        start_buttons = ["/history", "info", "/clearhistory"]
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*start_buttons)
        # mess = f'Вітаю {message.from_user.first_name}'
        # bot.send_message(message.chat.id, mess)
        bot.send_message(message.chat.id, "button", reply_markup=keyboard)

    @bot.message_handler(commands=['history'])
    def show_history(message):
        user_id = message.from_user.id
        history_records = get_chat_history(user_id)

        # Форматуємо історію для відображення
        formatted_history = ''
        for record in history_records:
            formatted_history += f"Ти: {record['text']}\nEVA: {record['response']}\n\n"

        # Відправляємо історію користувачу
        if formatted_history:
            bot.send_message(message.chat.id, formatted_history)
        else:
            bot.send_message(message.chat.id, "Історія чату порожня.")

    @bot.message_handler(commands=['clearhistory'])
    def handle_clear_history(message):
        user_id = message.from_user.id
        clear_chat_history(user_id)
        bot.send_message(message.chat.id, "Ваша історія чату була видалена.")

    @bot.message_handler(content_types=['text'])
    def send_text(message):
        hello_msg = ['hello', 'hi', 'привіт', 'вітаю']
        info_msg = ['info', 'інфо']

        if message.text.lower() in hello_msg:
            bot.send_message(message.chat.id, f"Привіт! {message.from_user.first_name}\nЧим я можу тобі допомогти?",
                             parse_mode='html')
        elif message.text.lower() in info_msg:
            bot.send_message(message.chat.id, f"Інформація про користувача:\n {message}")
        else:
            response_text = None
            try:
                if message.text.lower():
                    response_text = question_to_ai(message.from_user.id, message.text)
                    bot.send_message(message.chat.id, response_text, parse_mode='html')

                # Збереження повідомлень у MongoDB (тільки якщо є відповідь від GPT-3)
                if response_text:
                    chat_record = {
                        'user_id': message.from_user.id,
                        'username': message.from_user.username,
                        'text': message.text,
                        'response': response_text
                    }
                    DB_MONGO.insert_one(chat_record)
            except Exception as e:
                logger.error(f"Error while processing the message: {e}")
                bot.send_message(message.chat.id, "Вибачте, виникла помилка під час обробки вашого повідомлення.")

    bot.polling(none_stop=True)


def main():
    try:
        scheduler_enemy()
        telegram_bot()

    except Exception as ex:
        logger.error(f'Main error: {ex}')


if __name__ == '__main__':
    main()
