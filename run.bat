@echo off
setlocal
cd /d "%~dp0"

set "VENV_DIR=.venv"
set "PY=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"

if not exist "%PY%" (
  echo [setup] Creating venv...
  py -3 -m venv "%VENV_DIR%" || goto :fail
  "%PY%" -m pip install --upgrade pip || goto :fail
  if exist requirements.txt (
    echo [setup] Installing requirements...
    "%PIP%" install -r requirements.txt || goto :fail
  )
)

"%PY%" -m base_game.main
goto :eof

:fail
echo.
echo [ERROR] Setup or run failed. See messages above.
pause
endlocal
