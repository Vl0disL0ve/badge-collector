from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ..keyboards.inline import (
    badges_list, badge_actions, badge_photos, photo_actions,
    condition_buttons, cancel_button, back_button
)
from ..utils.api import (
    get_badges, get_badge, create_badge, update_badge, delete_badge,
    add_photo, delete_photo, make_main_photo, get_tags
)
import io
import json

# Состояния для создания значка
BADGE_NAME = 1
BADGE_DESC = 2
BADGE_YEAR = 3
BADGE_MATERIAL = 4
BADGE_CONDITION = 5
BADGE_TAGS = 6
BADGE_PHOTOS = 7

# Состояния для редактирования
EDIT_CHOICE = 10
EDIT_NAME = 11
EDIT_DESC = 12
EDIT_YEAR = 13
EDIT_MATERIAL = 14
EDIT_CONDITION = 15
EDIT_TAGS = 16

async def show_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список значков в наборе"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    set_id = context.user_data.get('selected_set_id')
    set_name = context.user_data.get('selected_set_name', 'Набор')
    
    if not token:
        await query.edit_message_text("❌ Сессия истекла.")
        return
    
    try:
        result = await get_badges(token, set_id=set_id, limit=50)
        badges = result.get('items', [])
        context.user_data['badges'] = badges
        context.user_data['badges_page'] = 0
        
        if not badges:
            await query.edit_message_text(
                f"📭 *В наборе \"{set_name}\" пока нет значков*\n\n"
                f"Добавьте первый значок, нажав кнопку ниже.",
                parse_mode="Markdown",
                reply_markup=back_button("back_to_set")
            )
        else:
            await query.edit_message_text(
                f"🏷️ *Значки в наборе \"{set_name}\"* ({len(badges)})\n\n"
                f"Выберите значок для просмотра:",
                parse_mode="Markdown",
                reply_markup=badges_list(badges, 0)
            )
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def badges_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пагинация значков"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split("_")[-1])
    context.user_data['badges_page'] = page
    
    badges = context.user_data.get('badges', [])
    await query.edit_message_reply_markup(
        reply_markup=badges_list(badges, page)
    )

async def badge_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор значка для просмотра"""
    query = update.callback_query
    await query.answer()
    
    badge_id = int(query.data.split("_")[1])
    context.user_data['selected_badge_id'] = badge_id
    
    token = context.user_data.get('token')
    
    try:
        badge = await get_badge(token, badge_id)
        context.user_data['selected_badge'] = badge
        
        condition_map = {
            'excellent': '⭐ Отличное',
            'good': '👍 Хорошее',
            'average': '👌 Среднее',
            'poor': '⚠️ Плохое'
        }
        
        condition_text = condition_map.get(badge.get('condition'), 'Не указано')
        tags_text = ', '.join(badge.get('tags', [])) if badge.get('tags') else 'Нет'
        
        # Формируем сообщение
        message = (
            f"🏷️ *{badge['name']}*\n\n"
            f"📝 *Описание:* {badge.get('description', '—')}\n"
            f"📅 *Год:* {badge.get('year', '—')}\n"
            f"🔩 *Материал:* {badge.get('material', '—')}\n"
            f"⭐ *Состояние:* {condition_text}\n"
            f"🏷️ *Теги:* {tags_text}\n"
            f"📸 *Фото:* {len(badge.get('photos', []))} шт.\n"
            f"📅 *Добавлен:* {badge.get('created_at', '—')[:10]}"
        )
        
        # Отправляем фото если есть
        main_photo = badge.get('main_photo_url')
        if main_photo:
            photo_url = f"http://localhost:8000{main_photo}"
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=badge_actions(badge_id)
            )
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=photo_url
            )
        else:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=badge_actions(badge_id)
            )
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def badge_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание значка"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['new_badge'] = {}
    context.user_data['new_badge_photos'] = []
    
    await query.edit_message_text(
        "📝 *Добавление нового значка*\n\n"
        "Введите название значка (до 200 символов):",
        parse_mode="Markdown",
        reply_markup=cancel_button()
    )
    return BADGE_NAME

async def badge_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название значка"""
    name = update.message.text.strip()
    
    if len(name) > 200:
        await update.message.reply_text(
            "❌ Название слишком длинное (макс. 200 символов).\nПопробуйте еще раз:",
            reply_markup=cancel_button()
        )
        return BADGE_NAME
    
    context.user_data['new_badge']['name'] = name
    
    await update.message.reply_text(
        "📝 Введите описание значка (или /skip чтобы пропустить):",
        reply_markup=cancel_button()
    )
    return BADGE_DESC

async def badge_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание значка"""
    text = update.message.text.strip()
    
    if text == "/skip":
        description = None
    else:
        description = text
    
    context.user_data['new_badge']['description'] = description
    
    await update.message.reply_text(
        "📅 Введите год выпуска (4 цифры, или /skip):",
        reply_markup=cancel_button()
    )
    return BADGE_YEAR

async def badge_year_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить год"""
    text = update.message.text.strip()
    
    if text == "/skip":
        year = None
    else:
        try:
            year = int(text)
            if year < 1800 or year > 2026:
                raise ValueError
        except:
            await update.message.reply_text(
                "❌ Введите корректный год (1800-2026) или /skip:",
                reply_markup=cancel_button()
            )
            return BADGE_YEAR
    
    context.user_data['new_badge']['year'] = year
    
    await update.message.reply_text(
        "🔩 Введите материал (или /skip):",
        reply_markup=cancel_button()
    )
    return BADGE_MATERIAL

async def badge_material_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить материал"""
    text = update.message.text.strip()
    
    if text == "/skip":
        material = None
    else:
        material = text
    
    context.user_data['new_badge']['material'] = material
    
    await update.message.reply_text(
        "⭐ Выберите состояние:",
        reply_markup=condition_buttons()
    )
    return BADGE_CONDITION

async def badge_condition_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить состояние"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cond_skip":
        condition = None
    else:
        condition = query.data.replace("cond_", "")
    
    context.user_data['new_badge']['condition'] = condition
    
    await query.edit_message_text(
        "🏷️ Введите теги через запятую (например: спорт, олимпиада)\n"
        "Или /skip чтобы пропустить:",
        reply_markup=cancel_button()
    )
    return BADGE_TAGS

async def badge_tags_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить теги"""
    text = update.message.text.strip()
    
    if text == "/skip":
        tags = []
    else:
        tags = [t.strip() for t in text.split(',') if t.strip()]
    
    context.user_data['new_badge']['tags'] = json.dumps(tags)
    
    await update.message.reply_text(
        "📸 Отправьте фотографии значка (JPEG/PNG, до 5 шт, мин. 500×500px)\n"
        "После каждой фотографии нажмите /next для продолжения или /done когда закончите:\n\n"
        "Первое фото станет главным.",
        reply_markup=cancel_button()
    )
    return BADGE_PHOTOS

async def badge_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить фото значка"""
    if update.message.photo:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()
        
        context.user_data['new_badge_photos'].append(('photo.jpg', io.BytesIO(file_bytes), 'image/jpeg'))
        
        await update.message.reply_text(
            f"✅ Фото {len(context.user_data['new_badge_photos'])}/5 добавлено.\n"
            "Отправьте следующее фото, или /done для завершения:"
        )
        return BADGE_PHOTOS
    
    return BADGE_PHOTOS

async def badge_photos_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить добавление фото и создать значок"""
    token = context.user_data.get('token')
    set_id = context.user_data.get('selected_set_id')
    badge_data = context.user_data.get('new_badge', {})
    photos = context.user_data.get('new_badge_photos', [])
    
    if not photos:
        await update.message.reply_text(
            "❌ Нужно добавить хотя бы одно фото.\n"
            "Отправьте фото или /cancel для отмены:"
        )
        return BADGE_PHOTOS
    
    # Подготавливаем form data
    form_data = {
        'name': badge_data.get('name'),
        'set_id': str(set_id),
    }
    
    if badge_data.get('description'):
        form_data['description'] = badge_data['description']
    if badge_data.get('year'):
        form_data['year'] = str(badge_data['year'])
    if badge_data.get('material'):
        form_data['material'] = badge_data['material']
    if badge_data.get('condition'):
        form_data['condition'] = badge_data['condition']
    if badge_data.get('tags'):
        form_data['tags'] = badge_data['tags']
    
    # Подготавливаем файлы
    files = {}
    for i, photo_data in enumerate(photos):
        files[f'photos'] = photo_data
    
    await update.message.reply_text("⏳ Создание значка...")
    
    try:
        result = await create_badge(token, form_data, files)
        
        await update.message.reply_text(
            f"✅ *Значок \"{badge_data['name']}\" добавлен!*",
            parse_mode="Markdown"
        )
        
        # Обновляем список значков
        badges_result = await get_badges(token, set_id=set_id, limit=50)
        context.user_data['badges'] = badges_result.get('items', [])
        
        from .start import show_menu
        await show_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def badge_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить значок"""
    query = update.callback_query
    await query.answer()
    
    badge_id = context.user_data.get('selected_badge_id')
    token = context.user_data.get('token')
    set_id = context.user_data.get('selected_set_id')
    
    try:
        await delete_badge(token, badge_id)
        
        await query.edit_message_text(
            "✅ *Значок удален!*",
            parse_mode="Markdown",
            reply_markup=back_button("back_to_badges")
        )
        
        # Обновляем список значков
        badges_result = await get_badges(token, set_id=set_id, limit=50)
        context.user_data['badges'] = badges_result.get('items', [])
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def badge_photos_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать все фото значка"""
    query = update.callback_query
    await query.answer()
    
    badge = context.user_data.get('selected_badge', {})
    photos = badge.get('photos', [])
    
    if not photos:
        await query.edit_message_text(
            "📷 У этого значка нет фотографий.",
            reply_markup=back_button(f"back_to_badge_{badge.get('id')}")
        )
        return
    
    context.user_data['current_photos'] = photos
    
    await query.edit_message_text(
        f"📸 *Фотографии значка* ({len(photos)} шт.)\n\n"
        f"Выберите фото для управления:",
        parse_mode="Markdown",
        reply_markup=badge_photos(photos, badge.get('id'))
    )

async def photo_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор фото для действий"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    badge_id = int(parts[1])
    photo_id = int(parts[2])
    
    photos = context.user_data.get('current_photos', [])
    photo = next((p for p in photos if p['id'] == photo_id), None)
    
    if photo:
        context.user_data['selected_photo_id'] = photo_id
        is_main = photo.get('is_main', False)
        
        await query.edit_message_text(
            f"🖼️ *Фото #{photo_id}*\n\n"
            f"Статус: {'⭐ Главное' if is_main else '📷 Обычное'}",
            parse_mode="Markdown",
            reply_markup=photo_actions(badge_id, photo_id, is_main)
        )

async def photo_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сделать фото главным"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    badge_id = int(parts[2])
    photo_id = int(parts[3])
    token = context.user_data.get('token')
    
    try:
        await make_main_photo(token, badge_id, photo_id)
        
        await query.edit_message_text(
            "✅ *Фото установлено как главное!*",
            parse_mode="Markdown"
        )
        
        # Обновляем данные значка
        badge = await get_badge(token, badge_id)
        context.user_data['selected_badge'] = badge
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def photo_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить фото"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    badge_id = int(parts[2])
    photo_id = int(parts[3])
    token = context.user_data.get('token')
    
    try:
        await delete_photo(token, badge_id, photo_id)
        
        await query.edit_message_text(
            "✅ *Фото удалено!*",
            parse_mode="Markdown"
        )
        
        # Обновляем данные значка
        badge = await get_badge(token, badge_id)
        context.user_data['selected_badge'] = badge
        
        photos = badge.get('photos', [])
        context.user_data['current_photos'] = photos
        
        if photos:
            await query.edit_message_text(
                f"📸 *Фотографии значка* ({len(photos)} шт.)",
                parse_mode="Markdown",
                reply_markup=badge_photos(photos, badge_id)
            )
        else:
            await query.edit_message_text(
                "📷 У значка больше нет фотографий.",
                reply_markup=back_button(f"back_to_badge_{badge_id}")
            )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def add_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить новое фото к значку"""
    query = update.callback_query
    await query.answer()
    
    badge_id = int(query.data.split("_")[-1])
    context.user_data['add_photo_badge_id'] = badge_id
    
    await query.edit_message_text(
        "📸 Отправьте фото для добавления (JPEG/PNG, до 10 МБ, мин. 500×500px):",
        reply_markup=cancel_button()
    )
    return BADGE_PHOTOS  # Используем то же состояние

async def add_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка добавления фото"""
    if update.message.photo:
        badge_id = context.user_data.get('add_photo_badge_id')
        token = context.user_data.get('token')
        
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()
        
        try:
            result = await add_photo(
                token, badge_id,
                ('photo.jpg', io.BytesIO(file_bytes), 'image/jpeg')
            )
            
            await update.message.reply_text("✅ Фото добавлено!")
            
            # Обновляем данные значка
            badge = await get_badge(token, badge_id)
            context.user_data['selected_badge'] = badge
            
            from .start import show_menu
            await show_menu(update, context)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END