from telegram import Update
from telegram.ext import ContextTypes
from ..keyboards.inline import main_menu, back_to_main

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    telegram_id = user.id
    
    # Проверяем, привязан ли пользователь
    token = context.user_data.get('token')
    
    if token:
        try:
            from ..utils.api import get_profile
            profile = get_profile(token)
            context.user_data['user_id'] = profile['id']
            context.user_data['is_admin'] = profile.get('is_admin', False)
            
            await update.message.reply_text(
                f"🎉 *С возвращением, {user.first_name}!*\n\n"
                f"Ваш аккаунт привязан к сайту.\n"
                f"Ваш email: `{profile['email']}`\n\n"
                f"Я помогу управлять вашей коллекцией значков.",
                parse_mode="Markdown",
                reply_markup=main_menu()
            )
        except Exception as e:
            await update.message.reply_text(
                f"⚠️ Ошибка при получении профиля. Возможно, сессия устарела.\n"
                f"Используйте /link для повторной привязки."
            )
    else:
        await update.message.reply_text(
            f"👋 *Привет, {user.first_name}!*\n\n"
            f"Я бот для управления коллекцией значков.\n\n"
            f"🔗 *Для начала работы привяжите аккаунт:*\n"
            f"1. Зарегистрируйтесь на сайте: http://localhost:8000/html/register.html\n"
            f"2. Используйте команду /link для генерации кода привязки\n"
            f"3. Введите код в разделе профиля на сайте\n\n"
            f"📌 *Команды:*\n"
            f"/start - это меню\n"
            f"/link - привязать Telegram к сайту\n"
            f"/help - помощь",
            parse_mode="Markdown",
            reply_markup=back_to_main()
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📚 *Помощь по боту*\n\n"
        "🔐 *Авторизация:*\n"
        "/link - сгенерировать код для привязки аккаунта\n\n"
        "📁 *Коллекция:*\n"
        "Главное меню → Моя коллекция\n"
        "Просмотр категорий, наборов и значков\n\n"
        "➕ *Добавление:*\n"
        "Главное меню → Добавить значок\n"
        "Или в наборе → Добавить значок\n\n"
        "✏️ *Редактирование:*\n"
        "В карточке значка → Редактировать\n\n"
        "👤 *Профиль:*\n"
        "Главное меню → Профиль\n"
        "Статистика, привязка Telegram, экспорт\n\n"
        "❓ *Дополнительно:*\n"
        "/cancel - отменить текущее действие",
        parse_mode="Markdown"
    )

async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать главное меню (для callback)"""
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text(
            "🏠 *Главное меню*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
    else:
        await update.message.reply_text(
            "🏠 *Главное меню*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )