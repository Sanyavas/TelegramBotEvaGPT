import json
import os
import re
from datetime import datetime
import requests
import logging

from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

from mongo_db import DB_MONGO_ENEMY

logging.basicConfig(level=logging.INFO)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
base_url = "https://index.minfin.com.ua/ua/russian-invading/casualties"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/90.0.4430.93 Safari/537.36'
}
URL_PREFIX = '/month.php?month='

TIME_NOW = datetime.now().strftime('%d-%m-%Y %H:%M:%S')


def get_urls():
    try:
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.select('div[class=ajaxmonth] h4[class=normal] a')
        urls = ['/']
        for a in content:
            url = URL_PREFIX + re.search(r'\d{4}-\d{2}', a['href']).group()
            urls.append(url)
        return urls
    except requests.RequestException as e:
        logger.error(f"Помилка при отриманні URL {base_url}: {e}")
        return []


def spider(urls):
    data = []
    for url in urls:
        try:
            response = requests.get(base_url + url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.select('ul[class=see-also] li[class=gold]')
            for el in content:
                result = {}
                date = el.find('span', attrs={"class": "black"}).text
                if "Див. також" in date:
                    continue
                try:
                    date = datetime.strptime(date, "%d.%m.%Y").isoformat()
                    date = date[:10]
                except ValueError as err:
                    logger.error(f'Error for date: {date} {err}')
                    continue
                result.update({'date': date})
                losses = el.find('div').find('div').find('ul')
                for loss in losses:
                    name, quantity, *_ = loss.text.split('—')
                    name = name.strip()
                    quantity = int(re.search(r'\d+', quantity).group())
                    result[name] = quantity
                data.append(result)
        except requests.RequestException as e:
            logger.error(f"Помилка при отриманні URL {url}: {e}")
    return data


def main_enemy():
    try:
        urls_for_scraping = get_urls()
        scraped_data = spider(urls_for_scraping)
        logger.info(f"Enemy Loses updated json for {scraped_data[0]['date']}. Date start function: {TIME_NOW}")

        DB_MONGO_ENEMY.delete_many({})
        DB_MONGO_ENEMY.insert_many(scraped_data)
        logger.info(f"Втрати ворога додані до MongoDB")
        # with open('enemy_losses.json', 'w', encoding='utf-8') as fd:
        #     json.dump(scraped_data, fd, ensure_ascii=False, indent=4)
    except Exception as ex:
        logger.error(f"Помилка при додаванні втрат ворога: {ex}")


def scheduler_enemy():
    #  Використовується APScheduler для запуску задачі (функції) main_enemy кожні 540 хвилин
    scheduler = BackgroundScheduler()
    scheduler.add_job(main_enemy, 'interval', minutes=540)
    scheduler.start()
    logger.info(f"Scheduler started... {TIME_NOW}")


if __name__ == '__main__':
    scheduler_enemy()
    # main_enemy()
