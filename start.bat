@echo off
setlocal
echo.
echo ========================================
echo   NextRole AI - Developer Startup
echo ========================================
echo.

REM 1. Ensure root node_modules for 'concurrently'
if exist node_modules goto skip_root_npm
echo [System] root/node_modules not found. Installing concurrently...
call npm install
:skip_root_npm

REM 2. Ensure frontend node_modules
if exist frontend\node_modules goto skip_frontend_npm
echo [System] frontend/node_modules not found. Installing frontend deps...
pushd frontend
call npm install
popd
:skip_frontend_npm

REM 3. Inform user about backend venv if missing
if exist backend\.venv goto skip_venv_msg
echo [Warning] Backend virtual environment (.venv) not found.
echo [Action] To set it up, run:
echo          cd backend
echo          python -m venv .venv
echo          .venv\Scripts\activate
echo          pip install -r requirements.txt
echo.
:skip_venv_msg

REM 4. Launch both services
echo [Process] Starting Frontend (port 3000) and Backend (port 8000)...
echo.
call npm run dev
pause
