from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("📁 Моя коллекция", callback_data="menu_collection")],
        [InlineKeyboardButton("👤 Профиль", callback_data="menu_profile")],
        [InlineKeyboardButton("➕ Добавить значок", callback_data="menu_add_badge")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_to_main():
    """Кнопка возврата в главное меню"""
    keyboard = [[InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]]
    return InlineKeyboardMarkup(keyboard)

def back_button(callback_data="menu_main"):
    """Кнопка назад"""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)

def cancel_button():
    """Кнопка отмены"""
    keyboard = [[InlineKeyboardButton("❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

def categories_list(categories, page=0, items_per_page=5):
    """Список категорий с пагинацией"""
    start = page * items_per_page
    end = start + items_per_page
    current_cats = categories[start:end]
    
    keyboard = []
    for cat in current_cats:
        keyboard.append([InlineKeyboardButton(
            f"📁 {cat['name']} ({cat.get('sets_count', 0)})",
            callback_data=f"cat_{cat['id']}"
        )])
    
    # Пагинация
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("◀️", callback_data=f"cat_page_{page-1}"))
    if end < len(categories):
        pagination.append(InlineKeyboardButton("▶️", callback_data=f"cat_page_{page+1}"))
    if pagination:
        keyboard.append(pagination)
    
    keyboard.append([InlineKeyboardButton("➕ Создать категорию", callback_data="cat_create")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def sets_list(sets, page=0, items_per_page=5):
    """Список наборов с пагинацией"""
    start = page * items_per_page
    end = start + items_per_page
    current_sets = sets[start:end]
    
    keyboard = []
    for s in current_sets:
        percent = s.get('completion_percent', 0)
        keyboard.append([InlineKeyboardButton(
            f"📦 {s['name']} ({s['collected_count']}/{s['total_count']} - {percent:.0f}%)",
            callback_data=f"set_{s['id']}"
        )])
    
    # Пагинация
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("◀️", callback_data=f"set_page_{page-1}"))
    if end < len(sets):
        pagination.append(InlineKeyboardButton("▶️", callback_data=f"set_page_{page+1}"))
    if pagination:
        keyboard.append(pagination)
    
    keyboard.append([InlineKeyboardButton("➕ Создать набор", callback_data="set_create")])
    keyboard.append([InlineKeyboardButton("◀️ Назад к категориям", callback_data="back_to_categories")])
    
    return InlineKeyboardMarkup(keyboard)

def set_actions(set_id, set_name):
    """Действия с набором"""
    keyboard = [
        [InlineKeyboardButton("🏷️ Посмотреть значки", callback_data=f"set_badges_{set_id}")],
        [InlineKeyboardButton("✏️ Редактировать набор", callback_data=f"set_edit_{set_id}")],
        [InlineKeyboardButton("🗑️ Удалить набор", callback_data=f"set_delete_{set_id}")],
        [InlineKeyboardButton("➕ Добавить значок", callback_data=f"set_add_badge_{set_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_sets")],
    ]
    return InlineKeyboardMarkup(keyboard)

def badges_list(badges, page=0, items_per_page=5):
    """Список значков"""
    start = page * items_per_page
    end = start + items_per_page
    current_badges = badges[start:end]
    
    keyboard = []
    for b in current_badges:
        keyboard.append([InlineKeyboardButton(
            f"🏷️ {b['name']}",
            callback_data=f"badge_{b['id']}"
        )])
    
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("◀️", callback_data=f"badge_page_{page-1}"))
    if end < len(badges):
        pagination.append(InlineKeyboardButton("▶️", callback_data=f"badge_page_{page+1}"))
    if pagination:
        keyboard.append(pagination)
    
    keyboard.append([InlineKeyboardButton("➕ Добавить значок", callback_data=f"add_badge_to_set")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_set")])
    
    return InlineKeyboardMarkup(keyboard)

def badge_actions(badge_id):
    """Действия со значком"""
    keyboard = [
        [InlineKeyboardButton("✏️ Редактировать", callback_data=f"badge_edit_{badge_id}")],
        [InlineKeyboardButton("🗑️ Удалить", callback_data=f"badge_delete_{badge_id}")],
        [InlineKeyboardButton("📸 Фотографии", callback_data=f"badge_photos_{badge_id}")],
        [InlineKeyboardButton("🔄 Переместить в набор", callback_data=f"badge_move_{badge_id}")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_badges")],
    ]
    return InlineKeyboardMarkup(keyboard)

def badge_photos(photos, badge_id):
    """Список фото значка"""
    keyboard = []
    for p in photos:
        main_mark = "⭐ " if p['is_main'] else ""
        keyboard.append([InlineKeyboardButton(
            f"{main_mark}Фото {p['id']}",
            callback_data=f"photo_{badge_id}_{p['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton("➕ Добавить фото", callback_data=f"add_photo_{badge_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"back_to_badge_{badge_id}")])
    
    return InlineKeyboardMarkup(keyboard)

def photo_actions(badge_id, photo_id, is_main):
    """Действия с фото"""
    keyboard = []
    if not is_main:
        keyboard.append([InlineKeyboardButton("⭐ Сделать главным", callback_data=f"photo_main_{badge_id}_{photo_id}")])
    keyboard.append([InlineKeyboardButton("🗑️ Удалить", callback_data=f"photo_delete_{badge_id}_{photo_id}")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"badge_photos_{badge_id}")])
    
    return InlineKeyboardMarkup(keyboard)

def condition_buttons():
    """Кнопки выбора состояния"""
    keyboard = [
        [InlineKeyboardButton("Отличное", callback_data="cond_excellent")],
        [InlineKeyboardButton("Хорошее", callback_data="cond_good")],
        [InlineKeyboardButton("Среднее", callback_data="cond_average")],
        [InlineKeyboardButton("Плохое", callback_data="cond_poor")],
        [InlineKeyboardButton("Пропустить", callback_data="cond_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)

def profile_menu(is_admin=False):
    """Меню профиля"""
    keyboard = [
        [InlineKeyboardButton("📊 Статистика", callback_data="profile_stats")],
        [InlineKeyboardButton("🔗 Привязать Telegram", callback_data="profile_link")],
        [InlineKeyboardButton("📤 Экспорт коллекции", callback_data="profile_export")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("👑 Админ-панель", callback_data="admin_panel")])
    keyboard.append([InlineKeyboardButton("🚪 Выйти из аккаунта", callback_data="profile_logout")])
    keyboard.append([InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)

def export_sets(sets):
    """Выбор набора для экспорта"""
    keyboard = []
    for s in sets:
        keyboard.append([InlineKeyboardButton(
            f"📦 {s['name']}",
            callback_data=f"export_set_{s['id']}"
        )])
    keyboard.append([InlineKeyboardButton("📤 Все значки", callback_data="export_all")])
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_profile")])
    
    return InlineKeyboardMarkup(keyboard)

def admin_panel():
    """Админ-панель меню"""
    keyboard = [
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("➕ Добавить пользователя", callback_data="admin_add_user")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_profile")],
    ]
    return InlineKeyboardMarkup(keyboard)