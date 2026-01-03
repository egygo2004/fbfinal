@echo off
setlocal enabledelayedexpansion
title FB OTP Local - VPN Edition
color 0b

echo ======================================================
echo       Facebook OTP Local Automation (VPN)
echo ======================================================
echo.

:: Note: Make sure to run this script as Administrator for OpenVPN to work properly.
echo.

:: Start OpenVPN Interactive Service for proper route handling
echo Starting OpenVPN Service...
net start OpenVPNServiceInteractive >nul 2>&1
if !errorLevel! == 0 (
    echo [OK] OpenVPN Interactive Service started
) else (
    echo [INFO] OpenVPN Service already running or not available
)
echo.
if not exist "config.env" (
    echo.
    echo -- Configuration Setup --
    set /p TG_TOKEN="Enter Telegram Bot Token: "
    set /p TG_CHAT_ID="Enter Telegram Chat ID: "
    echo TELEGRAM_TOKEN=!TG_TOKEN!> config.env
    echo TELEGRAM_CHAT_ID=!TG_CHAT_ID!>> config.env
    echo [OK] config.env created.
)

:: Load environment variables
for /f "tokens=1,2 delims==" %%a in (config.env) do (
    set %%a=%%b
)

:: Options
echo.
echo Select Mode:
echo [1] Headless Mode (Hidden Browser - Faster)
echo [2] Visible Mode (See what's happening - Testing)
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
    echo Running: python fb_otp_local.py !phone! %VISIBLE_ARG%
    python -u fb_otp_local.py !phone! %VISIBLE_ARG%
) else (
    if not exist "numbers.txt" (
        echo [ERROR] numbers.txt not found! Create it with one number per line.
    ) else (
        echo Running: python fb_otp_local.py numbers.txt %VISIBLE_ARG%
        python -u fb_otp_local.py numbers.txt %VISIBLE_ARG%
    )
)

if !errorLevel! neq 0 (
    echo.
    echo [ERROR] The script encountered an error (Code: !errorLevel!)
    pause
)

echo.
echo Done processing.
pause
