#!/usr/bin/env python3
"""
Quick Local Test Script for Innovate AI
Run this to test your Lambda functions locally without AWS deployment
"""

import json
import sys
import os
from pathlib import Path

# Add the lambda_deployment directory to Python path
lambda_dir = Path(__file__).parent / "lambda_deployment"
sys.path.insert(0, str(lambda_dir))

try:
    from lambda_function import lambda_handler
    print("✅ Successfully imported lambda_function")
except ImportError as e:
    print(f"❌ Failed to import lambda_function: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

def test_endpoint(method, path, body=None):
    """Test a Lambda endpoint locally"""
    event = {
        'httpMethod': method,
        'path': path,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body) if body else None,
        'queryStringParameters': None
    }
    
    try:
        response = lambda_handler(event, {})
        status = response.get('statusCode', 500)
        body = json.loads(response.get('body', '{}'))
        
        print(f"\n🔍 Testing {method} {path}")
        print(f"Status: {status}")
        print(f"Response: {json.dumps(body, indent=2)}")
        
        return status == 200
        
    except Exception as e:
        print(f"\n❌ Error testing {method} {path}: {str(e)}")
        return False

def main():
    print("🧪 Innovate AI - Quick Local Testing")
    print("=" * 50)
    
    tests = [
        ("POST", "/ai/conversation", {"message": "Analyze customers with frequent late payments"}),
        ("POST", "/ai/analyze-customers", {"limit": 3}),
        ("POST", "/ai/draft-email", {"customer_id": "CUST001", "reminder_type": "first", "amount_due": 1500.00}),
        ("GET", "/ai/email-drafts", None),
        ("GET", "/ai/email-history", None),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, path, body in tests:
        if test_endpoint(method, path, body):
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Lambda function is working correctly.")
        print("\n🚀 Next steps:")
        print("1. Run 'cd finnovate-dashboard && npm start' to test the frontend")
        print("2. Open http://localhost:3000 in your browser")
        print("3. Test the AI chatbot and email dashboard")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")
        print("This might be expected if AWS services aren't configured.")
        print("The frontend will still work with fallback responses!")

if __name__ == "__main__":
    main()