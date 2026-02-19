@echo off
title Mhantappu Saga Server Launcher
color 0A

echo ================================================
echo   MHANTAPPU SAGA PRIVATE SERVER LAUNCHER
echo ================================================
echo.
echo All rights reserved by Ninja Sage. 
echo Play ninja sage at https://ninjasage.id
echo.
echo [INFO] Make sure XAMPP Apache and MySQL are running!
echo [INFO] Check XAMPP Control Panel first.
echo.
pause

echo.
echo [1/2] Starting Laravel Server...
start "Laravel Server" cmd /k "cd /d D:\xampp\htdocs\amf && echo [LARAVEL] Starting on http://127.0.0.1:8000 && php artisan serve"

echo [*] Waiting 8 seconds for Laravel to initialize...
timeout /t 8 /nobreak >nul

echo.
echo [2/2] Starting Cloudflare Tunnel...
echo [*] Please wait, extracting tunnel URL...

REM Create temp batch to capture cloudflared output
echo @echo off > temp_tunnel.bat
echo cd /d D:\xampp\htdocs\amf >> temp_tunnel.bat
echo cloudflared.exe tunnel --url http://localhost:8000 ^> tunnel_output.txt 2^>^&1 >> temp_tunnel.bat

start "Cloudflare Tunnel" cmd /k "temp_tunnel.bat"

echo [*] Waiting 15 seconds for tunnel to establish...
timeout /t 15 /nobreak >nul

REM Extract URL from output
if exist "D:\xampp\htdocs\amf\tunnel_output.txt" (
    for /f "tokens=*" %%i in ('findstr "trycloudflare.com" "D:\xampp\htdocs\amf\tunnel_output.txt"') do (
        set "line=%%i"
        for /f "tokens=*" %%j in ('echo %%i ^| findstr "https://"') do (
            for /f "tokens=2 delims= " %%k in ("%%j") do (
                set "tunnel_url=%%k"
            )
        )
    )
)

echo.
echo ================================================
echo [SUCCESS] Mhantappu Saga Server started!
echo ================================================
echo.

if defined tunnel_url (
    echo [TUNNEL URLs] Copy these URLs:
    echo.
    echo 1. Main URL:
    echo %tunnel_url%
    echo.
    echo 2. Gateway URL ^(for game client^):
    echo %tunnel_url%/gateway.php
    echo.
    echo ================================================
    echo.
    
    REM Save URLs to file for easy copy
    echo %tunnel_url% > tunnel_urls.txt
    echo %tunnel_url%/gateway.php >> tunnel_urls.txt
    echo URLs saved to tunnel_urls.txt
) else (
    echo [WARNING] Could not auto-detect tunnel URL
    echo Check the "Cloudflare Tunnel" window manually
    echo Look for: https://random-word-1234.trycloudflare.com
)

echo.
echo Share the Gateway URL to your players!
echo.
echo To stop server: Close both terminal windows or run stop_server.bat
echo ================================================

REM Cleanup temp files
if exist temp_tunnel.bat del temp_tunnel.bat

pause

