@echo off
echo 🧪 Innovate AI - Quick Frontend Test
echo ====================================

cd /d "d:\github_project\The-great-hackathon\finnovate-dashboard"

echo 📦 Installing dependencies...
call npm install

echo 🚀 Starting development server...
echo.
echo 🌐 The app will open in your browser at http://localhost:3000
echo.
echo ✨ Test these features:
echo   1. Click the AI chatbot template buttons
echo   2. Try the email management dashboard  
echo   3. Test the preview functionality
echo.
echo 📝 Note: The app uses fallback responses for demo purposes
echo    so it will work even without backend connectivity!
echo.
echo Press Ctrl+C to stop the server when done testing
echo.

call npm start