from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from telethon import TelegramClient
from utils.json_utils import add_group, load_json
from utils.logger import logger
from config import GROUPS_FILE, ADMIN_ID

router = Router()

@router.message(Command("add_group"))
async def add_group_command(message: Message, client: TelegramClient):
    """Добавляет группу для отслеживания"""
    try:
        # Проверяем права администратора
        if message.from_user.id != ADMIN_ID:
            await message.reply("❌ У вас нет прав для выполнения этой команды.")
            return
            
        # Получаем ID или username группы из аргументов команды
        args = message.text.split()
        if len(args) != 2:
            await message.reply(
                "❌ Неверный формат команды.\n"
                "Используйте: /add_group <ID | @username>"
            )
            return
            
        group_id = args[1]
        
        try:
            # Получаем информацию о группе
            group = await client.get_entity(group_id)
            group_data = {
                'id': group.id,
                'username': group.username,
                'title': group.title,
                'members_count': (await client.get_participants(group, limit=0)).total
            }
            
            # Добавляем группу
            if add_group(GROUPS_FILE, group_data):
                await message.reply(
                    f"✅ Группа добавлена для отслеживания:\n\n"
                    f"📌 {group_data['title']}\n"
                    f"🔗 @{group_data['username']}\n"
                    f"👥 Участников: {group_data['members_count']}"
                )
                logger.info(f"Группа {group_id} добавлена для отслеживания")
            else:
                await message.reply("❌ Группа уже отслеживается или произошла ошибка.")
                
        except Exception as e:
            await message.reply("❌ Не удалось найти группу или получить информацию о ней.")
            logger.error(f"Ошибка при поиске группы {group_id}: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при добавлении группы: {e}")
        await message.reply("❌ Произошла ошибка при добавлении группы.")

@router.message(Command("groups_list"))
async def show_groups(message: Message):
    """Показывает список отслеживаемых групп"""
    try:
        # Проверяем права администратора
        if message.from_user.id != ADMIN_ID:
            await message.reply("❌ У вас нет прав для выполнения этой команды.")
            return
            
        # Загружаем список групп
        groups = load_json(GROUPS_FILE)
        
        if not groups:
            await message.reply("📝 Список групп пуст.")
            return
            
        # Формируем сообщение
        response = "📋 Отслеживаемые группы:\n\n"
        for group_id, group_data in groups.items():
            response += (
                f"📌 {group_data['title']}\n"
                f"🔗 @{group_data['username']}\n"
                f"👥 Участников: {group_data['members_count']}\n"
                f"📅 Добавлена: {group_data['added_date']}\n\n"
            )
            
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Ошибка при выводе списка групп: {e}")
        await message.reply("❌ Произошла ошибка при получении списка групп.") 