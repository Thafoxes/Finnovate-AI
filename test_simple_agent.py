#!/usr/bin/env python3
"""
Simple Bedrock Agent test with basic questions
Tests what works vs what needs permissions
"""

import boto3
import json
import time

def test_simple_agent_questions():
    try:
        print("🤖 Testing Simple PaymentIntelligenceAgent Questions...")
        print("=" * 60)
        
        client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
        agent_id = 'VSKNCYS2GY'
        agent_alias_id = 'TSTALIASID'
        session_id = f"simple_test_{int(time.time())}"
        
        # Simple questions that don't require Lambda functions
        simple_questions = [
            "What is payment intelligence?",
            "How can I improve my invoice collection process?",
            "What are the best practices for payment reminders?",
            "Help me understand customer payment patterns",
            "What should I look for in late paying customers?",
            "How do I create effective reminder emails?"
        ]
        
        successful_tests = 0
        total_tests = len(simple_questions)
        
        for i, question in enumerate(simple_questions, 1):
            print(f"\n🔍 Test {i}/{total_tests}: {question}")
            print("-" * 40)
            
            try:
                response = client.invoke_agent(
                    agentId=agent_id,
                    agentAliasId=agent_alias_id,
                    sessionId=session_id,
                    inputText=question
                )
                
                # Parse response
                agent_response = ""
                completion = response.get('completion', [])
                
                for event in completion:
                    if 'chunk' in event:
                        chunk = event['chunk']
                        if 'bytes' in chunk:
                            agent_response += chunk['bytes'].decode('utf-8')
                
                if agent_response.strip():
                    print(f"✅ SUCCESS:")
                    print(agent_response.strip())
                    successful_tests += 1
                else:
                    print("❌ No response received")
                
            except Exception as e:
                print(f"❌ FAILED: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"🎯 Results: {successful_tests}/{total_tests} tests successful")
        
        if successful_tests > 0:
            print("✅ Your Bedrock Agent is working for general questions!")
            print("💡 You can use it for real AI conversations in your app")
            return True
        else:
            print("❌ Agent needs configuration or permissions")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_simple_agent_questions()