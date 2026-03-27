from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ..keyboards.inline import (
    categories_list, back_to_main, cancel_button, back_button
)
from ..utils.api import get_categories, create_category, delete_category

# Состояния для создания категории
CAT_NAME = 1
CAT_DESC = 2

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список категорий"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    if not token:
        await query.edit_message_text(
            "❌ Сессия истекла. Используйте /link для повторной привязки."
        )
        return
    
    try:
        categories = await get_categories(token)
        context.user_data['categories'] = categories
        context.user_data['categories_page'] = 0
        
        if not categories:
            await query.edit_message_text(
                "📭 *У вас пока нет категорий*\n\n"
                "Создайте первую категорию, нажав кнопку ниже.",
                parse_mode="Markdown",
                reply_markup=categories_list([], 0)
            )
        else:
            await query.edit_message_text(
                f"📁 *Мои категории* ({len(categories)})\n\n"
                f"Выберите категорию для просмотра наборов:",
                parse_mode="Markdown",
                reply_markup=categories_list(categories, 0)
            )
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка загрузки категорий: {str(e)}"
        )

async def categories_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пагинация категорий"""
    query = update.callback_query
    await query.answer()
    
    page = int(query.data.split("_")[-1])
    context.user_data['categories_page'] = page
    
    categories = context.user_data.get('categories', [])
    await query.edit_message_reply_markup(
        reply_markup=categories_list(categories, page)
    )

async def category_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор категории - переходим к наборам"""
    query = update.callback_query
    await query.answer()
    
    category_id = int(query.data.split("_")[1])
    context.user_data['selected_category_id'] = category_id
    
    # Находим название категории
    categories = context.user_data.get('categories', [])
    category_name = next((c['name'] for c in categories if c['id'] == category_id), "Категория")
    context.user_data['selected_category_name'] = category_name
    
    # Переходим к списку наборов
    from .sets import show_sets
    await show_sets(update, context)

async def category_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать создание категории"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📝 *Создание новой категории*\n\n"
        "Введите название категории (до 100 символов):",
        parse_mode="Markdown",
        reply_markup=cancel_button()
    )
    return CAT_NAME

async def category_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить название категории"""
    name = update.message.text.strip()
    
    if len(name) > 100:
        await update.message.reply_text(
            "❌ Название слишком длинное (макс. 100 символов).\n"
            "Попробуйте еще раз:",
            reply_markup=cancel_button()
        )
        return CAT_NAME
    
    context.user_data['new_category_name'] = name
    
    await update.message.reply_text(
        "📝 Введите описание категории (или /skip чтобы пропустить):",
        reply_markup=cancel_button()
    )
    return CAT_DESC

async def category_desc_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить описание категории"""
    text = update.message.text.strip()
    
    if text == "/skip":
        description = None
    else:
        description = text
    
    token = context.user_data.get('token')
    name = context.user_data.get('new_category_name')
    
    try:
        await create_category(token, name, description)
        
        await update.message.reply_text(
            f"✅ *Категория \"{name}\" создана!*",
            parse_mode="Markdown"
        )
        
        # Обновляем список категорий
        categories = await get_categories(token)
        context.user_data['categories'] = categories
        
        from .start import show_menu
        await show_menu(update, context)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка создания категории: {str(e)}"
        )
    
    return ConversationHandler.END

async def category_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить категорию"""
    query = update.callback_query
    await query.answer()
    
    # Получаем ID категории из callback_data (ожидаем формат "cat_delete_{id}")
    # Пока не реализовано, добавим кнопку удаления в список категорий позже
    
    await query.edit_message_text(
        "⚠️ *Удаление категории*\n\n"
        "Эта функция будет доступна в следующей версии.",
        parse_mode="Markdown",
        reply_markup=back_button("back_to_categories")
    )