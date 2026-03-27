@echo off
chcp 65001 >nul
title Badge Collector - Установка зависимостей
color 0A

echo ================================================
echo        Альбом коллекционера - Установка
echo ================================================
echo.

echo [1/2] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не установлен!
    echo.
    echo Установите Python 3.10 или выше с официального сайта:
    echo https://www.python.org/downloads/
    echo.
    echo Важно: При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
python --version
echo.

echo [2/2] Установка пакетов (может занять 2-5 минут)...
echo.

echo Установка основных пакетов...
pip install fastapi uvicorn sqlalchemy python-jose[cryptography] passlib[bcrypt] python-multipart pillow python-dotenv requests -q

echo Установка ML-пакетов (OpenCV, rembg)...
pip install opencv-python rembg numpy -q

echo Установка пакетов для Telegram бота...
pip install python-telegram-bot httpx -q

echo.
echo ================================================
echo   Установка завершена!
echo   Запустите run.bat для старта сервера
echo ================================================
pause