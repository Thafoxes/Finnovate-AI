#!/bin/bash
# Frontend Testing Automation Script
# Run this to test frontend integration with local AI server

echo "🧪 Frontend Integration Testing Script"
echo "======================================"

# Function to check if server is running
check_server() {
    local url=$1
    local name=$2
    if curl -s "$url" > /dev/null; then
        echo "✅ $name is running"
        return 0
    else
        echo "❌ $name is not running"
        return 1
    fi
}

echo ""
echo "📡 Checking Servers..."

# Check AI bot server
check_server "http://localhost:5000/health" "AI Bot Server (Port 5000)"
ai_server=$?

# Check React server
check_server "http://localhost:3000" "React Frontend (Port 3000)"
react_server=$?

echo ""

if [ $ai_server -eq 0 ] && [ $react_server -eq 0 ]; then
    echo "✅ Both servers are running! Ready for testing."
    echo ""
    echo "🎯 Testing Checklist:"
    echo "1. Open http://localhost:3000 in browser"
    echo "2. Navigate to AI Assistant page"
    echo "3. Test chat: 'What overdue invoices do we have?'"
    echo "4. Test email generation"
    echo "5. Check dashboard functionality"
    echo ""
    echo "📋 API Endpoints to test:"
    echo "• GET  /health"
    echo "• GET  /invoices"
    echo "• GET  /invoices/overdue"
    echo "• POST /ai/chat"
    echo "• POST /ai/generate-email"
    echo "• GET  /campaigns"
elif [ $ai_server -eq 0 ]; then
    echo "⚠️  AI Bot Server is running, but React frontend is not."
    echo ""
    echo "🚀 Start React frontend:"
    echo "cd finnovate-dashboard"
    echo "npm start"
elif [ $react_server -eq 0 ]; then
    echo "⚠️  React frontend is running, but AI Bot Server is not."
    echo ""
    echo "🚀 Start AI Bot Server:"
    echo "cd lambda_deployment"
    echo "python local_server.py"
else
    echo "❌ Both servers are down."
    echo ""
    echo "🚀 Start both servers:"
    echo "Terminal 1: cd lambda_deployment && python local_server.py"
    echo "Terminal 2: cd finnovate-dashboard && npm start"
fi

echo ""
echo "📝 Frontend Configuration:"
echo "Make sure finnovate-dashboard/.env contains:"
echo "REACT_APP_API_BASE_URL=http://localhost:5000"

# Test API endpoints if AI server is running
if [ $ai_server -eq 0 ]; then
    echo ""
    echo "🔍 Quick API Tests:"
    
    echo -n "Health Check: "
    if curl -s "http://localhost:5000/health" | grep -q "healthy"; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
    fi
    
    echo -n "Invoices API: "
    if curl -s "http://localhost:5000/invoices" | grep -q "success\|invoices"; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
    fi
    
    echo -n "AI Chat API: "
    if curl -s -X POST "http://localhost:5000/ai/chat" \
        -H "Content-Type: application/json" \
        -d '{"message":"test"}' | grep -q "response"; then
        echo "✅ PASS"
    else
        echo "❌ FAIL"
    fi
fi

echo ""
echo "🎉 Happy Testing!"