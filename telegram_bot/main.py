import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from .config import TOKEN, PROXY_URL
from .handlers import start, auth, categories, sets, badges, profile, admin
from .states.badge_states import (
    BADGE_NAME, BADGE_DESC, BADGE_YEAR, BADGE_MATERIAL,
    BADGE_CONDITION, BADGE_TAGS, BADGE_PHOTOS,
    EDIT_CHOICE, EDIT_NAME, EDIT_DESC, EDIT_YEAR, EDIT_MATERIAL, EDIT_CONDITION, EDIT_TAGS
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Настройка прокси
    if PROXY_URL:
        request = HTTPXRequest(proxy_url=PROXY_URL)
        app = Application.builder().token(TOKEN).request(request).build()
        print(f"🔧 Используется прокси: {PROXY_URL}")
    else:
        app = Application.builder().token(TOKEN).build()
    
    # ========== COMMAND HANDLERS ==========
    app.add_handler(CommandHandler("start", start.start))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("link", auth.link))
    
    # ========== CALLBACK HANDLERS ==========
    # Главное меню
    app.add_handler(CallbackQueryHandler(start.show_menu, pattern="^menu_"))
    
    # Категории
    app.add_handler(CallbackQueryHandler(categories.show_categories, pattern="^menu_collection$"))
    app.add_handler(CallbackQueryHandler(categories.categories_page_callback, pattern="^cat_page_"))
    app.add_handler(CallbackQueryHandler(categories.category_select_callback, pattern="^cat_\\d+$"))
    app.add_handler(CallbackQueryHandler(categories.category_create_start, pattern="^cat_create$"))
    app.add_handler(CallbackQueryHandler(categories.category_delete_callback, pattern="^cat_delete_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^back_to_categories$"))
    
    # Наборы
    app.add_handler(CallbackQueryHandler(sets.sets_page_callback, pattern="^set_page_"))
    app.add_handler(CallbackQueryHandler(sets.set_select_callback, pattern="^set_\\d+$"))
    app.add_handler(CallbackQueryHandler(sets.set_create_start, pattern="^set_create$"))
    app.add_handler(CallbackQueryHandler(sets.set_delete_callback, pattern="^set_delete_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^back_to_sets$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^back_to_set$"))
    
    # Значки
    app.add_handler(CallbackQueryHandler(badges.show_badges, pattern="^set_badges_"))
    app.add_handler(CallbackQueryHandler(badges.badges_page_callback, pattern="^badge_page_"))
    app.add_handler(CallbackQueryHandler(badges.badge_select_callback, pattern="^badge_\\d+$"))
    app.add_handler(CallbackQueryHandler(badges.badge_delete_callback, pattern="^badge_delete_"))
    app.add_handler(CallbackQueryHandler(badges.badge_photos_callback, pattern="^badge_photos_"))
    app.add_handler(CallbackQueryHandler(badges.photo_select_callback, pattern="^photo_\\d+_\\d+$"))
    app.add_handler(CallbackQueryHandler(badges.photo_main_callback, pattern="^photo_main_"))
    app.add_handler(CallbackQueryHandler(badges.photo_delete_callback, pattern="^photo_delete_"))
    app.add_handler(CallbackQueryHandler(badges.add_photo_callback, pattern="^add_photo_"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^back_to_badges$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: None, pattern="^back_to_badge_"))
    app.add_handler(CallbackQueryHandler(badges.badge_add_start, pattern="^menu_add_badge$"))
    app.add_handler(CallbackQueryHandler(badges.badge_add_start, pattern="^set_add_badge_"))
    app.add_handler(CallbackQueryHandler(badges.badge_add_start, pattern="^add_badge_to_set$"))
    
    # Профиль
    app.add_handler(CallbackQueryHandler(profile.show_profile, pattern="^menu_profile$"))
    app.add_handler(CallbackQueryHandler(profile.profile_stats, pattern="^profile_stats$"))
    app.add_handler(CallbackQueryHandler(profile.profile_export, pattern="^profile_export$"))
    app.add_handler(CallbackQueryHandler(profile.export_set_callback, pattern="^export_"))
    app.add_handler(CallbackQueryHandler(profile.profile_logout, pattern="^profile_logout$"))
    
    # Админ
    app.add_handler(CallbackQueryHandler(admin.show_admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin.admin_stats, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin.admin_users, pattern="^admin_users$"))
    
    # Общие
    app.add_handler(CallbackQueryHandler(auth.link_callback, pattern="^link_confirm$"))
    
    # ========== CONVERSATION HANDLERS ==========
    
    # Создание категории
    cat_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(categories.category_create_start, pattern="^cat_create$")],
        states={
            categories.CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, categories.category_name_input)],
            categories.CAT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, categories.category_desc_input)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: None)],
    )
    app.add_handler(cat_conv)
    
    # Создание набора
    set_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(sets.set_create_start, pattern="^set_create$")],
        states={
            sets.SET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sets.set_name_input)],
            sets.SET_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, sets.set_desc_input)],
            sets.SET_TOTAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sets.set_total_input)],
            sets.SET_PHOTO: [
                MessageHandler(filters.PHOTO, sets.set_photo_input),
                CommandHandler("skip", sets.set_skip_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: None)],
    )
    app.add_handler(set_conv)
    
    # Создание значка
    badge_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(badges.badge_add_start, pattern="^menu_add_badge$"),
            CallbackQueryHandler(badges.badge_add_start, pattern="^set_add_badge_"),
            CallbackQueryHandler(badges.badge_add_start, pattern="^add_badge_to_set$"),
        ],
        states={
            BADGE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges.badge_name_input)],
            BADGE_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges.badge_desc_input)],
            BADGE_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges.badge_year_input)],
            BADGE_MATERIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges.badge_material_input)],
            BADGE_CONDITION: [CallbackQueryHandler(badges.badge_condition_callback)],
            BADGE_TAGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, badges.badge_tags_input)],
            BADGE_PHOTOS: [
                MessageHandler(filters.PHOTO, badges.badge_photo_input),
                CommandHandler("done", badges.badge_photos_done),
            ],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: None)],
    )
    app.add_handler(badge_conv)
    
    # Добавление фото
    add_photo_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(badges.add_photo_callback, pattern="^add_photo_")],
        states={
            BADGE_PHOTOS: [MessageHandler(filters.PHOTO, badges.add_photo_input)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: None)],
    )
    app.add_handler(add_photo_conv)
    
    # Добавление пользователя (админ)
    add_user_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin.admin_add_user_start, pattern="^admin_add_user$")],
        states={
            admin.ADD_USER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.admin_add_user_email)],
            admin.ADD_USER_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin.admin_add_user_pass)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: None)],
    )
    app.add_handler(add_user_conv)
    
    print("🤖 Telegram-бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()