from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings
from ..models import Base
import os

if settings.DATABASE_URL.startswith("sqlite:///./"):
    db_path = os.path.abspath(settings.DATABASE_URL.replace("sqlite:///./", ""))
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()