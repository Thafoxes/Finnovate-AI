"""
InnovateAI-Invoice Lambda Function
Domain: Invoice Management with DDD patterns
Handles: Invoice CRUD, business rules, validations, email reminders
"""

import json
import boto3
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
ses_client = boto3.client('ses', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

# Environment variables
INVOICE_TABLE_NAME = os.environ.get('INVOICE_TABLE_NAME', 'InvoiceManagementTable')
SES_SOURCE_EMAIL = os.environ.get('SES_SOURCE_EMAIL', 'noreply@innovateai.com')

# Domain Models (DDD)
class InvoiceStatus(Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

@dataclass
class Invoice:
    invoice_id: str
    customer_id: str
    customer_name: str
    invoice_number: str
    amount: float
    due_date: str
    status: InvoiceStatus
    created_date: str
    items: List[dict]
    
    def is_overdue(self) -> bool:
        """Domain logic: Check if invoice is overdue"""
        try:
            due = datetime.fromisoformat(self.due_date.replace('Z', '+00:00'))
            return datetime.now() > due and self.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
        except:
            return False
    
    def calculate_days_overdue(self) -> int:
        """Domain logic: Calculate days overdue"""
        if not self.is_overdue():
            return 0
        try:
            due = datetime.fromisoformat(self.due_date.replace('Z', '+00:00'))
            return (datetime.now() - due).days
        except:
            return 0

class InvoiceRepository:
    """Repository pattern for Invoice data access"""
    
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            response = self.table.get_item(
                Key={'PK': f'INVOICE#{invoice_id}', 'SK': 'METADATA'}
            )
            if 'Item' in response:
                return self._item_to_invoice(response['Item'])
            return None
        except Exception as e:
            print(f"Error getting invoice {invoice_id}: {e}")
            return None
    
    def get_all(self) -> List[Invoice]:
        """Get all invoices"""
        try:
            response = self.table.scan(
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={':sk': 'METADATA'}
            )
            return [self._item_to_invoice(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error getting all invoices: {e}")
            return []
    
    def get_by_customer(self, customer_id: str) -> List[Invoice]:
        """Get invoices by customer ID"""
        try:
            response = self.table.query(
                IndexName='CustomerIndex',  # Assuming we have this GSI
                KeyConditionExpression='customer_id = :customer_id',
                ExpressionAttributeValues={':customer_id': customer_id}
            )
            return [self._item_to_invoice(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error getting invoices for customer {customer_id}: {e}")
            # Fallback to scan with filter
            return self._get_by_customer_fallback(customer_id)
    
    def _get_by_customer_fallback(self, customer_id: str) -> List[Invoice]:
        """Fallback method using scan"""
        try:
            response = self.table.scan(
                FilterExpression='SK = :sk AND customer_id = :customer_id',
                ExpressionAttributeValues={
                    ':sk': 'METADATA',
                    ':customer_id': customer_id
                }
            )
            return [self._item_to_invoice(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error in fallback customer query: {e}")
            return []
    
    def get_overdue(self) -> List[Invoice]:
        """Get overdue invoices"""
        try:
            response = self.table.scan(
                FilterExpression='SK = :sk AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':sk': 'METADATA',
                    ':status': 'OVERDUE'
                }
            )
            return [self._item_to_invoice(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error getting overdue invoices: {e}")
            return []
    
    def save(self, invoice: Invoice) -> bool:
        """Save invoice to database"""
        try:
            item = self._invoice_to_item(invoice)
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error saving invoice: {e}")
            return False
    
    def update_status(self, invoice_id: str, new_status: InvoiceStatus) -> bool:
        """Update invoice status"""
        try:
            self.table.update_item(
                Key={'PK': f'INVOICE#{invoice_id}', 'SK': 'METADATA'},
                UpdateExpression='SET #status = :status, updated_date = :updated',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': new_status.value,
                    ':updated': datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating invoice status: {e}")
            return False
    
    def _item_to_invoice(self, item: dict) -> Invoice:
        """Convert DynamoDB item to Invoice domain object"""
        return Invoice(
            invoice_id=item.get('invoice_id', ''),
            customer_id=item.get('customer_id', ''),
            customer_name=item.get('customer_name', ''),
            invoice_number=item.get('invoice_number', ''),
            amount=float(item.get('total_amount', 0)),
            due_date=item.get('due_date', ''),
            status=InvoiceStatus(item.get('status', 'DRAFT')),
            created_date=item.get('created_date', ''),
            items=item.get('items', [])
        )
    
    def _invoice_to_item(self, invoice: Invoice) -> dict:
        """Convert Invoice domain object to DynamoDB item"""
        return {
            'PK': f'INVOICE#{invoice.invoice_id}',
            'SK': 'METADATA',
            'invoice_id': invoice.invoice_id,
            'customer_id': invoice.customer_id,
            'customer_name': invoice.customer_name,
            'invoice_number': invoice.invoice_number,
            'total_amount': Decimal(str(invoice.amount)),
            'due_date': invoice.due_date,
            'status': invoice.status.value,
            'created_date': invoice.created_date,
            'items': invoice.items,
            'updated_date': datetime.now().isoformat()
        }

class InvoiceDomainService:
    """Domain service for Invoice business logic"""
    
    def __init__(self, repository: InvoiceRepository):
        self.repository = repository
    
    def get_payment_summary(self) -> dict:
        """Get comprehensive payment summary"""
        invoices = self.repository.get_all()
        
        total_invoices = len(invoices)
        total_amount = sum(inv.amount for inv in invoices)
        
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
        overdue_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.OVERDUE]
        pending_invoices = [inv for inv in invoices if inv.status in [InvoiceStatus.SENT, InvoiceStatus.DRAFT]]
        
        return {
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'paid_invoices': len(paid_invoices),
            'paid_amount': sum(inv.amount for inv in paid_invoices),
            'overdue_invoices': len(overdue_invoices),
            'overdue_amount': sum(inv.amount for inv in overdue_invoices),
            'pending_invoices': len(pending_invoices),
            'pending_amount': sum(inv.amount for inv in pending_invoices),
            'average_invoice_amount': total_amount / total_invoices if total_invoices > 0 else 0
        }
    
    def get_overdue_analysis(self) -> dict:
        """Get detailed overdue analysis"""
        overdue_invoices = self.repository.get_overdue()
        
        if not overdue_invoices:
            return {
                'total_overdue': 0,
                'total_amount': 0,
                'average_days_overdue': 0,
                'critical_invoices': 0,
                'by_customer': {}
            }
        
        total_amount = sum(inv.amount for inv in overdue_invoices)
        total_days = sum(inv.calculate_days_overdue() for inv in overdue_invoices)
        critical_invoices = [inv for inv in overdue_invoices if inv.calculate_days_overdue() > 30]
        
        # Group by customer
        by_customer = {}
        for inv in overdue_invoices:
            customer = inv.customer_name
            if customer not in by_customer:
                by_customer[customer] = {'count': 0, 'amount': 0}
            by_customer[customer]['count'] += 1
            by_customer[customer]['amount'] += inv.amount
        
        return {
            'total_overdue': len(overdue_invoices),
            'total_amount': total_amount,
            'average_days_overdue': total_days / len(overdue_invoices),
            'critical_invoices': len(critical_invoices),
            'by_customer': by_customer
        }

class EmailService:
    """Service for sending email reminders"""
    
    def __init__(self, ses_client, source_email: str):
        self.ses_client = ses_client
        self.source_email = source_email
    
    def send_overdue_reminder(self, invoice: Invoice, customer_email: str) -> bool:
        """Send overdue payment reminder"""
        try:
            subject = f"Payment Reminder - Invoice {invoice.invoice_number}"
            
            body = f"""
            Dear {invoice.customer_name},
            
            This is a friendly reminder that Invoice {invoice.invoice_number} for ${invoice.amount:.2f} 
            was due on {invoice.due_date} and is now {invoice.calculate_days_overdue()} days overdue.
            
            Please process payment at your earliest convenience.
            
            Thank you,
            InnovateAI Finance Team
            """
            
            response = self.ses_client.send_email(
                Source=self.source_email,
                Destination={'ToAddresses': [customer_email]},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending email reminder: {e}")
            return False

# Lambda Handler Functions
def handle_get_invoice_summary(repository: InvoiceDomainService):
    """Handle get invoice summary request"""
    try:
        summary = repository.get_payment_summary()
        
        # Also get actual invoice list for the frontend
        all_invoices = repository.repository.get_all()
        invoice_list = []
        
        for inv in all_invoices:
            invoice_list.append({
                'invoice_id': inv.invoice_id,
                'customer_name': inv.customer_name,
                'invoice_number': inv.invoice_number,
                'amount': inv.amount,
                'total_amount': inv.amount,
                'due_date': inv.due_date,
                'status': inv.status.value,
                'created_date': inv.created_date,
                'items': inv.items,
                'is_overdue': inv.is_overdue(),
                'days_overdue': inv.calculate_days_overdue(),
                'paid_amount': inv.amount if inv.status.value == 'PAID' else 0,
                'remaining_balance': 0 if inv.status.value == 'PAID' else inv.amount
            })
        
        # Return both summary and invoice list
        return success_response({
            'summary': summary,
            'invoices': invoice_list,  # Add this for the frontend
            'total_count': len(invoice_list)
        })
    except Exception as e:
        return error_response(f"Error getting invoice summary: {str(e)}")

def handle_get_overdue_invoices(repository: InvoiceRepository):
    """Handle get overdue invoices request"""
    try:
        overdue_invoices = repository.get_overdue()
        invoice_data = []
        
        for inv in overdue_invoices:
            invoice_data.append({
                'invoice_id': inv.invoice_id,
                'customer_name': inv.customer_name,
                'invoice_number': inv.invoice_number,
                'amount': inv.amount,
                'due_date': inv.due_date,
                'days_overdue': inv.calculate_days_overdue()
            })
        
        return success_response({
            'overdue_invoices': invoice_data,
            'total_count': len(invoice_data),
            'total_amount': sum(inv['amount'] for inv in invoice_data)
        })
    except Exception as e:
        return error_response(f"Error getting overdue invoices: {str(e)}")

def handle_get_invoice_details(repository: InvoiceRepository, params: dict):
    """Handle get invoice details request"""
    try:
        invoice_id = params.get('invoice_id')
        if not invoice_id:
            return error_response("invoice_id is required", 400)
        
        invoice = repository.get_by_id(invoice_id)
        if not invoice:
            return error_response(f"Invoice {invoice_id} not found", 404)
        
        return success_response({
            'invoice_id': invoice.invoice_id,
            'customer_name': invoice.customer_name,
            'invoice_number': invoice.invoice_number,
            'amount': invoice.amount,
            'due_date': invoice.due_date,
            'status': invoice.status.value,
            'created_date': invoice.created_date,
            'items': invoice.items,
            'is_overdue': invoice.is_overdue(),
            'days_overdue': invoice.calculate_days_overdue()
        })
    except Exception as e:
        return error_response(f"Error getting invoice details: {str(e)}")

def handle_get_customer_invoices(repository: InvoiceRepository, params: dict):
    """Handle get customer invoices request"""
    try:
        customer_id = params.get('customer_id')
        if not customer_id:
            return error_response("customer_id is required", 400)
        
        invoices = repository.get_by_customer(customer_id)
        
        invoice_data = []
        for inv in invoices:
            invoice_data.append({
                'invoice_id': inv.invoice_id,
                'invoice_number': inv.invoice_number,
                'amount': inv.amount,
                'due_date': inv.due_date,
                'status': inv.status.value,
                'is_overdue': inv.is_overdue()
            })
        
        return success_response({
            'customer_id': customer_id,
            'invoices': invoice_data,
            'total_count': len(invoice_data),
            'total_amount': sum(inv['amount'] for inv in invoice_data)
        })
    except Exception as e:
        return error_response(f"Error getting customer invoices: {str(e)}")

def handle_update_invoice_status(repository: InvoiceRepository, params: dict):
    """Handle update invoice status request"""
    try:
        invoice_id = params.get('invoice_id')
        new_status = params.get('status')
        
        if not invoice_id or not new_status:
            return error_response("invoice_id and status are required", 400)
        
        try:
            status_enum = InvoiceStatus(new_status.upper())
        except ValueError:
            return error_response(f"Invalid status: {new_status}", 400)
        
        success = repository.update_status(invoice_id, status_enum)
        
        if success:
            return success_response({'message': f'Invoice {invoice_id} status updated to {new_status}'})
        else:
            return error_response("Failed to update invoice status")
            
    except Exception as e:
        return error_response(f"Error updating invoice status: {str(e)}")

def success_response(data=None, message=None, status_code=200):
    """Create standardized success response"""
    response_body = {'success': True}
    
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
        'body': json.dumps(response_body, default=str)
    }

def error_response(error_message, status_code=500):
    """Create standardized error response"""
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

def lambda_handler(event, context):
    """
    Invoice Lambda Handler - Routes internal service calls
    Invoice Lambda Handler - Routes both internal and API Gateway calls
    """
    try:
        print(f"=== INVOICE LAMBDA HANDLER ===")
        print(f"Event: {json.dumps(event)}")
        
        # Handle OPTIONS requests for CORS
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
                },
                'body': ''
            }
        
        # Handle API Gateway calls (has httpMethod)
        if 'httpMethod' in event:
            return handle_api_gateway_request(event)
        
        # Handle internal Lambda calls (has action) - your original logic
        else:
            return handle_internal_request(event)
            
    except Exception as e:
        print(f"Invoice Lambda error: {e}")
        return error_response(f"Internal server error: {str(e)}")

def handle_api_gateway_request(event):
    """Handle requests from API Gateway"""
    http_method = event.get('httpMethod')
    path = event.get('path', '')
    query_params = event.get('queryStringParameters') or {}
    
    # Initialize repository and services
    repository = InvoiceRepository(INVOICE_TABLE_NAME)
    domain_service = InvoiceDomainService(repository)
    
    if http_method == 'GET':
        if query_params.get('customer_id'):
            return handle_get_customer_invoices(repository, query_params)
        elif query_params.get('invoice_id'):
            return handle_get_invoice_details(repository, query_params)
        elif 'overdue' in path:
            return handle_get_overdue_invoices(repository)
        else:
            return handle_get_invoice_summary(domain_service)
    else:
        return error_response(f"Method {http_method} not allowed", 405)

def handle_internal_request(event):
    """Handle requests from other Lambda functions"""
    # Initialize repository and services
    repository = InvoiceRepository(INVOICE_TABLE_NAME)
    domain_service = InvoiceDomainService(repository)
    
    # Get action and parameters from event
    action = event.get('action', '')
    params = event.get('params', {})
    
    print(f"Internal Action: {action}, Params: {params}")
    
    # Route based on action
    if action == 'get_invoice_summary':
        return handle_get_invoice_summary(domain_service)
    elif action == 'get_overdue_invoices':
        return handle_get_overdue_invoices(repository)
    elif action == 'get_invoice_details':
        return handle_get_invoice_details(repository, params)
    elif action == 'get_customer_invoices':
        return handle_get_customer_invoices(repository, params)
    elif action == 'update_invoice_status':
        return handle_update_invoice_status(repository, params)
    else:
        return error_response(f"Unknown action: {action}", 400)