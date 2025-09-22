"""
InnovateAI-Chatbot Lambda Function
Dedicated AI chatbot with Bedrock Agent integration
Separated from backend database operations
"""

import json
import boto3
import os
import time
from datetime import datetime

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

# Bedrock Agent Configuration
AGENT_ID = 'VSKNCYS2GY'
AGENT_ALIAS_ID = 'TSTALIASID'  # Use TSTALIASID for working draft

# Backend Lambda function names for data operations
INVOICE_LAMBDA_FUNCTION = 'InnovateAI-Invoice'
CUSTOMER_LAMBDA_FUNCTION = 'InnovateAI-Customer'

def invoke_backend_service(service_type, action, params=None):
    """
    Invoke the appropriate backend Lambda function for data operations
    service_type: 'invoice' or 'customer'
    """
    try:
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Choose the right Lambda function
        if service_type == 'invoice':
            function_name = INVOICE_LAMBDA_FUNCTION
        elif service_type == 'customer':
            function_name = CUSTOMER_LAMBDA_FUNCTION
        else:
            raise ValueError(f"Unknown service type: {service_type}")
        
        payload = {
            'action': action,
            'params': params or {}
        }
        
        print(f"Calling {function_name} with action: {action}")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        print(f"Backend response: {response_payload}")
        
        return response_payload
        
    except Exception as e:
        print(f"Error invoking {service_type} service: {e}")
        return None

def get_comprehensive_context_for_agent():
    """
    Get comprehensive invoice and customer context data
    This provides rich context to the Bedrock Agent
    """
    try:
        context_data = ""
        
        # Get invoice summary from Invoice Lambda
        invoice_response = invoke_backend_service('invoice', 'get_invoice_summary')
        if invoice_response and invoice_response.get('success'):
            data = invoice_response.get('data', {})
            
            context_data += f"""
INVOICE DATA CONTEXT:
- Total Invoices: {data.get('total_invoices', 0)}
- Total Amount: ${data.get('total_amount', 0):,.2f}
- Paid Invoices: {data.get('paid_invoices', 0)} (${data.get('paid_amount', 0):,.2f})
- Overdue Invoices: {data.get('overdue_invoices', 0)} (${data.get('overdue_amount', 0):,.2f})
- Pending Invoices: {data.get('pending_invoices', 0)} (${data.get('pending_amount', 0):,.2f})
- Average Invoice: ${data.get('average_invoice_amount', 0):,.2f}
"""
        
        # Get customer statistics from Customer Lambda
        customer_response = invoke_backend_service('customer', 'get_customer_statistics')
        if customer_response and customer_response.get('success'):
            data = customer_response.get('data', {})
            
            context_data += f"""
CUSTOMER DATA CONTEXT:
- Total Customers: {data.get('total_customers', 0)}
- High Risk Customers: {data.get('high_risk_customers', 0)}
- Average Risk Score: {data.get('average_risk_score', 0)}
- Total Customer Value: ${data.get('total_customer_value', 0):,.2f}
- Risk Distribution: Low({data.get('risk_distribution', {}).get('LOW', 0)}), Medium({data.get('risk_distribution', {}).get('MEDIUM', 0)}), High({data.get('risk_distribution', {}).get('HIGH', 0)}), Critical({data.get('risk_distribution', {}).get('CRITICAL', 0)})
"""
        
        # Get recent overdue invoices for context
        overdue_response = invoke_backend_service('invoice', 'get_overdue_invoices')
        if overdue_response and overdue_response.get('success'):
            overdue_data = overdue_response.get('data', {})
            overdue_invoices = overdue_data.get('overdue_invoices', [])
            
            if overdue_invoices:
                context_data += f"""
RECENT OVERDUE INVOICES:
"""
                for inv in overdue_invoices[:5]:  # Show top 5 overdue
                    context_data += f"- Invoice {inv.get('invoice_number', 'N/A')}: ${inv.get('amount', 0):,.2f} - {inv.get('customer_name', 'Unknown')} ({inv.get('days_overdue', 0)} days overdue)\n"
                
                if len(overdue_invoices) > 5:
                    context_data += f"... and {len(overdue_invoices) - 5} more overdue invoices\n"
        
        return context_data if context_data else "Financial data is available but could not be loaded for context."
        
    except Exception as e:
        print(f"Error getting comprehensive context: {e}")
        return "Financial data is available but could not be loaded for context."

def invoke_payment_intelligence_agent(message, session_id=None):
    """
    Invoke the PaymentIntelligenceAgent with invoice context data
    Focused purely on AI conversation handling
    """
    try:
        if not session_id:
            session_id = f"session_{int(time.time())}"
        
        # Get comprehensive context from both Invoice and Customer services
        context_data = get_comprehensive_context_for_agent()
        
        # Enhanced message with context
        enhanced_message = f"""{context_data}

USER QUESTION: {message}

Please provide intelligent insights based on the above invoice data context. If the user is asking about cash flow, overdue invoices, customer analysis, or payment patterns, use the provided data context to give specific answers."""
        
        print(f"Invoking Bedrock Agent with enhanced message: {enhanced_message[:200]}...")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=enhanced_message
        )
        
        # Parse the streaming response
        agent_response = ""
        completion = response.get('completion', [])
        
        for event in completion:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        print(f"Agent response received: {len(agent_response)} characters")
        
        return {
            'success': True,
            'response': agent_response.strip(),
            'session_id': session_id,
            'source': 'bedrock_agent'
        }
        
    except Exception as e:
        print(f"Bedrock Agent error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'session_id': session_id
        }

class BedrockAgentHandler:
    """
    Handle Bedrock Agent action group requests
    Routes function calls to the backend service
    """
    
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    def handle_agent_request(self, event, context):
        """Handle Bedrock Agent action group requests"""
        try:
            print(f"BEDROCK AGENT HANDLER - Event: {json.dumps(event)}")
            
            # Extract function information
            function_name = event.get('function', '')
            parameters = event.get('parameters', [])
            action_group = event.get('actionGroup', '')
            
            print(f"Function: {function_name}, Parameters: {parameters}, Action Group: {action_group}")
            
            # Convert parameters to dict
            params_dict = {}
            for param in parameters:
                params_dict[param.get('name', '')] = param.get('value', '')
            
            print(f"Converted parameters: {params_dict}")
            print(f"Looking for function: '{function_name}' in function mapping...")
            
            # Route to appropriate backend service based on function name
            function_mapping = {
                # Invoice service functions - with Bedrock Agent naming convention
                'GET__InvoiceManagement__get_overdue_invoices': ('invoice', 'get_overdue_invoices'),
                'GET__InvoiceManagement__get_invoice_details': ('invoice', 'get_invoice_details'), 
                'GET__InvoiceManagement__get_customer_invoices': ('invoice', 'get_customer_invoices'),
                'PUT__InvoiceManagement__update_invoice_status': ('invoice', 'update_invoice_status'),
                'GET__InvoiceManagement__get_payment_summary': ('invoice', 'get_invoice_summary'),
                'GET__InvoiceManagement__get_invoice_summary': ('invoice', 'get_invoice_summary'),
                
                # Customer service functions - with Bedrock Agent naming convention
                'GET__CustomerManagement__get_customer_statistics': ('customer', 'get_customer_statistics'),
                'GET__CustomerManagement__get_customer_by_id': ('customer', 'get_customer_by_id'),
                'GET__CustomerManagement__get_high_risk_customers': ('customer', 'get_high_risk_customers'),
                'GET__CustomerManagement__get_risk_analysis': ('customer', 'get_risk_analysis'),
                
                # Legacy function names (without prefix) for backward compatibility
                'get_overdue_invoices': ('invoice', 'get_overdue_invoices'),
                'get_invoice_details': ('invoice', 'get_invoice_details'), 
                'get_customer_invoices': ('invoice', 'get_customer_invoices'),
                'update_invoice_status': ('invoice', 'update_invoice_status'),
                'get_payment_summary': ('invoice', 'get_invoice_summary'),
                'get_invoice_summary': ('invoice', 'get_invoice_summary'),
                'get_customer_statistics': ('customer', 'get_customer_statistics'),
                'get_customer_by_id': ('customer', 'get_customer_by_id'),
                'get_high_risk_customers': ('customer', 'get_high_risk_customers'),
                'get_risk_analysis': ('customer', 'get_risk_analysis')
            }
            
            if function_name not in function_mapping:
                print(f"ERROR: Function '{function_name}' not found in mapping!")
                print(f"Available functions: {list(function_mapping.keys())}")
                return {
                    "messageVersion": "1.0",
                    "response": {
                        "actionGroup": action_group,
                        "function": function_name,
                        "functionResponse": {
                            "responseBody": {
                                "TEXT": {
                                    "body": json.dumps({
                                        "error": f"Unknown function: {function_name}",
                                        "available_functions": list(function_mapping.keys())
                                    })
                                }
                            }
                        }
                    }
                }
            
            service_type, backend_action = function_mapping[function_name]
            print(f"Routing to service: {service_type}, action: {backend_action}")
            
            # Call appropriate backend service
            backend_response = invoke_backend_service(service_type, backend_action, params_dict)
            print(f"Backend response received: {backend_response}")
            
            # Handle API Gateway response format vs direct response format
            if backend_response:
                # Check if this is an API Gateway response format
                if 'statusCode' in backend_response and 'body' in backend_response:
                    # This is an API Gateway response - parse the body
                    if backend_response.get('statusCode') == 200:
                        try:
                            body_data = json.loads(backend_response['body'])
                            if body_data.get('success'):
                                response_data = body_data.get('data', {})
                                print(f"Successful API Gateway response data: {response_data}")
                            else:
                                response_data = {"error": "Backend operation failed", "details": body_data}
                                print(f"Backend operation failed: {body_data}")
                        except json.JSONDecodeError as e:
                            response_data = {"error": "Invalid JSON response", "details": str(e)}
                            print(f"JSON decode error: {e}")
                    else:
                        response_data = {"error": "Backend service HTTP error", "status_code": backend_response.get('statusCode')}
                        print(f"Backend HTTP error: {backend_response.get('statusCode')}")
                # Direct response format (success/data structure)
                elif backend_response.get('success'):
                    response_data = backend_response.get('data', {})
                    print(f"Successful direct response data: {response_data}")
                else:
                    response_data = {"error": "Backend service error", "details": backend_response}
                    print(f"Backend service error: {backend_response}")
            else:
                response_data = {"error": "No response from backend service"}
                print("No response from backend service")
            
            # Return in Bedrock Agent format
            agent_response = {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": action_group,
                    "function": function_name,
                    "functionResponse": {
                        "responseBody": {
                            "TEXT": {
                                "body": json.dumps(response_data, default=str)
                            }
                        }
                    }
                }
            }
            print(f"Returning agent response: {json.dumps(agent_response)}")
            return agent_response
            
        except Exception as e:
            print(f"ERROR in BedrockAgentHandler: {str(e)}")
            return {
                "messageVersion": "1.0",
                "response": {
                    "actionGroup": action_group,
                    "function": function_name,
                    "functionResponse": {
                        "responseBody": {
                            "TEXT": {
                                "body": json.dumps({"error": str(e)})
                            }
                        }
                    }
                }
            }

def extract_suggested_actions(response_text):
    """Extract suggested actions from AI response"""
    actions = []
    response_lower = response_text.lower()
    
    if 'analyze' in response_lower or 'analysis' in response_lower:
        actions.append('Analyze customer payment patterns')
    if 'email' in response_lower or 'reminder' in response_lower:
        actions.append('Draft reminder emails')
    if 'report' in response_lower or 'summary' in response_lower:
        actions.append('Generate payment summary')
    if 'overdue' in response_lower:
        actions.append('View overdue invoices')
    
    return actions[:3]  # Limit to 3 actions

def success_response(data=None, message=None, status_code=200):
    """Create a standardized success response"""
    response_body = {
        'success': True
    }
    
    if data is not None:
        response_body['data'] = data
    
    if message:
        response_body['message'] = message
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(response_body)
    }

def error_response(error_message, status_code=500):
    """Create a standardized error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'success': False,
            'error': error_message
        })
    }

def handle_ai_chat(event):
    """Handle AI chat requests from frontend"""
    try:
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        session_id = body.get('session_id') or body.get('conversationId')
        
        print(f"AI Chat received message: {message}")
        print(f"Session ID: {session_id}")
        
        if not message:
            return error_response("Message is required", 400)
        
        # Use Bedrock Agent for AI response
        agent_result = invoke_payment_intelligence_agent(message, session_id)
        
        if agent_result and agent_result['success']:
            return success_response({
                'response': agent_result['response'],
                'session_id': agent_result['session_id'],
                'source': 'bedrock_agent',
                'suggested_actions': extract_suggested_actions(agent_result['response'])
            })
        else:
            # Fallback response
            return success_response({
                'response': "I'm having trouble processing your request right now. Please try again.",
                'session_id': session_id or f"session_{int(time.time())}",
                'source': 'fallback',
                'suggested_actions': ['Try again', 'Contact support']
            })
            
    except Exception as e:
        print(f"Error in handle_ai_chat: {e}")
        return error_response(f"Chat processing error: {str(e)}")

def lambda_handler(event, context):
    """
    Main Lambda handler for AI chatbot functionality
    Routes between chat interface and Bedrock Agent action groups
    """
    try:
        print(f"=== CHATBOT LAMBDA HANDLER ===")
        print(f"Event: {json.dumps(event)}")
        
        # Check if this is a Bedrock Agent action group request (function call)
        # Priority: Action group requests with apiPath (function calls)
        if 'actionGroup' in event and 'apiPath' in event:
            print("DETECTED: Bedrock Agent Action Group Request")
            
            action_path = event.get('apiPath', '')
            input_text = event.get('inputText', '')
            session_id = event.get('sessionId', f"session_{int(time.time())}")
            
            print(f"Agent received message: {input_text}")
            print(f"Session ID: {session_id}")
            print(f"API Path: {action_path}")
            
            # Route based on API path
            if '/get_overdue_invoices' in action_path:
                print("Calling InnovateAI-Invoice with action: get_overdue_invoices")
                backend_response = invoke_backend_service('invoice', 'get_overdue_invoices')
                print(f"Backend response: {backend_response}")
                
                if backend_response and backend_response.get('statusCode') == 200:
                    try:
                        body_data = json.loads(backend_response['body'])
                        if body_data.get('success'):
                            overdue_data = body_data.get('data', {})
                            overdue_count = overdue_data.get('total_count', 0)
                            overdue_amount = overdue_data.get('total_amount', 0)
                            
                            response_text = f"There are {overdue_count} overdue invoices with a total amount of ${overdue_amount:,.2f}."
                            
                            print(f"Returning response: {response_text}")
                            return {
                                'messageVersion': '1.0',
                                'response': {
                                    'actionGroup': event['actionGroup'],
                                    'apiPath': event['apiPath'], 
                                    'httpMethod': event['httpMethod'],
                                    'httpStatusCode': 200,
                                    'responseBody': {
                                        'TEXT': {
                                            'body': response_text
                                        }
                                    }
                                }
                            }
                    except Exception as e:
                        print(f"Error processing backend response: {e}")
                
                # Error response for failed overdue invoice query
                print("Returning error response for failed overdue invoice query")
                return {
                    'messageVersion': '1.0',
                    'response': {
                        'actionGroup': event['actionGroup'],
                        'apiPath': event['apiPath'],
                        'httpMethod': event['httpMethod'],
                        'httpStatusCode': 500,
                        'responseBody': {
                            'TEXT': {
                                'body': 'Unable to retrieve overdue invoice information at this time.'
                            }
                        }
                    }
                }
            
            # Default response for unhandled paths
            print("Returning default error response for unhandled API path")
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': event.get('actionGroup', ''),
                    'apiPath': event.get('apiPath', ''),
                    'httpMethod': event.get('httpMethod', 'GET'),
                    'httpStatusCode': 400,
                    'responseBody': {
                        'TEXT': {
                            'body': 'Unable to process the request.'
                        }
                    }
                }
            }
        
        # Check if this is a legacy Bedrock Agent action group request (function call)
        if 'actionGroup' in event and 'function' in event and 'inputText' not in event:
            print("DETECTED: Legacy Bedrock Agent Action Group Request")
            bedrock_handler = BedrockAgentHandler()
            return bedrock_handler.handle_agent_request(event, context)
        
        # Check if this is a Bedrock Agent invocation (full agent conversation)
        if 'inputText' in event and 'agent' in event:
            print("DETECTED: Bedrock Agent Full Invocation")
            # This means we need to handle the conversation and return a response
            # Extract the user message
            user_message = event.get('inputText', '')
            session_id = event.get('sessionId', f"session_{int(time.time())}")
            
            print(f"Agent received message: {user_message}")
            print(f"Session ID: {session_id}")
            
            # For now, let's check if this is asking about overdue invoices
            if 'overdue' in user_message.lower() and 'invoice' in user_message.lower():
                # Call our backend service directly
                backend_response = invoke_backend_service('invoice', 'get_overdue_invoices')
                
                if backend_response and backend_response.get('statusCode') == 200:
                    try:
                        body_data = json.loads(backend_response['body'])
                        if body_data.get('success'):
                            overdue_data = body_data.get('data', {})
                            overdue_count = overdue_data.get('total_count', 0)
                            overdue_amount = overdue_data.get('total_amount', 0)
                            
                            response_text = f"You currently have {overdue_count} overdue invoices totaling ${overdue_amount:,.2f}."
                            
                            return {
                                "messageVersion": "1.0",
                                "response": {
                                    "responseText": response_text,
                                    "sessionAttributes": event.get('sessionAttributes', {}),
                                    "promptSessionAttributes": event.get('promptSessionAttributes', {})
                                }
                            }
                    except Exception as e:
                        print(f"Error processing backend response: {e}")
            
            # Default response for other queries
            return {
                "messageVersion": "1.0", 
                "response": {
                    "responseText": "I can help you with invoice management. Try asking about overdue invoices, payment summaries, or customer information.",
                    "sessionAttributes": event.get('sessionAttributes', {}),
                    "promptSessionAttributes": event.get('promptSessionAttributes', {})
                }
            }
        
        # Handle API Gateway requests
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        
        print(f"HTTP Method: {http_method}, Path: {path}")
        
        # Handle CORS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Max-Age': '86400'
                },
                'body': ''
            }
        
        # Route chat requests
        if http_method == 'POST' and ('/chat' in path or '/ai' in path):
            return handle_ai_chat(event)
        
        # Default response
        return error_response("Endpoint not found", 404)
        
    except Exception as e:
        print(f"Lambda handler error: {e}")
        return error_response(f"Internal server error: {str(e)}")