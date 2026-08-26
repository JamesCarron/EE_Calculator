@echo off
rem EE Calculator launcher: rebuild the page when pixi is available, then open it.
cd /d "%~dp0"
where pixi >nul 2>nul
if %errorlevel%==0 (
    pixi run build
) else (
    echo pixi not found - opening the committed page without rebuilding.
)
start "" "%~dp0EE_Calculator.html"
