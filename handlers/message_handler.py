from aiogram import Router, F
from aiogram.types import Message
from utils.json_utils import load_json
from utils.logger import logger
from config import GROUPS_FILE, CONTACTS_FILE
from . import contacts_handler

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message):
    """Обработчик новых сообщений в группе"""
    try:
        # Проверяем, отслеживается ли группа
        groups = load_json(GROUPS_FILE)
        group_id = str(message.chat.id)
        
        if group_id not in groups:
            return
            
        # Получаем информацию о пользователе
        user = message.from_user
        if not user:
            return
            
        user_data = {
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': None  # Телефон получим при добавлении контакта
        }
        
        # Пробуем добавить пользователя в контакты
        await contacts_handler.process_new_contact(message, user_data)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения из группы: {e}") 