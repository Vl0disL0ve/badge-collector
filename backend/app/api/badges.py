from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import os
import uuid
import shutil
from PIL import Image
from datetime import datetime
from ..core import config, database, security
from ..models import User, Set, Badge, Photo, Tag, BadgeTag, Condition, BadgeFeature
from ..schemas import BadgeResponse
from ..services.similarity import extract_features

router = APIRouter()


@router.post("/badges", response_model=BadgeResponse)
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
        condition=condition_enum,
        rotation_angle=0
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
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        
        try:
            img = Image.open(filepath)
            width, height = img.size
            img.close()
            
            if width < 50 or height < 50:
                os.remove(filepath)
                db.rollback()
                raise HTTPException(400, f"Photo {i+1}: Image must be at least 50x50px")
            
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
    
    if saved_photos:
        features = extract_features(saved_photos[0].file_path)
        feature_vector = json.dumps(features.tolist())
        badge_feature = BadgeFeature(badge_id=badge.id, feature_vector=feature_vector)
        db.add(badge_feature)
    
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
        set_name=set_item.name,
        user_id=badge.user_id,
        rotation_angle=badge.rotation_angle,
        created_at=badge.created_at,
        updated_at=badge.updated_at,
        main_photo_url=f"/uploads/{os.path.basename(saved_photos[0].file_path)}" if saved_photos else None,
        photos=[{"id": p.id, "file_path": f"/uploads/{os.path.basename(p.file_path)}", "is_main": p.is_main} for p in saved_photos],
        tags=tag_names
    )


@router.get("/badges", response_model=dict)
def get_badges(
    search: Optional[str] = Query(None),
    set_id: Optional[int] = Query(None),
    condition: Optional[str] = Query(None),
    tag_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
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
        query = query.join(BadgeTag).filter(BadgeTag.tag_id == tag_id).distinct()
    
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


@router.get("/badges/{badge_id}", response_model=BadgeResponse)
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
        rotation_angle=badge.rotation_angle,
        created_at=badge.created_at,
        updated_at=badge.updated_at,
        main_photo_url=f"/uploads/{os.path.basename(main_photo.file_path)}" if main_photo else None,
        photos=[{"id": p.id, "file_path": f"/uploads/{os.path.basename(p.file_path)}", "is_main": p.is_main} for p in photos],
        tags=[t.name for t in tags]
    )


@router.put("/badges/{badge_id}")
def update_badge(
    badge_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    material: Optional[str] = Form(None),
    condition: Optional[str] = Form(None),
    set_id: Optional[int] = Form(None),
    tags: Optional[str] = Form(None),
    rotation_angle: Optional[float] = Form(None),
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
    if rotation_angle is not None:
        badge.rotation_angle = rotation_angle
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


@router.delete("/badges/{badge_id}")
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


@router.post("/badges/{badge_id}/photos")
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
            if img.width < 50 or img.height < 50:
                os.remove(filepath)
                raise HTTPException(400, "Image must be at least 50x50px")
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


@router.delete("/badges/{badge_id}/photos/{photo_id}")
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


@router.put("/badges/{badge_id}/photos/{photo_id}/make-main")
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