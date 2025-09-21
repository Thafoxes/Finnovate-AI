@echo off
echo 🧪 Frontend Integration Testing Script
echo ======================================

echo.
echo 📡 Checking Servers...

REM Check AI bot server
curl -s http://localhost:5000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ AI Bot Server is running
    set ai_server=1
) else (
    echo ❌ AI Bot Server is not running
    set ai_server=0
)

REM Check React server
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ React Frontend is running
    set react_server=1
) else (
    echo ❌ React Frontend is not running
    set react_server=0
)

echo.

if %ai_server% equ 1 if %react_server% equ 1 (
    echo ✅ Both servers are running! Ready for testing.
    echo.
    echo 🎯 Testing Checklist:
    echo 1. Open http://localhost:3000 in browser
    echo 2. Navigate to AI Assistant page
    echo 3. Test chat: "What overdue invoices do we have?"
    echo 4. Test email generation
    echo 5. Check dashboard functionality
    echo.
    echo 📋 API Endpoints to test:
    echo • GET  /health
    echo • GET  /invoices
    echo • GET  /invoices/overdue
    echo • POST /ai/chat
    echo • POST /ai/generate-email
    echo • GET  /campaigns
) else if %ai_server% equ 1 (
    echo ⚠️  AI Bot Server is running, but React frontend is not.
    echo.
    echo 🚀 Start React frontend:
    echo cd finnovate-dashboard
    echo npm start
) else if %react_server% equ 1 (
    echo ⚠️  React frontend is running, but AI Bot Server is not.
    echo.
    echo 🚀 Start AI Bot Server:
    echo cd lambda_deployment
    echo python local_server.py
) else (
    echo ❌ Both servers are down.
    echo.
    echo 🚀 Start both servers:
    echo Terminal 1: cd lambda_deployment ^&^& python local_server.py
    echo Terminal 2: cd finnovate-dashboard ^&^& npm start
)

echo.
echo 📝 Frontend Configuration:
echo Make sure finnovate-dashboard\.env contains:
echo REACT_APP_API_BASE_URL=http://localhost:5000

if %ai_server% equ 1 (
    echo.
    echo 🔍 Quick API Tests:
    
    echo | set /p="Health Check: "
    curl -s "http://localhost:5000/health" | findstr "healthy" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ PASS
    ) else (
        echo ❌ FAIL
    )
    
    echo | set /p="Invoices API: "
    curl -s "http://localhost:5000/invoices" | findstr "success invoices" >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ PASS
    ) else (
        echo ❌ FAIL
    )
)

echo.
echo 🎉 Happy Testing!
pause