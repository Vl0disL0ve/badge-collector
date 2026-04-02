@echo off
chcp 65001 >nul
title Badge Collector - Управление администраторами
color 0A

echo ================================================
echo        Управление администраторами
echo ================================================
echo.

cd /d "%~dp0backend"

if "%1"=="" goto :menu
if "%1"=="-l" goto :list
goto :direct

:menu
echo Выберите действие:
echo.
echo 1. Назначить администратора
echo 2. Снять права администратора
echo 3. Показать всех администраторов
echo 4. Сделать первого пользователя админом
echo.
set /p choice="Ваш выбор (1-4): "

if "%choice%"=="1" goto :add
if "%choice%"=="2" goto :remove
if "%choice%"=="3" goto :list
if "%choice%"=="4" goto :make_first
goto :end

:add
echo.
set /p email="Введите email пользователя: "
if "%email%"=="" (
    echo Ошибка: Email не может быть пустым
    goto :end
)
python manage_admins.py "%email%" --add
goto :end

:remove
echo.
set /p email="Введите email пользователя: "
if "%email%"=="" (
    echo Ошибка: Email не может быть пустым
    goto :end
)
python manage_admins.py "%email%" --remove
goto :end

:list
python manage_admins.py --list
goto :end

:make_first
python manage_admins.py --make-first-admin
goto :end

:direct
python manage_admins.py %*
goto :end

:end
echo.
pause
cd /d "%~dp0"