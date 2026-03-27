from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ..keyboards.inline import (
    sets_list, set_actions, back_to_main, cancel_button, back_button
)
from ..utils.api import get_sets, create_set, update_set, delete_set

# Состояния для создания набора
SET_NAME = 1
SET_DESC = 2
SET_TOTAL = 3
SET_PHOTO = 4

async def show_sets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список наборов в выбранной категории"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    category_id = context.user_data.get('selected_category_id')
    category_name = context.user_data.get('selected_category_name', 'Категория')
    
    if not token:
        await query.edit_message_text("❌ Сессия истекла.")
        return
    
    try:
        sets = await get_sets(token, category_id)
        context.user_data['sets'] = sets
        context.user_data['sets_page'] = 0
        
        if not sets:
            await query.edit_message_text(
                f"📭 *В категории \"{category_name}\" пока нет наборов*\n\n"
                f"Создайте первый набор, нажав кнопку ниже.",
                parse_mode="Markdown",
                reply_markup=back_button("back_to_categories")
            )
        else:
            await query.edit_message_text(
                f"📦 *Наборы в категории \"{category_name}\"* ({len(sets)})\n\n"
                f"Выберите набор для просмотра значков:",
                parse_mode="Markdown",
                reply_markup=sets_list(sets, 0)
            )
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def sets_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пагинация наборов"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split("_")[-1])
    context.user_data['sets_page'] = page
    
    sets = context.user_data.get('sets', [])
    await query.edit_message_reply_markup(
        reply_markup=sets_list(sets, page)
    )

async def set_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор набора"""
    query = update.callback_query
    await query.answer()
    
    set_id = int(query.data.split("_")[1])
    context.user_data['selected_set_id'] = set_id
    
    # Находим название набора
    sets = context.user_data.get('sets', [])
    set_name = next((s['name'] for s in sets if s['id'] == set_id), "Набор")
    
    await query.edit_message_text(
        f"📦 *{set_name}*\n\n"
        f"Собрано: {next((s['collected_count'] for s in sets if s['id'] == set_id), 0)} / {next((s['total_count'] for s in sets if s['id'] == set_id), 0)}\n"
        f"Прогресс: {next((s['completion_percent'] for s in sets if s['id'] == set_id), 0):.0f}%\n\n"
        f"Выберите действие:",
        parse_mode="Markdown",
        reply_markup=set_actions(set_id, set_name)
    )

async def set_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание набора"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *Создание нового набора*\n\n"
        "Введите название набора (до 150 символов):",
        parse_mode="Markdown",
        reply_markup=cancel_button()
    )
    return SET_NAME

async def set_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название набора"""
    name = update.message.text.strip()
    
    if len(name) > 150:
        await update.message.reply_text(
            "❌ Название слишком длинное (макс. 150 символов).\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_button()
        )
        return SET_NAME
    
    context.user_data['new_set_name'] = name
    
    await update.message.reply_text(
        "📝 Введите описание набора (или /skip чтобы пропустить):",
        reply_markup=cancel_button()
    )
    return SET_DESC

async def set_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание набора"""
    text = update.message.text.strip()
    
    if text == "/skip":
        description = None
    else:
        description = text
    
    context.user_data['new_set_description'] = description
    
    await update.message.reply_text(
        "🔢 Введите общее количество значков в наборе (целое число):",
        reply_markup=cancel_button()
    )
    return SET_TOTAL

async def set_total_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить количество значков"""
    try:
        total = int(update.message.text.strip())
        if total < 0:
            raise ValueError
    except:
        await update.message.reply_text(
            "❌ Введите целое положительное число:",
            reply_markup=cancel_button()
        )
        return SET_TOTAL
    
    context.user_data['new_set_total'] = total
    
    await update.message.reply_text(
        "📸 Отправьте фото набора (JPEG/PNG, до 10 МБ)\n"
        "Или нажмите /skip чтобы пропустить:",
        reply_markup=cancel_button()
    )
    return SET_PHOTO

async def set_photo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить фото набора"""
    token = context.user_data.get('token')
    category_id = context.user_data.get('selected_category_id')
    
    # Собираем данные
    from telegram import InputFile
    import io
    
    name = context.user_data.get('new_set_name')
    description = context.user_data.get('new_set_description')
    total = context.user_data.get('new_set_total')
    
    form_data = {
        'name': name,
        'description': description,
        'total_count': str(total),
        'category_id': str(category_id) if category_id else None
    }
    
    files = {}
    
    if update.message.photo:
        # Получаем фото
        photo = update.message.photo[-1]
        file = await photo.get_file()
        file_bytes = await file.download_as_bytearray()
        files['photo'] = ('photo.jpg', io.BytesIO(file_bytes), 'image/jpeg')
    
    try:
        await create_set(token, form_data, files)
        
        await update.message.reply_text(
            f"✅ *Набор \"{name}\" создан!*",
            parse_mode="Markdown"
        )
        
        # Обновляем список наборов
        sets = await get_sets(token, category_id)
        context.user_data['sets'] = sets
        
        # Показываем наборы
        from .start import show_menu
        await show_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END

async def set_skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропустить фото"""
    if update.message.text == "/skip":
        token = context.user_data.get('token')
        category_id = context.user_data.get('selected_category_id')
        
        name = context.user_data.get('new_set_name')
        description = context.user_data.get('new_set_description')
        total = context.user_data.get('new_set_total')
        
        form_data = {
            'name': name,
            'description': description,
            'total_count': str(total),
            'category_id': str(category_id) if category_id else None
        }
        
        try:
            await create_set(token, form_data, {})
            
            await update.message.reply_text(
                f"✅ *Набор \"{name}\" создан!*",
                parse_mode="Markdown"
            )
            
            sets = await get_sets(token, category_id)
            context.user_data['sets'] = sets
            
            from .start import show_menu
            await show_menu(update, context)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        
        return ConversationHandler.END
    
    return await set_photo_input(update, context)

async def set_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить набор"""
    query = update.callback_query
    await query.answer()
    
    set_id = context.user_data.get('selected_set_id')
    token = context.user_data.get('token')
    
    try:
        await delete_set(token, set_id)
        
        await query.edit_message_text(
            "✅ *Набор удален!*",
            parse_mode="Markdown",
            reply_markup=back_button("back_to_categories")
        )
        
        # Обновляем список наборов
        category_id = context.user_data.get('selected_category_id')
        sets = await get_sets(token, category_id)
        context.user_data['sets'] = sets
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")