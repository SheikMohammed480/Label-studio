@echo off
title Zlendo Studio Services

echo ========================================================
echo Starting Zlendo Studio Services
echo   [1/3] Backend (Django)    - Port 4464
echo   [2/3] Frontend (React UI) - Port 4467
echo   [3/3] ML Backend (YOLO)   - Port 4466
echo ========================================================
echo.

echo [1/3] Starting Backend (Django) - Port 4464...
start "Zlendo Studio Backend - 4464" cmd /k "cd /d C:\Zlendo-studio\label-studio\label_studio && call C:\Zlendo-studio\venv\Scripts\activate.bat && python manage.py runserver 0.0.0.0:4464"

echo [2/3] Starting Frontend (React UI) - Port 4467...
start "Zlendo Studio Frontend - 4467" cmd /k "cd /d C:\Zlendo-studio\label-studio\web && npm run dev"

echo [3/3] Starting ML Backend (YOLO) - Port 4466...
start "Zlendo Studio ML Backend - 4466" cmd /k "cd /d C:\Zlendo-studio\label-studio-ml-backend\label-studio-ml-backend && call C:\Zlendo-studio\venv\Scripts\activate.bat && label-studio-ml start my_ml_backend -p 4466"

echo.
echo All 3 Zlendo Studio services launched!
echo   Frontend:    http://45.64.105.163:4467
echo   Backend:     http://45.64.105.163:4464
echo   ML Backend:  http://45.64.105.163:4466
echo.
pause
