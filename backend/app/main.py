from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import os
import shutil
import uuid
from PIL import Image
from . import models, database, auth

app = FastAPI()

# CORS для фронтенда и бота
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Путь к папке с фронтендом
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend')

# Подключаем статические файлы фронтенда
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_PATH, "html")), name="static")
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_PATH, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_PATH, "js")), name="js")

# Статические файлы (фото)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Временное хранилище для кодов привязки Telegram (в реальном проекте используй Redis)
telegram_codes = {}  # code -> (user_id, expires_at)

# ========== АУТЕНТИФИКАЦИЯ ==========

@app.post("/api/register")
def register(email: str, password: str, db: Session = Depends(database.get_db)):
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(400, "Email already registered")
    
    user = models.User(
        email=email,
        password_hash=auth.get_password_hash(password),
        email_confirmed_at=datetime.utcnow()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/login")
def login(email: str, password: str, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "telegram_id": user.telegram_id}}

@app.get("/api/me")
def get_me(current_user = Depends(auth.get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "telegram_id": current_user.telegram_id}

# ========== ПРИВЯЗКА TELEGRAM ==========

@app.post("/api/telegram/generate-code")
def generate_telegram_code(db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    """Генерирует код для привязки Telegram"""
    code = secrets.randbelow(1000000)
    code_str = f"{code:06d}"
    
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    telegram_codes[code_str] = (user.id, expires_at)
    
    # Очищаем старые коды
    for key, (_, exp) in list(telegram_codes.items()):
        if exp < datetime.utcnow():
            del telegram_codes[key]
    
    return {"code": code_str, "expires_in": 900}

@app.post("/api/telegram/verify-code")
def verify_telegram_code(code: str, telegram_id: int, db: Session = Depends(database.get_db)):
    """Проверяет код (вызывается из бота)"""
    if code not in telegram_codes:
        raise HTTPException(400, "Invalid or expired code")
    
    user_id, expires_at = telegram_codes[code]
    if expires_at < datetime.utcnow():
        del telegram_codes[code]
        raise HTTPException(400, "Code expired")
    
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    user.telegram_id = telegram_id
    db.commit()
    
    del telegram_codes[code]
    return {"message": "Telegram account linked successfully"}

# ========== КАТЕГОРИИ ==========

@app.post("/api/categories")
def create_category(name: str, description: str = "", db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    category = models.Category(name=name, description=description)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@app.get("/api/categories")
def get_categories(db: Session = Depends(database.get_db)):
    return db.query(models.Category).all()

@app.delete("/api/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    
    # Проверяем, есть ли значки в этой категории
    badges_count = db.query(models.Badge).filter(models.Badge.category_id == category_id).count()
    if badges_count > 0:
        raise HTTPException(400, "Cannot delete category with badges")
    
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}

# ========== НАБОРЫ ==========

@app.post("/api/sets")
def create_set(
    name: str,
    description: str = "",
    total_count: int = None,
    db: Session = Depends(database.get_db),
    user = Depends(auth.get_current_user)
):
    new_set = models.Set(
        user_id=user.id,
        name=name,
        description=description,
        total_count=total_count
    )
    db.add(new_set)
    db.commit()
    db.refresh(new_set)
    return new_set

@app.get("/api/sets")
def get_sets(db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    return db.query(models.Set).filter(models.Set.user_id == user.id).all()

@app.delete("/api/sets/{set_id}")
def delete_set(set_id: int, db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    set_item = db.query(models.Set).filter(models.Set.id == set_id, models.Set.user_id == user.id).first()
    if not set_item:
        raise HTTPException(404, "Set not found")
    
    # Отвязываем значки от набора
    db.query(models.Badge).filter(models.Badge.set_id == set_id).update({"set_id": None})
    
    db.delete(set_item)
    db.commit()
    return {"message": "Set deleted"}

# ========== ЗНАЧКИ ==========

@app.post("/api/badges")
def create_badge(
    name: str = Form(...),
    description: str = Form(""),
    year: int = Form(None),
    material: str = Form(""),
    condition: str = Form(None),
    category_id: int = Form(None),
    set_id: int = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    user = Depends(auth.get_current_user)
):
    # Валидация фото
    if photo.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(400, "Only JPEG/PNG allowed")
    
    # Сохраняем фото
    ext = photo.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = f"uploads/{filename}"
    
    with open(filepath, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        img = Image.open(filepath)
        if img.width < 500 or img.height < 500:
            os.remove(filepath)
            raise HTTPException(400, "Image must be at least 500x500px")
        if os.path.getsize(filepath) > 10 * 1024 * 1024:
            os.remove(filepath)
            raise HTTPException(400, "Image must be ≤10MB")
    except Exception as e:
        os.remove(filepath)
        raise HTTPException(400, f"Invalid image: {e}")
    
    # Проверяем категорию
    if category_id:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(400, "Category not found")
    
    # Проверяем набор
    if set_id:
        set_item = db.query(models.Set).filter(models.Set.id == set_id, models.Set.user_id == user.id).first()
        if not set_item:
            raise HTTPException(400, "Set not found")
    
    # Создаём значок
    badge = models.Badge(
        user_id=user.id,
        name=name,
        description=description if description else None,
        year=year if year and year > 0 else None,
        material=material if material else None,
        condition=models.Condition(condition) if condition and condition in ["excellent", "good", "average", "poor"] else None,
        category_id=category_id if category_id else None,
        set_id=set_id if set_id else None
    )
    db.add(badge)
    db.flush()
    
    # Создаём фото
    photo_record = models.Photo(
        badge_id=badge.id,
        file_path=filepath,
        is_main=True
    )
    db.add(photo_record)
    
    db.commit()
    db.refresh(badge)
    
    return {"id": badge.id, "name": badge.name}

@app.get("/api/badges")
def get_badges(
    search: str = "",
    category_id: int = None,
    set_id: int = None,
    condition: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(database.get_db),
    user = Depends(auth.get_current_user)
):
    query = db.query(models.Badge).filter(models.Badge.user_id == user.id)
    
    if search:
        query = query.filter(models.Badge.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(models.Badge.category_id == category_id)
    if set_id:
        query = query.filter(models.Badge.set_id == set_id)
    if condition:
        query = query.filter(models.Badge.condition == condition)
    
    total = query.count()
    badges = query.order_by(models.Badge.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for b in badges:
        photo = db.query(models.Photo).filter(models.Photo.badge_id == b.id, models.Photo.is_main == True).first()
        result.append({
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "year": b.year,
            "material": b.material,
            "condition": b.condition.value if b.condition else None,
            "category_id": b.category_id,
            "set_id": b.set_id,
            "photo_url": f"/{photo.file_path}" if photo else None,
            "created_at": b.created_at
        })
    
    # Гарантируем, что items — всегда массив
    return {
        "total": total,
        "items": result if result else [],
        "limit": limit,
        "offset": offset
    }

@app.get("/api/badges/{badge_id}")
def get_badge(badge_id: int, db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    badge = db.query(models.Badge).filter(models.Badge.id == badge_id, models.Badge.user_id == user.id).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photos = db.query(models.Photo).filter(models.Photo.badge_id == badge_id).all()
    category = db.query(models.Category).filter(models.Category.id == badge.category_id).first() if badge.category_id else None
    set_item = db.query(models.Set).filter(models.Set.id == badge.set_id).first() if badge.set_id else None
    
    return {
        "id": badge.id,
        "name": badge.name,
        "description": badge.description,
        "year": badge.year,
        "material": badge.material,
        "condition": badge.condition.value if badge.condition else None,
        "category": {"id": category.id, "name": category.name} if category else None,
        "set": {"id": set_item.id, "name": set_item.name} if set_item else None,
        "photos": [{"id": p.id, "file_path": p.file_path, "is_main": p.is_main} for p in photos],
        "created_at": badge.created_at
    }

@app.put("/api/badges/{badge_id}")
def update_badge(
    badge_id: int,
    name: str = Form(None),
    description: str = Form(""),
    year: int = Form(None),
    material: str = Form(""),
    condition: str = Form(None),
    category_id: int = Form(None),
    set_id: int = Form(None),
    db: Session = Depends(database.get_db),
    user = Depends(auth.get_current_user)
):
    badge = db.query(models.Badge).filter(models.Badge.id == badge_id, models.Badge.user_id == user.id).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    if name:
        badge.name = name
    if description:
        badge.description = description
    if year:
        badge.year = year
    if material:
        badge.material = material
    if condition and condition in ["excellent", "good", "average", "poor"]:
        badge.condition = models.Condition(condition)
    if category_id:
        category = db.query(models.Category).filter(models.Category.id == category_id).first()
        if not category:
            raise HTTPException(400, "Category not found")
        badge.category_id = category_id
    if set_id is not None:
        if set_id == 0:
            badge.set_id = None
        else:
            set_item = db.query(models.Set).filter(models.Set.id == set_id, models.Set.user_id == user.id).first()
            if not set_item:
                raise HTTPException(400, "Set not found")
            badge.set_id = set_id
    
    db.commit()
    return {"message": "Badge updated"}

@app.delete("/api/badges/{badge_id}")
def delete_badge(badge_id: int, db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    badge = db.query(models.Badge).filter(models.Badge.id == badge_id, models.Badge.user_id == user.id).first()
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    photos = db.query(models.Photo).filter(models.Photo.badge_id == badge_id).all()
    for p in photos:
        if os.path.exists(p.file_path):
            os.remove(p.file_path)
        db.delete(p)
    
    db.delete(badge)
    db.commit()
    
    return {"message": "Badge deleted"}

# ========== ЭКСПОРТ ==========

@app.get("/api/export")
def export_collection(db: Session = Depends(database.get_db), user = Depends(auth.get_current_user)):
    badges = db.query(models.Badge).filter(models.Badge.user_id == user.id).all()
    
    if not badges:
        raise HTTPException(404, "No badges to export")
    
    from PIL import Image, ImageDraw
    
    thumb_size = 200
    spacing = 20
    cols = 4
    
    rows = (len(badges) + cols - 1) // cols
    img_width = cols * (thumb_size + spacing) + spacing
    img_height = rows * (thumb_size + spacing) + spacing
    
    result_img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(result_img)
    
    for idx, badge in enumerate(badges):
        row = idx // cols
        col = idx % cols
        x = spacing + col * (thumb_size + spacing)
        y = spacing + row * (thumb_size + spacing)
        
        photo = db.query(models.Photo).filter(models.Photo.badge_id == badge.id, models.Photo.is_main == True).first()
        if photo and os.path.exists(photo.file_path):
            thumb = Image.open(photo.file_path)
            thumb.thumbnail((thumb_size, thumb_size))
            result_img.paste(thumb, (x, y))
        else:
            draw.rectangle([x, y, x+thumb_size, y+thumb_size], fill="gray", outline="black")
            draw.text((x+10, y+thumb_size//2), "Нет фото", fill="white")
        
        draw.text((x, y+thumb_size+5), badge.name[:30], fill="black")
    
    export_path = f"uploads/export_{user.id}_{uuid.uuid4().hex[:6]}.jpg"
    result_img.save(export_path)
    
    return {"file_url": f"/{export_path}"}