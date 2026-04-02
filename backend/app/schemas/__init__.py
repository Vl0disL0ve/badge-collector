from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from ..models import Condition


# ========== AUTH ==========
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    telegram_id: Optional[int] = None
    is_admin: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    user: UserResponse


# ========== CATEGORIES (многие-ко-многим с наборами) ==========
class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    set_ids: Optional[List[int]] = None  # ID наборов для привязки при создании


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    set_ids: Optional[List[int]] = None  # ID наборов для привязки/отвязки


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    sets_count: int = 0
    sets: List[dict] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== SETS (многие-ко-многим с категориями) ==========
class SetCreate(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    total_count: int = 0
    category_ids: Optional[List[int]] = None  # ID категорий для привязки


class SetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=150)
    description: Optional[str] = None
    total_count: Optional[int] = None
    category_ids: Optional[List[int]] = None


class SetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    total_count: int = 0
    user_id: int
    photo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    collected_count: int = 0
    completion_percent: float = 0.0
    categories: List[dict] = []

    class Config:
        from_attributes = True


# ========== BADGES ==========
class BadgeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=1000, le=9999)
    material: Optional[str] = Field(None, max_length=100)
    condition: Optional[Condition] = None
    set_id: int
    tags: Optional[List[str]] = None


class BadgeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=1000, le=9999)
    material: Optional[str] = Field(None, max_length=100)
    condition: Optional[Condition] = None
    set_id: Optional[int] = None
    tags: Optional[List[str]] = None
    rotation_angle: Optional[float] = None


class BadgeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    year: Optional[int] = None
    material: Optional[str] = None
    condition: Optional[str] = None
    set_id: int
    set_name: Optional[str] = None
    user_id: int
    rotation_angle: float = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    main_photo_url: Optional[str] = None
    photos: List[dict] = []
    tags: List[str] = []

    class Config:
        from_attributes = True


# ========== PHOTOS ==========
class PhotoResponse(BaseModel):
    id: int
    file_path: str
    is_main: bool
    uploaded_at: datetime


# ========== TAGS ==========
class TagCreate(BaseModel):
    name: str = Field(..., max_length=50)


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=50)


class TagResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== DETECT BADGES ==========
class DetectedBadge(BaseModel):
    id: int
    name: str
    x: int
    y: int
    width: int
    height: int
    confidence: Optional[float] = None  # делаем необязательным

class DetectBadgesResponse(BaseModel):
    success: bool
    badges_count: int
    badges: List[DetectedBadge]
    message: Optional[str] = None


# ========== EXPORT ==========
class ExportResponse(BaseModel):
    file_url: str


# ========== TELEGRAM (отложено) ==========
class TelegramCodeResponse(BaseModel):
    code: str
    expires_in: int


class TelegramVerifyRequest(BaseModel):
    code: str
    telegram_id: int


# ========== IMAGE EDITOR (новый) ==========
class AxisDetectionResponse(BaseModel):
    success: bool
    angle: float
    confidence: float
    message: Optional[str] = None


class RotateCustomRequest(BaseModel):
    angle: float
    badge_id: Optional[int] = None


class RotateCustomResponse(BaseModel):
    success: bool
    image_url: str
    angle: float
    message: Optional[str] = None


class CropToBadgeResponse(BaseModel):
    success: bool
    image_url: str
    bounds: dict
    message: Optional[str] = None