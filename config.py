# Конфигурация Telethon
API_ID = 'ваш_api_id'
API_HASH = 'ваш_api_hash'
BOT_TOKEN = 'токен_вашего_бота'

# Команды бота
BOT_COMMANDS = [
    ('start', 'Запустить бота'),
    ('add_group', 'Добавить группу для отслеживания'),
    ('groups', 'Показать список отслеживаемых групп'),
    ('contacts', 'Показать список контактов'),
    ('blacklist', 'Добавить пользователя в черный список'),
    ('blacklist_list', 'Показать черный список'),
    ('stats', 'Показать статистику'),
    ('help', 'FAQ и справка по использованию')
]

# Пути к файлам данных
DATA_DIR = 'data'
CONTACTS_FILE = f'{DATA_DIR}/contacts.json'
BLACKLIST_FILE = f'{DATA_DIR}/blacklist.json'
GROUPS_FILE = f'{DATA_DIR}/groups.json'
STATS_FILE = f'{DATA_DIR}/stats.json'
ADMINS_FILE = f'{DATA_DIR}/admins.json' 