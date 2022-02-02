"""Telegram-бот, который отправляет сообщение о статусе домашней работы."""

import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(name)s, [%(levelname)s], %(message)s'
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as t_err:
        raise t_err


def get_api_answer(current_timestamp):
    """Делает запрос к API-сервиса. На вход получает временную метку.
    В случае успешного запроса возвращает ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, params=params, headers=HEADERS)
    except ConnectionError as error:
        logger.error(error)
        raise error
    if response.status_code != requests.codes.ok:
        response.raise_for_status()
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность.
    На вход принимает ответ API, приведенный к типам данных Python.
    Если ответ API соответствует ожиданиям, то функция возвращает
    список домашних работ, доступный в ответе API по ключу 'homeworks'.
    """
    try:
        homeworks = response["homeworks"]
        response["current_date"]
    except KeyError as k_err:
        logger.error(k_err)
        raise k_err
    if not isinstance(homeworks, list):
        raise TypeError
    if homeworks == []:
        logger.debug("Новые статусы отсутствуют")
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    На вход функция получает только один элемент из списка домашних работ.
    В случае успеха, возвращает подготовленную для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_STATUSES
    """
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        logger.error("Недокументированный статус домашней работы")
        raise Exception
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет наличие всех переменных, необходимых для работы программы.
    Возвращает False если нет хотя бы одной переменной, иначе — True.
    """
    tokens = {
        'practicum_token': PRACTICUM_TOKEN,
        'telegram_token': TELEGRAM_TOKEN,
        'telegram_chat_id': TELEGRAM_CHAT_ID,
    }
    for key, value in tokens.items():
        if value in ('', None):
            logger.critical(f'Ошибка! Отсутствует {key}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.debug('Бот запущен')
        bot = Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                for work in homeworks:
                    message = parse_status(work)
                    send_message(bot, message)
                    logger.info(f'Сообщение {message} успешно отправлено')
                current_timestamp = current_timestamp = int(
                    response['current_date']
                )
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                bot.send_message(TELEGRAM_CHAT_ID, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
