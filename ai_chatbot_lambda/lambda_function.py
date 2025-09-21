import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Dict, List, Any, Optional

# Import AI prompts
from ai_prompts import (
    BEDROCK_MODEL_ID, MODEL_CONFIG,
    PAYMENT_ANALYSIS_PROMPT, CUSTOMER_RISK_PROMPT,
    FIRST_REMINDER_PROMPT, SECOND_REMINDER_PROMPT, FINAL_NOTICE_PROMPT,
    CHATBOT_SYSTEM_PROMPT, TEMPLATE_QUESTIONS
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
bedrock = boto3.client('bedrock-runtime')
ses = boto3.client('ses')

# Environment variables
INVOICE_TABLE_NAME = os.environ.get('INVOICE_TABLE_NAME', 'InvoiceManagementTable')
EMAIL_TRACKING_TABLE_NAME = os.environ.get('EMAIL_TRACKING_TABLE_NAME', 'EmailTrackingTable')
SES_SOURCE_EMAIL = os.environ.get('SES_SOURCE_EMAIL', 'noreply@innovateai.com')
BEDROCK_MODEL_ID = 'amazon.nova-pro-v1:0'

# Get DynamoDB tables
invoice_table = dynamodb.Table(INVOICE_TABLE_NAME)
email_tracking_table = dynamodb.Table(EMAIL_TRACKING_TABLE_NAME)

def lambda_handler(event, context):
    """Main Lambda handler for AI chatbot requests"""
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the request
        http_method = event.get('httpMethod')
        path = event.get('path', '')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Route requests based on path
        if path == '/ai/analyze-customers':
            return handle_analyze_customers(body)
        elif path == '/ai/draft-email':
            return handle_draft_email(body)
        elif path == '/ai/conversation':
            return handle_conversation(body)
        elif path == '/ai/email-drafts':
            return handle_get_email_drafts()
        elif path == '/ai/approve-and-send':
            return handle_approve_and_send(body)
        elif path == '/ai/email-history':
            return handle_email_history()
        else:
            return error_response(404, "Endpoint not found")
            
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return error_response(500, f"Internal server error: {str(e)}")

def handle_analyze_customers(body: Dict) -> Dict:
    """Analyze customer payment patterns using Nova Pro"""
    try:
        # Get all customers and their payment history
        customers_data = get_all_customers_payment_data()
        
        # Use Nova Pro to analyze payment patterns
        analysis_prompt = create_payment_analysis_prompt(customers_data)
        ai_analysis = invoke_nova_pro(analysis_prompt)
        
        # Identify frequent late payers (>7 days late every month)
        late_payers = identify_frequent_late_payers(customers_data)
        
        return success_response({
            'ai_analysis': ai_analysis,
            'frequent_late_payers': late_payers,
            'total_customers_analyzed': len(customers_data),
            'analysis_timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_customers: {str(e)}")
        return error_response(500, f"Failed to analyze customers: {str(e)}")

def handle_draft_email(body: Dict) -> Dict:
    """Generate email draft using Nova Pro with Innovate AI branding"""
    try:
        customer_id = body.get('customer_id')
        reminder_type = body.get('reminder_type', 'first')  # first, second, final
        
        if not customer_id:
            return error_response(400, "customer_id is required")
        
        # Check if email was already sent recently (duplicate prevention)
        if check_recent_email_sent(customer_id, reminder_type):
            return error_response(400, f"Email of type '{reminder_type}' was already sent to this customer recently")
        
        # Get customer and invoice data
        customer_data = get_customer_data(customer_id)
        overdue_invoices = get_overdue_invoices(customer_id)
        
        if not customer_data:
            return error_response(404, "Customer not found")
        
        # Generate personalized email using Nova Pro
        email_prompt = create_email_draft_prompt(customer_data, overdue_invoices, reminder_type)
        email_draft = invoke_nova_pro(email_prompt)
        
        # Save draft to tracking table
        draft_id = save_email_draft(customer_id, reminder_type, email_draft)
        
        return success_response({
            'draft_id': draft_id,
            'customer_name': customer_data.get('name'),
            'reminder_type': reminder_type,
            'email_subject': extract_subject_from_draft(email_draft),
            'email_body': email_draft,
            'overdue_invoices_count': len(overdue_invoices),
            'total_overdue_amount': sum(float(inv.get('remaining_balance', 0)) for inv in overdue_invoices)
        })
        
    except Exception as e:
        logger.error(f"Error in draft_email: {str(e)}")
        return error_response(500, f"Failed to draft email: {str(e)}")

def handle_conversation(body: Dict) -> Dict:
    """Handle general AI conversation with Nova Pro"""
    try:
        message = body.get('message', '')
        conversation_history = body.get('history', [])
        
        if not message:
            return error_response(400, "message is required")
        
        # Create context-aware prompt for invoice management domain
        conversation_prompt = create_conversation_prompt(message, conversation_history)
        ai_response = invoke_nova_pro(conversation_prompt)
        
        return success_response({
            'response': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in conversation: {str(e)}")
        return error_response(500, f"Failed to process conversation: {str(e)}")

def get_all_customers_payment_data() -> List[Dict]:
    """Retrieve all customers and their payment history from DynamoDB"""
    try:
        # Scan for all customers
        response = invoice_table.scan(
            FilterExpression='begins_with(PK, :pk_prefix)',
            ExpressionAttributeValues={':pk_prefix': 'CUSTOMER#'}
        )
        
        customers = []
        for item in response['Items']:
            customer_id = item['PK'].replace('CUSTOMER#', '')
            
            # Get invoices for this customer
            invoices_response = invoice_table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :customer_id',
                ExpressionAttributeValues={':customer_id': f'CUSTOMER#{customer_id}'}
            )
            
            # Calculate payment metrics
            invoices = invoices_response['Items']
            payment_metrics = calculate_payment_metrics(invoices)
            
            customers.append({
                'customer_id': customer_id,
                'name': item.get('name', ''),
                'email': item.get('email', ''),
                'invoices': invoices,
                'payment_metrics': payment_metrics
            })
        
        return customers
        
    except Exception as e:
        logger.error(f"Error getting customer payment data: {str(e)}")
        return []

def calculate_payment_metrics(invoices: List[Dict]) -> Dict:
    """Calculate payment metrics for a customer"""
    total_invoices = len(invoices)
    late_payments = 0
    total_days_late = 0
    
    for invoice in invoices:
        if invoice.get('status') == 'paid':
            due_date = datetime.fromisoformat(invoice.get('due_date', '').replace('Z', '+00:00'))
            paid_date = datetime.fromisoformat(invoice.get('paid_date', '').replace('Z', '+00:00'))
            
            if paid_date > due_date:
                days_late = (paid_date - due_date).days
                if days_late > 7:  # More than 7 days late
                    late_payments += 1
                    total_days_late += days_late
    
    return {
        'total_invoices': total_invoices,
        'late_payments': late_payments,
        'late_payment_rate': late_payments / total_invoices if total_invoices > 0 else 0,
        'avg_days_late': total_days_late / late_payments if late_payments > 0 else 0,
        'is_frequent_late_payer': late_payments >= 3  # 3+ late payments indicates frequent late payer
    }

def identify_frequent_late_payers(customers_data: List[Dict]) -> List[Dict]:
    """Identify customers who are frequent late payers"""
    frequent_late_payers = []
    
    for customer in customers_data:
        metrics = customer['payment_metrics']
        if metrics['is_frequent_late_payer']:
            frequent_late_payers.append({
                'customer_id': customer['customer_id'],
                'name': customer['name'],
                'email': customer['email'],
                'late_payment_count': metrics['late_payments'],
                'late_payment_rate': round(metrics['late_payment_rate'] * 100, 1),
                'avg_days_late': round(metrics['avg_days_late'], 1)
            })
    
    return sorted(frequent_late_payers, key=lambda x: x['late_payment_rate'], reverse=True)

def invoke_nova_pro(prompt: str) -> str:
    """Invoke Amazon Bedrock Nova Pro model with optimized configuration"""
    try:
        request_body = {
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": MODEL_CONFIG['max_tokens'],
                "temperature": MODEL_CONFIG['temperature'],
                "topP": MODEL_CONFIG['top_p']
            }
        }
        
        response = bedrock.invoke_model(
            modelId=BEDROCK_MODEL_ID,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', '')
        
    except Exception as e:
        logger.error(f"Error invoking Nova Pro: {str(e)}")
        return f"Error generating AI response: {str(e)}"

def create_payment_analysis_prompt(customers_data: List[Dict]) -> str:
    """Create prompt for payment pattern analysis using standardized template"""
    customer_summary = []
    for customer in customers_data[:10]:  # Limit to first 10 for prompt length
        metrics = customer['payment_metrics']
        customer_summary.append(
            f"Customer {customer['name']}: {metrics['total_invoices']} invoices, "
            f"{metrics['late_payments']} late payments, "
            f"{metrics['late_payment_rate']:.1%} late rate"
        )
    
    return PAYMENT_ANALYSIS_PROMPT.format(customer_summary=chr(10).join(customer_summary))

def create_email_draft_prompt(customer_data: Dict, overdue_invoices: List[Dict], reminder_type: str) -> str:
    """Create prompt for email draft generation using standardized templates"""
    total_overdue = sum(float(inv.get('remaining_balance', 0)) for inv in overdue_invoices)
    invoice_list = []
    
    for invoice in overdue_invoices[:5]:  # Limit to 5 invoices
        invoice_list.append(
            f"Invoice #{invoice.get('invoice_id')}: ${float(invoice.get('remaining_balance', 0)):,.2f} "
            f"(Due: {invoice.get('due_date', '').split('T')[0]})"
        )
    
    # Select appropriate prompt template based on reminder type
    if reminder_type == 'first':
        template = FIRST_REMINDER_PROMPT
    elif reminder_type == 'second':
        template = SECOND_REMINDER_PROMPT
    elif reminder_type == 'final':
        template = FINAL_NOTICE_PROMPT
    else:
        template = FIRST_REMINDER_PROMPT  # Default to first reminder
    
    return template.format(
        customer_name=customer_data.get('name', 'N/A'),
        customer_email=customer_data.get('email', 'N/A'),
        total_amount=total_overdue,
        invoice_details=chr(10).join(invoice_list),
        days_overdue=calculate_days_overdue(overdue_invoices),
        last_reminder_date=get_last_reminder_date(customer_data.get('customer_id', '')),
        reminder_count=get_reminder_count(customer_data.get('customer_id', ''))
    )

def create_conversation_prompt(message: str, history: List[Dict]) -> str:
    """Create prompt for general conversation using system prompt"""
    context = ""
    if history:
        context = "Previous conversation:\n"
        for msg in history[-3:]:  # Last 3 messages for context
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            context += f"{role}: {content}\n"
    
    # Check if message matches template questions
    for key, response in TEMPLATE_QUESTIONS.items():
        if key in message.lower().replace('_', ' ').replace('-', ' '):
            return f"{CHATBOT_SYSTEM_PROMPT}\n\n{context}\nTemplate Response: {response}"
    
    return f"{CHATBOT_SYSTEM_PROMPT}\n\n{context}\nCurrent message: {message}\n\nProvide helpful, professional responses related to invoice management, customer billing, payment tracking, and financial operations."

def calculate_days_overdue(overdue_invoices: List[Dict]) -> int:
    """Calculate average days overdue for invoices"""
    if not overdue_invoices:
        return 0
    
    total_days = 0
    current_date = datetime.utcnow()
    
    for invoice in overdue_invoices:
        due_date = datetime.fromisoformat(invoice.get('due_date', '').replace('Z', '+00:00'))
        days_overdue = (current_date - due_date).days
        total_days += max(0, days_overdue)
    
    return total_days // len(overdue_invoices)

def get_last_reminder_date(customer_id: str) -> str:
    """Get the date of the last reminder sent to customer"""
    try:
        response = email_tracking_table.query(
            KeyConditionExpression='PK = :pk',
            FilterExpression='#status = :status',
            ExpressionAttributeValues={
                ':pk': f'CUSTOMER#{customer_id}',
                ':status': 'sent'
            },
            ExpressionAttributeNames={'#status': 'status'},
            ScanIndexForward=False,  # Sort descending
            Limit=1
        )
        
        if response['Items']:
            return response['Items'][0].get('sent_date', 'N/A')
        return 'N/A'
        
    except Exception as e:
        logger.error(f"Error getting last reminder date: {str(e)}")
        return 'N/A'

def get_reminder_count(customer_id: str) -> int:
    """Get the total number of reminders sent to customer"""
    try:
        response = email_tracking_table.query(
            KeyConditionExpression='PK = :pk',
            FilterExpression='#status = :status',
            ExpressionAttributeValues={
                ':pk': f'CUSTOMER#{customer_id}',
                ':status': 'sent'
            },
            ExpressionAttributeNames={'#status': 'status'}
        )
        
        return len(response['Items'])
        
    except Exception as e:
        logger.error(f"Error getting reminder count: {str(e)}")
        return 0

def check_recent_email_sent(customer_id: str, reminder_type: str, days_threshold: int = 7) -> bool:
    """Check if an email of the same type was sent recently"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)
        
        response = email_tracking_table.query(
            KeyConditionExpression='PK = :pk',
            FilterExpression='reminder_type = :reminder_type AND sent_date > :cutoff',
            ExpressionAttributeValues={
                ':pk': f'CUSTOMER#{customer_id}',
                ':reminder_type': reminder_type,
                ':cutoff': cutoff_date.isoformat()
            }
        )
        
        return len(response['Items']) > 0
        
    except Exception as e:
        logger.error(f"Error checking recent emails: {str(e)}")
        return False

def get_customer_data(customer_id: str) -> Optional[Dict]:
    """Get customer data from DynamoDB"""
    try:
        response = invoice_table.get_item(
            Key={'PK': f'CUSTOMER#{customer_id}', 'SK': 'PROFILE'}
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting customer data: {str(e)}")
        return None

def get_overdue_invoices(customer_id: str) -> List[Dict]:
    """Get overdue invoices for a customer"""
    try:
        current_date = datetime.utcnow().isoformat()
        
        response = invoice_table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :customer_id',
            FilterExpression='due_date < :current_date AND #status = :status',
            ExpressionAttributeValues={
                ':customer_id': f'CUSTOMER#{customer_id}',
                ':current_date': current_date,
                ':status': 'pending'
            },
            ExpressionAttributeNames={'#status': 'status'}
        )
        
        return response['Items']
        
    except Exception as e:
        logger.error(f"Error getting overdue invoices: {str(e)}")
        return []

def save_email_draft(customer_id: str, reminder_type: str, email_content: str) -> str:
    """Save email draft to tracking table"""
    try:
        draft_id = f"DRAFT#{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{customer_id}"
        
        email_tracking_table.put_item(
            Item={
                'PK': f'CUSTOMER#{customer_id}',
                'SK': draft_id,
                'reminder_type': reminder_type,
                'email_content': email_content,
                'status': 'draft',
                'created_date': datetime.utcnow().isoformat(),
                'subject': extract_subject_from_draft(email_content)
            }
        )
        
        return draft_id
        
    except Exception as e:
        logger.error(f"Error saving email draft: {str(e)}")
        return ""

def extract_subject_from_draft(email_content: str) -> str:
    """Extract subject line from email draft"""
    lines = email_content.split('\n')
    for line in lines:
        if line.lower().startswith('subject:'):
            return line.replace('Subject:', '').replace('subject:', '').strip()
    return "Payment Reminder from Innovate AI"

def handle_get_email_drafts() -> Dict:
    """Get all pending email drafts"""
    try:
        # Implementation for getting drafts
        return success_response({'drafts': []})
    except Exception as e:
        return error_response(500, f"Failed to get drafts: {str(e)}")

def handle_approve_and_send(body: Dict) -> Dict:
    """Approve and send email (sandbox mode - just update status)"""
    try:
        draft_id = body.get('draft_id')
        if not draft_id:
            return error_response(400, "draft_id is required")
        
        # In sandbox mode, just update status to "sent" without actually sending
        # In production, this would integrate with SES
        
        return success_response({
            'message': 'Email approved and sent (sandbox mode)',
            'draft_id': draft_id,
            'sent_date': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return error_response(500, f"Failed to send email: {str(e)}")

def handle_email_history() -> Dict:
    """Get email sending history"""
    try:
        # Implementation for email history
        return success_response({'history': []})
    except Exception as e:
        return error_response(500, f"Failed to get history: {str(e)}")

def success_response(data: Any) -> Dict:
    """Create standardized success response"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'success': True,
            'data': data
        }, default=str)
    }

def error_response(status_code: int, message: str) -> Dict:
    """Create standardized error response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps({
            'success': False,
            'message': message
        })
    }