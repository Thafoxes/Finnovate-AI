#!/usr/bin/env python3
"""
Quick test for PaymentIntelligenceAgent
Tests your real Bedrock Agent before integrating with frontend
"""

import boto3
import json
import time

def test_payment_intelligence_agent():
    try:
        print("🤖 Testing PaymentIntelligenceAgent...")
        print("=" * 50)
        
        # Initialize Bedrock Agent Runtime client
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        
        # Your agent details from Bedrock console
        agent_id = 'VSKNCYS2GY'  # From your Bedrock console
        agent_alias_id = 'TSTALIASID'  # Default test alias
        session_id = f"test_session_{int(time.time())}"
        
        # Test messages
        test_messages = [
            "Analyze customers with frequent late payments",
            "Draft a reminder email for overdue invoices",
            "What payment patterns should I watch for?",
            "Help me create a bulk email campaign"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🔍 Test {i}: {message}")
            print("-" * 30)
            
            try:
                response = client.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=agent_alias_id,
                    sessionId=session_id,
                    inputText=message
                )
                
                # Parse streaming response
                agent_response = ""
                completion = response.get('completion', [])
                
                for event in completion:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            agent_response += chunk['bytes'].decode('utf-8')
                
                print(f"✅ Agent Response:")
                print(agent_response)
                
            except Exception as e:
                print(f"❌ Test {i} failed: {str(e)}")
        
        print("\n" + "=" * 50)
        print("🎉 Agent testing complete!")
        print(f"Agent ID: {agent_id}")
        print(f"Session: {session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials: aws sts get-caller-identity")
        print("2. Verify Bedrock permissions")
        print("3. Ensure agent is in 'Prepared' status")
        return False

if __name__ == "__main__":
    test_payment_intelligence_agent()