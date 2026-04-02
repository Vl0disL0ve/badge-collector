from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
import json
import os
import uuid
import shutil
from PIL import Image
from datetime import datetime
from ..core import config, database, security
from ..models import User, Set, Badge, Category, set_categories
from ..schemas import SetCreate, SetUpdate, SetResponse

router = APIRouter()


@router.post("/sets", response_model=SetResponse)
def create_set(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    total_count: int = Form(0),
    category_ids: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    category_id_list = []
    if category_ids:
        try:
            category_id_list = json.loads(category_ids)
        except:
            category_id_list = [int(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
    
    categories = []
    if category_id_list:
        categories = db.query(Category).filter(
            Category.id.in_(category_id_list),
            Category.user_id == current_user.id
        ).all()
    
    photo_url = None
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
            photo_url = f"/uploads/{filename}"
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise HTTPException(400, f"Invalid image: {e}")
    
    new_set = Set(
        user_id=current_user.id,
        name=name,
        description=description,
        total_count=total_count,
        photo_path=photo_path
    )
    db.add(new_set)
    db.flush()
    
    if categories:
        new_set.categories = categories
    
    db.commit()
    db.refresh(new_set)
    
    collected = db.query(Badge).filter(Badge.set_id == new_set.id).count()
    
    return SetResponse(
        id=new_set.id,
        name=new_set.name,
        description=new_set.description,
        total_count=new_set.total_count,
        user_id=new_set.user_id,
        photo_path=photo_url,
        created_at=new_set.created_at,
        updated_at=new_set.updated_at,
        collected_count=collected,
        completion_percent=(collected / new_set.total_count * 100) if new_set.total_count > 0 else 0,
        categories=[{"id": c.id, "name": c.name} for c in new_set.categories]
    )


@router.get("/sets", response_model=List[SetResponse])
def get_sets(
    category_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    query = db.query(Set).filter(Set.user_id == current_user.id)
    
    if category_id:
        query = query.join(set_categories).filter(set_categories.c.category_id == category_id)
    
    sets = query.options(joinedload(Set.categories)).all()
    
    result = []
    for s in sets:
        collected = db.query(Badge).filter(Badge.set_id == s.id).count()
        result.append(SetResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            total_count=s.total_count,
            user_id=s.user_id,
            photo_path=f"/uploads/{os.path.basename(s.photo_path)}" if s.photo_path else None,
            created_at=s.created_at,
            updated_at=s.updated_at,
            collected_count=collected,
            completion_percent=(collected / s.total_count * 100) if s.total_count > 0 else 0,
            categories=[{"id": c.id, "name": c.name} for c in s.categories]
        ))
    return result


@router.get("/sets/{set_id}", response_model=SetResponse)
def get_set(
    set_id: int,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    set_item = db.query(Set).filter(
        Set.id == set_id,
        Set.user_id == current_user.id
    ).options(joinedload(Set.categories)).first()
    
    if not set_item:
        raise HTTPException(404, "Set not found")
    
    collected = db.query(Badge).filter(Badge.set_id == set_id).count()
    
    return SetResponse(
        id=set_item.id,
        name=set_item.name,
        description=set_item.description,
        total_count=set_item.total_count,
        user_id=set_item.user_id,
        photo_path=f"/uploads/{os.path.basename(set_item.photo_path)}" if set_item.photo_path else None,
        created_at=set_item.created_at,
        updated_at=set_item.updated_at,
        collected_count=collected,
        completion_percent=(collected / set_item.total_count * 100) if set_item.total_count > 0 else 0,
        categories=[{"id": c.id, "name": c.name} for c in set_item.categories]
    )


@router.put("/sets/{set_id}", response_model=SetResponse)
def update_set(
    set_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    total_count: Optional[int] = Form(None),
    category_ids: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    set_item = db.query(Set).filter(
        Set.id == set_id,
        Set.user_id == current_user.id
    ).first()
    
    if not set_item:
        raise HTTPException(404, "Set not found")
    
    if name is not None:
        set_item.name = name
    if description is not None:
        set_item.description = description
    if total_count is not None:
        set_item.total_count = total_count
    
    if category_ids is not None:
        category_id_list = []
        try:
            category_id_list = json.loads(category_ids)
        except:
            category_id_list = [int(cid.strip()) for cid in category_ids.split(",") if cid.strip()]
        
        categories = db.query(Category).filter(
            Category.id.in_(category_id_list),
            Category.user_id == current_user.id
        ).all()
        set_item.categories = categories
    
    photo_url = None
    if photo:
        if photo.content_type not in ["image/jpeg", "image/png"]:
            raise HTTPException(400, "Only JPEG/PNG allowed")
        
        if set_item.photo_path and os.path.exists(set_item.photo_path):
            os.remove(set_item.photo_path)
        
        ext = photo.filename.split(".")[-1]
        filename = f"set_{uuid.uuid4()}.{ext}"
        filepath = os.path.join(config.settings.UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        
        set_item.photo_path = filepath
        photo_url = f"/uploads/{filename}"
    else:
        photo_url = f"/uploads/{os.path.basename(set_item.photo_path)}" if set_item.photo_path else None
    
    set_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(set_item)
    
    collected = db.query(Badge).filter(Badge.set_id == set_id).count()
    
    return SetResponse(
        id=set_item.id,
        name=set_item.name,
        description=set_item.description,
        total_count=set_item.total_count,
        user_id=set_item.user_id,
        photo_path=photo_url,
        created_at=set_item.created_at,
        updated_at=set_item.updated_at,
        collected_count=collected,
        completion_percent=(collected / set_item.total_count * 100) if set_item.total_count > 0 else 0,
        categories=[{"id": c.id, "name": c.name} for c in set_item.categories]
    )


@router.delete("/sets/{set_id}")
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
        from ..models import Photo
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