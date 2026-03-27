from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from ..keyboards.inline import admin_panel, back_button
from ..utils.api import get_admin_stats, get_admin_users, create_admin_user, delete_admin_user

# Состояния для добавления пользователя
ADD_USER_EMAIL = 1
ADD_USER_PASS = 2

async def show_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать админ-панель"""
    query = update.callback_query
    await query.answer()
    
    is_admin = context.user_data.get('is_admin', False)
    
    if not is_admin:
        await query.edit_message_text(
            "⛔ У вас нет прав администратора.",
            reply_markup=back_button("menu_profile")
        )
        return
    
    await query.edit_message_text(
        "👑 *Административная панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=admin_panel()
    )

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    
    try:
        stats = await get_admin_stats(token)
        
        message = (
            f"📊 *Статистика системы*\n\n"
            f"👥 *Пользователи:* {stats['total_users']}\n"
            f"🏷️ *Значки:* {stats['total_badges']}\n"
            f"📦 *Наборы:* {stats['total_sets']}\n"
            f"📁 *Категории:* {stats['total_categories']}\n\n"
            f"📈 *Регистрации за последние 7 дней:*\n"
        )
        
        for reg in stats.get('registrations', []):
            message += f"  • {reg['date']}: {reg['count']} новых\n"
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=back_button("admin_panel")
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список пользователей"""
    query = update.callback_query
    await query.answer()
    
    token = context.user_data.get('token')
    
    try:
        users = await get_admin_users(token)
        context.user_data['admin_users'] = users
        
        if not users:
            await query.edit_message_text(
                "📭 Пользователи не найдены.",
                reply_markup=back_button("admin_panel")
            )
            return
        
        message = "👥 *Список пользователей*\n\n"
        for u in users[:10]:  # Показываем первых 10
            admin_mark = "👑 " if u.get('is_admin') else ""
            message += f"• {admin_mark}{u['email']} (ID: {u['id']})\n"
            if u.get('telegram_id'):
                message += f"  🔗 Telegram: {u['telegram_id']}\n"
        
        if len(users) > 10:
            message += f"\n*Всего: {len(users)} пользователей*"
        
        await query.edit_message_text(
            message,
            parse_mode="Markdown",
            reply_markup=back_button("admin_panel")
        )
        
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")

async def admin_add_user_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать добавление пользователя"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "➕ *Добавление пользователя*\n\n"
        "Введите email нового пользователя:",
        parse_mode="Markdown",
        reply_markup=back_button("admin_panel")
    )
    return ADD_USER_EMAIL

async def admin_add_user_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить email пользователя"""
    email = update.message.text.strip()
    context.user_data['new_user_email'] = email
    
    await update.message.reply_text(
        "🔒 Введите пароль (минимум 6 символов):"
    )
    return ADD_USER_PASS

async def admin_add_user_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получить пароль и создать пользователя"""
    password = update.message.text.strip()
    email = context.user_data.get('new_user_email')
    token = context.user_data.get('token')
    
    if len(password) < 6:
        await update.message.reply_text(
            "❌ Пароль должен быть минимум 6 символов.\nПопробуйте еще раз:"
        )
        return ADD_USER_PASS
    
    try:
        result = await create_admin_user(token, email, password)
        
        await update.message.reply_text(
            f"✅ Пользователь {email} создан!",
            reply_markup=back_button("admin_panel")
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    return ConversationHandler.END