import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from config import (
    BOT_TOKEN, API_ID, API_HASH,
    GROUPS_FILE, CONTACTS_FILE, BLACKLIST_FILE,
    ADMINS_FILE, STATS_FILE, BOT_COMMANDS
)
from handlers import (
    base_handler, group_handler,
    contacts_handler, blacklist_handler,
    stats_handler, message_handler
)
from utils.json_utils import (
    init_json_files, load_json, save_json,
    update_stats
)
from utils.logger import logger
from utils.telegram_utils import add_contact_to_telegram, get_group_info, is_admin_in_group, get_user_info
from datetime import datetime

# Инициализация JSON файлов с дефолтными значениями
DEFAULT_FILES = {
    GROUPS_FILE: {},
    CONTACTS_FILE: {},
    BLACKLIST_FILE: {},
    ADMINS_FILE: {},
    STATS_FILE: {
        'total_contacts': 0,
        'total_groups': 0,
        'total_blacklisted': 0
    }
}

async def notify_admin(bot: Bot, group_id: int, user_data: dict):
    """Отправляет уведомление админу группы о новом контакте"""
    try:
        admins = load_json(ADMINS_FILE)
        group_admins = admins.get(str(group_id), {})
        
        for admin_id in group_admins:
            try:
                message = (
                    f"✅ <b>Новый контакт добавлен из группы {user_data.get('group_title', 'Неизвестная группа')}:</b>\n\n"
                    f"👤 {user_data['first_name']} {user_data.get('last_name', '')}\n"
                    f"🔗 @{user_data.get('username', 'Нет username')}\n"
                    f"📱 {user_data.get('phone', 'Нет телефона')}\n"
                    f"🆔 {user_data['id']}"
                )
                await bot.send_message(int(admin_id), message)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений админам: {e}")

async def start_client():
    """Запускает клиент Telethon и выполняет аутентификацию"""
    client = TelegramClient(
        'user_session',
        API_ID,
        API_HASH,
        system_version="4.16.30-vxCUSTOM",
        device_model="Telegram Desktop",
        app_version="4.8.1"
    )
    
    try:
        await client.connect()
        
        if not await client.is_user_authorized():
            logger.info("Сессия не найдена. Начинаем процесс авторизации...")
            
            try:
                phone = input("Пожалуйста, введите ваш номер телефона (в международном формате, например +79123456789): ")
                await client.send_code_request(phone)
                code = input("Введите код подтверждения, отправленный в Telegram: ")
                
                try:
                    await client.sign_in(phone, code)
                except SessionPasswordNeededError:
                    # Если включена двухфакторная аутентификация
                    password = input("Введите пароль двухфакторной аутентификации: ")
                    await client.sign_in(password=password)
                
                logger.info("Авторизация успешно завершена!")
                return client
                
            except Exception as e:
                logger.error(f"Ошибка при авторизации: {e}")
                return None
            
        return client
    except Exception as e:
        logger.error(f"Ошибка при запуске Telethon клиента: {e}")
        return None

async def main():
    """Основная функция запуска бота"""
    try:
        # Отключаем отладочные логи Telethon
        logging.getLogger('telethon').setLevel(logging.WARNING)
        logging.getLogger('aiohttp').setLevel(logging.WARNING)
        
        # Инициализируем JSON файлы
        init_json_files(DEFAULT_FILES)
        
        # Запускаем клиент Telethon
        client = await start_client()
        if not client:
            logger.error("Не удалось запустить Telethon клиент. Убедитесь, что вы правильно ввели данные авторизации.")
            return
            
        logger.info("Telethon клиент успешно запущен")
        
        # Инициализируем бота
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Добавляем клиент Telethon к боту для доступа из хэндлеров
        bot.telethon_client = client
        
        # Устанавливаем команды бота
        commands = [
            BotCommand(command=command, description=desc)
            for command, desc in BOT_COMMANDS
        ]
        await bot.set_my_commands(commands)
        
        # Инициализируем диспетчер
        dp = Dispatcher()
        
        # Регистрируем все хэндлеры
        dp.include_router(base_handler.router)
        dp.include_router(group_handler.router)
        dp.include_router(contacts_handler.router)
        dp.include_router(blacklist_handler.router)
        dp.include_router(stats_handler.router)
        dp.include_router(message_handler.router)
        
        # Добавляем обработчик новых сообщений в Telethon
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                if not event.is_group:
                    return
                    
                # Получаем информацию о группе и отправителе
                group = await event.get_chat()
                sender = await event.get_sender()
                
                # Проверяем, отслеживается ли группа
                groups = load_json(GROUPS_FILE)
                if str(group.id) not in groups:
                    return
                    
                # Получаем данные пользователя
                user_data = {
                    'id': sender.id,
                    'username': sender.username,
                    'first_name': sender.first_name,
                    'last_name': getattr(sender, 'last_name', ''),
                    'phone': getattr(sender, 'phone', ''),
                    'group_id': str(group.id),
                    'group_title': group.title
                }
                
                # Пробуем добавить контакт
                try:
                    # Сначала проверяем, есть ли пользователь уже в базе
                    contacts = load_json(CONTACTS_FILE)
                    user_id_str = str(user_data['id'])
                    
                    if user_id_str in contacts:
                        logger.info(f"Контакт {user_data['first_name']} уже есть в базе")
                        return
                    
                    # Если контакта нет в базе, пробуем добавить
                    contact_result = await add_contact_to_telegram(client, user_data)
                    if contact_result:
                        # Уведомляем админа только для новых контактов
                        await notify_admin(bot, group.id, user_data)
                        logger.info(f"Добавлен новый контакт: {user_data['first_name']} из группы {group.title}")
                        # Обновляем статистику после добавления контакта
                        update_stats(STATS_FILE, GROUPS_FILE, CONTACTS_FILE, BLACKLIST_FILE)
                except Exception as e:
                    logger.error(f"Ошибка при добавлении контакта: {e}")
            
            except Exception as e:
                logger.error(f"Ошибка при обработке нового сообщения: {e}")
        
        # Запускаем бота
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        # Закрываем клиент Telethon при выходе
        if 'client' in locals():
            await client.disconnect()
            
if __name__ == "__main__":
    asyncio.run(main())
