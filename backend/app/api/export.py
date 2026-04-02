from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import os
import uuid
import shutil
import tempfile
from PIL import Image
from datetime import datetime
from ..core import config, database, security
from ..models import User, Badge, Photo, Set, Tag, BadgeTag
from ..schemas import ExportResponse

router = APIRouter()


@router.get("/export", response_model=ExportResponse)
def export_collection(
    set_id: Optional[int] = None,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(security.get_current_user)
):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    if set_id:
        badges = db.query(Badge).filter(
            Badge.user_id == current_user.id,
            Badge.set_id == set_id
        ).all()
        set_item = db.query(Set).filter(Set.id == set_id).first()
        title = f"Набор: {set_item.name}" if set_item else "Экспорт"
    else:
        badges = db.query(Badge).filter(Badge.user_id == current_user.id).all()
        title = "Моя коллекция"
    
    if not badges:
        raise HTTPException(404, "Нет значков для экспорта")
    
    try:
        pdfmetrics.registerFont(TTFont('Arial', 'C:\\Windows\\Fonts\\arial.ttf'))
        font_name = 'Arial'
    except:
        font_name = 'Helvetica'
    
    temp_dir = tempfile.gettempdir()
    pdf_filename = f"export_{current_user.id}_{uuid.uuid4().hex[:8]}.pdf"
    pdf_path = os.path.join(temp_dir, pdf_filename)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(A4),
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=font_name, fontSize=24, alignment=1, spaceAfter=20)
    subtitle_style = ParagraphStyle('CustomSubtitle', parent=styles['Normal'], fontName=font_name, fontSize=12, alignment=1, spaceAfter=30)
    badge_name_style = ParagraphStyle('BadgeName', parent=styles['Normal'], fontName=font_name, fontSize=10, alignment=0, spaceAfter=5, leading=12)
    desc_style = ParagraphStyle('DescStyle', parent=styles['Normal'], fontName=font_name, fontSize=9, alignment=0, leading=11)
    
    elements = []
    elements.append(Paragraph(f"📛 {title}", title_style))
    elements.append(Paragraph(f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 10*mm))
    
    for badge in badges:
        main_photo = db.query(Photo).filter(Photo.badge_id == badge.id, Photo.is_main == True).first()
        tags = db.query(Tag).join(BadgeTag).filter(BadgeTag.badge_id == badge.id).all()
        tag_names = [t.name for t in tags[:3]]
        
        table_data = []
        
        if main_photo and os.path.exists(main_photo.file_path):
            try:
                with Image.open(main_photo.file_path) as img:
                    img.thumbnail((200, 200))
                    temp_img = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                    img.save(temp_img.name, 'JPEG', quality=85)
                    pdf_img = RLImage(temp_img.name, width=50*mm, height=50*mm)
                    photo_cell = pdf_img
            except:
                photo_cell = Paragraph("Нет фото", badge_name_style)
        else:
            photo_cell = Paragraph("Нет фото", badge_name_style)
        
        info_lines = [f"<b>{badge.name}</b>"]
        if badge.description:
            info_lines.append(f"<i>{badge.description}</i>")
        if badge.year:
            info_lines.append(f"Год: {badge.year}")
        if badge.material:
            info_lines.append(f"Материал: {badge.material}")
        if badge.condition:
            cond_map = {'excellent': 'Отличное', 'good': 'Хорошее', 'average': 'Среднее', 'poor': 'Плохое'}
            info_lines.append(f"Состояние: {cond_map.get(badge.condition.value, badge.condition.value)}")
        if tag_names:
            info_lines.append(f"Теги: {', '.join(tag_names)}")
        
        desc_cell = Paragraph("<br/>".join(info_lines), desc_style)
        
        table_data.append([photo_cell, desc_cell])
        
        badge_table = Table(table_data, colWidths=[60*mm, 100*mm])
        badge_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 1, colors.lightgrey),
        ]))
        
        elements.append(badge_table)
        elements.append(Spacer(1, 5*mm))
    
    doc.build(elements)
    
    final_path = os.path.join(config.settings.UPLOAD_DIR, pdf_filename)
    shutil.move(pdf_path, final_path)
    
    return {"file_url": f"/uploads/{pdf_filename}"}