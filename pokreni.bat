@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
    goto done
)

where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
    goto done
)

echo Greska: Python 3 nije instaliran ili nije u PATH-u.
pause
exit /b 1

:done
if errorlevel 1 pause
