import json
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from utils.logger import logger
from config import BLACKLIST_FILE

def init_json_files(default_files: Dict[str, Any]) -> None:
    """Инициализирует JSON файлы с дефолтными значениями"""
    for file_path, default_data in default_files.items():
        path = Path(file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=4)
            logger.info(f"Создан файл {file_path} с дефолтными значениями")

def load_json(file_path: str) -> Dict[str, Any]:
    """Загружает данные из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Ошибка при чтении файла {file_path}")
        return {}

def save_json(file_path: str, data: Dict[str, Any]) -> bool:
    """Сохраняет данные в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {file_path}: {e}")
        return False

def add_contact(file_path: str, user_data: Dict[str, Any]) -> bool:
    """Добавляет новый контакт в JSON файл"""
    contacts = load_json(file_path)
    user_id = str(user_data['id'])
    
    if user_id not in contacts:
        contacts[user_id] = {
            **user_data,
            'added_date': datetime.now().isoformat()
        }
        return save_json(file_path, contacts)
    return False

def add_to_blacklist(file_path: str, user_data: Dict[str, Any]) -> bool:
    """Добавляет пользователя в черный список"""
    blacklist = load_json(file_path)
    user_id = str(user_data['id'])
    
    if user_id not in blacklist:
        blacklist[user_id] = {
            **user_data,
            'added_date': datetime.now().isoformat()
        }
        return save_json(file_path, blacklist)
    return False

def is_in_blacklist(file_path: str, user_id: int) -> bool:
    """Проверяет, находится ли пользователь в черном списке"""
    blacklist = load_json(file_path)
    return str(user_id) in blacklist

def add_group(file_path: str, group_data: Dict[str, Any]) -> bool:
    """Добавляет новую группу в JSON файл"""
    groups = load_json(file_path)
    group_id = str(group_data['id'])
    
    if group_id not in groups:
        groups[group_id] = {
            **group_data,
            'added_date': datetime.now().isoformat(),
            'contacts_count': 0
        }
        return save_json(file_path, groups)
    return False

def update_stats(stats_file: str, groups_file: str, contacts_file: str, blacklist_file: str):
    """Обновляет статистику"""
    try:
        groups = load_json(groups_file)
        contacts = load_json(contacts_file)
        blacklist = load_json(blacklist_file)
        
        # Подсчитываем контакты по группам
        group_contacts = {}
        for group_id in groups:
            group_contacts[group_id] = 0
            
        # Считаем контакты для каждой группы
        for contact in contacts.values():
            if 'group_id' in contact:
                group_id = str(contact['group_id'])
                if group_id in group_contacts:
                    group_contacts[group_id] += 1
        
        # Обновляем статистику групп
        for group_id, count in group_contacts.items():
            if group_id in groups:
                groups[group_id]['contacts_count'] = count
        
        # Сохраняем обновленные данные групп
        save_json(groups_file, groups)
                
        stats = {
            'total_contacts': len(contacts),
            'total_groups': len(groups),
            'blacklisted': len(blacklist),
            'groups_stats': [
                {
                    'id': group_id,
                    'title': group_data['title'],
                    'username': group_data.get('username', ''),
                    'contacts_count': group_data.get('contacts_count', 0)
                }
                for group_id, group_data in groups.items()
            ],
            'last_update': datetime.now().strftime("%d.%m.%Y %H:%M")
        }
        
        save_json(stats_file, stats)
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении статистики: {e}")
        return False 