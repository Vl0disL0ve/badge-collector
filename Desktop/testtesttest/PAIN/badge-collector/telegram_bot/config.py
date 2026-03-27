import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = "http://localhost:8000/api"

# Настройки прокси (если нужен)
PROXY_URL = os.getenv("PROXY_URL", None)  # Пример: socks5://127.0.0.1:1080 или http://127.0.0.1:8080

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")