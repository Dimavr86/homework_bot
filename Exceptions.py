class TelegramApiError(Exception):
    """Ошибка при обращении к API Telegram."""


class ResponseJsonEmpty(Exception):
    """Пустой ответ от API Яндекс.Домашка."""


class ConnectionApiError(Exception):
    """Подключиться к API Яндекс не удалось."""
