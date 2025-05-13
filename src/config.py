import os
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Telegram Bot токен
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
if not TELEGRAM_TOKEN:
    logger.error("Не указан токен Telegram бота в переменных окружения (TELEGRAM_TOKEN)")

# VK API параметры
VK_LOGIN = os.getenv("VK_LOGIN", "")
VK_PASSWORD = os.getenv("VK_PASSWORD", "")
VK_CLIENT_SECRET = os.getenv("VK_CLIENT_SECRET", "")
VK_SERVICE_TOKEN = os.getenv("VK_SERVICE_TOKEN", "")
VK_APP_ID = os.getenv("VK_APP_ID", "")

# Админ ID (для уведомлений об ошибках)
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")

# Интервал опроса VK API в секундах (не менее 20с)
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "30"))
if POLLING_INTERVAL < 20:
    logger.warning("Интервал опроса VK API слишком маленький, установлено минимальное значение 20 секунд")
    POLLING_INTERVAL = 20

# Путь к файлу базы данных SQLite
DB_PATH = os.getenv("DB_PATH", "vk_tracker.db")

# Параметры для webhook (для использования на PythonAnywhere)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")  # Например, https://username.pythonanywhere.com
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN", "")

# Функция для преобразования Unix-времени в московское время
def format_time(unix_time):
    """Конвертирует Unix-время в строку формата HH:MM:SS по московскому времени"""
    from datetime import timezone, timedelta
    
    # Московский часовой пояс (UTC+3)
    moscow_tz = timezone(timedelta(hours=3))
    
    # Преобразование в московское время
    dt = datetime.fromtimestamp(unix_time, tz=timezone.utc).astimezone(moscow_tz)
    
    # Формат вывода: часы:минуты:секунды (по МСК)
    return dt.strftime("%H:%M:%S (МСК)")
