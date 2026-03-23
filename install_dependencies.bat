@echo off
title Установка зависимостей
echo ========================================
echo   Установка зависимостей проекта
echo ========================================
echo.

pip install -r config/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo ✅ Зависимости установлены!
echo.
pause