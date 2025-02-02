from aiogram import Router, F
from aiogram.types import CallbackQuery
from utils.json_utils import load_json, save_json
from utils.logger import logger
from config import GROUPS_FILE, CONTACTS_FILE, BLACKLIST_FILE, ADMINS_FILE

router = Router()

async def check_admin_rights(user_id: int) -> bool:
    """Проверяет права администратора"""
    admins = load_json(ADMINS_FILE)
    for group_admins in admins.values():
        if str(user_id) in group_admins:
            return True
    return False

@router.callback_query(F.data.startswith("delete_group_"))
async def delete_group(callback: CallbackQuery):
    """Удаляет группу из списка отслеживаемых"""
    try:
        # Проверяем права администратора
        if not await check_admin_rights(callback.from_user.id):
            await callback.answer("❌ У вас нет прав для выполнения этой команды.")
            return
            
        group_id = callback.data.replace("delete_group_", "")
        groups = load_json(GROUPS_FILE)
        
        if group_id in groups:
            group_data = groups.pop(group_id)
            if save_json(GROUPS_FILE, groups):
                await callback.answer(f"✅ Группа {group_data['title']} удалена")
                await callback.message.edit_text(
                    f"Группа {group_data['title']} удалена из списка отслеживаемых"
                )
                logger.info(f"Группа {group_id} удалена из списка отслеживаемых")
            else:
                await callback.answer("❌ Ошибка при удалении группы")
        else:
            await callback.answer("❌ Группа не найдена")
            
    except Exception as e:
        logger.error(f"Ошибка при удалении группы: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("remove_contact_"))
async def remove_contact(callback: CallbackQuery):
    """Удаляет контакт из списка"""
    try:
        # Проверяем права администратора
        if not await check_admin_rights(callback.from_user.id):
            await callback.answer("❌ У вас нет прав для выполнения этой команды.")
            return
            
        user_id = callback.data.replace("remove_contact_", "")
        contacts = load_json(CONTACTS_FILE)
        
        if user_id in contacts:
            contact_data = contacts.pop(user_id)
            if save_json(CONTACTS_FILE, contacts):
                await callback.answer(f"✅ Контакт удален")
                await callback.message.edit_text(
                    f"Контакт {contact_data.get('first_name', '')} {contact_data.get('last_name', '')} удален"
                )
                logger.info(f"Контакт {user_id} удален")
            else:
                await callback.answer("❌ Ошибка при удалении контакта")
        else:
            await callback.answer("❌ Контакт не найден")
            
    except Exception as e:
        logger.error(f"Ошибка при удалении контакта: {e}")
        await callback.answer("❌ Произошла ошибка")

@router.callback_query(F.data.startswith("remove_blacklist_"))
async def remove_from_blacklist(callback: CallbackQuery):
    """Удаляет пользователя из черного списка"""
    try:
        # Проверяем права администратора
        if not await check_admin_rights(callback.from_user.id):
            await callback.answer("❌ У вас нет прав для выполнения этой команды.")
            return
            
        user_id = callback.data.replace("remove_blacklist_", "")
        blacklist = load_json(BLACKLIST_FILE)
        
        if user_id in blacklist:
            user_data = blacklist.pop(user_id)
            if save_json(BLACKLIST_FILE, blacklist):
                await callback.answer("✅ Пользователь удален из черного списка")
                await callback.message.edit_text(
                    f"Пользователь {user_data.get('first_name', '')} {user_data.get('last_name', '')} "
                    "удален из черного списка"
                )
                logger.info(f"Пользователь {user_id} удален из черного списка")
            else:
                await callback.answer("❌ Ошибка при удалении из черного списка")
        else:
            await callback.answer("❌ Пользователь не найден в черном списке")
            
    except Exception as e:
        logger.error(f"Ошибка при удалении из черного списка: {e}")
        await callback.answer("❌ Произошла ошибка") 