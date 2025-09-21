"""
Test Script for AI Payment Intelligence System
Run this to test various AI bot functionalities locally
"""

import requests
import json
import time
from typing import Dict, Any

class AIBotTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_health(self) -> bool:
        """Test if server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server is healthy")
                print(f"   Status: {data.get('status')}")
                print(f"   Environment: {data.get('environment')}")
                print(f"   AWS Region: {data.get('aws_region')}")
                print(f"   Bedrock Model: {data.get('bedrock_model')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            return False
    
    def test_bedrock_connection(self) -> bool:
        """Test AWS Bedrock connection"""
        try:
            print("\n🤖 Testing Bedrock Connection...")
            response = self.session.get(f"{self.base_url}/test-bedrock")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Bedrock connection successful")
                print(f"   Model ID: {data.get('model_id')}")
                print(f"   Region: {data.get('region')}")
                print(f"   Sample Response: {data.get('model_response', '')[:100]}...")
                return True
            else:
                error_data = response.json()
                print(f"❌ Bedrock connection failed:")
                print(f"   Error: {error_data.get('message')}")
                print(f"   Suggestion: {error_data.get('suggestion')}")
                return False
        except Exception as e:
            print(f"❌ Bedrock test error: {e}")
            return False
    
    def test_invoice_data(self) -> bool:
        """Test invoice data retrieval"""
        try:
            print("\n📄 Testing Invoice Data...")
            
            # Test all invoices
            response = self.session.get(f"{self.base_url}/invoices")
            if response.status_code == 200:
                invoices = response.json()
                print(f"✅ Retrieved {len(invoices)} invoices")
                
                # Test overdue invoices
                overdue_response = self.session.get(f"{self.base_url}/invoices/overdue")
                if overdue_response.status_code == 200:
                    overdue = overdue_response.json()
                    print(f"✅ Retrieved {len(overdue)} overdue invoices")
                    return True
                else:
                    print(f"❌ Overdue invoices failed: {overdue_response.status_code}")
                    return False
            else:
                print(f"❌ Invoice data failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Invoice test error: {e}")
            return False
    
    def test_ai_chat(self) -> bool:
        """Test AI chat functionality"""
        try:
            print("\n💬 Testing AI Chat...")
            
            test_messages = [
                "What overdue invoices do we have?",
                "Generate a payment reminder for customer CUST001",
                "Show me the payment history for Acme Corporation",
                "Create a collection strategy for customers with invoices over $1000"
            ]
            
            for message in test_messages:
                print(f"\n   Testing: '{message}'")
                
                chat_data = {
                    "message": message,
                    "context": "payment_management"
                }
                
                response = self.session.post(
                    f"{self.base_url}/ai/chat",
                    json=chat_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Response received ({len(result.get('response', ''))} chars)")
                    print(f"   📝 Preview: {result.get('response', '')[:100]}...")
                else:
                    print(f"   ❌ Chat failed: {response.status_code}")
                    try:
                        error = response.json()
                        print(f"   Error: {error.get('error')}")
                    except:
                        print(f"   Raw error: {response.text}")
                    return False
                
                time.sleep(1)  # Rate limiting
            
            return True
        except Exception as e:
            print(f"❌ AI chat test error: {e}")
            return False
    
    def test_email_generation(self) -> bool:
        """Test email generation"""
        try:
            print("\n📧 Testing Email Generation...")
            
            email_request = {
                "invoice_id": "test-invoice-001",
                "customer_name": "Test Customer",
                "customer_email": "test@example.com",
                "amount": 1500.00,
                "days_overdue": 15,
                "tone": "professional"
            }
            
            response = self.session.post(
                f"{self.base_url}/ai/generate-email",
                json=email_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Email generated successfully")
                print(f"   Subject: {result.get('subject', '')}")
                print(f"   Body length: {len(result.get('body', ''))} chars")
                print(f"   Tone: {result.get('tone', '')}")
                return True
            else:
                print(f"❌ Email generation failed: {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error.get('error')}")
                except:
                    print(f"   Raw error: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Email generation test error: {e}")
            return False
    
    def test_campaigns(self) -> bool:
        """Test campaign management"""
        try:
            print("\n🎯 Testing Campaign Management...")
            
            # Get existing campaigns
            response = self.session.get(f"{self.base_url}/campaigns")
            if response.status_code == 200:
                campaigns = response.json()
                print(f"✅ Retrieved {len(campaigns)} existing campaigns")
                
                # Create new campaign
                campaign_data = {
                    "campaign_name": "Local Test Campaign",
                    "target_customers": ["CUST001", "CUST002"],
                    "strategy": "graduated_reminders"
                }
                
                create_response = self.session.post(
                    f"{self.base_url}/campaigns",
                    json=campaign_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if create_response.status_code in [200, 201]:
                    print(f"✅ Campaign created successfully")
                    return True
                else:
                    print(f"❌ Campaign creation failed: {create_response.status_code}")
                    return False
            else:
                print(f"❌ Campaign retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Campaign test error: {e}")
            return False
    
    def run_full_test_suite(self):
        """Run all tests"""
        print("🧪 AI Payment Intelligence - Local Testing Suite")
        print("=" * 60)
        
        results = {
            "Health Check": self.test_health(),
            "Bedrock Connection": self.test_bedrock_connection(),
            "Invoice Data": self.test_invoice_data(),
            "AI Chat": self.test_ai_chat(),
            "Email Generation": self.test_email_generation(),
            "Campaign Management": self.test_campaigns()
        }
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary:")
        print("-" * 30)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:20} {status}")
            if result:
                passed += 1
        
        print("-" * 30)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Your AI bot is ready for AWS deployment.")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        
        return passed == total

if __name__ == "__main__":
    print("Starting AI Bot Local Tests...")
    print("Make sure the local server is running: python local_server.py")
    print("")
    
    tester = AIBotTester()
    tester.run_full_test_suite()