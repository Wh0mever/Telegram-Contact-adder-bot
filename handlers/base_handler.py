from functools import wraps
from aiogram import Router, F, Bot
from aiogram.types import Message, BotCommand, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.json_utils import load_json
from utils.logger import logger
from config import BOT_COMMANDS, ADMINS_FILE
from . import contacts_handler, group_handler, blacklist_handler, stats_handler

router = Router()

def private_messages_only(func):
    """Декоратор для обработки команд только в личных сообщениях"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if message.chat.type != "private":
            return
        return await func(message, *args, **kwargs)
    return wrapper

class AddGroupStates(StatesGroup):
    """Состояния для добавления группы"""
    waiting_for_username = State()
    waiting_for_id = State()

class BlacklistStates(StatesGroup):
    """Состояния для добавления в черный список"""
    waiting_for_user = State()

async def setup_bot_commands(bot: Bot):
    """Установка команд бота"""
    try:
        commands = [BotCommand(command=command, description=desc) for command, desc in BOT_COMMANDS]
        await bot.set_my_commands(commands)
        logger.info("Команды бота успешно установлены")
    except Exception as e:
        logger.error(f"Ошибка при установке команд бота: {e}")

def get_keyboard():
    """Создает клавиатуру с основными командами"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📱 Контакты"),
                KeyboardButton(text="👥 Группы")
            ],
            [
                KeyboardButton(text="⛔️ Черный список"),
                KeyboardButton(text="📊 Статистика")
            ],
            [
                KeyboardButton(text="➕ Группа по @username"),
                KeyboardButton(text="➕ Группа по ID")
            ],
            [
                KeyboardButton(text="❌ Заблокировать"),
                KeyboardButton(text="❓ FAQ")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    )
    return keyboard

@router.message(Command("start"))
@private_messages_only
async def start_command(message: Message):
    """Обработчик команды /start"""
    try:
        welcome_text = (
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            "🤖 Я бот для отслеживания контактов в Telegram группах.\n\n"
            "📌 <b>Основные команды:</b>\n"
            "/add_group - Добавить группу для отслеживания\n"
            "/groups - Показать список отслеживаемых групп\n"
            "/contacts - Показать список собранных контактов\n"
            "/blacklist - Добавить пользователя в черный список\n"
            "/blacklist_list - Показать черный список\n"
            "/stats - Показать статистику\n"
            "/help - Показать FAQ и справку\n\n"
            "🔍 Выберите команду с помощью кнопок ниже или введите ее вручную."
        )
        
        await message.reply(
            welcome_text,
            reply_markup=get_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await message.reply("❌ Произошла ошибка при запуске бота.")

@router.message(Command("help"))
@router.message(F.text == "❓ FAQ")
@private_messages_only
async def help_command(message: Message):
    """Обработчик команды /help и кнопки FAQ"""
    try:
        faq_text = (
            "📚 <b>FAQ и Руководство пользователя</b>\n\n"
            "🤔 <b>Как использовать бота?</b>\n"
            "1. Добавьте бота в вашу группу\n"
            "2. Назначьте бота администратором\n"
            "3. Используйте кнопки '➕ Группа по @username' или '➕ Группа по ID'\n\n"
            
            "📝 <b>Основные функции:</b>\n"
            "• Автоматический сбор контактов из групп\n"
            "• Черный список для нежелательных пользователей\n"
            "• Статистика по группам и контактам\n"
            "• Управление несколькими группами\n\n"
            
            "❗️ <b>Важные моменты:</b>\n"
            "• Бот должен быть администратором группы\n"
            "• Пользователь, добавивший группу, становится её админом в боте\n"
            "• Контакты автоматически добавляются при активности в группе\n\n"
            
            "🛠 <b>Команды администратора:</b>\n"
            "• /add_group - Добавить новую группу\n"
            "• /blacklist - Заблокировать пользователя\n"
            "• /stats - Просмотр статистики\n\n"
            
            "📞 <b>Контакты и поддержка:</b>\n"
            "• Telegram: @ctrltg\n"
            "• Веб-сайт: whomever.tech\n\n"
            
            "🔄 <b>Обновления:</b>\n"
            "• Следите за обновлениями бота\n"
            "• Новые функции добавляются регулярно"
        )
        
        await message.reply(faq_text)
        
    except Exception as e:
        logger.error(f"Ошибка в команде /help: {e}")
        await message.reply("❌ Произошла ошибка при отображении справки.")

@router.message(F.text == "📱 Контакты")
@private_messages_only
async def contacts_button(message: Message):
    """Обработчик кнопки Контакты"""
    await contacts_handler.list_contacts(message)

@router.message(F.text == "👥 Группы")
@private_messages_only
async def groups_button(message: Message):
    """Обработчик кнопки Группы"""
    await group_handler.list_groups(message)

@router.message(F.text == "⛔️ Черный список")
@private_messages_only
async def blacklist_button(message: Message):
    """Обработчик кнопки Черный список"""
    await blacklist_handler.show_blacklist(message)

@router.message(F.text == "📊 Статистика")
@private_messages_only
async def stats_button(message: Message):
    """Обработчик кнопки Статистика"""
    await stats_handler.show_stats(message)

@router.message(Command("add_group"))
@router.message(F.text == "➕ Группа по @username")
@private_messages_only
async def add_group_by_username_button(message: Message, state: FSMContext):
    """Обработчик кнопки добавления группы по username"""
    await state.set_state(AddGroupStates.waiting_for_username)
    await message.reply(
        "Отправьте @username группы, которую хотите отслеживать.\n"
        "Например: @groupname\n\n"
        "❗️ Убедитесь, что бот добавлен в группу и назначен администратором."
    )

@router.message(F.text == "➕ Группа по ID")
@private_messages_only
async def add_group_by_id_button(message: Message, state: FSMContext):
    """Обработчик кнопки добавления группы по ID"""
    await state.set_state(AddGroupStates.waiting_for_id)
    await message.reply(
        "Отправьте ID группы, которую хотите отслеживать.\n"
        "ID должно начинаться с -100, например: -100123456789\n\n"
        "❗️ Убедитесь, что бот добавлен в группу и назначен администратором."
    )

@router.message(AddGroupStates.waiting_for_username)
@private_messages_only
async def process_group_username(message: Message, state: FSMContext):
    """Обработчик ввода username группы"""
    await state.clear()
    username = message.text.strip()
    if not username.startswith('@'):
        username = f"@{username}"
    
    # Создаем команду и отправляем ее через тот же бот
    command_text = f"/add_group {username}"
    await group_handler.add_group_command(message.model_copy(update={'text': command_text}))

@router.message(AddGroupStates.waiting_for_id)
@private_messages_only
async def process_group_id(message: Message, state: FSMContext):
    """Обработчик ввода ID группы"""
    await state.clear()
    try:
        group_id = message.text.strip()
        if not group_id.startswith('-100'):
            await message.reply(
                "❌ Неверный формат ID группы.\n"
                "ID должно начинаться с -100, например: -100123456789"
            )
            return
            
        # Проверяем, что оставшаяся часть - число
        int(group_id[4:])
        
        # Создаем команду и отправляем ее через тот же бот
        command_text = f"/add_group {group_id}"
        await group_handler.add_group_command(message.model_copy(update={'text': command_text}))
        
    except ValueError:
        await message.reply(
            "❌ Неверный формат ID группы.\n"
            "ID должно начинаться с -100, например: -100123456789"
        )

@router.message(F.text == "❌ Заблокировать")
@private_messages_only
async def blacklist_add_button(message: Message, state: FSMContext):
    """Обработчик кнопки Заблокировать"""
    # Проверяем права администратора
    admins = load_json(ADMINS_FILE)
    is_admin = False
    for group_admins in admins.values():
        if str(message.from_user.id) in group_admins:
            is_admin = True
            break
            
    if not is_admin:
        await message.reply("❌ У вас нет прав для выполнения этой команды.")
        return

    await state.set_state(BlacklistStates.waiting_for_user)
    await message.reply(
        "Отправьте ID или @username пользователя, которого хотите заблокировать.\n\n"
        "Например:\n"
        "• 123456789\n"
        "• @username\n\n"
        "❗️ Вы можете заблокировать только тех пользователей, которые есть в ваших контактах."
    )

@router.message(BlacklistStates.waiting_for_user)
@private_messages_only
async def process_blacklist_user(message: Message, state: FSMContext):
    """Обработчик ввода пользователя для черного списка"""
    await state.clear()
    
    # Создаем команду и отправляем ее через тот же бот
    command_text = f"/blacklist {message.text.strip()}"
    await blacklist_handler.blacklist_command(message.model_copy(update={'text': command_text}))

# Обработчики текстовых кнопок
@router.message(F.text == "📊 Статистика")
async def button_stats(message: Message):
    """Обработчик кнопки статистики"""
    await message.answer("Выполняю команду /stats")
    await message.bot.send_message(message.chat.id, "/stats")

@router.message(F.text == "👥 Контакты")
async def button_contacts(message: Message):
    """Обработчик кнопки контактов"""
    await message.answer("Выполняю команду /contacts")
    await message.bot.send_message(message.chat.id, "/contacts")

@router.message(F.text == "⛔️ Черный список")
async def button_blacklist(message: Message):
    """Обработчик кнопки черного списка"""
    await message.answer("Выполняю команду /blacklist_list")
    await message.bot.send_message(message.chat.id, "/blacklist_list")

@router.message(F.text == "📋 Группы")
async def button_groups(message: Message):
    """Обработчик кнопки групп"""
    await message.answer("Выполняю команду /groups")
    await message.bot.send_message(message.chat.id, "/groups")

@router.message(F.text == "➕ Добавить группу")
async def button_add_group(message: Message):
    """Обработчик кнопки добавления группы"""
    await message.answer("Выполняю команду /add_group")
    await message.bot.send_message(message.chat.id, "/add_group") 