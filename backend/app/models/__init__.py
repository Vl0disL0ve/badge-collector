from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, Table, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class Condition(str, enum.Enum):
    """Состояние значка"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    POOR = "poor"


# Таблица связи категорий и наборов (многие-ко-многим)
set_categories = Table(
    'set_categories',
    Base.metadata,
    Column('set_id', Integer, ForeignKey('sets.id', ondelete='CASCADE'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telegram_id = Column(Integer, unique=True, nullable=True)
    is_admin = Column(Boolean, default=False)
    email_confirmed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    sets = relationship("Set", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("Badge", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    admin_logs = relationship("AdminLog", back_populates="admin")
    visits = relationship("UserVisit", back_populates="user")


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="categories")
    sets = relationship("Set", secondary=set_categories, back_populates="categories")


class Set(Base):
    __tablename__ = "sets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    total_count = Column(Integer, default=0)
    photo_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sets")
    categories = relationship("Category", secondary=set_categories, back_populates="sets")
    badges = relationship("Badge", back_populates="set", cascade="all, delete-orphan")


class Badge(Base):
    __tablename__ = "badges"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    set_id = Column(Integer, ForeignKey("sets.id", ondelete='CASCADE'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    material = Column(String(100), nullable=True)
    condition = Column(Enum(Condition), nullable=True)
    rotation_angle = Column(Float, default=0)  # Сохраняем угол поворота для редактора
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="badges")
    set = relationship("Set", back_populates="badges")
    photos = relationship("Photo", back_populates="badge", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="badge_tags", back_populates="badges")
    feature = relationship("BadgeFeature", back_populates="badge", uselist=False, cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(Integer, primary_key=True)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete='CASCADE'), nullable=False)
    file_path = Column(String(255), nullable=False)
    processed_path = Column(String(255), nullable=True)
    is_main = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    badge = relationship("Badge", back_populates="photos")


class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), nullable=False)
    name = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tags")
    badges = relationship("Badge", secondary="badge_tags", back_populates="tags")


class BadgeTag(Base):
    __tablename__ = "badge_tags"
    
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete='CASCADE'), primary_key=True)


class BadgeFeature(Base):
    __tablename__ = "badge_features"
    
    id = Column(Integer, primary_key=True)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete='CASCADE'), nullable=False, unique=True)
    feature_vector = Column(Text, nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    badge = relationship("Badge", back_populates="feature")


class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    action = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    admin = relationship("User", back_populates="admin_logs")


class UserVisit(Base):
    __tablename__ = "user_visits"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete='SET NULL'), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    visited_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="visits")


# Экспорт всех моделей
__all__ = [
    "Base",
    "User",
    "Category",
    "Set",
    "Badge",
    "Photo",
    "Tag",
    "BadgeTag",
    "BadgeFeature",
    "AdminLog",
    "UserVisit",
    "Condition",
    "set_categories"
]