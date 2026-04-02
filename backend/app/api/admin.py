from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import os
from ..core import database, security
from ..models import User, Badge, Set, Category, Photo, Tag
from ..schemas import UserResponse

router = APIRouter()


@router.get("/admin/stats")
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
        registrations.append({"date": date.strftime("%Y-%m-%d"), "count": count})
    
    return {
        "total_users": total_users,
        "total_badges": total_badges,
        "total_sets": total_sets,
        "total_categories": total_categories,
        "registrations": registrations
    }


@router.get("/admin/users")
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


@router.post("/admin/users")
def create_admin_user(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Валидация
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
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

@router.delete("/admin/users/{user_id}")
def delete_admin_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    # Проверка прав администратора
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    # Нельзя удалить самого себя
    if user_id == current_user.id:
        raise HTTPException(400, "Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    
    # Удаляем все данные пользователя
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