@echo off
chcp 65001 >nul
title Badge Collector - Запуск сервера
color 0A

echo ================================================
echo        Альбом коллекционера - Запуск
echo ================================================
echo.

echo [1/2] Проверка базы данных...
cd backend
if not exist "badge_collector.db" (
    echo База данных не найдена. Создаю новую...
    python database\init_db.py
    echo.
) else (
    echo База данных найдена.
    echo.
)

echo [2/2] Запуск сервера...
echo.
echo ================================================
echo   Сервер запускается на http://localhost:8000
echo   Откройте в браузере: http://localhost:8000/html/login.html
echo ================================================
echo.
echo   Для остановки сервера нажмите Ctrl+C
echo.

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause