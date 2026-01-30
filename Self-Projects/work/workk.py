@echo off
SETLOCAL

:: 1. Define local environment folder name
set VENV_DIR=%USERPROFILE%\.myapp_venv

:: 2. Check if the venv exists; if not, create and install requirements
if not exist "%VENV_DIR%" (
    echo Creating local environment...
    python -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate"
    echo Installing dependencies from shared drive...
    pip install -r "%~dp0requirements.txt"
) else (
    call "%VENV_DIR%\Scripts\activate"
)

:: 3. Run the script ( %~dp0 ensures it finds the script in the same folder as the .bat)
python "%~dp0my_script.py"

pause
