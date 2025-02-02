from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from telethon import TelegramClient
from utils.telegram_utils import add_contact_to_telegram
from utils.json_utils import add_contact, load_json, is_in_blacklist
from utils.logger import logger
from config import CONTACTS_FILE, BLACKLIST_FILE, ADMINS_FILE

router = Router()

@router.message(Command("contacts"))
async def list_contacts(message: Message):
    """Показывает список добавленных контактов"""
    try:
        # Проверяем права администратора через admins.json
        admins = load_json(ADMINS_FILE)
        is_admin = False
        for group_admins in admins.values():
            if str(message.from_user.id) in group_admins:
                is_admin = True
                break
                
        if not is_admin:
            await message.reply("❌ У вас нет прав для выполнения этой команды.")
            return
            
        # Загружаем список контактов
        contacts = load_json(CONTACTS_FILE)
        
        if not contacts:
            await message.reply("📝 Список контактов пуст.")
            return
            
        # Формируем сообщение со списком контактов
        response = "📋 Список добавленных контактов:\n\n"
        for user_id, user_data in contacts.items():
            response += (
                f"👤 {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
                f"🔗 @{user_data.get('username', 'Нет username')}\n"
                f"📅 Добавлен: {user_data['added_date']}\n\n"
            )
            
        # Разбиваем сообщение на части, если оно слишком длинное
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.reply(response[x:x+4096])
        else:
            await message.reply(response)
            
    except Exception as e:
        logger.error(f"Ошибка при выводе списка контактов: {e}")
        await message.reply("❌ Произошла ошибка при получении списка контактов.")

async def process_new_contact(message: Message, user_data: dict) -> bool:
    """Обрабатывает нового пользователя"""
    try:
        user_id = user_data['id']
        
        # Проверяем черный список
        if is_in_blacklist(BLACKLIST_FILE, user_id):
            logger.info(f"Пользователь {user_id} находится в черном списке")
            return False
            
        # Проверяем, есть ли уже такой контакт
        contacts = load_json(CONTACTS_FILE)
        if str(user_id) in contacts:
            logger.info(f"Пользователь {user_id} уже добавлен в контакты")
            return False
            
        # Добавляем в контакты Telegram
        result = await add_contact_to_telegram(message.bot.client, user_data)
        if result:
            # Сохраняем в JSON
            if add_contact(CONTACTS_FILE, result):
                logger.info(f"Пользователь {user_id} успешно добавлен в контакты")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Ошибка при обработке нового контакта: {e}")
        return False 