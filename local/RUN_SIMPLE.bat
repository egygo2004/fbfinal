@echo off
setlocal enabledelayedexpansion
title FB OTP Simple (Manual VPN)
color 0b

echo ======================================================
echo       Facebook OTP Automation (Manual VPN)
echo ======================================================
echo.
echo IMPORTANT: Connect to VPN MANUALLY before running!
echo Use ProtonVPN app or OpenVPN GUI to connect first.
echo.
echo ======================================================

:: Load environment variables
if exist "config.env" (
    for /f "tokens=1,2 delims==" %%a in (config.env) do (
        set %%a=%%b
    )
)

:: Options
echo.
echo Select Mode:
echo [1] Headless Mode (Hidden Browser - Faster)
echo [2] Visible Mode (See what's happening)
echo.
set /p mode="Choice (1-2): "

set VISIBLE_ARG=
if "%mode%"=="2" set VISIBLE_ARG=--visible

echo.
echo [1] Process single number
echo [2] Process numbers.txt
echo.
set /p target_choice="Choice (1-2): "

:: Check if Python is installed
python --version >nul 2>&1
if !errorLevel! neq 0 (
    echo [ERROR] Python not found! Please install Python from python.org
    pause
    exit /b
)

if "%target_choice%"=="1" (
    set /p phone="Enter phone number (with +): "
    echo Running: python fb_otp_simple.py !phone! %VISIBLE_ARG%
    python -u fb_otp_simple.py !phone! %VISIBLE_ARG%
) else (
    if not exist "numbers.txt" (
        echo [ERROR] numbers.txt not found! Create it with one number per line.
    ) else (
        echo Running: python fb_otp_simple.py numbers.txt %VISIBLE_ARG%
        python -u fb_otp_simple.py numbers.txt %VISIBLE_ARG%
    )
)

echo.
echo Done processing.
pause
