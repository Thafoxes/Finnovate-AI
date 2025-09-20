"""Enhanced Lambda with DDD concepts - Single File Approach"""

import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Domain Value Objects (in same file)
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

# Domain Entity (simplified)
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

# Domain Service
class InvoiceNumberGenerator:
    @staticmethod
    def generate() -> str:
        return f"INV-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"

# Application Service
class InvoiceApplicationService:
    def __init__(self, dynamodb_table):
        self.table = dynamodb_table
        self.number_generator = InvoiceNumberGenerator()
    
    def create_invoice(self, command_data: dict) -> Invoice:
        # Create line items
        line_items = []
        for item_data in command_data.get('line_items', []):
            line_item = InvoiceLineItem(
                description=item_data['description'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Money(Decimal(str(item_data['unit_price'])), 
                               item_data.get('currency', 'USD'))
            )
            line_items.append(line_item)
        
        # Create invoice
        invoice = Invoice(
            invoice_id=str(uuid.uuid4()),
            invoice_number=self.number_generator.generate(),
            customer_id=command_data.get('customer_id', 'unknown'),
            customer_name=command_data.get('customer_name', 'Unknown'),
            customer_email=command_data.get('customer_email', 'unknown@example.com'),
            issue_date=datetime.fromisoformat(command_data.get('issue_date', datetime.now().isoformat())),
            due_date=datetime.fromisoformat(command_data.get('due_date', datetime.now().isoformat())),
            status=InvoiceStatus.DRAFT,
            line_items=line_items
        )
        
        # Save to DynamoDB
        self._save_invoice(invoice)
        
        return invoice
    
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
            'created_at': datetime.now().isoformat()
        }
        self.table.put_item(Item=invoice_item)
        
        # Save line items
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

# Lambda Handler
def lambda_handler(event, context):
    """Enhanced Lambda handler with DDD concepts"""
    
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Initialize services
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('InvoiceManagementTable')
        invoice_service = InvoiceApplicationService(table)
        
        # Route requests
        http_method = event.get('httpMethod', 'POST')
        
        if http_method == 'POST':
            return handle_create_invoice(event, invoice_service)
        elif http_method == 'GET':
            return handle_get_invoices(table)
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Method not allowed'})
            }
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }

def handle_create_invoice(event, invoice_service):
    """Handle invoice creation with DDD"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Use application service
        invoice = invoice_service.create_invoice(body)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
            'success': True,
            'invoice_id': invoice.invoice_id,
            'invoice_number': invoice.invoice_number,
            'total_amount': float(invoice.total_amount.amount),
            'currency': invoice.total_amount.currency,
            'status': invoice.status.value,
            'line_items_count': len(invoice.line_items),
            'message': 'Invoice created successfully with DDD'
        }, default=str)  # Add this default=str parameter

        }
        
    except Exception as e:
        print(f"Create invoice error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to create invoice: {str(e)}'})
        }

def handle_get_invoices(table):
    """Get invoices (same as before)"""
    try:
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
                'total_amount': item.get('total_amount', 0),
                'status': item.get('status'),
                'created_at': item.get('created_at')
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': True,
                'invoices': invoices,
                'count': len(invoices),
                'message': 'Retrieved with DDD architecture'
            })
        }
        
    except Exception as e:
        print(f"Get invoices error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': f'Failed to get invoices: {str(e)}'})
        }