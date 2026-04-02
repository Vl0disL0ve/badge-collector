import cv2
import numpy as np
from PIL import Image
import os
import uuid
from rembg import remove
from typing import List, Dict, Tuple, Optional


def auto_rotate(image_path: str) -> dict:
    """
    Автоматическое выравнивание значка с центрированием в квадрат
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
            pad = 20
            x = max(0, x - pad)
            y = max(0, y - pad)
            w_crop = min(rotated.shape[1] - x, w_crop + 2 * pad)
            h_crop = min(rotated.shape[0] - y, h_crop + 2 * pad)
            cropped = rotated[y:y+h_crop, x:x+w_crop]
        else:
            cropped = rotated
        
        # Центрирование в квадрат
        cropped = center_to_square(cropped)
        
        # Сохраняем
        base_dir = os.path.dirname(image_path)
        filename = f"auto_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        print(f"✅ Auto rotate: угол {best_angle}°, центрировано")
        return {"angle": best_angle, "image_path": out_path}
        
    except Exception as e:
        print(f"Auto rotate error: {e}")
        return {"angle": 0, "image_path": image_path}


def detect_axis(image_path: str) -> dict:
    """
    Определение оси значка (главный угол поворота)
    Возвращает угол в градусах и уверенность
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "angle": 0, "confidence": 0, "message": "Cannot read image"}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Размытие
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(blurred, 255, 
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {"success": False, "angle": 0, "confidence": 0, "message": "No contours found"}
        
        # Находим самый большой контур
        largest = max(contours, key=cv2.contourArea)
        
        # Получаем минимальный ограничивающий прямоугольник
        rect = cv2.minAreaRect(largest)
        angle = rect[2]
        
        # Нормализуем угол (-45..45)
        if angle < -45:
            angle = 90 + angle
        
        # Уверенность = отношение площади контура к площади прямоугольника
        area = cv2.contourArea(largest)
        rect_area = rect[1][0] * rect[1][1]
        confidence = min(1.0, area / rect_area) if rect_area > 0 else 0
        
        return {
            "success": True,
            "angle": float(angle),
            "confidence": float(confidence),
            "message": f"Detected axis: {angle:.1f}°"
        }
        
    except Exception as e:
        return {"success": False, "angle": 0, "confidence": 0, "message": str(e)}


def rotate_to_axis(image_path: str, axis_angle: float) -> dict:
    """
    Поворот значка к заданной оси (выравнивание)
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "image_path": image_path, "angle": axis_angle, "message": "Cannot read image"}
        
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # Поворачиваем так, чтобы ось стала вертикальной/горизонтальной
        rotation_angle = -axis_angle
        rot_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
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
        
        # Центрируем в квадрат
        cropped = center_to_square(cropped)
        
        # Сохраняем
        base_dir = os.path.dirname(image_path)
        filename = f"axis_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        return {
            "success": True,
            "image_path": out_path,
            "angle": rotation_angle,
            "message": f"Rotated to axis: {rotation_angle:.1f}°"
        }
        
    except Exception as e:
        return {"success": False, "image_path": image_path, "angle": 0, "message": str(e)}


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
        
        # Центрируем в квадрат
        cropped = center_to_square(cropped)
        
        # Сохраняем
        base_dir = os.path.dirname(image_path)
        filename = f"rot_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        return {"angle": angle, "image_path": out_path}
        
    except Exception as e:
        print(f"Rotate error: {e}")
        return {"error": str(e)}


def rotate_custom(image_path: str, angle: float) -> dict:
    """
    Поворот изображения на произвольный угол
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "image_path": image_path, "angle": angle, "message": "Cannot read image"}
        
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        rot_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
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
        
        # Центрируем в квадрат
        cropped = center_to_square(cropped)
        
        # Сохраняем
        base_dir = os.path.dirname(image_path)
        filename = f"custom_{uuid.uuid4().hex[:8]}.jpg"
        out_path = os.path.join(base_dir, filename)
        cv2.imwrite(out_path, cropped)
        
        return {
            "success": True,
            "image_path": out_path,
            "angle": angle,
            "message": f"Rotated by {angle:.1f}°"
        }
        
    except Exception as e:
        return {"success": False, "image_path": image_path, "angle": angle, "message": str(e)}


def center_to_square(image: np.ndarray) -> np.ndarray:
    """
    Центрирование объекта в квадратное полотно
    """
    try:
        h, w = image.shape[:2]
        
        # Находим реальный объект (обрезаем белые поля)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        coords = cv2.findNonZero(binary)
        
        if coords is not None:
            x, y, obj_w, obj_h = cv2.boundingRect(coords)
            obj = image[y:y+obj_h, x:x+obj_w]
        else:
            obj = image
            obj_h, obj_w = obj.shape[:2]
        
        # Делаем квадрат с отступами
        max_side = max(obj_h, obj_w)
        padding = int(max_side * 0.15)  # 15% отступ
        square_size = max_side + padding * 2
        
        # Создаём белое полотно
        squared = np.ones((square_size, square_size, 3), dtype=np.uint8) * 255
        
        # Центрируем объект
        y_offset = (square_size - obj_h) // 2
        x_offset = (square_size - obj_w) // 2
        squared[y_offset:y_offset+obj_h, x_offset:x_offset+obj_w] = obj
        
        return squared
        
    except Exception as e:
        print(f"Center to square error: {e}")
        return image


def remove_background(image_path: str) -> dict:
    """
    Удаление фона с помощью rembg + автоцентрирование
    """
    try:
        from PIL import Image, ImageOps
        
        # Читаем исходное изображение
        with open(image_path, 'rb') as f:
            input_data = f.read()
        
        # Удаляем фон
        output_data = remove(input_data)
        
        # Сохраняем временный PNG
        base_dir = os.path.dirname(image_path)
        filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
        temp_png = os.path.join(base_dir, filename)
        
        with open(temp_png, 'wb') as f:
            f.write(output_data)
        
        # Открываем PNG с прозрачностью
        img = Image.open(temp_png)
        
        # Находим bounding box объекта (непрозрачные пиксели)
        if img.mode == 'RGBA':
            alpha = img.split()[-1]
            bbox = alpha.getbbox()
            
            if bbox:
                # Обрезаем по bounding box
                cropped = img.crop(bbox)
                
                # Создаём квадратное полотно с отступами
                width, height = cropped.size
                max_side = max(width, height)
                padding = int(max_side * 0.1)
                new_size = max_side + padding * 2
                
                # Создаём белый фон
                result = Image.new('RGB', (new_size, new_size), (255, 255, 255))
                
                # Центрируем объект
                x_offset = (new_size - width) // 2
                y_offset = (new_size - height) // 2
                
                if cropped.mode == 'RGBA':
                    result.paste(cropped, (x_offset, y_offset), cropped.split()[-1])
                else:
                    result.paste(cropped, (x_offset, y_offset))
                
                img = result
            else:
                # Если объект не найден, просто конвертируем
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[-1])
                else:
                    bg.paste(img)
                img = bg
        else:
            # Уже без альфа-канала
            img = img.convert('RGB')
        
        # Сохраняем JPG
        jpg_path = temp_png.replace('.png', '.jpg')
        img.save(jpg_path, 'JPEG', quality=95)
        
        # Удаляем временный PNG
        os.remove(temp_png)
        
        print(f"✅ Background removed and centered: {jpg_path}")
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

def detect_badges_on_set(image_path: str) -> List[Dict]:
    """
    Детекция значков на фото набора
    Возвращает список словарей с координатами и площадью
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(blurred, 255, 
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV, 11, 2)
        
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected = []
        min_area = 500
        max_area = img.shape[0] * img.shape[1] * 0.5
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area or area > max_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            pad = 20
            x = max(0, x - pad)
            y = max(0, y - pad)
            w = min(img.shape[1] - x, w + 2 * pad)
            h = min(img.shape[0] - y, h + 2 * pad)
            
            detected.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "area": area
            })
        
        detected.sort(key=lambda b: b["area"], reverse=True)
        return detected
        
    except Exception as e:
        print(f"Detect badges error: {e}")
        return []