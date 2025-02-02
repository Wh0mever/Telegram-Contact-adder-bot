import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(name='TelethonBot'):
    """Настройка логгера"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Создаем обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Создаем форматтер
    formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(formatter)

    # Добавляем обработчик к логгеру
    logger.addHandler(console_handler)

    # Настраиваем логирование для всех используемых библиотек
    for lib in ['telethon', 'aiogram', 'aiohttp', 'asyncio']:
        lib_logger = logging.getLogger(lib)
        lib_logger.setLevel(logging.DEBUG)
        lib_logger.addHandler(console_handler)

    return logger

# Создаем логгер
logger = setup_logger() 