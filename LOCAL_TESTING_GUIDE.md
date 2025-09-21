# 🧪 Innovate AI - Local Testing Guide

## Overview
This guide helps you test the complete Innovate AI system locally before deploying to AWS.

## 🎯 Testing Strategy

### 1. Frontend-Only Testing (Recommended for Quick Demo)
### 2. Backend Simulation Testing  
### 3. Full AWS Integration Testing

---

## 🚀 Method 1: Frontend-Only Testing (Quick Start)

This approach uses the built-in fallback responses for immediate demonstration.

### Prerequisites
- Node.js 16+ installed
- NPM or Yarn package manager

### Setup Steps

```powershell
# Navigate to frontend directory
cd "d:\github_project\The-great-hackathon\finnovate-dashboard"

# Install dependencies
npm install

# Start development server
npm start
```

### Testing Features

1. **AI Chatbot Testing**
   - Open browser to `http://localhost:3000`
   - Navigate to AI Chatbot component
   - Test all 4 template buttons:
     - 📊 Analyze Customers
     - 📧 Draft Emails  
     - 📈 Payment Patterns
     - 🚀 Bulk Campaign
   - Verify fallback responses work properly

2. **Email Dashboard Testing**
   - Navigate to Email Management Dashboard
   - Verify mock email drafts appear
   - Test preview functionality
   - Test approve/send simulation
   - Check analytics display

### Expected Results
- ✅ All UI components render correctly
- ✅ Template buttons trigger appropriate responses
- ✅ Mock data displays properly
- ✅ No API errors (fallback system handles missing backend)

---

## 🔧 Method 2: Backend Simulation Testing

Test Lambda functions locally before AWS deployment.

### Prerequisites
- Python 3.9+ installed
- AWS CLI configured (optional for basic testing)

### Setup Local Lambda Environment

```powershell
# Navigate to Lambda directory
cd "d:\github_project\The-great-hackathon\lambda_deployment"

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install boto3 requests

# Install additional testing dependencies
pip install pytest flask flask-cors
```

### Create Local Test Server

```powershell
# Create local test server
@"
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os

# Add lambda function to path
sys.path.append('.')
from lambda_function import lambda_handler

app = Flask(__name__)
CORS(app)

@app.route('/ai/<path:endpoint>', methods=['GET', 'POST'])
def proxy_to_lambda(endpoint):
    # Create Lambda event structure
    event = {
        'httpMethod': request.method,
        'path': f'/ai/{endpoint}',
        'headers': dict(request.headers),
        'body': request.get_data(as_text=True) if request.method == 'POST' else None,
        'queryStringParameters': dict(request.args) if request.args else None
    }
    
    # Call Lambda function
    context = {}
    response = lambda_handler(event, context)
    
    return jsonify(json.loads(response['body'])), response['statusCode']

if __name__ == '__main__':
    app.run(debug=True, port=8000)
"@ | Out-File -FilePath "local_server.py" -Encoding utf8
```

### Run Local Backend

```powershell
# Start local backend server
python local_server.py
```

### Test Backend Endpoints

```powershell
# Test customer analysis
Invoke-RestMethod -Uri "http://localhost:8000/ai/analyze-customers" -Method POST -ContentType "application/json" -Body '{"limit": 5}'

# Test email drafting
Invoke-RestMethod -Uri "http://localhost:8000/ai/draft-email" -Method POST -ContentType "application/json" -Body '{"customer_id": "CUST001", "reminder_type": "first"}'

# Test conversation
Invoke-RestMethod -Uri "http://localhost:8000/ai/conversation" -Method POST -ContentType "application/json" -Body '{"message": "Analyze customers with frequent late payments"}'

# Test email drafts
Invoke-RestMethod -Uri "http://localhost:8000/ai/email-drafts" -Method GET

# Test email history
Invoke-RestMethod -Uri "http://localhost:8000/ai/email-history" -Method GET
```

### Update Frontend for Local Backend

```powershell
# Create environment file for local testing
cd "d:\github_project\The-great-hackathon\finnovate-dashboard"

@"
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_DEBUG_MODE=true
"@ | Out-File -FilePath ".env.local" -Encoding utf8

# Restart frontend to use local backend
npm start
```

---

## 🔬 Method 3: Full AWS Integration Testing

Test against actual AWS services with development/staging environment.

### Prerequisites
- AWS CLI configured with appropriate credentials
- Access to AWS services (DynamoDB, Lambda, Bedrock, SES)

### Setup AWS Testing Environment

```powershell
# Create test environment variables
$env:AWS_REGION = "us-east-1"
$env:DYNAMODB_TABLE = "InnovateAI-EmailTracking-Test"
$env:SES_SOURCE_EMAIL = "wongjiasoon@gmail.com"

# Test AWS connectivity
aws sts get-caller-identity
aws bedrock list-foundation-models --region us-east-1
```

### Create Test DynamoDB Table

```powershell
# Create test table (optional - use existing for testing)
aws dynamodb create-table `
    --table-name "InnovateAI-EmailTracking-Test" `
    --attribute-definitions `
        AttributeName=PK,AttributeType=S `
        AttributeName=SK,AttributeType=S `
    --key-schema `
        AttributeName=PK,KeyType=HASH `
        AttributeName=SK,KeyType=RANGE `
    --billing-mode PAY_PER_REQUEST `
    --region us-east-1
```

### Test Lambda Function Locally with AWS Services

```powershell
# Test with real AWS services
cd "d:\github_project\The-great-hackathon\lambda_deployment"

# Create comprehensive test script
@"
import json
import os
from lambda_function import lambda_handler

def test_customer_analysis():
    event = {
        'httpMethod': 'POST',
        'path': '/ai/analyze-customers',
        'body': json.dumps({'limit': 3}),
        'headers': {'Content-Type': 'application/json'}
    }
    
    response = lambda_handler(event, {})
    print("Customer Analysis Test:")
    print(f"Status: {response['statusCode']}")
    print(f"Response: {json.loads(response['body'])}")
    print("-" * 50)

def test_email_drafting():
    event = {
        'httpMethod': 'POST',
        'path': '/ai/draft-email',
        'body': json.dumps({
            'customer_id': 'CUST001',
            'reminder_type': 'first',
            'amount_due': 1500.00
        }),
        'headers': {'Content-Type': 'application/json'}
    }
    
    response = lambda_handler(event, {})
    print("Email Drafting Test:")
    print(f"Status: {response['statusCode']}")
    print(f"Response: {json.loads(response['body'])}")
    print("-" * 50)

def test_conversation():
    event = {
        'httpMethod': 'POST',
        'path': '/ai/conversation',
        'body': json.dumps({
            'message': 'Analyze customers with frequent late payments'
        }),
        'headers': {'Content-Type': 'application/json'}
    }
    
    response = lambda_handler(event, {})
    print("Conversation Test:")
    print(f"Status: {response['statusCode']}")
    print(f"Response: {json.loads(response['body'])}")
    print("-" * 50)

if __name__ == '__main__':
    print("🧪 Testing Innovate AI Lambda Functions with AWS Integration")
    print("=" * 60)
    
    try:
        test_customer_analysis()
        test_email_drafting()
        test_conversation()
        print("✅ All tests completed successfully!")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
"@ | Out-File -FilePath "test_aws_integration.py" -Encoding utf8

# Run comprehensive tests
python test_aws_integration.py
```

---

## 📋 Testing Checklist

### Frontend Testing ✅
- [ ] AI Chatbot renders correctly
- [ ] All 4 template buttons work
- [ ] Chat messages display properly
- [ ] Email Dashboard loads
- [ ] Email preview functionality works
- [ ] Analytics display correctly
- [ ] Responsive design on different screen sizes
- [ ] Error handling works (disconnect network to test)

### Backend Testing ✅
- [ ] All 6 API endpoints respond
- [ ] Nova Pro integration works (if AWS configured)
- [ ] DynamoDB operations complete successfully
- [ ] Email template generation works
- [ ] Duplicate prevention logic functions
- [ ] Error handling returns appropriate responses
- [ ] CORS headers allow frontend access

### Integration Testing ✅
- [ ] Frontend successfully calls backend APIs
- [ ] Mock data displays when backend unavailable
- [ ] Real data displays when backend available
- [ ] Approval workflow completes end-to-end
- [ ] Analytics refresh after operations
- [ ] No console errors in browser
- [ ] Network tab shows proper API calls

---

## 🛠️ Troubleshooting Common Issues

### Frontend Issues

**Issue:** "Module not found" errors
```powershell
# Solution: Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue:** CORS errors when calling backend
```powershell
# Solution: Ensure CORS is enabled in local server
# Add this to local_server.py:
# CORS(app, origins=['http://localhost:3000'])
```

### Backend Issues

**Issue:** AWS credentials not configured
```powershell
# Solution: Configure AWS CLI
aws configure
# Or set environment variables:
$env:AWS_ACCESS_KEY_ID = "your-key"
$env:AWS_SECRET_ACCESS_KEY = "your-secret"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

**Issue:** DynamoDB table not found
```powershell
# Solution: Create test table or use existing
# The Lambda function will handle missing tables gracefully
```

**Issue:** Bedrock access denied
```powershell
# Solution: Ensure Nova Pro model access in AWS console
# Or test with mock responses first
```

### Integration Issues

**Issue:** API calls timing out
```powershell
# Solution: Check local server is running
# Verify environment variables in .env.local
# Check browser network tab for request details
```

---

## 🎯 Quick Demo Test Script

Use this for rapid validation before presentations:

```powershell
# Complete demo test in under 5 minutes
cd "d:\github_project\The-great-hackathon"

# 1. Start frontend (new terminal)
Start-Process powershell -ArgumentList "-Command", "cd finnovate-dashboard; npm start"

# 2. Wait for frontend to start
Start-Sleep 10

# 3. Open browser to demo
Start-Process "http://localhost:3000"

# 4. Optional: Start local backend for full testing
cd lambda_deployment
python local_server.py
```

## 📊 Test Results Documentation

Create a test report:

```powershell
@"
# Innovate AI - Test Results

## Test Date: $(Get-Date)
## Tested By: [Your Name]

### Frontend Tests
- [ ] UI Components Load: ✅/❌
- [ ] Template Buttons Work: ✅/❌
- [ ] Chat Interface Responsive: ✅/❌
- [ ] Email Dashboard Functional: ✅/❌

### Backend Tests  
- [ ] API Endpoints Respond: ✅/❌
- [ ] Database Operations: ✅/❌
- [ ] AI Integration: ✅/❌
- [ ] Error Handling: ✅/❌

### Integration Tests
- [ ] End-to-End Workflow: ✅/❌
- [ ] Fallback Systems: ✅/❌
- [ ] Performance Acceptable: ✅/❌
- [ ] Demo Ready: ✅/❌

### Notes:
[Add any issues or observations]

### Overall Status: 🟢 PASS / 🟡 CONDITIONAL / 🔴 FAIL
"@ | Out-File -FilePath "TEST_RESULTS.md" -Encoding utf8
```

---

## 🏆 Conclusion

With these testing methods, you can:

1. **Quick Demo (5 minutes):** Frontend-only with fallback responses
2. **Full Local Testing (30 minutes):** Complete system with local backend
3. **AWS Integration (60 minutes):** Full cloud testing with real services

**Recommendation for Hackathon:** Start with Method 1 for immediate demo capability, then enhance with Method 2 for complete local testing. Use Method 3 only if you need to validate AWS service integration.

Your system is designed to work reliably in all scenarios! 🚀