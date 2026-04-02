from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional
import os
import uuid
import shutil
import cv2
import numpy as np
from ..core import config, security
from ..models import User
from ..services.ml import (
    process_image, rotate_image, remove_background,
    detect_axis, rotate_custom, detect_badges_on_set
)
from ..schemas import AxisDetectionResponse, RotateCustomResponse, DetectBadgesResponse

router = APIRouter()


@router.post("/process-image")
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
        return {"success": False, "error": str(e)}


@router.post("/rotate-image")
async def rotate_image_endpoint(
    photo: UploadFile = File(...),
    angle: int = Form(...),
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
        return {"success": False, "error": str(e)}


@router.post("/remove-background")
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
            return {"success": False, "error": result.get("error", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/detect-axis", response_model=AxisDetectionResponse)
async def detect_axis_endpoint(
    photo: UploadFile = File(...),
    current_user: User = Depends(security.get_current_user)
):
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        result = detect_axis(temp_path)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return AxisDetectionResponse(
            success=result["success"],
            angle=result["angle"],
            confidence=result["confidence"],
            message=result.get("message")
        )
    except Exception as e:
        return AxisDetectionResponse(
            success=False,
            angle=0,
            confidence=0,
            message=str(e)
        )


@router.post("/rotate-custom", response_model=RotateCustomResponse)
async def rotate_custom_endpoint(
    photo: UploadFile = File(...),
    angle: float = Form(...),
    current_user: User = Depends(security.get_current_user)
):
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        result = rotate_custom(temp_path, angle)
        
        return RotateCustomResponse(
            success=result["success"],
            image_url=f"/uploads/{os.path.basename(result['image_path'])}",
            angle=result["angle"],
            message=result.get("message")
        )
    except Exception as e:
        return RotateCustomResponse(
            success=False,
            image_url="",
            angle=0,
            message=str(e)
        )


@router.post("/detect-badges", response_model=DetectBadgesResponse)
async def detect_badges_endpoint(
    photo: UploadFile = File(...),
    current_user: User = Depends(security.get_current_user)
):
    """Детекция всех значков на фото набора"""
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        detected = detect_badges_on_set(temp_path)
        
        badges_info = []
        for i, d in enumerate(detected):
            badges_info.append({
                "id": i,
                "name": f"Значок {i + 1}",
                "x": int(d['x']),
                "y": int(d['y']),
                "width": int(d['width']),
                "height": int(d['height']),
                "confidence": d.get('area', 0) / 10000 if d.get('area') else None
            })
        
        return DetectBadgesResponse(
            success=True,
            badges_count=len(badges_info),
            badges=badges_info,
            message=f"Найдено {len(badges_info)} значков"
        )
    except Exception as e:
        return DetectBadgesResponse(
            success=False,
            badges_count=0,
            badges=[],
            message=str(e)
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/crop-image")
async def crop_image_endpoint(
    photo: UploadFile = File(...),
    x: int = Form(...),
    y: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    current_user: User = Depends(security.get_current_user)
):
    """Вырезать область из изображения по координатам"""
    ext = photo.filename.split(".")[-1]
    temp_filename = f"temp_{uuid.uuid4()}.{ext}"
    temp_path = os.path.join(config.settings.UPLOAD_DIR, temp_filename)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(photo.file, f)
    
    try:
        img = cv2.imread(temp_path)
        if img is None:
            raise HTTPException(400, "Cannot read image")
        
        h, w = img.shape[:2]
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        width = min(width, w - x)
        height = min(height, h - y)
        
        if width <= 0 or height <= 0:
            raise HTTPException(400, "Invalid crop area")
        
        cropped = img[y:y+height, x:x+width]
        
        filename = f"crop_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(config.settings.UPLOAD_DIR, filename)
        cv2.imwrite(filepath, cropped)
        
        return {"success": True, "image_url": f"/uploads/{filename}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)