@echo off
title Stop Mhantappu Saga Server
color 0C

echo ================================================
echo   STOPPING MHANTAPPU SAGA PRIVATE SERVER
echo ================================================
echo.
echo All rights reserved by Ninja Sage.
echo Play ninja sage at https://ninjasage.id
echo.

echo Stopping servers...

REM Kill Laravel (php.exe dari artisan serve)
taskkill /F /IM php.exe >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Laravel server stopped
) else (
    echo ⚠️  Laravel server was not running
)

REM Kill Cloudflare Tunnel
taskkill /F /IM cloudflared.exe >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Cloudflare tunnel stopped
) else (
    echo ⚠️  Cloudflare tunnel was not running
)

REM Cleanup tunnel files
if exist "D:\xampp\htdocs\amf\tunnel_output.txt" del "D:\xampp\htdocs\amf\tunnel_output.txt"
if exist "D:\xampp\htdocs\amf\tunnel_urls.txt" del "D:\xampp\htdocs\amf\tunnel_urls.txt"
if exist "D:\xampp\htdocs\amf\temp_tunnel.bat" del "D:\xampp\htdocs\amf\temp_tunnel.bat"

echo ✅ Cleanup completed

echo.
echo [SUCCESS] Mhantappu Saga server stopped!
echo.
echo Note: XAMPP Apache and MySQL still running
echo Stop them manually in XAMPP Control Panel if needed
echo.
echo Thank you for playing Mhantappu Saga!
echo ================================================
pause

