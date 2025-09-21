@echo off
echo 🚀 Starting AI Payment Intelligence Local Development Environment
echo ================================================================

echo.
echo 📋 Step 1: Checking Python environment...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo.
echo 📦 Step 2: Installing dependencies...
pip install -r requirements-local.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo 🔧 Step 3: Checking environment variables...
if not exist .env (
    echo ❌ .env file not found!
    echo Please create .env file with your AWS credentials
    echo See AWS_SETUP_GUIDE.md section 6.2 for details
    pause
    exit /b 1
) else (
    echo ✅ .env file found
)

echo.
echo 🌐 Step 4: Starting local development server...
echo Server will run at: http://localhost:5000
echo Frontend should connect to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python local_server.py