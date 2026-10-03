@echo off
setlocal
cd /d "%~dp0\.."

if not exist ".venv-packaging\Scripts\python.exe" (
    py -3 -m venv .venv-packaging
    if errorlevel 1 goto :failed
)

set "BUILD_PYTHON=%CD%\.venv-packaging\Scripts\python.exe"
"%BUILD_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :failed
"%BUILD_PYTHON%" -m pip install -e ".[packaging]"
if errorlevel 1 goto :failed
"%BUILD_PYTHON%" -m PyInstaller --noconfirm --clean --distpath "dist\windows-x64" --workpath "build\pyinstaller-windows-x64" build\banking-support-evaluation.spec
if errorlevel 1 goto :failed

echo Built Windows executable: dist\windows-x64\BankingSupportEvaluation.exe
pause
exit /b 0

:failed
echo Build failed. Check that Python 3.11 or newer is installed and available as "py".
pause
exit /b 1