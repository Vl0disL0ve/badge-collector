@echo off
title Badge Collector - Backend
echo ========================================
echo   Запуск бэкенда (FastAPI)
echo ========================================
echo.

cd ..\backend
echo Запуск сервера...
uvicorn app.main:app --reload --port 8000

pause