import os
import logging
import requests
import secrets
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes, ConversationHandler

# Загружаем .env из папки config
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'config', '.env'))

# Конфигурация
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = "http://localhost:8000/api"

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env файле")

# Состояния для ConversationHandler
PHOTO, CATEGORY, SET, NAME, DESCRIPTION, YEAR, MATERIAL, CONDITION = range(8)

logging.basicConfig(level=logging.INFO)

# Временное хранилище для сессий пользователей
user_sessions = {}

def get_headers(telegram_id):
    return {}

# ========== КОМАНДЫ ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Альбом коллекционера*\n\n"
        "Я помогу тебе управлять коллекцией значков.\n\n"
        "📌 *Команды:*\n"
        "/link - привязать Telegram к сайту\n"
        "/add - добавить значок\n"
        "/list - мои значки\n"
        "/badge <id> - посмотреть значок\n"
        "/find <текст> - поиск\n"
        "/filter - фильтрация\n"
        "/export - экспорт коллекции\n"
        "/help - помощь",
        parse_mode="Markdown"
    )

async def link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    try:
        response = requests.post(f"{API_BASE_URL}/telegram/generate-code", headers=get_headers(telegram_id))
        if response.status_code == 200:
            data = response.json()
            code = data['code']
            await update.message.reply_text(
                f"🔐 *Привязка аккаунта*\n\n"
                f"Ваш код: `{code}`\n\n"
                f"Введите этот код на сайте в разделе профиля.\n"
                f"Код действителен 15 минут.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Сначала авторизуйтесь на сайте")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['telegram_id'] = update.effective_user.id
    await update.message.reply_text(
        "📸 *Добавление значка*\n\n"
        "Отправьте фото значка (JPEG или PNG, не менее 500×500px)",
        parse_mode="Markdown"
    )
    return PHOTO

async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    
    context.user_data['photo_file_id'] = photo.file_id
    context.user_data['photo_unique_id'] = photo.file_unique_id
    
    await update.message.reply_text("✏️ Введите название значка:")
    return NAME

async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "📝 Введите описание (или /skip)",
        parse_mode="Markdown"
    )
    return DESCRIPTION

async def add_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "/skip":
        context.user_data['description'] = update.message.text
    else:
        context.user_data['description'] = ""
    
    await update.message.reply_text("📅 Введите год выпуска (или /skip)")
    return YEAR

async def add_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "/skip":
        try:
            context.user_data['year'] = int(update.message.text)
        except:
            await update.message.reply_text("❌ Введите число или /skip")
            return YEAR
    else:
        context.user_data['year'] = None
    
    await update.message.reply_text("🔩 Введите материал (или /skip)")
    return MATERIAL

async def add_material(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text != "/skip":
        context.user_data['material'] = update.message.text
    else:
        context.user_data['material'] = ""
    
    keyboard = [
        [InlineKeyboardButton("Отличное", callback_data="excellent")],
        [InlineKeyboardButton("Хорошее", callback_data="good")],
        [InlineKeyboardButton("Среднее", callback_data="average")],
        [InlineKeyboardButton("Плохое", callback_data="poor")],
        [InlineKeyboardButton("Пропустить", callback_data="skip")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⭐ Выберите состояние:", reply_markup=reply_markup)
    return CONDITION

async def add_condition_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data != "skip":
        context.user_data['condition'] = query.data
    else:
        context.user_data['condition'] = None
    
    try:
        response = requests.get(f"{API_BASE_URL}/categories", headers=get_headers(context.user_data['telegram_id']))
        categories = response.json() if response.status_code == 200 else []
    except:
        categories = []
    
    if categories:
        keyboard = []
        for cat in categories[:10]:
            keyboard.append([InlineKeyboardButton(cat['name'], callback_data=f"cat_{cat['id']}")])
        keyboard.append([InlineKeyboardButton("Без категории", callback_data="cat_0")])
        
        await query.edit_message_text(
            "📂 Выберите категорию:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return CATEGORY
    else:
        context.user_data['category_id'] = None
        await finish_badge(query, context)
        return ConversationHandler.END

async def add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data != "cat_0":
        category_id = int(query.data.split("_")[1])
        context.user_data['category_id'] = category_id
    else:
        context.user_data['category_id'] = None
    
    try:
        response = requests.get(f"{API_BASE_URL}/sets", headers=get_headers(context.user_data['telegram_id']))
        sets = response.json() if response.status_code == 200 else []
    except:
        sets = []
    
    if sets:
        keyboard = []
        for s in sets[:10]:
            keyboard.append([InlineKeyboardButton(s['name'], callback_data=f"set_{s['id']}")])
        keyboard.append([InlineKeyboardButton("Без набора", callback_data="set_0")])
        
        await query.edit_message_text(
            "📦 Выберите набор:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SET
    else:
        context.user_data['set_id'] = None
        await finish_badge(query, context)
        return ConversationHandler.END

async def add_set_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data != "set_0":
        set_id = int(query.data.split("_")[1])
        context.user_data['set_id'] = set_id
    else:
        context.user_data['set_id'] = None
    
    await finish_badge(query, context)
    return ConversationHandler.END

async def finish_badge(update, context):
    # TODO: реальная отправка фото на бэкенд
    await update.edit_message_text(
        "✅ *Значок добавлен!*\n\n"
        f"Название: {context.user_data.get('name')}\n"
        f"Категория: {context.user_data.get('category_id')}\n"
        f"Набор: {context.user_data.get('set_id')}",
        parse_mode="Markdown"
    )
    context.user_data.clear()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Добавление отменено")
    context.user_data.clear()
    return ConversationHandler.END

async def list_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 *Мои значки*\n\n"
        "Функция в разработке.",
        parse_mode="Markdown"
    )

async def badge_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите ID: /badge 1")
        return
    
    badge_id = args[0]
    await update.message.reply_text(f"🏷 *Значок #{badge_id}*\n\nФункция в разработке.", parse_mode="Markdown")

async def find_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("❌ Укажите текст для поиска: /find текст")
        return
    
    query = " ".join(args)
    await update.message.reply_text(f"🔍 Поиск: {query}\n\nФункция в разработке.")

async def filter_badges(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔎 *Фильтр*\n\n"
        "Выберите параметр:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("По категории", callback_data="filter_category")],
            [InlineKeyboardButton("По набору", callback_data="filter_set")],
            [InlineKeyboardButton("По состоянию", callback_data="filter_condition")]
        ])
    )

async def filter_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"🔎 Фильтр: {query.data}\n\nФункция в разработке.")

async def export_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 *Экспорт коллекции*\n\nФункция в разработке.", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *Помощь*\n\n"
        "/start - главное меню\n"
        "/link - привязать Telegram к сайту\n"
        "/add - добавить значок\n"
        "/list - список значков\n"
        "/badge <id> - посмотреть значок\n"
        "/find <текст> - поиск\n"
        "/filter - фильтрация\n"
        "/export - экспорт коллекции\n"
        "/help - это сообщение",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, add_photo)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_description)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_year)],
            MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_material)],
            CONDITION: [CallbackQueryHandler(add_condition_callback)],
            CATEGORY: [CallbackQueryHandler(add_category_callback)],
            SET: [CallbackQueryHandler(add_set_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("link", link))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("list", list_badges))
    app.add_handler(CommandHandler("badge", badge_detail))
    app.add_handler(CommandHandler("find", find_badges))
    app.add_handler(CommandHandler("filter", filter_badges))
    app.add_handler(CommandHandler("export", export_collection))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(filter_callback, pattern="filter_"))
    
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()