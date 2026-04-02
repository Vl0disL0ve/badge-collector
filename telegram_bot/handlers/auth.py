from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards.inline import main_menu, back_to_main, cancel_button
from ..utils.api import generate_link_code, get_user_token, get_profile

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /link - генерация кода привязки"""
    telegram_id = update.effective_user.id
    
    # Проверяем, не привязан ли уже
    token = get_user_token(telegram_id)
    if token:
        await update.message.reply_text(
            "✅ *Ваш аккаунт уже привязан!*\n\n"
            "Вы можете управлять коллекцией через главное меню.",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        return
    
    try:
        # Генерируем код (нужен временный токен для неавторизованного запроса)
        # Для генерации кода не нужна авторизация
        import requests
        from ..config import API_BASE_URL
        
        response = requests.post(f"{API_BASE_URL}/telegram/generate-code")
        if response.status_code == 200:
            data = response.json()
            code = data['code']
            
            await update.message.reply_text(
                f"🔐 *Привязка аккаунта*\n\n"
                f"Ваш код: `{code}`\n\n"
                f"1. Зайдите на сайт: http://localhost:8000/html/profile.html\n"
                f"2. В разделе 'Привязка Telegram' введите этот код\n"
                f"3. После подтверждения вы сможете управлять коллекцией через бота\n\n"
                f"⏰ Код действителен 15 минут.",
                parse_mode="Markdown",
                reply_markup=cancel_button()
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка генерации кода. Попробуйте позже."
            )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}\n\n"
            f"Убедитесь, что бэкенд запущен на http://localhost:8000"
        )

async def link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callback после ввода кода на сайте"""
    query = update.callback_query
    await query.answer()
    
    telegram_id = update.effective_user.id
    
    # Проверяем привязку
    token = get_user_token(telegram_id)
    if token:
        context.user_data['token'] = token
        try:
            profile = get_profile(token)
            context.user_data['user_id'] = profile['id']
            context.user_data['is_admin'] = profile.get('is_admin', False)
            
            await query.edit_message_text(
                f"✅ *Аккаунт успешно привязан!*\n\n"
                f"Email: `{profile['email']}`\n\n"
                f"Теперь вы можете управлять коллекцией через бота.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        except Exception as e:
            await query.edit_message_text(
                f"❌ Ошибка получения профиля: {str(e)}"
            )
    else:
        await query.edit_message_text(
            "❌ Привязка не найдена.\n\n"
            "Используйте /link для генерации нового кода."
        )