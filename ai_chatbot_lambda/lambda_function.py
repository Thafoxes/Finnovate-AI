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
        
        # Save draft as template to tracking table
        template_id = save_email_draft(customer_id, reminder_type, email_draft)
        
        # Update daily analytics for template creation
        update_daily_template_creation()
        
        return success_response({
            'template_id': template_id,
            'customer_name': customer_data.get('name'),
            'customer_id': customer_id,
            'reminder_type': reminder_type,
            'email_subject': extract_subject_from_draft(email_draft),
            'email_preview': email_draft[:300] + '...' if len(email_draft) > 300 else email_draft,
            'overdue_invoices_count': len(overdue_invoices),
            'total_overdue_amount': sum(float(inv.get('remaining_balance', 0)) for inv in overdue_invoices),
            'status': 'drafted',
            'next_step': 'Review and approve template for sending',
            'created_at': datetime.utcnow().isoformat()
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
    """Save email draft as template to tracking table using new schema"""
    try:
        template_id = f"template_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{customer_id}"
        current_time = datetime.utcnow().isoformat()
        
        # Extract subject and personalization data
        subject = extract_subject_from_draft(email_content)
        customer_data = get_customer_data(customer_id)
        overdue_invoices = get_overdue_invoices(customer_id)
        
        # Create personalization data
        personalization_data = {
            'customer_name': customer_data.get('name', 'N/A') if customer_data else 'N/A',
            'total_amount_due': sum(float(inv.get('remaining_balance', 0)) for inv in overdue_invoices),
            'overdue_invoices_count': len(overdue_invoices),
            'days_overdue': calculate_days_overdue(overdue_invoices)
        }
        
        # Save as email template entity
        email_tracking_table.put_item(
            Item={
                'PK': f'TEMPLATE#{template_id}',
                'SK': 'v#1',
                'Type': 'email_template',
                'template_id': template_id,
                'version': 1,
                'customer_id': customer_id,
                'reminder_type': reminder_type,
                'status': 'drafted',
                'subject': subject,
                'body_text': email_content,
                'body_html': convert_text_to_html(email_content),
                'personalization_data': personalization_data,
                'created_by': 'ai_system',
                'created_at': current_time,
                'approved_by': None,
                'approved_at': None,
                'sent_at': None,
                'ai_prompt_used': f'{reminder_type.upper()}_REMINDER_PROMPT',
                # GSI1 for querying by status
                'GSI1PK': 'TEMPLATE_STATUS#drafted',
                'GSI1SK': f'created_at#{current_time}'
            }
        )
        
        return template_id
        
    except Exception as e:
        logger.error(f"Error saving email template: {str(e)}")
        return ""

def get_customer_name(customer_id: str) -> str:
    """Get customer name from customer data"""
    try:
        customer_data = get_customer_data(customer_id)
        return customer_data.get('name', 'Unknown Customer') if customer_data else 'Unknown Customer'
    except Exception as e:
        logger.error(f"Error getting customer name: {str(e)}")
        return 'Unknown Customer'

def get_email_template(template_id: str) -> Optional[Dict]:
    """Get email template by ID"""
    try:
        response = email_tracking_table.get_item(
            Key={'PK': f'TEMPLATE#{template_id}', 'SK': 'v#1'}
        )
        return response.get('Item')
    except Exception as e:
        logger.error(f"Error getting email template: {str(e)}")
        return None

def approve_template(template_id: str, approver: str) -> None:
    """Approve email template - update status from drafted to approved"""
    try:
        current_time = datetime.utcnow().isoformat()
        
        # Update template status
        email_tracking_table.update_item(
            Key={'PK': f'TEMPLATE#{template_id}', 'SK': 'v#1'},
            UpdateExpression='SET #status = :status, approved_by = :approver, approved_at = :time, GSI1PK = :gsi1pk',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'approved',
                ':approver': approver,
                ':time': current_time,
                ':gsi1pk': 'TEMPLATE_STATUS#approved'
            }
        )
        
    except Exception as e:
        logger.error(f"Error approving template: {str(e)}")
        raise

def send_email_sandbox_mode(template: Dict) -> Dict:
    """Simulate email sending in sandbox mode"""
    try:
        current_time = datetime.utcnow().isoformat()
        template_id = template['template_id']
        customer_id = template['customer_id']
        reminder_type = template['reminder_type']
        
        # Update template status to sent
        email_tracking_table.update_item(
            Key={'PK': f'TEMPLATE#{template_id}', 'SK': 'v#1'},
            UpdateExpression='SET #status = :status, sent_at = :time, GSI1PK = :gsi1pk',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'sent',
                ':time': current_time,
                ':gsi1pk': 'TEMPLATE_STATUS#sent'
            }
        )
        
        # Create email sending record
        email_tracking_table.put_item(
            Item={
                'PK': f'SENT#{customer_id}',
                'SK': f'#{reminder_type}#{current_time}',
                'Type': 'email_sent',
                'template_id': template_id,
                'customer_id': customer_id,
                'reminder_type': reminder_type,
                'invoice_id': template.get('personalization_data', {}).get('invoice_id', 'N/A'),
                'subject': template.get('subject', ''),
                'sent_at': current_time,
                'ses_message_id': f'sandbox-{template_id}',
                'delivery_status': 'sent',
                'template_version': template.get('version', 1),
                # GSI1 for querying by reminder type
                'GSI1PK': f'REMINDER_TYPE#{reminder_type}',
                'GSI1SK': f'sent_at#{current_time}'
            }
        )
        
        return {
            'simulation': 'sandbox_mode',
            'would_send_to': template.get('customer_id'),
            'subject': template.get('subject'),
            'delivery_status': 'simulated_success',
            'message': 'Email would be sent via Amazon SES in production'
        }
        
    except Exception as e:
        logger.error(f"Error in sandbox email sending: {str(e)}")
        raise

def update_customer_email_state(customer_id: str, reminder_type: str) -> None:
    """Update customer email state tracking"""
    try:
        current_time = datetime.utcnow().isoformat()
        
        # Get existing customer state or create new one
        try:
            response = email_tracking_table.get_item(
                Key={'PK': f'CUSTOMER#{customer_id}', 'SK': 'EMAIL_STATE'}
            )
            customer_state = response.get('Item', {})
        except:
            customer_state = {}
        
        # Update reminder tracking
        reminder_field = f'{reminder_type}_reminder_sent'
        updates = {
            reminder_field: current_time,
            'last_email_sent': current_time,
            'total_emails_sent': customer_state.get('total_emails_sent', 0) + 1
        }
        
        # Build update expression dynamically
        update_expression = 'SET '
        expression_values = {}
        for key, value in updates.items():
            update_expression += f'{key} = :{key.replace("_", "")}, '
            expression_values[f':{key.replace("_", "")}'] = value
        
        update_expression = update_expression.rstrip(', ')
        
        email_tracking_table.put_item(
            Item={
                'PK': f'CUSTOMER#{customer_id}',
                'SK': 'EMAIL_STATE',
                'Type': 'customer_email_state',
                'customer_id': customer_id,
                **{k: v for k, v in updates.items()},
                'opt_out_status': customer_state.get('opt_out_status', False),
                'bounce_count': customer_state.get('bounce_count', 0),
                'complaint_count': customer_state.get('complaint_count', 0),
                # GSI1 for analytics
                'GSI1PK': 'CUSTOMER_STATE',
                'GSI1SK': f'last_email_sent#{current_time}'
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating customer email state: {str(e)}")
        raise

def update_email_analytics(reminder_type: str) -> None:
    """Update daily email analytics"""
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Get existing analytics or create new
        try:
            response = email_tracking_table.get_item(
                Key={'PK': f'ANALYTICS#{today}', 'SK': 'DAILY_SUMMARY'}
            )
            analytics = response.get('Item', {})
        except:
            analytics = {}
        
        # Update counters
        emails_sent = analytics.get('emails_sent', 0) + 1
        reminder_field = f'{reminder_type}_reminders'
        reminder_count = analytics.get(reminder_field, 0) + 1
        
        email_tracking_table.put_item(
            Item={
                'PK': f'ANALYTICS#{today}',
                'SK': 'DAILY_SUMMARY',
                'Type': 'email_analytics',
                'date': today,
                'templates_created': analytics.get('templates_created', 0),
                'templates_approved': analytics.get('templates_approved', 0) + 1,
                'emails_sent': emails_sent,
                'first_reminders': analytics.get('first_reminders', 0) + (1 if reminder_type == 'first' else 0),
                'second_reminders': analytics.get('second_reminders', 0) + (1 if reminder_type == 'second' else 0),
                'final_notices': analytics.get('final_notices', 0) + (1 if reminder_type == 'final' else 0),
                'bounce_rate': 0.0,  # Sandbox mode
                'delivery_rate': 1.0,  # Sandbox mode
                # GSI1 for time series analytics
                'GSI1PK': 'ANALYTICS',
                'GSI1SK': f'date#{today}'
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating email analytics: {str(e)}")
        raise

def get_daily_email_analytics(date: str) -> Dict:
    """Get daily email analytics"""
    try:
        response = email_tracking_table.get_item(
            Key={'PK': f'ANALYTICS#{date}', 'SK': 'DAILY_SUMMARY'}
        )
        
        if response.get('Item'):
            analytics = response['Item']
            return {
                'date': analytics.get('date'),
                'emails_sent': analytics.get('emails_sent', 0),
                'first_reminders': analytics.get('first_reminders', 0),
                'second_reminders': analytics.get('second_reminders', 0),
                'final_notices': analytics.get('final_notices', 0),
                'templates_created': analytics.get('templates_created', 0),
                'templates_approved': analytics.get('templates_approved', 0),
                'delivery_rate': analytics.get('delivery_rate', 1.0),
                'bounce_rate': analytics.get('bounce_rate', 0.0)
            }
        else:
            return {
                'date': date,
                'emails_sent': 0,
                'first_reminders': 0,
                'second_reminders': 0,
                'final_notices': 0,
                'templates_created': 0,
                'templates_approved': 0,
                'delivery_rate': 0.0,
                'bounce_rate': 0.0
            }
            
    except Exception as e:
        logger.error(f"Error getting daily analytics: {str(e)}")
        return {}

def update_daily_template_creation() -> None:
    """Update daily analytics for template creation"""
    try:
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Get existing analytics or create new
        try:
            response = email_tracking_table.get_item(
                Key={'PK': f'ANALYTICS#{today}', 'SK': 'DAILY_SUMMARY'}
            )
            analytics = response.get('Item', {})
        except:
            analytics = {}
        
        email_tracking_table.put_item(
            Item={
                'PK': f'ANALYTICS#{today}',
                'SK': 'DAILY_SUMMARY',
                'Type': 'email_analytics',
                'date': today,
                'templates_created': analytics.get('templates_created', 0) + 1,
                'templates_approved': analytics.get('templates_approved', 0),
                'emails_sent': analytics.get('emails_sent', 0),
                'first_reminders': analytics.get('first_reminders', 0),
                'second_reminders': analytics.get('second_reminders', 0),
                'final_notices': analytics.get('final_notices', 0),
                'bounce_rate': analytics.get('bounce_rate', 0.0),
                'delivery_rate': analytics.get('delivery_rate', 1.0),
                # GSI1 for time series analytics
                'GSI1PK': 'ANALYTICS',
                'GSI1SK': f'date#{today}'
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating template creation analytics: {str(e)}")

def convert_text_to_html(text_content: str) -> str:
    """Convert plain text email to HTML format"""
    try:
        # Simple text to HTML conversion
        html_content = text_content.replace('\n', '<br>\n')
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ color: #2c5aa0; border-bottom: 2px solid #2c5aa0; padding-bottom: 10px; }}
                .content {{ margin: 20px 0; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Innovate AI - Payment Management</h2>
            </div>
            <div class="content">
                {html_content}
            </div>
            <div class="footer">
                <p>This email was generated by Innovate AI automated payment management system.</p>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error converting to HTML: {str(e)}")
        return text_content

def extract_subject_from_draft(email_content: str) -> str:
    """Extract subject line from email draft"""
    lines = email_content.split('\n')
    for line in lines:
        if line.lower().startswith('subject:'):
            return line.replace('Subject:', '').replace('subject:', '').strip()
    return "Payment Reminder from Innovate AI"

def handle_get_email_drafts() -> Dict:
    """Get all pending email drafts for approval"""
    try:
        # Query all draft templates by status
        response = email_tracking_table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :status',
            ExpressionAttributeValues={':status': 'TEMPLATE_STATUS#drafted'},
            ScanIndexForward=False  # Get newest first
        )
        
        drafts = []
        for item in response['Items']:
            drafts.append({
                'template_id': item.get('template_id', ''),
                'customer_id': item.get('customer_id', ''),
                'customer_name': get_customer_name(item.get('customer_id', '')),
                'reminder_type': item.get('reminder_type', ''),
                'subject': item.get('subject', ''),
                'created_at': item.get('created_at', ''),
                'personalization_data': item.get('personalization_data', {}),
                'preview': item.get('body_text', '')[:200] + '...'  # First 200 chars
            })
        
        return success_response({
            'drafts': drafts,
            'total_pending': len(drafts),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting email drafts: {str(e)}")
        return error_response(500, f"Failed to get drafts: {str(e)}")

def handle_approve_and_send(body: Dict) -> Dict:
    """Approve email template and trigger sending (sandbox mode)"""
    try:
        template_id = body.get('template_id')
        approver = body.get('approver', 'system')
        
        if not template_id:
            return error_response(400, "template_id is required")
        
        # Get the template
        template = get_email_template(template_id)
        if not template:
            return error_response(404, "Template not found")
        
        if template.get('status') != 'drafted':
            return error_response(400, f"Template status is {template.get('status')}, can only approve drafted templates")
        
        # Update template status to approved
        approve_template(template_id, approver)
        
        # In sandbox mode, simulate sending
        send_result = send_email_sandbox_mode(template)
        
        # Update customer email state
        update_customer_email_state(template['customer_id'], template['reminder_type'])
        
        # Create analytics entry
        update_email_analytics(template['reminder_type'])
        
        return success_response({
            'message': 'Email approved and sent successfully (sandbox mode)',
            'template_id': template_id,
            'customer_id': template['customer_id'],
            'reminder_type': template['reminder_type'],
            'sent_date': datetime.utcnow().isoformat(),
            'sandbox_simulation': send_result
        })
        
    except Exception as e:
        logger.error(f"Error approving and sending email: {str(e)}")
        return error_response(500, f"Failed to send email: {str(e)}")

def handle_email_history() -> Dict:
    """Get email sending history and analytics"""
    try:
        # Get recent sent emails
        response = email_tracking_table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :status',
            ExpressionAttributeValues={':status': 'TEMPLATE_STATUS#sent'},
            ScanIndexForward=False,
            Limit=50  # Get last 50 sent emails
        )
        
        sent_emails = []
        for item in response['Items']:
            sent_emails.append({
                'template_id': item.get('template_id', ''),
                'customer_id': item.get('customer_id', ''),
                'customer_name': get_customer_name(item.get('customer_id', '')),
                'reminder_type': item.get('reminder_type', ''),
                'subject': item.get('subject', ''),
                'sent_at': item.get('sent_at', ''),
                'delivery_status': 'delivered'  # Sandbox mode
            })
        
        # Get today's analytics
        today = datetime.utcnow().strftime('%Y-%m-%d')
        analytics = get_daily_email_analytics(today)
        
        return success_response({
            'recent_emails': sent_emails,
            'daily_analytics': analytics,
            'total_emails': len(sent_emails),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting email history: {str(e)}")
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