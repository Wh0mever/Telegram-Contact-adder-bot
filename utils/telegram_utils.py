import logging
from telethon import TelegramClient
from telethon.tl.functions.contacts import AddContactRequest
from telethon.tl.types import InputUser, User
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from datetime import datetime
from typing import Dict, Any, Optional, Union
from utils.logger import logger
from config import CONTACTS_FILE
from utils.json_utils import load_json, save_json

async def add_contact_to_telegram(
    client: TelegramClient,
    user_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Добавляет пользователя в контакты Telegram
    
    Args:
        client: Экземпляр TelegramClient
        user_data: Словарь с данными пользователя
        
    Returns:
        Dict с результатом операции или None в случае ошибки
    """
    try:
        try:
            user = await client.get_entity(user_data['id'])
        except Exception:
            try:
                if user_data.get('username'):
                    user = await client.get_entity(f"@{user_data['username']}")
                else:
                    raise ValueError("Нет доступных данных для поиска пользователя")
            except Exception as e:
                logger.error(f"Не удалось найти пользователя: {e}")
                return None

        if not isinstance(user, User):
            logger.error("Найденная сущность не является пользователем")
            return None

        try:
            # Создаем InputUser для добавления контакта
            input_user = InputUser(
                user_id=user.id,
                access_hash=user.access_hash
            )

            # Добавляем контакт через AddContactRequest
            result = await client(AddContactRequest(
                id=input_user,
                first_name=user.first_name or "Unknown",
                last_name=user.last_name or "",
                phone=str(user.phone) if user.phone else ""
            ))
            
            if result:
                # Создаем запись для базы
                contacts = load_json(CONTACTS_FILE)
                user_id_str = str(user.id)
                
                contact_data = {
                    'id': user_id_str,
                    'username': user.username or '',
                    'first_name': user.first_name or "Unknown",
                    'last_name': user.last_name or '',
                    'phone': str(user.phone) if user.phone else '',
                    'group_id': user_data.get('group_id', ''),  # Сохраняем ID группы
                    'group_title': user_data.get('group_title', ''),
                    'added_date': datetime.now().strftime("%d.%m.%Y %H:%M")
                }
                
                # Сохраняем в базу
                contacts[user_id_str] = contact_data
                save_json(CONTACTS_FILE, contacts)
                logger.debug(f"Контакт {user.first_name} добавлен в базу")
                
                return contact_data
            else:
                logger.error("Не удалось добавить контакт")
                return None

        except Exception as e:
            logger.error(f"Ошибка при добавлении контакта: {e}")
            return None

    except Exception as e:
        logger.error(f"Общая ошибка при добавлении контакта: {e}")
        return None

async def get_group_info(client: TelegramClient, group_id: str) -> Optional[Dict[str, Any]]:
    """
    Получает информацию о группе
    
    Args:
        client: Экземпляр TelegramClient
        group_id: ID или username группы
        
    Returns:
        Dict с информацией о группе или None в случае ошибки
    """
    try:
        # Если это ID группы (начинается с -100)
        if group_id.startswith('-100'):
            try:
                # Преобразуем ID в int, убрав -100
                channel_id = int(group_id[4:])
                # Добавляем обратно -100 в числовом формате
                full_id = int(f"-100{channel_id}")
                entity = await client.get_entity(full_id)
            except ValueError as e:
                logger.error(f"Неверный формат ID группы {group_id}: {e}")
                return None
        else:
            # Если это username, используем как есть
            try:
                entity = await client.get_entity(group_id)
            except ValueError as e:
                logger.error(f"Не удалось найти группу по username {group_id}: {e}")
                return None
        
        if not isinstance(entity, (Channel, Chat)):
            logger.error(f"Сущность {group_id} не является группой или каналом")
            return None
            
        # Получаем количество участников
        participants_count = 0
        if isinstance(entity, Channel):
            try:
                participants = await client(GetParticipantsRequest(
                    channel=entity,
                    filter=ChannelParticipantsSearch(''),
                    offset=0,
                    limit=0,
                    hash=0
                ))
                participants_count = participants.count
            except Exception as e:
                logger.error(f"Ошибка при получении количества участников для {group_id}: {e}")
                participants_count = 0
                
        return {
            'id': str(entity.id),
            'title': entity.title,
            'username': entity.username,
            'participants_count': participants_count,
            'contacts_count': 0,
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о группе {group_id}: {e}")
        return None

async def is_admin_in_group(client: TelegramClient, group_id: str, user_id: int) -> bool:
    """
    Проверяет, является ли пользователь администратором группы
    
    Args:
        client: Экземпляр TelegramClient
        group_id: ID или username группы
        user_id: ID пользователя для проверки
        
    Returns:
        True если пользователь админ, False в противном случае
    """
    try:
        # Если это ID группы (начинается с -100)
        if group_id.startswith('-100'):
            # Преобразуем ID в int, убрав -100
            channel_id = int(group_id[4:])
            # Добавляем обратно -100 в числовом формате
            full_id = int(f"-100{channel_id}")
            entity = await client.get_entity(full_id)
        else:
            # Если это username, используем как есть
            entity = await client.get_entity(group_id)
        
        if not isinstance(entity, (Channel, Chat)):
            logger.error(f"Сущность {group_id} не является группой или каналом")
            return False
            
        # Получаем информацию о пользователе в группе
        try:
            participant = await client.get_permissions(entity, user_id)
            return participant.is_admin
        except ValueError as e:
            if "not a member" in str(e).lower():
                logger.info(f"Пользователь {user_id} не является участником группы {group_id}")
                return False
            logger.error(f"Ошибка при получении прав пользователя: {e}")
            return False
        except Exception as e:
            if "not a member" in str(e).lower() or "no user" in str(e).lower():
                logger.info(f"Пользователь {user_id} не является участником группы {group_id}")
                return False
            logger.error(f"Ошибка при получении прав пользователя: {e}")
            return False
        
    except ValueError as e:
        logger.error(f"Неверный формат ID группы: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке прав администратора: {e}")
        return False

async def get_user_info(client: TelegramClient, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает информацию о пользователе
    
    Args:
        client: Экземпляр TelegramClient
        user_id: ID пользователя
        
    Returns:
        Dict с информацией о пользователе или None в случае ошибки
    """
    try:
        user = await client.get_entity(user_id)
        
        if not isinstance(user, User):
            return None
            
        return {
            'id': str(user.id),
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone if hasattr(user, 'phone') else None,
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        return None 