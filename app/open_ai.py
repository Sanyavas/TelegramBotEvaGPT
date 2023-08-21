import os
import json
import logging
from pathlib import Path

import openai
import dotenv

from mongo_db import get_chat_history, get_enemy_losses

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_KEY = os.getenv('OPENAI_KEY')

# BASE_DIR = Path(__file__).resolve().parent.parent
# current_dir = os.path.dirname(os.path.abspath(__file__))
# enemy_losses = os.path.join(current_dir, 'enemy_losses.json')
#
#
# def load_enemy_losses():
#     with open(enemy_losses, 'r', encoding='utf-8') as file:
#         data = json.load(file)
#     return data[:3]  # 3 останні дати втрат москалів


def question_to_ai(user_id, question):
    openai.api_key = OPENAI_KEY
    # enemy_losses_data = load_enemy_losses()
    enemy_losses = get_enemy_losses()
    worker = "Your name is EVA. " \
             "You are an assistant who answers questions clearly and as briefly as possible. " \
             "Always strive to give concise answers. " \
             "Answer in Ukrainian, unless otherwise indicated. " \
             # f"Information about the losses of the enemy: {enemy_losses}, these are the official losses of muscovites in Ukraine"

    # Отримати кілька останніх повідомлень із бази даних
    chat_hist = get_chat_history(user_id)
    messages = [{"role": "system", "content": worker}]
    for record in chat_hist:  # Отримати останні 5 повідомлень
        messages.append({"role": "user", "content": record['text']})
        messages.append({"role": "assistant", "content": record['response']})

    if len(question) > 4000:  # Перевіряємо обмеження на довжину запиту
        logger.warning(f"Too long question from user {user_id}: {question}")
        return "Ваше питання занадто довге. Спробуйте скоротити його."
    messages.append({"role": "user", "content": question})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=500,
        messages=messages
    )

    total_tokens = response.get("usage").get("total_tokens")
    logger.info(f"Start request to GPT with messages: {messages}")
    logger.info(f'Total tokens: {total_tokens}')

    return response.choices[0].message.content.strip()
