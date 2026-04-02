import cv2
import numpy as np
import json
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Badge, BadgeFeature, Photo


def extract_features(image_path: str) -> np.ndarray:
    """
    Извлечение признаков из изображения
    Комбинация: цветовая гистограмма (512) + ORB дескрипторы (32) = 544
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return np.zeros(544)
        
        # 1. Цветовая гистограмма в HSV (8x8x8 = 512)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        # 2. ORB ключевые точки
        orb = cv2.ORB_create(nfeatures=100)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        keypoints, descriptors = orb.detectAndCompute(gray, None)
        
        if descriptors is not None and len(descriptors) > 0:
            # Усредняем дескрипторы по всем ключевым точкам
            orb_features = np.mean(descriptors, axis=0)
            # Обрезаем или дополняем до 32
            if len(orb_features) > 32:
                orb_features = orb_features[:32]
            elif len(orb_features) < 32:
                orb_features = np.pad(orb_features, (0, 32 - len(orb_features)))
        else:
            orb_features = np.zeros(32)
        
        # Комбинируем
        features = np.concatenate([hist, orb_features])
        
        # Нормализация для косинусного расстояния
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features
        
    except Exception as e:
        print(f"Feature extraction error: {e}")
        return np.zeros(544)


def compute_similarity(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Косинусное сходство (0-1, где 1 = идентичны)
    """
    if len(features1) != len(features2):
        return 0.0
    
    dot = np.dot(features1, features2)
    return float(dot)


def find_similar_badges(
    db: Session, 
    badge_id: int, 
    user_id: int,
    threshold: float = 0.75,
    limit: int = 10
) -> list:
    """
    Найти похожие значки по векторному сходству
    """
    # Получаем вектор текущего значка
    current_feature = db.query(BadgeFeature).filter(
        BadgeFeature.badge_id == badge_id
    ).first()
    
    if not current_feature:
        return []
    
    current_vec = np.array(json.loads(current_feature.feature_vector))
    
    # Получаем все остальные значки пользователя
    other_badges = db.query(Badge, BadgeFeature).join(
        BadgeFeature, Badge.id == BadgeFeature.badge_id
    ).filter(
        Badge.user_id == user_id,
        Badge.id != badge_id
    ).all()
    
    results = []
    for badge, feature in other_badges:
        other_vec = np.array(json.loads(feature.feature_vector))
        similarity = compute_similarity(current_vec, other_vec)
        
        if similarity >= threshold:
            # Получаем главное фото
            main_photo = db.query(Photo).filter(
                Photo.badge_id == badge.id,
                Photo.is_main == True
            ).first()
            
            results.append({
                "id": badge.id,
                "name": badge.name,
                "similarity": round(similarity * 100, 1),
                "main_photo_url": f"/uploads/{os.path.basename(main_photo.file_path)}" if main_photo else None
            })
    
    # Сортируем по убыванию сходства
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:limit]


def update_all_features(db: Session, user_id: Optional[int] = None) -> int:
    """
    Обновить векторы признаков для всех значков
    """
    query = db.query(Badge)
    if user_id:
        query = query.filter(Badge.user_id == user_id)
    
    badges = query.all()
    updated = 0
    
    for badge in badges:
        main_photo = db.query(Photo).filter(
            Photo.badge_id == badge.id,
            Photo.is_main == True
        ).first()
        
        if main_photo and main_photo.file_path and os.path.exists(main_photo.file_path):
            features = extract_features(main_photo.file_path)
            vector_json = json.dumps(features.tolist())
            
            existing = db.query(BadgeFeature).filter(
                BadgeFeature.badge_id == badge.id
            ).first()
            
            if existing:
                existing.feature_vector = vector_json
            else:
                new_feature = BadgeFeature(
                    badge_id=badge.id,
                    feature_vector=vector_json
                )
                db.add(new_feature)
            updated += 1
            print(f"  ✅ Updated features for badge {badge.id}: {badge.name}")
    
    db.commit()
    return updated


def get_badge_vector(badge_id: int, db: Session) -> Optional[np.ndarray]:
    """
    Получить вектор значка по ID
    """
    feature = db.query(BadgeFeature).filter(BadgeFeature.badge_id == badge_id).first()
    if feature:
        return np.array(json.loads(feature.feature_vector))
    return None