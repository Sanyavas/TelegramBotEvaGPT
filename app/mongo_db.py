import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import dotenv

# Завантажте змінні середовища з .env файлу
dotenv.load_dotenv()
# З'єднання з MongoDB
client = MongoClient(os.getenv('MONGO_URI'), server_api=ServerApi('1'))
DB_MONGO = client.chat_history.users_history


def get_chat_history(user_id):
    """Отримання історії чату для певного користувача"""
    history = DB_MONGO.find({'user_id': user_id})
    return list(history)


def clear_chat_history(user_id):
    """Очищення історії чату для певного користувача"""
    DB_MONGO.delete_many({'user_id': user_id})
