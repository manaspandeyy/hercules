@echo off
REM ============================================================
REM  Hercules - Daily Tracker
REM  Double-click to launch. First run sets up a local virtual
REM  environment and installs dependencies automatically.
REM ============================================================

cd /d "%~dp0"

cls
echo.
echo     ==================================================
echo.
echo              H  E  R  C  U  L  E  S
echo.
echo            [ Daily Tracker - your day, measured ]
echo.
echo     ==================================================
echo.

if not exist ".venv\Scripts\pythonw.exe" (
    echo  Setting up for the first time. This only happens once...
    echo.
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo  ERROR: Python was not found. Install Python 3.10+ from python.org
        echo  and make sure "Add Python to PATH" is checked.
        echo.
        pause
        exit /b 1
    )
    call ".venv\Scripts\python.exe" -m pip install --upgrade pip
    call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo  ERROR: Failed to install dependencies. See messages above.
        echo.
        pause
        exit /b 1
    )
    REM Generate the app icon up front so the window + shortcut have it.
    call ".venv\Scripts\python.exe" -c "import icon; icon.ensure_icon()"
)

REM Create a desktop shortcut with the app icon on first run.
if not exist "%USERPROFILE%\Desktop\Hercules.lnk" (
    powershell -NoProfile -Command ^
      "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Hercules.lnk');" ^
      "$s.TargetPath='%~f0';" ^
      "$s.WorkingDirectory='%~dp0';" ^
      "$s.IconLocation='%~dp0data\app_icon.ico';" ^
      "$s.Description='Hercules Daily Tracker';" ^
      "$s.Save()" >nul 2>&1
)

REM Launch with pythonw so no terminal window lingers behind the app.
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0
