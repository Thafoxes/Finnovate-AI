"""Complete Invoice Management Lambda with Full DDD Implementation"""

import json
import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any

# Domain Value Objects
class InvoiceStatus(Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"

@dataclass
class Money:
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

@dataclass
class InvoiceLineItem:
    description: str
    quantity: Decimal
    unit_price: Money
    
    @property
    def line_total(self) -> Money:
        return Money(self.unit_price.amount * self.quantity, self.unit_price.currency)

# Domain Entity
@dataclass
class Invoice:
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: str
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    line_items: List[InvoiceLineItem]
    version: int = 1
    
    @property
    def total_amount(self) -> Money:
        if not self.line_items:
            return Money(Decimal('0'))
        
        total = self.line_items[0].line_total
        for item in self.line_items[1:]:
            total = Money(total.amount + item.line_total.amount, total.currency)
        return total
    
    @property
    def is_overdue(self) -> bool:
        return self.due_date < datetime.now() and self.status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]

# Domain Services
class InvoiceStatusTransitionService:
    VALID_TRANSITIONS = {
        InvoiceStatus.DRAFT: [InvoiceStatus.SENT, InvoiceStatus.CANCELLED],
        InvoiceStatus.SENT: [InvoiceStatus.PAID, InvoiceStatus.OVERDUE, InvoiceStatus.CANCELLED],
        InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.CANCELLED],
        InvoiceStatus.PAID: [],
        InvoiceStatus.CANCELLED: []
    }
    
    @classmethod
    def can_transition(cls, current_status: InvoiceStatus, new_status: InvoiceStatus) -> bool:
        return new_status in cls.VALID_TRANSITIONS.get(current_status, [])
    
    @classmethod
    def validate_transition(cls, invoice: Invoice, new_status: InvoiceStatus) -> bool:
        if not cls.can_transition(invoice.status, new_status):
            return False
        
        # Auto-transition to overdue if past due date
        if new_status == InvoiceStatus.OVERDUE and not invoice.is_overdue:
            return False
            
        return True

class InvoiceNumberGenerator:
    @staticmethod
    def generate() -> str:
        return f"INV-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"

class OverdueDetectionService:
    @staticmethod
    def detect_overdue_invoices(invoices: List[Invoice]) -> List[Invoice]:
        overdue = []
        for invoice in invoices:
            if invoice.is_overdue and invoice.status == InvoiceStatus.SENT:
                overdue.append(invoice)
        return overdue

# Application Service
class InvoiceApplicationService:
    def __init__(self, dynamodb_table):
        self.table = dynamodb_table
        self.number_generator = InvoiceNumberGenerator()
        self.status_service = InvoiceStatusTransitionService()
        self.overdue_service = OverdueDetectionService()
    
    def create_invoice(self, command_data: dict) -> Invoice:
        line_items = []
        for item_data in command_data.get('line_items', []):
            line_item = InvoiceLineItem(
                description=item_data['description'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Money(Decimal(str(item_data['unit_price'])), 
                               item_data.get('currency', 'USD'))
            )
            line_items.append(line_item)
        
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            invoice_number=self.number_generator.generate(),
            customer_id=command_data.get('customer_id', 'unknown'),
            customer_name=command_data.get('customer_name', 'Unknown'),
            customer_email=command_data.get('customer_email', 'unknown@example.com'),
            issue_date=datetime.fromisoformat(command_data.get('issue_date', datetime.now().isoformat())),
            due_date=datetime.fromisoformat(command_data.get('due_date', (datetime.now() + timedelta(days=30)).isoformat())),
            status=InvoiceStatus.DRAFT,
            line_items=line_items
        )
        
        self._save_invoice(invoice)
        return invoice
    
    def update_invoice_status(self, invoice_id: str, new_status: str, reason: str = "") -> Invoice:
        invoice = self._get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        new_status_enum = InvoiceStatus(new_status)
        
        if not self.status_service.validate_transition(invoice, new_status_enum):
            raise ValueError(f"Invalid status transition from {invoice.status.value} to {new_status}")
        
        invoice.status = new_status_enum
        invoice.version += 1
        
        self._save_invoice(invoice)
        self._save_status_history(invoice_id, invoice.status.value, new_status, reason)
        
        return invoice
    
    def process_payment(self, invoice_id: str, payment_amount: Decimal) -> Invoice:
        invoice = self._get_invoice_by_id(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice {invoice_id} not found")
        
        if payment_amount >= invoice.total_amount.amount:
            invoice.status = InvoiceStatus.PAID
            invoice.version += 1
            self._save_invoice(invoice)
            self._save_payment_record(invoice_id, payment_amount, "FULL_PAYMENT")
        else:
            self._save_payment_record(invoice_id, payment_amount, "PARTIAL_PAYMENT")
        
        return invoice
    
    def delete_invoice(self, invoice_id: str) -> bool:
        invoice = self._get_invoice_by_id(invoice_id)
        if not invoice:
            return False
        
        if invoice.status not in [InvoiceStatus.DRAFT, InvoiceStatus.CANCELLED]:
            raise ValueError("Can only delete draft or cancelled invoices")
        
        # Delete main invoice and line items
        self.table.delete_item(Key={'PK': f'INVOICE#{invoice_id}', 'SK': 'METADATA'})
        
        # Delete line items
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'INVOICE#{invoice_id}',
                ':sk': 'LINEITEM#'
            }
        )
        
        for item in response.get('Items', []):
            self.table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
        
        return True
    
    def detect_and_update_overdue(self) -> List[str]:
        # Get all sent invoices
        response = self.table.scan(
            FilterExpression='SK = :sk AND #status = :status',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':sk': 'METADATA',
                ':status': 'SENT'
            }
        )
        
        updated_invoices = []
        for item in response.get('Items', []):
            due_date = datetime.fromisoformat(item['due_date'])
            if due_date < datetime.now():
                invoice_id = item['invoice_id']
                self.update_invoice_status(invoice_id, InvoiceStatus.OVERDUE.value, "Auto-detected overdue")
                updated_invoices.append(invoice_id)
        
        return updated_invoices
    
    def _get_invoice_by_id(self, invoice_id: str) -> Optional[Invoice]:
        try:
            # Get main invoice
            response = self.table.get_item(
                Key={'PK': f'INVOICE#{invoice_id}', 'SK': 'METADATA'}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # Get line items
            line_items_response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': f'INVOICE#{invoice_id}',
                    ':sk': 'LINEITEM#'
                }
            )
            
            line_items = []
            for line_item_data in line_items_response.get('Items', []):
                line_item = InvoiceLineItem(
                    description=line_item_data['description'],
                    quantity=line_item_data['quantity'],
                    unit_price=Money(line_item_data['unit_price'], line_item_data['currency'])
                )
                line_items.append(line_item)
            
            return Invoice(
                invoice_id=item['invoice_id'],
                invoice_number=item['invoice_number'],
                customer_id=item['customer_id'],
                customer_name=item['customer_name'],
                customer_email=item['customer_email'],
                issue_date=datetime.fromisoformat(item['issue_date']),
                due_date=datetime.fromisoformat(item['due_date']),
                status=InvoiceStatus(item['status']),
                line_items=line_items,
                version=item.get('version', 1)
            )
            
        except Exception as e:
            print(f"Error getting invoice {invoice_id}: {str(e)}")
            return None
    
    def _save_invoice(self, invoice: Invoice):
        # Save main invoice
        invoice_item = {
            'PK': f'INVOICE#{invoice.invoice_id}',
            'SK': 'METADATA',
            'invoice_id': invoice.invoice_id,
            'invoice_number': invoice.invoice_number,
            'customer_id': invoice.customer_id,
            'customer_name': invoice.customer_name,
            'customer_email': invoice.customer_email,
            'issue_date': invoice.issue_date.isoformat(),
            'due_date': invoice.due_date.isoformat(),
            'status': invoice.status.value,
            'total_amount': invoice.total_amount.amount,
            'currency': invoice.total_amount.currency,
            'version': invoice.version,
            'updated_at': datetime.now().isoformat()
        }
        self.table.put_item(Item=invoice_item)
        
        # Delete existing line items
        response = self.table.query(
            KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
            ExpressionAttributeValues={
                ':pk': f'INVOICE#{invoice.invoice_id}',
                ':sk': 'LINEITEM#'
            }
        )
        
        for item in response.get('Items', []):
            self.table.delete_item(Key={'PK': item['PK'], 'SK': item['SK']})
        
        # Save new line items
        for i, item in enumerate(invoice.line_items):
            line_item = {
                'PK': f'INVOICE#{invoice.invoice_id}',
                'SK': f'LINEITEM#{i+1:03d}',
                'description': item.description,
                'quantity': item.quantity,
                'unit_price': item.unit_price.amount,
                'currency': item.unit_price.currency,
                'line_total': item.line_total.amount
            }
            self.table.put_item(Item=line_item)
    
    def _save_status_history(self, invoice_id: str, old_status: str, new_status: str, reason: str):
        history_item = {
            'PK': f'INVOICE#{invoice_id}',
            'SK': f'HISTORY#{datetime.now().isoformat()}',
            'old_status': old_status,
            'new_status': new_status,
            'reason': reason,
            'changed_at': datetime.now().isoformat()
        }
        self.table.put_item(Item=history_item)
    
    def _save_payment_record(self, invoice_id: str, amount: Decimal, payment_type: str):
        payment_item = {
            'PK': f'INVOICE#{invoice_id}',
            'SK': f'PAYMENT#{datetime.now().isoformat()}',
            'amount': amount,
            'payment_type': payment_type,
            'payment_date': datetime.now().isoformat()
        }
        self.table.put_item(Item=payment_item)

# Lambda Handler
def lambda_handler(event, context):
    """Complete Invoice Management Lambda Handler"""
    
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Initialize services
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('InvoiceManagementTable')
        invoice_service = InvoiceApplicationService(table)
        
        # Route requests
        http_method = event.get('httpMethod', 'POST')
        path = event.get('path', '')
        
        if http_method == 'POST' and '/invoices' in path:
            return handle_create_invoice(event, invoice_service)
        elif http_method == 'GET' and '/invoices' in path:
            return handle_get_invoices(event, table, invoice_service)
        elif http_method == 'PUT' and '/invoices/' in path:
            return handle_update_invoice(event, invoice_service)
        elif http_method == 'DELETE' and '/invoices/' in path:
            return handle_delete_invoice(event, invoice_service)
        elif http_method == 'POST' and '/payments' in path:
            return handle_process_payment(event, invoice_service)
        elif http_method == 'POST' and '/overdue-check' in path:
            return handle_overdue_check(invoice_service)
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_create_invoice(event, invoice_service):
    """Handle invoice creation"""
    try:
        body = json.loads(event.get('body', '{}'))
        invoice = invoice_service.create_invoice(body)
        
        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'invoice_id': invoice.invoice_id,
                'invoice_number': invoice.invoice_number,
                'total_amount': float(invoice.total_amount.amount),
                'currency': invoice.total_amount.currency,
                'status': invoice.status.value,
                'message': 'Invoice created successfully'
            }, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to create invoice: {str(e)}'})
        }

def handle_get_invoices(event, table, invoice_service):
    """Handle getting invoices with optional filtering"""
    try:
        query_params = event.get('queryStringParameters') or {}
        invoice_id = query_params.get('invoice_id')
        
        if invoice_id:
            # Get specific invoice
            invoice = invoice_service._get_invoice_by_id(invoice_id)
            if not invoice:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invoice not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'invoice': {
                        'invoice_id': invoice.invoice_id,
                        'invoice_number': invoice.invoice_number,
                        'customer_name': invoice.customer_name,
                        'total_amount': float(invoice.total_amount.amount),
                        'currency': invoice.total_amount.currency,
                        'status': invoice.status.value,
                        'issue_date': invoice.issue_date.isoformat(),
                        'due_date': invoice.due_date.isoformat(),
                        'is_overdue': invoice.is_overdue,
                        'line_items': [
                            {
                                'description': item.description,
                                'quantity': float(item.quantity),
                                'unit_price': float(item.unit_price.amount),
                                'line_total': float(item.line_total.amount)
                            } for item in invoice.line_items
                        ]
                    }
                }, default=str)
            }
        else:
            # Get all invoices
            response = table.scan(
                FilterExpression='SK = :sk',
                ExpressionAttributeValues={':sk': 'METADATA'}
            )
            
            invoices = []
            for item in response.get('Items', []):
                invoices.append({
                    'invoice_id': item.get('invoice_id'),
                    'invoice_number': item.get('invoice_number'),
                    'customer_name': item.get('customer_name'),
                    'total_amount': float(item.get('total_amount', 0)),
                    'status': item.get('status'),
                    'due_date': item.get('due_date'),
                    'is_overdue': datetime.fromisoformat(item.get('due_date')) < datetime.now() and item.get('status') not in ['PAID', 'CANCELLED']
                })
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'invoices': invoices,
                    'count': len(invoices)
                }, default=str)
            }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to get invoices: {str(e)}'})
        }

def handle_update_invoice(event, invoice_service):
    """Handle invoice updates (status changes)"""
    try:
        path_params = event.get('pathParameters') or {}
        invoice_id = path_params.get('invoice_id')
        body = json.loads(event.get('body', '{}'))
        
        new_status = body.get('status')
        reason = body.get('reason', '')
        
        if not invoice_id or not new_status:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invoice_id and status are required'})
            }
        
        invoice = invoice_service.update_invoice_status(invoice_id, new_status, reason)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'invoice_id': invoice.invoice_id,
                'new_status': invoice.status.value,
                'message': 'Invoice status updated successfully'
            }, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to update invoice: {str(e)}'})
        }

def handle_delete_invoice(event, invoice_service):
    """Handle invoice deletion"""
    try:
        path_params = event.get('pathParameters') or {}
        invoice_id = path_params.get('invoice_id')
        
        if not invoice_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invoice_id is required'})
            }
        
        success = invoice_service.delete_invoice(invoice_id)
        
        if success:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Invoice deleted successfully'
                })
            }
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Invoice not found'})
            }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to delete invoice: {str(e)}'})
        }

def handle_process_payment(event, invoice_service):
    """Handle payment processing"""
    try:
        body = json.loads(event.get('body', '{}'))
        invoice_id = body.get('invoice_id')
        payment_amount = Decimal(str(body.get('payment_amount', 0)))
        
        if not invoice_id or payment_amount <= 0:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'invoice_id and payment_amount are required'})
            }
        
        invoice = invoice_service.process_payment(invoice_id, payment_amount)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'invoice_id': invoice.invoice_id,
                'payment_amount': float(payment_amount),
                'new_status': invoice.status.value,
                'message': 'Payment processed successfully'
            }, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to process payment: {str(e)}'})
        }

def handle_overdue_check(invoice_service):
    """Handle overdue invoice detection"""
    try:
        updated_invoices = invoice_service.detect_and_update_overdue()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'updated_invoices': updated_invoices,
                'count': len(updated_invoices),
                'message': f'Updated {len(updated_invoices)} overdue invoices'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to check overdue invoices: {str(e)}'})
        }