import boto3
import json
import os

def test_bedrock_access():
    """Test Amazon Bedrock Nova Pro access"""
    try:
        # Initialize Bedrock client
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Test prompt
        test_prompt = "Explain what you are and your capabilities for invoice management in 50 words."
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": test_prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 100,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        print("Testing Amazon Bedrock Nova Pro access...")
        print(f"Model ID: amazon.nova-pro-v1:0")
        print(f"Test prompt: {test_prompt}")
        print("-" * 50)
        
        # Invoke model
        response = bedrock.invoke_model(
            modelId='amazon.nova-pro-v1:0',
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
        
        print("✅ SUCCESS: Nova Pro responded!")
        print(f"Response: {ai_response}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_dynamodb_access():
    """Test DynamoDB access"""
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Test InvoiceManagementTable
        invoice_table = dynamodb.Table('InvoiceManagementTable')
        invoice_response = invoice_table.scan(Limit=1)
        print(f"✅ InvoiceManagementTable accessible: {len(invoice_response['Items'])} items found")
        
        # Test EmailTrackingTable
        email_table = dynamodb.Table('EmailTrackingTable')
        email_response = email_table.scan(Limit=1)
        print(f"✅ EmailTrackingTable accessible: {len(email_response['Items'])} items found")
        
        return True
        
    except Exception as e:
        print(f"❌ DynamoDB ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== AI SERVICE INTEGRATION TEST ===")
    print()
    
    print("1. Testing DynamoDB Access...")
    db_success = test_dynamodb_access()
    print()
    
    print("2. Testing Amazon Bedrock Nova Pro Access...")
    ai_success = test_bedrock_access()
    print()
    
    if db_success and ai_success:
        print("🎉 ALL TESTS PASSED! AI service integration is working!")
    else:
        print("⚠️  Some tests failed. Check permissions and configuration.")