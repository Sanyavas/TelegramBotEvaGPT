import os
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.server_api import ServerApi
import dotenv

# Завантажте змінні середовища з .env файлу
dotenv.load_dotenv()
# З'єднання з MongoDB
client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))
DB_MONGO_HISTORY = client.eva_gpt_bot.users_history
DB_MONGO_ENEMY = client.eva_gpt_bot.enemy_losses


def get_chat_history(user_id):
    """Отримання історії чату для певного користувача"""
    history = DB_MONGO_HISTORY.find({'user_id': user_id}).sort('_id', DESCENDING).limit(5)  # 5 останні повідомлення
    return list(history)


def get_enemy_losses():
    """Отримання даних про втрати ворога"""
    el = DB_MONGO_ENEMY.find().sort('_id', ASCENDING).limit(5)  # 5 перших зі списку дат
    return list(el)


def clear_chat_history(user_id):
    """Очищення історії чату для певного користувача"""
    DB_MONGO_HISTORY.delete_many({'user_id': user_id})
