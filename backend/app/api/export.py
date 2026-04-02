from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import uuid
import shutil
import tempfile
from PIL import Image as PILImage
from datetime import datetime
from ..core import config, database, security
from ..models import User, Badge, Photo, Set, Tag, BadgeTag
from ..schemas import ExportResponse

router = APIRouter()


@router.get("/export", response_model=ExportResponse)
def export_collection(
    set_id: Optional[int] = Query(None, description="ID набора для экспорта"),
    columns: Optional[int] = Query(3, ge=1, le=6, description="Количество колонок в сетке значков"),
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Принудительная конвертация columns в int
    try:
        columns = int(columns)
    except (TypeError, ValueError):
        columns = 3
    
    if columns < 1:
        columns = 1
    if columns > 6:
        columns = 6
    
    # Получаем данные
    if set_id:
        badges = db.query(Badge).filter(
            Badge.user_id == current_user.id,
            Badge.set_id == set_id
        ).order_by(Badge.created_at.desc()).all()
        set_item = db.query(Set).filter(Set.id == set_id, Set.user_id == current_user.id).first()
        if not set_item:
            raise HTTPException(404, "Набор не найден")
    else:
        badges = db.query(Badge).filter(
            Badge.user_id == current_user.id
        ).order_by(Badge.created_at.desc()).all()
        set_item = None
    
    if not badges:
        raise HTTPException(404, "Нет значков для экспорта")
    
    # Регистрируем шрифт для кириллицы
    font_name = 'Helvetica'
    font_paths = [
        'C:\\Windows\\Fonts\\arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont('CustomFont', font_path))
                font_name = 'CustomFont'
                break
            except:
                continue
    
    # Создаём временную папку для изображений
    temp_images_dir = tempfile.mkdtemp()
    
    try:
        # Настройки документа
        doc = SimpleDocTemplate(
            os.path.join(temp_images_dir, "output.pdf"),
            pagesize=A4,
            rightMargin=15*mm,
            leftMargin=15*mm,
            topMargin=20*mm,
            bottomMargin=15*mm
        )
        
        styles = getSampleStyleSheet()
        
        # Стили
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName=font_name,
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),
            alignment=1,
            spaceAfter=6
        )
        
        desc_style = ParagraphStyle(
            'DescStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=11,
            textColor=colors.HexColor('#4b5563'),
            alignment=1,
            spaceAfter=12
        )
        
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=9,
            textColor=colors.HexColor('#9ca3af'),
            alignment=1,
            spaceAfter=20
        )
        
        badge_name_style = ParagraphStyle(
            'BadgeNameStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=10,
            alignment=1,
            textColor=colors.HexColor('#374151'),
            spaceAfter=4,
            leading=12
        )
        
        badge_meta_style = ParagraphStyle(
            'BadgeMetaStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=8,
            alignment=1,
            textColor=colors.HexColor('#6b7280'),
            spaceAfter=3,
            leading=10
        )
        
        tag_style = ParagraphStyle(
            'TagStyle',
            parent=styles['Normal'],
            fontName=font_name,
            fontSize=7,
            alignment=1,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=2,
            leading=9
        )
        
        story = []
        
        # ========== ШАПКА ВО ВСЮ ШИРИНУ ==========
        if set_item:
            story.append(Paragraph(f"📦 {set_item.name}", title_style))
            if set_item.description:
                story.append(Paragraph(set_item.description, desc_style))
            story.append(Paragraph(
                f"<b>Всего значков:</b> {len(badges)} из {set_item.total_count or len(badges)}",
                desc_style
            ))
        else:
            story.append(Paragraph(f"📛 Вся коллекция", title_style))
            story.append(Paragraph(
                f"<b>Всего значков:</b> {len(badges)}",
                desc_style
            ))
        
        story.append(Paragraph(f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}", date_style))
        story.append(Spacer(1, 10))
        
        # ========== РАСЧЁТ СЕТКИ ==========
        page_width = 180 * mm
        cell_spacing = 6 * mm
        cell_width = (page_width - (columns - 1) * cell_spacing) / columns
        
        # Собираем данные для таблицы
        table_data = []
        row = []
        
        for i, badge in enumerate(badges):
            # Получаем главное фото
            main_photo = db.query(Photo).filter(
                Photo.badge_id == badge.id,
                Photo.is_main == True
            ).first()
            
            if not main_photo:
                main_photo = db.query(Photo).filter(Photo.badge_id == badge.id).first()
            
            # Получаем теги
            tags = db.query(Tag).join(BadgeTag).filter(BadgeTag.badge_id == badge.id).all()
            tag_names = [t.name for t in tags[:3]]
            
            # Создаём содержимое ячейки
            cell_content = []
            
            # ФОТО (сверху)
            temp_img_path = None
            if main_photo and os.path.exists(main_photo.file_path):
                try:
                    with PILImage.open(main_photo.file_path) as img:
                        # Ресайз для PDF
                        img_width, img_height = img.size
                        target_size = 80
                        if img_width > img_height:
                            scale = target_size / img_width
                        else:
                            scale = target_size / img_height
                        
                        new_width = int(img_width * scale)
                        new_height = int(img_height * scale)
                        
                        # Сохраняем во временную папку (НЕ УДАЛЯЕМ!)
                        temp_img_path = os.path.join(temp_images_dir, f"badge_{badge.id}_{i}.jpg")
                        img_resized = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                        img_resized.save(temp_img_path, 'JPEG', quality=85)
                        
                        pdf_img = RLImage(temp_img_path, width=new_width*0.75, height=new_height*0.75)
                        pdf_img.hAlign = 'CENTER'
                        cell_content.append(pdf_img)
                except Exception as e:
                    print(f"Image error for badge {badge.id}: {e}")
                    cell_content.append(Paragraph("🏷️ Нет фото", badge_name_style))
            else:
                cell_content.append(Paragraph("🏷️ Нет фото", badge_name_style))
            
            cell_content.append(Spacer(1, 4))
            
            # НАЗВАНИЕ
            badge_name = badge.name[:40] + "..." if len(badge.name) > 40 else badge.name
            cell_content.append(Paragraph(badge_name, badge_name_style))
            
            cell_content.append(Spacer(1, 2))
            
            # МЕТА-ИНФОРМАЦИЯ
            meta_parts = []
            if badge.year:
                meta_parts.append(f"📅 {badge.year}")
            if badge.material:
                meta_parts.append(f"🔩 {badge.material[:20]}")
            if badge.condition:
                condition_map = {'excellent': 'Отл', 'good': 'Хор', 'average': 'Ср', 'poor': 'Пл'}
                meta_parts.append(f"⭐ {condition_map.get(badge.condition.value, badge.condition.value)}")
            
            if meta_parts:
                cell_content.append(Paragraph(" | ".join(meta_parts), badge_meta_style))
            
            # ТЕГИ
            if tag_names:
                tags_text = " ".join([f"#{t}" for t in tag_names])
                cell_content.append(Paragraph(tags_text, tag_style))
            
            # Создаём ячейку с рамкой
            cell_frame = Table([[cell_content]], colWidths=[cell_width])
            cell_frame.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            row.append(cell_frame)
            
            # Если строка заполнена или это последний элемент
            if len(row) == columns or i == len(badges) - 1:
                while len(row) < columns:
                    empty_cell = Table([[""]], colWidths=[cell_width])
                    empty_cell.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
                    ]))
                    row.append(empty_cell)
                table_data.append(row)
                row = []
        
        # Создаём основную таблицу
        if table_data:
            col_widths = [cell_width] * columns
            main_table = Table(table_data, colWidths=col_widths)
            main_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(main_table)
        
        # Сборка PDF
        pdf_path = os.path.join(temp_images_dir, "output.pdf")
        doc.build(story)
        
        # Копируем в папку uploads
        pdf_filename = f"export_{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
        final_path = os.path.join(config.settings.UPLOAD_DIR, pdf_filename)
        shutil.copy2(pdf_path, final_path)
        
        return {"file_url": f"/uploads/{pdf_filename}"}
    
    finally:
        # Очищаем временную папку
        try:
            shutil.rmtree(temp_images_dir)
        except Exception as e:
            print(f"Error cleaning temp dir: {e}")