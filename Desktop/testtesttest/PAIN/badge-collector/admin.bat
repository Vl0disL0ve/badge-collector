@echo off
chcp 65001 >nul
title Badge Collector - Управление администраторами
color 0A

echo ================================================
echo        Управление администраторами
echo ================================================
echo.

cd backend

if "%1"=="" goto :menu
if "%1"=="-l" goto :list
goto :direct

:menu
echo Выберите действие:
echo.
echo 1. Назначить администратора
echo 2. Снять права администратора
echo 3. Показать всех администраторов
echo.
set /p choice="Ваш выбор (1-3): "

if "%choice%"=="1" goto :add
if "%choice%"=="2" goto :remove
if "%choice%"=="3" goto :list
goto :end

:add
echo.
set /p email="Введите email пользователя: "
python create_admin.py "%email%"
goto :end

:remove
echo.
set /p email="Введите email пользователя: "
python create_admin.py "%email%" -r
goto :end

:list
python create_admin.py -l
goto :end

:direct
python create_admin.py %*
goto :end

:end
echo.
pause
cd ..