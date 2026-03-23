# Альбом коллекционера

> Автоматизированная система учета коллекций значков

## 📋 Документация

| Документ | Ссылка |
|----------|--------|
| Техническое задание | [docs/technical-specification/README.md](docs/technical-specification/README.md) |
| Диаграмма классов | [docs/diagrams/class/class-diagram.drawio](docs/diagrams/class/class-diagram.drawio) |
| Диаграмма прецедентов | [docs/diagrams/use-case/use-case.puml](docs/diagrams/use-case/use-case.puml) |
| Диаграмма БД | [docs/diagrams/database/database-diagram.puml](docs/diagrams/database/database-diagram.puml) |
| Диаграмма компонентов | [docs/diagrams/component/component-diagram.puml](docs/diagrams/component/component-diagram.puml) |
| Архитектура решений | [docs/diagrams/solution-architecture/solution-architecture.puml](docs/diagrams/solution-architecture/solution-architecture.puml) |

---

## 🚀 Реализованный функционал

### Бэкенд (FastAPI)
- ✅ Аутентификация (регистрация, логин, JWT-токены)
- ✅ Управление категориями (CRUD)
- ✅ Управление наборами (CRUD)
- ✅ Управление значками (CRUD с валидацией)
- ✅ Загрузка фотографий (JPEG/PNG, ≤10MB, ≥500×500px)
- ✅ Поиск по названию
- ✅ Фильтрация по категории, набору, состоянию
- ✅ Экспорт коллекции в JPEG (1200px, 4 колонки)
- ✅ Привязка Telegram-аккаунта через код

### Фронтенд (HTML/CSS/JS)
- ✅ Страницы: вход, регистрация, коллекция, добавление значка, детальный просмотр
- ✅ Фильтры и поиск в реальном времени
- ✅ Загрузка фото через форму
- ✅ Кнопка экспорта коллекции

### Telegram-бот (python-telegram-bot)
- ✅ Команды: `/start`, `/link`, `/add`, `/list`, `/badge`, `/find`, `/filter`, `/export`, `/help`
- ✅ Пошаговое добавление значка (ConversationHandler)
- ✅ Привязка аккаунта через 6-значный код
- ✅ Интеграция с бэкендом через REST API

### База данных (SQLite)
- ✅ Таблицы: `users`, `categories`, `sets`, `badges`, `photos`, `badge_sets`, `admin_logs`, `user_visits`

---

## ⚠️ Не реализовано / Требует доработки

| Функция | Статус | Причина |
|---------|--------|---------|
| Множественные фото (до 5 шт) | 🟡 Частично | API готов, фронтенд ожидает доработки |
| Редактирование фото (поворот/кадрирование) | 🟡 Частично | API готов, фронтенд в разработке |
| Админ-панель | 🔴 Не реализовано | Низкий приоритет для MVP |
| Redis-очередь ML-операций | 🔴 Не реализовано | Запланировано на следующий этап |
| Подтверждение email | 🟡 Заглушка | Реализовано на уровне модели, требует интеграции |
| PostgreSQL вместо SQLite | 🟡 Заглушка | Используется SQLite для упрощения разработки |

---

## 🛠️ Запуск проекта

### Требования
- Python 3.10+
- Git (опционально)

### Установка зависимостей
```bash
install_dependencies.bat
```

### Запуск
```bash
start_all.bat
```

### После запуска:
- Бэкенд API: http://localhost:8000/docs
- Фронтенд: http://localhost:8000/static/login.html
- Telegram-бот: запущен в отдельном окне
