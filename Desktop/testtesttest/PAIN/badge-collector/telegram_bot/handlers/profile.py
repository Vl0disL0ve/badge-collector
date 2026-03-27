from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards.inline import profile_menu, export_sets, back_to_main, back_button, cancel_button
from ..utils.api import get_profile, get_categories, get_sets, get_badges, get_tags, export_collection

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать профиль пользователя"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    is_admin = context.user_data.get('is_admin', False)
    
    try:
        profile = await get_profile(token)
        categories = await get_categories(token)
        sets = await get_sets(token)
        badges_result = await get_badges(token, limit=1000)
        tags = await get_tags(token)
        
        total_badges = badges_result.get('total', 0)
        
        message = (
            f"👤 *Профиль*\n\n"
            f"📧 *Email:* {profile['email']}\n"
            f"🔗 *Telegram ID:* {profile.get('telegram_id', 'Не привязан')}\n"
            f"📅 *Зарегистрирован:* {profile['created_at'][:10]}\n\n"
            f"📊 *Статистика коллекции:*\n"
            f"📁 Категорий: {len(categories)}\n"
            f"📦 Наборов: {len(sets)}\n"
            f"🏷️ Значков: {total_badges}\n"
            f"🔖 Тегов: {len(tags)}"
        )
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=profile_menu(is_admin)
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def profile_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать расширенную статистику"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    
    try:
        categories = await get_categories(token)
        sets = await get_sets(token)
        badges_result = await get_badges(token, limit=1000)
        tags = await get_tags(token)
        
        total_badges = badges_result.get('total', 0)
        
        # Считаем по наборам
        sets_stats = []
        for s in sets:
            sets_stats.append(f"  • {s['name']}: {s['collected_count']}/{s['total_count']} ({s['completion_percent']:.0f}%)")
        
        sets_text = '\n'.join(sets_stats) if sets_stats else "  Нет наборов"
        
        message = (
            f"📊 *Детальная статистика*\n\n"
            f"📁 *Категории:* {len(categories)}\n"
            f"📦 *Наборы:* {len(sets)}\n"
            f"🏷️ *Значки:* {total_badges}\n"
            f"🔖 *Теги:* {len(tags)}\n\n"
            f"📦 *Прогресс по наборам:*\n{sets_text}"
        )
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=back_button("menu_profile")
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def profile_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт коллекции - выбор набора"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    
    try:
        sets = await get_sets(token)
        context.user_data['export_sets'] = sets
        
        if not sets:
            await query.edit_message_text(
                "📭 У вас пока нет наборов для экспорта.",
                reply_markup=back_button("menu_profile")
            )
        else:
            await query.edit_message_text(
                "📤 *Экспорт коллекции*\n\n"
                "Выберите набор для экспорта:",
                parse_mode="Markdown",
                reply_markup=export_sets(sets)
            )
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def export_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Экспорт выбранного набора"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    
    if query.data == "export_all":
        set_id = None
        set_name = "всех значков"
    else:
        set_id = int(query.data.split("_")[-1])
        sets = context.user_data.get('export_sets', [])
        set_name = next((s['name'] for s in sets if s['id'] == set_id), "набора")
    
    try:
        await query.edit_message_text(
            f"⏳ Генерация экспорта для {set_name}...\n\n"
            f"Пожалуйста, подождите."
        )
        
        result = await export_collection(token, set_id)
        
        if result.get('file_url'):
            file_url = f"http://localhost:8000{result['file_url']}"
            
            await query.edit_message_text(
                f"✅ *Экспорт готов!*\n\n"
                f"[📥 Скачать файл]({file_url})",
                parse_mode="Markdown",
                reply_markup=back_button("menu_profile")
            )
        else:
            await query.edit_message_text(
                "❌ Ошибка экспорта",
                reply_markup=back_button("menu_profile")
            )
            
    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=back_button("menu_profile")
        )

async def profile_logout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выйти из аккаунта"""
    query = update.callback_query
    await query.answer()
    
    context.user_data.clear()
    
    await query.edit_message_text(
        "🚪 *Вы вышли из аккаунта*\n\n"
        "Для повторного входа используйте /link",
        parse_mode="Markdown",
        reply_markup=back_to_main()
    )