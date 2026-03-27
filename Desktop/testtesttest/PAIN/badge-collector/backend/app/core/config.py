import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'config', '.env'))

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../badge_collector.db")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@badge-collector.com")
    
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")
    
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'uploads')

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)