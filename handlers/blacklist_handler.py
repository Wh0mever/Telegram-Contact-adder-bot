from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from telethon import TelegramClient
from utils.telegram_utils import get_user_info
from utils.json_utils import load_json, save_json, add_to_blacklist
from utils.logger import logger
from config import BLACKLIST_FILE, ADMINS_FILE, CONTACTS_FILE

router = Router()

@router.message(Command("blacklist"))
async def blacklist_command(message: Message):
    """Добавляет пользователя в черный список"""
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
            
        # Получаем ID или username пользователя из аргументов команды
        args = message.text.split()
        if len(args) != 2:
            await message.reply(
                "❌ Неверный формат команды.\n"
                "Используйте: /blacklist <ID или @username пользователя>"
            )
            return
            
        user_input = args[1].strip()
        
        # Загружаем список контактов
        contacts = load_json(CONTACTS_FILE)
        
        # Ищем пользователя в контактах
        user_data = None
        user_id = None
        
        # Если передан ID
        if user_input.isdigit() or (user_input.startswith('-') and user_input[1:].isdigit()):
            user_id = str(user_input)
            if user_id in contacts:
                user_data = contacts[user_id]
        # Если передан username
        elif user_input.startswith('@'):
            username = user_input[1:]  # Убираем @
            # Ищем пользователя по username в контактах
            for contact_id, contact_data in contacts.items():
                if contact_data.get('username', '').lower() == username.lower():
                    user_data = contact_data
                    user_id = contact_id
                    break
        else:
            await message.reply(
                "❌ Неверный формат ID или username.\n"
                "ID должно быть числом, а username должен начинаться с @"
            )
            return
            
        if not user_data:
            await message.reply(
                "❌ Пользователь не найден в ваших контактах.\n"
                "Вы можете заблокировать только тех пользователей, которые есть в ваших контактах."
            )
            return
            
        # Проверяем, не в черном ли списке уже пользователь
        blacklist = load_json(BLACKLIST_FILE)
        if user_id in blacklist:
            await message.reply("❌ Этот пользователь уже находится в черном списке.")
            return
            
        # Добавляем в черный список
        if add_to_blacklist(BLACKLIST_FILE, user_data):
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            username = user_data.get('username', 'Нет username')
            
            await message.reply(
                f"✅ Пользователь добавлен в черный список:\n\n"
                f"👤 {first_name} {last_name}\n"
                f"🔗 @{username}\n"
                f"🆔 {user_id}"
            )
            logger.info(f"Пользователь {user_id} добавлен в черный список")
        else:
            await message.reply("❌ Произошла ошибка при добавлении в черный список.")
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении в черный список: {e}")
        await message.reply("❌ Произошла ошибка при добавлении в черный список.")

@router.message(Command("blacklist_list"))
async def show_blacklist(message: Message):
    """Показывает черный список"""
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
            
        # Загружаем черный список
        blacklist = load_json(BLACKLIST_FILE)
        
        if not blacklist:
            await message.reply("📝 Черный список пуст.")
            return
            
        # Формируем сообщение
        response = "⛔️ Черный список:\n\n"
        for user_id, user_data in blacklist.items():
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            username = user_data.get('username', 'Нет username')
            added_date = user_data.get('added_date', 'Дата не указана')
            
            response += (
                f"👤 {first_name} {last_name}\n"
                f"🔗 @{username}\n"
                f"🆔 {user_id}\n"
                f"📅 Добавлен: {added_date}\n\n"
            )
            
        # Разбиваем сообщение на части, если оно слишком длинное
        if len(response) > 4096:
            for x in range(0, len(response), 4096):
                await message.reply(response[x:x+4096])
        else:
            await message.reply(response)
            
    except Exception as e:
        logger.error(f"Ошибка при выводе черного списка: {e}")
        await message.reply("❌ Произошла ошибка при получении черного списка.") 