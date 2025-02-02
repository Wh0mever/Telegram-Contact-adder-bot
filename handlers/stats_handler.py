from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from utils.json_utils import load_json, update_stats
from utils.logger import logger
from config import (
    STATS_FILE,
    GROUPS_FILE,
    CONTACTS_FILE,
    BLACKLIST_FILE,
    ADMINS_FILE
)

router = Router()

@router.message(Command("stats"))
async def show_stats(message: Message):
    """Показывает статистику"""
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
            
        # Обновляем статистику
        update_stats(STATS_FILE, GROUPS_FILE, CONTACTS_FILE, BLACKLIST_FILE)
        
        # Загружаем статистику
        stats = load_json(STATS_FILE)
        
        if not stats:
            await message.reply("📊 Статистика пуста.")
            return
            
        # Формируем сообщение
        response = (
            "📊 Статистика бота\n\n"
            f"👥 Добавлено контактов: {stats['total_contacts']}\n"
            f"👥 Групп в обработке: {stats['total_groups']}\n"
            f"⛔️ В черном списке: {stats['blacklisted']}\n\n"
            "📈 Статистика по группам:\n\n"
        )
        
        # Добавляем статистику по каждой группе
        for group in stats['groups_stats']:
            response += (
                f"📌 {group['title']}\n"
                f"🔗 @{group['username']}\n"
                f"👥 Добавлено контактов: {group['contacts_count']}\n\n"
            )
            
        response += f"\n🕒 Последнее обновление: {stats['last_update']}"
        
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Ошибка при выводе статистики: {e}")
        await message.reply("❌ Произошла ошибка при получении статистики.") 