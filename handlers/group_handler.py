from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.json_utils import load_json, save_json, add_group
from utils.logger import logger
from utils.telegram_utils import get_group_info, is_admin_in_group
from config import GROUPS_FILE, ADMINS_FILE

router = Router()

@router.message(Command("add_group"))
async def add_group_command(message: Message):
    """Обработчик команды добавления группы"""
    try:
        # Получаем ID или username группы из аргументов команды
        args = message.text.split()
        if len(args) != 2:
            await message.answer(
                "❌ Неверный формат команды.\n"
                "Используйте: /add_group <ID или @username группы>"
            )
            return
            
        group_id = args[1].replace('@', '')  # Убираем @ если есть
        user_id = message.from_user.id
        
        try:
            # Получаем клиент из контекста бота
            client = message.bot.telethon_client
            if not client:
                logger.error("Telethon клиент не найден")
                await message.answer("❌ Ошибка подключения к Telegram.")
                return

            # Получаем информацию о группе
            group_info = await get_group_info(client, group_id)
            if not group_info:
                await message.answer("❌ Не удалось получить информацию о группе.")
                return
                
            # Проверяем, является ли бот администратором группы
            bot_id = (await client.get_me()).id
            if not await is_admin_in_group(client, group_id, bot_id):
                await message.answer(
                    "❌ Бот должен быть администратором группы.\n"
                    "Добавьте бота в администраторы и попробуйте снова."
                )
                return
                
            # Добавляем группу в список
            if add_group(GROUPS_FILE, group_info):
                # Добавляем пользователя как админа группы
                admins = load_json(ADMINS_FILE)
                group_id_str = str(group_info['id'])
                
                if group_id_str not in admins:
                    admins[group_id_str] = {}
                    
                admins[group_id_str][str(user_id)] = {
                    'added_date': group_info['added_date'],
                    'username': message.from_user.username,
                    'first_name': message.from_user.first_name,
                    'last_name': message.from_user.last_name
                }
                
                save_json(ADMINS_FILE, admins)
                
                # Отправляем уведомление
                await message.answer(
                    f"✅ Группа успешно добавлена!\n\n"
                    f"📌 Название: {group_info['title']}\n"
                    f"👥 Участников: {group_info['participants_count']}\n"
                    f"🔗 Username: @{group_info['username'] if group_info['username'] else 'отсутствует'}\n\n"
                    f"👤 Вы назначены администратором этой группы в боте.\n"
                    f"📩 Вам будут приходить уведомления о новых контактах."
                )
                logger.info(f"Добавлена новая группа: {group_info['title']} ({group_id}), админ: {user_id}")
            else:
                await message.answer("❌ Группа уже добавлена или произошла ошибка.")
                
        except ValueError as e:
            await message.answer(f"❌ Ошибка: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка при добавлении группы {group_id}: {e}")
            await message.answer("❌ Произошла ошибка при добавлении группы.")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке команды add_group: {e}")
        await message.answer("❌ Произошла ошибка при добавлении группы.")

@router.message(Command("groups"))
async def list_groups(message: Message):
    """Показывает список добавленных групп"""
    try:
        user_id = str(message.from_user.id)
        admins = load_json(ADMINS_FILE)
        
        # Находим группы, где пользователь является админом
        admin_groups = []
        for group_id, group_admins in admins.items():
            if user_id in group_admins:
                admin_groups.append(group_id)
                
        if not admin_groups:
            await message.reply("📝 У вас нет добавленных групп.")
            return
            
        # Загружаем список групп
        groups = load_json(GROUPS_FILE)
        
        # Формируем сообщение со списком групп
        response = "📋 Ваши группы:\n\n"
        for group_id in admin_groups:
            if group_id in groups:
                group_data = groups[group_id]
                response += (
                    f"📌 {group_data['title']}\n"
                    f"👥 Участников: {group_data['participants_count']}\n"
                    f"📊 Добавлено контактов: {group_data['contacts_count']}\n"
                    f"📅 Дата добавления: {group_data['added_date']}\n"
                    f"🔗 {f'@{group_data['username']}' if group_data['username'] else 'Нет username'}\n\n"
                )
            
        await message.reply(response)
        
    except Exception as e:
        logger.error(f"Ошибка при выводе списка групп: {e}")
        await message.reply("❌ Произошла ошибка при получении списка групп.") 