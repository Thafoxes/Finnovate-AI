#!/usr/bin/env python3
"""
Updated Lambda function with Bedrock Agent integration
This replaces your Nova Pro calls with real Bedrock Agent calls
"""

import boto3
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock Agent Runtime client
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Your Bedrock Agent configuration
AGENT_ID = 'VSKNCYS2GY'
AGENT_ALIAS_ID = 'TSTALIASID'

def invoke_payment_intelligence_agent(message: str, session_id: str = None) -> Dict[str, Any]:
    """
    Invoke the PaymentIntelligenceAgent for real AI responses
    """
    try:
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        logger.info(f"Invoking Bedrock Agent with message: {message[:100]}...")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=message
        )
        
        # Parse the streaming response
        agent_response = ""
        completion = response.get('completion', [])
        
        for event in completion:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        logger.info(f"Agent response received: {len(agent_response)} characters")
        
        return {
            'success': True,
            'response': agent_response.strip(),
            'session_id': session_id,
            'source': 'bedrock_agent'
        }
        
    except Exception as e:
        logger.error(f"Bedrock Agent error: {str(e)}")
        
        # Provide helpful fallback based on the error
        if "dependencyFailedException" in str(e):
            fallback_response = generate_fallback_for_dependency_error(message)
        else:
            fallback_response = generate_general_fallback(message)
        
        return {
            'success': False,
            'error': str(e),
            'response': fallback_response,
            'session_id': session_id,
            'source': 'fallback'
        }

def generate_fallback_for_dependency_error(message: str) -> str:
    """Generate intelligent fallback when agent has dependency issues"""
    message_lower = message.lower()
    
    if 'analyze' in message_lower and 'customer' in message_lower:
        return """Based on typical payment patterns, I can provide some insights:

**High-Risk Customer Indicators:**
• Payments consistently late by 7+ days
• Partial payments becoming more frequent  
• Communication delays when contacted
• Recent changes in payment method

**Recommended Actions:**
1. Implement automated early warning alerts
2. Segment customers by payment behavior
3. Create personalized reminder sequences
4. Consider payment terms adjustments

Would you like me to help draft reminder emails for specific customers?"""

    elif 'email' in message_lower or 'reminder' in message_lower:
        return """I can help you create effective payment reminder emails:

**Email Strategy Recommendations:**
• **First Reminder (Day 1):** Gentle, friendly tone
• **Second Reminder (Day 7):** More urgent, include payment options
• **Final Notice (Day 14):** Clear consequences, payment deadline

**Template Elements:**
- Personalized greeting with customer name
- Clear invoice details and amount due
- Multiple payment options
- Professional but firm tone
- Contact information for questions

Would you like me to draft a specific reminder email template?"""

    elif 'pattern' in message_lower:
        return """Here are key payment patterns to monitor:

**Warning Signs:**
• Late payments increasing in frequency
• Payment amounts decreasing over time
• Longer delays between invoice and payment
• Increased customer service inquiries about payments

**Positive Indicators:**
• Consistent on-time payments
• Full amounts paid
• Quick response to communications
• Proactive payment notifications

**Analytics to Track:**
- Days Sales Outstanding (DSO)
- Payment velocity trends
- Customer payment scores
- Seasonal payment patterns

Would you like help setting up automated pattern detection?"""

    else:
        return """I'm here to help with invoice management and payment intelligence. I can assist with:

• **Customer Analysis** - Identify payment risks and patterns
• **Email Automation** - Create personalized reminder templates  
• **Payment Insights** - Track trends and performance metrics
• **Process Optimization** - Improve collection workflows

What specific aspect of payment management would you like to focus on?"""

def generate_general_fallback(message: str) -> str:
    """Generate general fallback response"""
    return """I'm experiencing a temporary connection issue with the payment intelligence system. However, I can still help you with:

• Draft payment reminder emails
• Analyze customer payment patterns
• Suggest collection strategies
• Create automation workflows

Please try your request again, or let me know how else I can assist with your invoice management needs."""

# Update your existing conversation handler
def handle_conversation_endpoint(event):
    """Handle conversation requests with Bedrock Agent integration"""
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        session_id = body.get('session_id')
        history = body.get('history', [])
        
        if not message:
            return create_response(400, {
                'success': False,
                'error': 'Message is required'
            })
        
        # Add context from conversation history if available
        if history:
            # Format recent conversation for context
            context_messages = []
            for msg in history[-3:]:  # Last 3 messages for context
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                context_messages.append(f"{role}: {content}")
            
            # Add context to the message
            contextual_message = f"Previous conversation:\n" + "\n".join(context_messages) + f"\n\nCurrent request: {message}"
        else:
            contextual_message = message
        
        # Use the real Bedrock Agent
        result = invoke_payment_intelligence_agent(contextual_message, session_id)
        
        return create_response(200, {
            'success': True,
            'data': {
                'response': result['response'],
                'session_id': result['session_id'],
                'source': result['source'],
                'agent_id': AGENT_ID if result['success'] else None
            }
        })
            
    except Exception as e:
        logger.error(f"Conversation endpoint error: {str(e)}")
        return create_response(500, {
            'success': False,
            'error': str(e)
        })

def create_response(status_code: int, body: dict) -> dict:
    """Create HTTP response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }

# Test function for local testing
def test_agent_integration():
    """Test the agent integration locally"""
    test_event = {
        'httpMethod': 'POST',
        'path': '/ai/conversation',
        'body': json.dumps({
            'message': 'Help me analyze customers with frequent late payments',
            'session_id': f'test_{int(time.time())}'
        })
    }
    
    response = handle_conversation_endpoint(test_event)
    print("Test Response:")
    print(json.dumps(response, indent=2))
    return response

if __name__ == "__main__":
    test_agent_integration()