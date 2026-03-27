import cv2
import numpy as np
from PIL import Image
import os
import uuid
from rembg import remove

def auto_rotate(image_path: str) -> dict:
    """
    Автоматическое выравнивание значка
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"angle": 0, "image_path": image_path}
        
        h, w = img.shape[:2]
        
        # Конвертируем в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Размытие для уменьшения шума
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(blurred, 255, 
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"angle": 0, "image_path": image_path}
        
        # Находим самый большой контур
        largest = max(contours, key=cv2.contourArea)
        
        # Получаем минимальный ограничивающий прямоугольник
        rect = cv2.minAreaRect(largest)
        angle = rect[2]
        
        # Определяем оптимальный угол (0, 90, 180, 270)
        target_angles = [0, 90, 180, 270]
        best_angle = min(target_angles, key=lambda a: min(abs(angle - a), 360 - abs(angle - a)))
        
        # Поворачиваем изображение
        if best_angle != 0:
            center = (w // 2, h // 2)
            rot_matrix = cv2.getRotationMatrix2D(center, -best_angle, 1.0)
            rotated = cv2.warpAffine(img, rot_matrix, (w, h), 
                                      flags=cv2.INTER_LINEAR,
                                      borderMode=cv2.BORDER_CONSTANT,
                                      borderValue=(255, 255, 255))
        else:
            rotated = img.copy()
        
        # Обрезаем белые края
        gray_rot = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
        _, binary_rot = cv2.threshold(gray_rot, 10, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(binary_rot)
        
        if coords is not None:
            x, y, w_crop, h_crop = cv2.boundingRect(coords)
            # Добавляем отступ
            pad = 20
            x = max(0, x - pad)
            y = max(0, y - pad)
            w_crop = min(rotated.shape[1] - x, w_crop + 2 * pad)
            h_crop = min(rotated.shape[0] - y, h_crop + 2 * pad)
            cropped = rotated[y:y+h_crop, x:x+w_crop]
        else:
            cropped = rotated
        
        # Сохраняем с уникальным именем
        base_dir = os.path.dirname(image_path)
        filename = f"auto_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        print(f"✅ Auto rotate: угол {best_angle}°")
        return {"angle": best_angle, "image_path": out_path}
        
    except Exception as e:
        print(f"Auto rotate error: {e}")
        return {"angle": 0, "image_path": image_path}


def rotate_image(image_path: str, angle: int) -> dict:
    """
    Поворот изображения на ±90°
    angle: 90 (вправо) или -90 (влево)
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Cannot read image"}
        
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # Поворачиваем
        rot_angle = angle if angle == 90 else -90
        rot_matrix = cv2.getRotationMatrix2D(center, rot_angle, 1.0)
        rotated = cv2.warpAffine(img, rot_matrix, (w, h), 
                                  flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=(255, 255, 255))
        
        # Обрезаем белые края
        gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(binary)
        
        if coords is not None:
            x, y, w_crop, h_crop = cv2.boundingRect(coords)
            pad = 20
            x = max(0, x - pad)
            y = max(0, y - pad)
            w_crop = min(rotated.shape[1] - x, w_crop + 2 * pad)
            h_crop = min(rotated.shape[0] - y, h_crop + 2 * pad)
            cropped = rotated[y:y+h_crop, x:x+w_crop]
        else:
            cropped = rotated
        
        # Сохраняем
        base_dir = os.path.dirname(image_path)
        filename = f"rot_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        print(f"✅ Rotate: угол {angle}°")
        return {"angle": angle, "image_path": out_path}
        
    except Exception as e:
        print(f"Rotate error: {e}")
        return {"error": str(e)}


def remove_background(image_path: str) -> dict:
    """
    Удаление фона с помощью rembg
    """
    try:
        # Читаем исходное изображение
        with open(image_path, 'rb') as f:
            input_data = f.read()
        
        # Удаляем фон
        output_data = remove(input_data)
        
        # Сохраняем результат
        base_dir = os.path.dirname(image_path)
        filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
        out_path = os.path.join(base_dir, filename)
        
        with open(out_path, 'wb') as f:
            f.write(output_data)
        
        # Конвертируем PNG в JPG с белым фоном
        png = Image.open(out_path)
        jpg_path = out_path.replace('.png', '.jpg')
        
        if png.mode == 'RGBA':
            bg = Image.new('RGB', png.size, (255, 255, 255))
            bg.paste(png, mask=png.split()[3])
            bg.save(jpg_path, 'JPEG', quality=95)
        else:
            png.convert('RGB').save(jpg_path, 'JPEG', quality=95)
        
        os.remove(out_path)
        
        print(f"✅ Background removed: {jpg_path}")
        return {"success": True, "image_path": jpg_path}
        
    except Exception as e:
        print(f"Remove background error: {e}")
        return {"success": False, "error": str(e)}


def process_image(image_path: str, auto_rotate: bool = True, remove_bg: bool = True) -> dict:
    """
    Полная обработка изображения
    """
    result = {
        "original_path": image_path,
        "processed_path": image_path,
        "steps": []
    }
    current = image_path
    
    if auto_rotate:
        print(f"🔄 Auto rotate: {current}")
        rot = auto_rotate(current)
        if "error" not in rot:
            current = rot["image_path"]
            result["steps"].append({"step": "auto_rotate", "angle": rot["angle"]})
            print(f"   → {current}")
    
    if remove_bg:
        print(f"✨ Remove background: {current}")
        bg = remove_background(current)
        if bg.get("success"):
            current = bg["image_path"]
            result["steps"].append({"step": "remove_background"})
            print(f"   → {current}")
    
    result["processed_path"] = current
    return result