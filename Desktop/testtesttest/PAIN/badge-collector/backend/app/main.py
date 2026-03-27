from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import os
import shutil
import uuid
from PIL import Image
from typing import List, Optional
import json

from .core import config, database, security
from .models import (
    User, Category, Set, Badge, Photo, Tag, BadgeTag, 
    AdminLog, UserVisit, Condition
)
from .schemas import (
    UserRegister, UserLogin, UserResponse, Token, TokenWithUser,
    CategoryCreate, CategoryResponse,
    SetCreate, SetResponse,
    BadgeCreate, BadgeUpdate, BadgeResponse,
    PhotoResponse, TagCreate, TagResponse,
    ExportResponse, TelegramCodeResponse, TelegramVerifyRequest
)
from .services.ml import auto_rotate, rotate_image, remove_background, process_image

app = FastAPI(title="Badge Collector API", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы (загрузки)
os.makedirs(config.settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=config.settings.UPLOAD_DIR), name="uploads")

# Статические файлы фронтенда
FRONTEND_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend")
app.mount("/html", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html")), name="html")
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_PATH, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_PATH, "js")), name="js")

# Временное хранилище для кодов привязки Telegram
telegram_codes = {}


# ========== AUTH ==========

@app.post("/api/register", response_model=TokenWithUser)
def register(user_data: UserRegister, db: Session = Depends(database.get_db)):
    if len(user_data.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = User(
        email=user_data.email,
        password_hash=security.get_password_hash(user_data.password),
        email_confirmed_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = security.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@app.post("/api/login", response_model=TokenWithUser)
def login(user_data: UserLogin, db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not security.verify_password(user_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    token = security.create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user)
    }


@app.get("/api/me", response_model=UserResponse)
def get_me(current_user: User = Depends(security.get_current_user)):
    return current_user


# ========== TELEGRAM ==========

@app.post("/api/telegram/generate-code", response_model=TelegramCodeResponse)
def generate_telegram_code(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    code = secrets.randbelow(1000000)
    code_str = f"{code:06d}"
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    telegram_codes[code_str] = (current_user.id, expires_at)
    
    for key, (_, exp) in list(telegram_codes.items()):
        if exp < datetime.utcnow():
            del telegram_codes[key]
    
    return {"code": code_str, "expires_in": 900}


@app.post("/api/telegram/verify-code")
def verify_telegram_code(
    request: TelegramVerifyRequest,
    db: Session = Depends(database.get_db)
):
    if request.code not in telegram_codes:
        raise HTTPException(400, "Invalid or expired code")
    
    user_id, expires_at = telegram_codes[request.code]
    if expires_at < datetime.utcnow():
        del telegram_codes[request.code]
        raise HTTPException(400, "Code expired")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    existing = db.query(User).filter(User.telegram_id == request.telegram_id).first()
    if existing and existing.id != user.id:
        raise HTTPException(400, "Telegram account already linked to another user")
    
    user.telegram_id = request.telegram_id
    db.commit()
    del telegram_codes[request.code]
    return {"message": "Telegram account linked successfully"}


# ========== CATEGORIES ==========

@app.post("/api/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = Category(
        user_id=current_user.id,
        name=data.name,
        description=data.description
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@app.get("/api/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    categories = db.query(Category).filter(Category.user_id == current_user.id).all()
    result = []
    for cat in categories:
        sets_count = db.query(Set).filter(Set.category_id == cat.id).count()
        result.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            user_id=cat.user_id,
            sets_count=sets_count
        ))
    return result


@app.delete("/api/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.user_id == current_user.id
    ).first()
    if not category:
        raise HTTPException(404, "Category not found")
    
    sets_count = db.query(Set).filter(Set.category_id == category_id).count()
    if sets_count > 0:
        raise HTTPException(400, "Cannot delete category with sets")
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


# ========== SETS ==========

@app.post("/api/sets", response_model=SetResponse)
def create_set(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    total_count: int = Form(0),
    category_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if category_id:
        category = db.query(Category).filter(
            Category.id == category_id,
            Category.user_id == current_user.id
        ).first()
        if not category:
            raise HTTPException(400, "Category not found")
    
    photo_path = None
    if photo:
        if photo.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(400, "Only JPEG/PNG allowed")
        
        ext = photo.filename.split(".")[-1]
        filename = f"set_{uuid.uuid4()}.{ext}"
        filepath = os.path.join(config.settings.UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        
        try:
            with Image.open(filepath) as img:
                if os.path.getsize(filepath) > 10 * 1024 * 1024:
                    os.remove(filepath)
                    raise HTTPException(400, "Image must be ≤10MB")
            photo_path = filepath
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(400, f"Invalid image: {e}")
    
    new_set = Set(
        user_id=current_user.id,
        category_id=category_id,
        name=name,
        description=description,
        total_count=total_count,
        photo_path=photo_path
    )
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    
    collected = db.query(Badge).filter(Badge.set_id == new_set.id).count()
    
    return SetResponse(
        id=new_set.id,
        name=new_set.name,
        description=new_set.description,
        total_count=new_set.total_count,
        category_id=new_set.category_id,
        user_id=new_set.user_id,
        photo_path=new_set.photo_path,
        created_at=new_set.created_at,
        updated_at=new_set.updated_at,
        collected_count=collected,
        completion_percent=(collected / new_set.total_count * 100) if new_set.total_count > 0 else 0
    )


@app.get("/api/sets", response_model=List[SetResponse])
def get_sets(
    category_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(Set).filter(Set.user_id == current_user.id)
    if category_id:
        query = query.filter(Set.category_id == category_id)
    
    sets = query.all()
    result = []
    for s in sets:
        collected = db.query(Badge).filter(Badge.set_id == s.id).count()
        result.append(SetResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            total_count=s.total_count,
            category_id=s.category_id,
            user_id=s.user_id,
            photo_path=s.photo_path,
            created_at=s.created_at,
            updated_at=s.updated_at,
            collected_count=collected,
            completion_percent=(collected / s.total_count * 100) if s.total_count > 0 else 0
        ))
    return result


@app.delete("/api/sets/{set_id}")
def delete_set(
    set_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    set_item = db.query(Set).filter(
        Set.id == set_id,
        Set.user_id == current_user.id
    ).first()
    if not set_item:
        raise HTTPException(404, "Set not found")
    
    badges = db.query(Badge).filter(Badge.set_id == set_id).all()
    for badge in badges:
        photos = db.query(Photo).filter(Photo.badge_id == badge.id).all()
        for p in photos:
            if os.path.exists(p.file_path):
                os.remove(p.file_path)
            db.delete(p)
        db.delete(badge)
    
    if set_item.photo_path and os.path.exists(set_item.photo_path):
        os.remove(set_item.photo_path)
    
    db.delete(set_item)
    db.commit()
    return {"message": "Set deleted"}


# ========== BADGES ==========

@app.post("/api/badges", response_model=BadgeResponse)
def create_badge(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    material: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    set_id: int = Form(...),
    tags: Optional[str] = Form(None),
    photos: List[UploadFile] = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    set_item = db.query(Set).filter(
        Set.id == set_id,
        Set.user_id == current_user.id
    ).first()
    if not set_item:
        raise HTTPException(400, "Set not found")
    
    if not photos or len(photos) == 0:
        raise HTTPException(400, "At least one photo is required")
    if len(photos) > 5:
        raise HTTPException(400, "Maximum 5 photos per badge")
    
    condition_enum = None
    if condition and condition in ["excellent", "good", "average", "poor"]:
        condition_enum = Condition(condition)
    
    badge = Badge(
        user_id=current_user.id,
        set_id=set_id,
        name=name,
        description=description,
        year=year if year and year > 0 else None,
        material=material,
        condition=condition_enum
    )
    db.add(badge)
    db.flush()
    
    saved_photos = []
    for i, photo in enumerate(photos):
        if photo.content_type not in ["image/jpeg", "image/png"]:
            db.rollback()
            raise HTTPException(400, f"Photo {i+1}: Only JPEG/PNG allowed")
        
        ext = photo.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        filepath = os.path.join(config.settings.UPLOAD_DIR, filename)
        
        try:
            with open(filepath, "wb") as f:
                shutil.copyfileobj(photo.file, f)
        except Exception as e:
            db.rollback()
            raise HTTPException(400, f"Photo {i+1}: Failed to save - {e}")
        
        try:
            img = Image.open(filepath)
            width, height = img.size
            img.close()
            
            if width < 500 or height < 500:
                os.remove(filepath)
                db.rollback()
                raise HTTPException(400, f"Photo {i+1}: Image must be at least 500x500px")
            
            file_size = os.path.getsize(filepath)
            if file_size > 10 * 1024 * 1024:
                os.remove(filepath)
                db.rollback()
                raise HTTPException(400, f"Photo {i+1}: Image must be ≤10MB")
                
        except HTTPException:
            raise
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            db.rollback()
            raise HTTPException(400, f"Photo {i+1}: Invalid image - {str(e)}")
        
        photo_record = Photo(
            badge_id=badge.id,
            file_path=filepath,
            is_main=(i == 0)
        )
        db.add(photo_record)
        saved_photos.append(photo_record)
    
    tag_names = []
    if tags:
        try:
            tag_names = json.loads(tags)
        except:
            tag_names = [t.strip() for t in tags.split(",") if t.strip()]
    
    for tag_name in tag_names[:10]:
        existing_tag = db.query(Tag).filter(
            Tag.user_id == current_user.id,
            Tag.name == tag_name.lower()
        ).first()
        if not existing_tag:
            existing_tag = Tag(user_id=current_user.id, name=tag_name.lower())
            db.add(existing_tag)
            db.flush()
        
        badge_tag = BadgeTag(badge_id=badge.id, tag_id=existing_tag.id)
        db.add(badge_tag)
    
    db.commit()
    db.refresh(badge)
    
    return BadgeResponse(
        id=badge.id,
        name=badge.name,
        description=badge.description,
        year=badge.year,
        material=badge.material,
        condition=badge.condition.value if badge.condition else None,
        set_id=badge.set_id,
        user_id=badge.user_id,
        created_at=badge.created_at,
        updated_at=badge.updated_at,
        main_photo_url=f"/uploads/{os.path.basename(saved_photos[0].file_path)}" if saved_photos else None,
        photos=[{"id": p.id, "file_path": f"/uploads/{os.path.basename(p.file_path)}", "is_main": p.is_main} for p in saved_photos],
        tags=tag_names
    )


@app.get("/api/badges", response_model=dict)
def get_badges(
    search: Optional[str] = "",
    set_id: Optional[int] = None,
    condition: Optional[str] = None,
    tag_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(Badge).filter(Badge.user_id == current_user.id)
    
    if search:
        query = query.filter(Badge.name.ilike(f"%{search}%"))
    if set_id:
        query = query.filter(Badge.set_id == set_id)
    if condition:
        query = query.filter(Badge.condition == condition)
    if tag_id:
        query = query.join(BadgeTag).filter(BadgeTag.tag_id == tag_id)
    
    total = query.count()
    badges = query.order_by(Badge.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for b in badges:
        main_photo = db.query(Photo).filter(Photo.badge_id == b.id, Photo.is_main == True).first()
        tags = db.query(Tag).join(BadgeTag).filter(BadgeTag.badge_id == b.id).all()
        set_item = db.query(Set).filter(Set.id == b.set_id).first()
        
        result.append({
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "year": b.year,
            "material": b.material,
            "condition": b.condition.value if b.condition else None,
            "set_id": b.set_id,
            "set_name": set_item.name if set_item else None,
            "main_photo_url": f"/uploads/{os.path.basename(main_photo.file_path)}" if main_photo else None,
            "tags": [t.name for t in tags],
            "created_at": b.created_at
        })
    
    return {
        "total": total,
        "items": result,
        "limit": limit,
        "offset": offset
    }


@app.get("/api/badges/{badge_id}", response_model=BadgeResponse)
def get_badge(
    badge_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photos = db.query(Photo).filter(Photo.badge_id == badge_id).all()
    main_photo = next((p for p in photos if p.is_main), photos[0] if photos else None)
    tags = db.query(Tag).join(BadgeTag).filter(BadgeTag.badge_id == badge_id).all()
    set_item = db.query(Set).filter(Set.id == badge.set_id).first()
    
    return BadgeResponse(
        id=badge.id,
        name=badge.name,
        description=badge.description,
        year=badge.year,
        material=badge.material,
        condition=badge.condition.value if badge.condition else None,
        set_id=badge.set_id,
        set_name=set_item.name if set_item else None,
        user_id=badge.user_id,
        created_at=badge.created_at,
        updated_at=badge.updated_at,
        main_photo_url=f"/uploads/{os.path.basename(main_photo.file_path)}" if main_photo else None,
        photos=[{"id": p.id, "file_path": f"/uploads/{os.path.basename(p.file_path)}", "is_main": p.is_main} for p in photos],
        tags=[t.name for t in tags]
    )


@app.put("/api/badges/{badge_id}")
def update_badge(
    badge_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    material: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    set_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    if name:
        badge.name = name
    if description is not None:
        badge.description = description
    if year:
        badge.year = year
    if material is not None:
        badge.material = material
    if condition and condition in ["excellent", "good", "average", "poor"]:
        badge.condition = Condition(condition)
    if set_id is not None:
        if set_id == 0:
            badge.set_id = None
        else:
            set_item = db.query(Set).filter(
                Set.id == set_id,
                Set.user_id == current_user.id
            ).first()
            if not set_item:
                raise HTTPException(400, "Set not found")
            badge.set_id = set_id
    
    if tags is not None:
        db.query(BadgeTag).filter(BadgeTag.badge_id == badge_id).delete()
        
        try:
            tag_names = json.loads(tags)
        except:
            tag_names = [t.strip() for t in tags.split(",") if t.strip()]
        
        for tag_name in tag_names[:10]:
            existing_tag = db.query(Tag).filter(
                Tag.user_id == current_user.id,
                Tag.name == tag_name.lower()
            ).first()
            if not existing_tag:
                existing_tag = Tag(user_id=current_user.id, name=tag_name.lower())
                db.add(existing_tag)
                db.flush()
            
            badge_tag = BadgeTag(badge_id=badge.id, tag_id=existing_tag.id)
            db.add(badge_tag)
    
    db.commit()
    return {"message": "Badge updated"}


@app.delete("/api/badges/{badge_id}")
def delete_badge(
    badge_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photos = db.query(Photo).filter(Photo.badge_id == badge_id).all()
    for p in photos:
        if os.path.exists(p.file_path):
            os.remove(p.file_path)
        db.delete(p)
    
    db.query(BadgeTag).filter(BadgeTag.badge_id == badge_id).delete()
    
    db.delete(badge)
    db.commit()
    
    return {"message": "Badge deleted"}


# ========== PHOTOS ==========

@app.post("/api/badges/{badge_id}/photos")
def add_photo(
    badge_id: int,
    photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photos_count = db.query(Photo).filter(Photo.badge_id == badge_id).count()
    if photos_count >= 5:
        raise HTTPException(400, "Maximum 5 photos per badge")
    
    if photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Only JPEG/PNG allowed")
    
    ext = photo.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(config.settings.UPLOAD_DIR, filename)
    
    with open(filepath, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        with Image.open(filepath) as img:
            if img.width < 500 or img.height < 500:
                os.remove(filepath)
                raise HTTPException(400, "Image must be at least 500x500px")
            if os.path.getsize(filepath) > 10 * 1024 * 1024:
                os.remove(filepath)
                raise HTTPException(400, "Image must be ≤10MB")
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(400, f"Invalid image: {e}")
    
    photo_record = Photo(
        badge_id=badge_id,
        file_path=filepath,
        is_main=False
    )
    db.add(photo_record)
    db.commit()
    
    return {"id": photo_record.id, "file_path": f"/uploads/{filename}", "is_main": False}


@app.delete("/api/badges/{badge_id}/photos/{photo_id}")
def delete_photo(
    badge_id: int,
    photo_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.badge_id == badge_id
    ).first()
    if not photo:
        raise HTTPException(404, "Photo not found")
    
    if os.path.exists(photo.file_path):
        os.remove(photo.file_path)
    
    was_main = photo.is_main
    db.delete(photo)
    
    if was_main:
        new_main = db.query(Photo).filter(Photo.badge_id == badge_id).first()
        if new_main:
            new_main.is_main = True
    
    db.commit()
    return {"message": "Photo deleted"}


@app.put("/api/badges/{badge_id}/photos/{photo_id}/make-main")
def make_main_photo(
    badge_id: int,
    photo_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.badge_id == badge_id
    ).first()
    if not photo:
        raise HTTPException(404, "Photo not found")
    
    db.query(Photo).filter(Photo.badge_id == badge_id).update({"is_main": False})
    
    photo.is_main = True
    db.commit()
    
    return {"message": "Photo set as main"}


# ========== TAGS ==========

@app.get("/api/tags", response_model=List[TagResponse])
def get_tags(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    return db.query(Tag).filter(Tag.user_id == current_user.id).all()


# ========== EXPORT ==========

@app.get("/api/export", response_model=ExportResponse)
def export_collection(
    set_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    """Экспорт коллекции в PDF с поддержкой русского языка"""
    
    if set_id:
        badges = db.query(Badge).filter(
            Badge.user_id == current_user.id,
            Badge.set_id == set_id
        ).all()
        set_item = db.query(Set).filter(Set.id == set_id).first()
        title = f"Набор: {set_item.name}" if set_item else "Экспорт"
    else:
        badges = db.query(Badge).filter(Badge.user_id == current_user.id).all()
        title = "Моя коллекция"
    
    if not badges:
        raise HTTPException(404, "Нет значков для экспорта")
    
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import tempfile
    import shutil
    import os
    
    # Регистрируем русский шрифт (используем стандартный Arial, который есть в Windows)
    try:
        # Пробуем загрузить Arial (обычно есть в Windows)
        pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
        font_name = 'Arial'
    except:
        try:
            # Альтернатива - Times New Roman
            pdfmetrics.registerFont(TTFont('TimesNewRoman', 'C:\\Windows\\Fonts\\times.ttf'))
            font_name = 'TimesNewRoman'
        except:
            # Если шрифты не найдены, используем стандартный (кириллица не будет работать)
            font_name = 'Helvetica'
            print("⚠️ Русский шрифт не найден, текст может отображаться некорректно")
    
    # Создаем временный файл для PDF
    temp_dir = tempfile.gettempdir()
    pdf_filename = f"export_{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)
    
    # Создаем PDF документ
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    # Стили с русским шрифтом
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        alignment=1,
        spaceAfter=20
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=12,
        textColor=colors.grey,
        alignment=1,
        spaceAfter=30
    )
    
    badge_name_style = ParagraphStyle(
        'BadgeName',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        alignment=1,
        spaceAfter=5,
        leading=12
    )
    
    info_style = ParagraphStyle(
        'InfoStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=9,
        alignment=1,
        leading=11
    )
    
    # Элементы документа
    elements = []
    
    # Заголовок
    elements.append(Paragraph(f"📛 {title}", title_style))
    elements.append(Paragraph(f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 10*mm))
    
    # Создаем таблицу
    table_data = []
    row_data = []
    
    condition_map = {
        'excellent': 'Отличное',
        'good': 'Хорошее',
        'average': 'Среднее',
        'poor': 'Плохое'
    }
    
    for i, badge in enumerate(badges):
        # Получаем главное фото
        main_photo = db.query(Photo).filter(
            Photo.badge_id == badge.id,
            Photo.is_main == True
        ).first()
        
        # Получаем теги
        tags = db.query(Tag).join(BadgeTag).filter(BadgeTag.badge_id == badge.id).all()
        tag_names = [t.name for t in tags[:3]]
        
        # Ячейка 1: Фото
        if main_photo and os.path.exists(main_photo.file_path):
            try:
                with Image.open(main_photo.file_path) as img:
                    img.thumbnail((250, 250))
                    temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    img.save(temp_img.name, 'JPEG', quality=85)
                    pdf_img = RLImage(temp_img.name, width=55*mm, height=55*mm)
                    row_data.append(pdf_img)
            except Exception as e:
                print(f"Ошибка загрузки фото: {e}")
                row_data.append(Paragraph("Нет фото", badge_name_style))
        else:
            row_data.append(Paragraph("Нет фото", badge_name_style))
        
        # Ячейка 2: Название
        badge_text = badge.name[:40] + ("..." if len(badge.name) > 40 else "")
        row_data.append(Paragraph(badge_text, badge_name_style))
        
        # Ячейка 3: Информация
        info_lines = []
        if badge.year:
            info_lines.append(f"Год: {badge.year}")
        if badge.material:
            info_lines.append(f"Материал: {badge.material}")
        if badge.condition:
            cond_text = condition_map.get(badge.condition.value, badge.condition.value)
            info_lines.append(f"Состояние: {cond_text}")
        if tag_names:
            info_lines.append(f"Теги: {', '.join(tag_names)}")
        
        info_text = "<br/>".join(info_lines) if info_lines else "Нет данных"
        row_data.append(Paragraph(info_text, info_style))
        
        # Ячейка 4: Пустая (для выравнивания)
        row_data.append(Paragraph("", info_style))
        
        # Каждые 4 значка — новая строка
        if len(row_data) >= 4:
            table_data.append(row_data[:4])
            row_data = []
    
    # Добавляем остаток
    if row_data:
        while len(row_data) < 4:
            row_data.append(Paragraph("", info_style))
        table_data.append(row_data[:4])
    
    # Создаем таблицу
    if table_data:
        col_widths = [65*mm, 50*mm, 70*mm, 15*mm]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        elements.append(table)
    
    # Строим PDF
    doc.build(elements)
    
    # Перемещаем в папку uploads
    final_path = os.path.join(config.settings.UPLOAD_DIR, pdf_filename)
    shutil.move(pdf_path, final_path)
    
    # Очищаем временные файлы
    for item in os.listdir(temp_dir):
        if item.startswith('tmp') and (item.endswith('.jpg') or item.endswith('.png')):
            try:
                os.remove(os.path.join(temp_dir, item))
            except:
                pass
    
    return {"file_url": f"/uploads/{pdf_filename}"}


# ========== ML FUNCTIONS ==========

@app.post("/api/process-image")
async def process_image_endpoint(
    photo: UploadFile = File(...),
    auto_rotate: bool = True,
    remove_bg: bool = True,
    current_user: User = Depends(security.get_current_user)
):
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        result = process_image(temp_path, auto_rotate, remove_bg)
        
        return {
            "success": True,
            "original_url": f"/uploads/{os.path.basename(result['original_path'])}",
            "processed_url": f"/uploads/{os.path.basename(result['processed_path'])}",
            "steps": result["steps"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/rotate-image")
async def rotate_image_endpoint(
    photo: UploadFile = File(...),
    angle: int = 90,
    current_user: User = Depends(security.get_current_user)
):
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        result = rotate_image(temp_path, angle)
        
        return {
            "success": True,
            "image_url": f"/uploads/{os.path.basename(result['image_path'])}",
            "angle": result["angle"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/remove-background")
async def remove_background_endpoint(
    photo: UploadFile = File(...),
    current_user: User = Depends(security.get_current_user)
):
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        result = remove_background(temp_path)
        
        if result.get("success"):
            return {
                "success": True,
                "image_url": f"/uploads/{os.path.basename(result['image_path'])}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Unknown error")
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ========== ADMIN PANEL ==========

@app.get("/api/admin/stats")
def get_admin_stats(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    total_users = db.query(User).count()
    total_badges = db.query(Badge).count()
    total_sets = db.query(Set).count()
    total_categories = db.query(Category).count()
    
    registrations = []
    for i in range(6, -1, -1):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = db.query(User).filter(
            User.created_at >= date,
            User.created_at < date + timedelta(days=1)
        ).count()
        registrations.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": count
        })
    
    return {
        "total_users": total_users,
        "total_badges": total_badges,
        "total_sets": total_sets,
        "total_categories": total_categories,
        "registrations": registrations
    }


@app.get("/api/admin/users")
def get_admin_users(
    search: Optional[str] = "",
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    query = db.query(User)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    
    users = query.order_by(User.created_at.desc()).all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "telegram_id": u.telegram_id,
            "is_admin": u.is_admin,
            "created_at": u.created_at
        }
        for u in users
    ]


@app.post("/api/admin/users")
def create_admin_user(
    email: str,
    password: str,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = User(
        email=email,
        password_hash=security.get_password_hash(password),
        email_confirmed_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"id": user.id, "email": user.email, "message": "User created"}


@app.delete("/api/admin/users/{user_id}")
def delete_admin_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    if user_id == current_user.id:
        raise HTTPException(400, "Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    badges = db.query(Badge).filter(Badge.user_id == user_id).all()
    for badge in badges:
        photos = db.query(Photo).filter(Photo.badge_id == badge.id).all()
        for p in photos:
            if os.path.exists(p.file_path):
                os.remove(p.file_path)
            db.delete(p)
        db.delete(badge)
    
    sets = db.query(Set).filter(Set.user_id == user_id).all()
    for s in sets:
        if s.photo_path and os.path.exists(s.photo_path):
            os.remove(s.photo_path)
        db.delete(s)
    
    categories = db.query(Category).filter(Category.user_id == user_id).all()
    for c in categories:
        db.delete(c)
    
    tags = db.query(Tag).filter(Tag.user_id == user_id).all()
    for t in tags:
        db.delete(t)
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted"}


# ========== HEALTH ==========

@app.get("/api/health")
def health_check():
    return {"status": "ok"}