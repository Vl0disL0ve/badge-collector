@echo off
chcp 65001 >nul
title Badge Collector - Запуск сервера
color 0A

echo ================================================
echo        Альбом коллекционера - Запуск
echo ================================================
echo.

echo [1/3] Проверка базы данных...
cd backend
if not exist "badge_collector.db" (
    echo База данных не найдена. Создаю новую...
    python database\init_db.py
    echo.
) else (
    echo База данных найдена.
    echo.
)

echo [2/3] Проверка таблиц...
python -c "from app.models import Base; from app.core.database import engine; Base.metadata.create_all(bind=engine); print('✅ Таблицы созданы')"
echo.

echo [3/3] Запуск сервера...
echo.
echo ================================================
echo   🌐 Сервер:      http://localhost:8000
echo   📚 API Docs:    http://localhost:8000/docs
echo   🔑 Логин:       http://localhost:8000/html/auth/login.html
echo   📁 Каталог:     http://localhost:8000/html/collection/index.html
echo   📡 API Base:    http://localhost:8000/api
echo ================================================
echo.
echo   Для остановки сервера нажмите Ctrl+C
echo.

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause