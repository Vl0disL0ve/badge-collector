from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class Condition(str, enum.Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=True)
    is_admin = Column(Boolean, default=False)
    email_confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

class Set(Base):
    __tablename__ = "sets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    total_count = Column(Integer)
    photo_path = Column(String(255))

class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    set_id = Column(Integer, ForeignKey("sets.id"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    material = Column(String(100), nullable=True)
    condition = Column(Enum(Condition), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True)
    badge_id = Column(Integer, ForeignKey("badges.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    processed_path = Column(String(255), nullable=True)
    is_main = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, server_default=func.now())

class BadgeSet(Base):
    __tablename__ = "badge_sets"
    
    badge_id = Column(Integer, ForeignKey("badges.id"), primary_key=True)
    set_id = Column(Integer, ForeignKey("sets.id"), primary_key=True)
    position = Column(Integer, default=0)

class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(Text, nullable=False)
    ip_address = Column(String(45))
    created_at = Column(DateTime, server_default=func.now())

class UserVisit(Base):
    __tablename__ = "user_visits"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    visited_at = Column(DateTime, server_default=func.now())