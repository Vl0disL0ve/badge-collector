from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from ..models import Condition

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

class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    sets_count: int = 0

    class Config:
        from_attributes = True

class SetCreate(BaseModel):
    name: str = Field(..., max_length=150)
    description: Optional[str] = None
    total_count: int = 0
    category_id: Optional[int] = None

class SetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    total_count: int = 0
    category_id: Optional[int] = None
    user_id: int
    photo_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    collected_count: int = 0
    completion_percent: float = 0.0

    class Config:
        from_attributes = True

class BadgeCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=1000, le=9999)
    material: Optional[str] = Field(None, max_length=100)
    condition: Optional[Condition] = None
    set_id: int

class BadgeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    year: Optional[int] = Field(None, ge=1000, le=9999)
    material: Optional[str] = Field(None, max_length=100)
    condition: Optional[Condition] = None
    set_id: Optional[int] = None

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
    created_at: datetime
    updated_at: Optional[datetime] = None
    main_photo_url: Optional[str] = None
    photos: List[dict] = []
    tags: List[str] = []

    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: int
    file_path: str
    is_main: bool
    uploaded_at: datetime

class TagCreate(BaseModel):
    name: str = Field(..., max_length=50)

class TagResponse(BaseModel):
    id: int
    name: str
    user_id: int

class ExportResponse(BaseModel):
    file_url: str

class TelegramCodeResponse(BaseModel):
    code: str
    expires_in: int

class TelegramVerifyRequest(BaseModel):
    code: str
    telegram_id: int