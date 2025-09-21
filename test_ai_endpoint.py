#!/usr/bin/env python3
"""
Quick test to verify the AI conversation endpoint is working with proper CORS
"""

import requests
import json

def test_ai_conversation_endpoint():
    """Test the AI conversation endpoint"""
    try:
        url = "https://59wn0kqhjl.execute-api.us-east-1.amazonaws.com/prod/ai/conversation"
        
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost:3000'
        }
        
        payload = {
            'message': 'How can I improve my invoice collection process?',
            'session_id': 'test_session_123'
        }
        
        print("🔍 Testing AI Conversation Endpoint...")
        print(f"URL: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print("-" * 50)
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("-" * 50)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS! Response:")
            print(json.dumps(data, indent=2))
            
            # Check if we got a real AI response
            if 'data' in data and 'response' in data['data']:
                ai_response = data['data']['response']
                if len(ai_response) > 100:  # Real AI responses are longer
                    print("\n🤖 REAL AI DETECTED!")
                    print(f"Response length: {len(ai_response)} characters")
                    print(f"Source: {data['data'].get('source', 'unknown')}")
                else:
                    print("\n⚠️ Fallback response detected")
            
            return True
            
        else:
            print(f"❌ FAILED! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_ai_conversation_endpoint()