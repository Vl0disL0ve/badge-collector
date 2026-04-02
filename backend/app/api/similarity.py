from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
from ..core import database, security
from ..models import User, Badge, Photo, BadgeFeature
from ..services.similarity import find_similar_badges, update_all_features, extract_features
from ..schemas import BadgeResponse

router = APIRouter()


@router.get("/badges/{badge_id}/similar")
def get_similar_badges(
    badge_id: int,
    threshold: float = 0.75,
    limit: int = 10,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    badge = db.query(Badge).filter(
        Badge.id == badge_id,
        Badge.user_id == current_user.id
    ).first()
    
    if not badge:
        raise HTTPException(404, "Badge not found")
    
    similar = find_similar_badges(db, badge_id, current_user.id, threshold, limit)
    return {"badge_id": badge_id, "similar": similar}


@router.post("/badges/{badge_id}/update-features")
def update_badge_features(
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
    
    main_photo = db.query(Photo).filter(
        Photo.badge_id == badge_id,
        Photo.is_main == True
    ).first()
    
    if not main_photo:
        raise HTTPException(400, "Badge has no main photo")
    
    features = extract_features(main_photo.file_path)
    vector_json = json.dumps(features.tolist())
    
    existing = db.query(BadgeFeature).filter(BadgeFeature.badge_id == badge_id).first()
    if existing:
        existing.feature_vector = vector_json
    else:
        new_feature = BadgeFeature(badge_id=badge_id, feature_vector=vector_json)
        db.add(new_feature)
    
    db.commit()
    return {"message": "Features updated"}


@router.post("/badges/update-all-features")
def update_all_badges_features(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    updated = update_all_features(db)
    return {"message": f"Updated {updated} badges"}


@router.post("/badges/update-my-features")
def update_my_badges_features(
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    updated = update_all_features(db, user_id=current_user.id)
    return {"message": f"Updated {updated} of your badges"}