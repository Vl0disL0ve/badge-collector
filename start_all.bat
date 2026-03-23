@echo off
title Badge Collector - Запуск всех сервисов
echo ========================================
echo   Запуск бэкенда и Telegram бота
echo ========================================
echo.

echo Запуск бэкенда в новом окне...
start cmd /k "cd backend && uvicorn app.main:app --reload --port 8000"

echo Запуск бота в новом окне...
start cmd /k "cd bot && python bot.py"

echo.
echo ✅ Все сервисы запущены!
echo.
echo 📱 Бэкенд: http://localhost:8000
echo 📱 API docs: http://localhost:8000/docs
echo 🤖 Telegram бот: запущен
echo.
echo Закрой окна, чтобы остановить сервисы.
pause