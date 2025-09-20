"""AWS DynamoDB Repository Implementation"""

import boto3
from typing import List, Optional
from ..domain.aggregates import InvoiceAggregate
from ..domain.value_objects import InvoiceId, CustomerId, InvoiceStatus
from ..infrastructure.repositories import IInvoiceRepository

class DynamoDbInvoiceRepository(IInvoiceRepository):
    """DynamoDB implementation of invoice repository"""
    
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def save(self, invoice_aggregate: InvoiceAggregate) -> None:
        """Save invoice aggregate to DynamoDB"""
        invoice = invoice_aggregate.invoice
        
        # Main invoice item
        invoice_item = {
            'PK': f'INVOICE#{invoice.invoice_id}',
            'SK': 'METADATA',
            'invoice_id': str(invoice.invoice_id),
            'invoice_number': str(invoice.invoice_number),
            'customer_id': str(invoice.customer_reference.customer_id),
            'customer_name': invoice.customer_reference.cached_name,
            'customer_email': invoice.customer_reference.cached_email,
            'issue_date': invoice.issue_date.isoformat(),
            'due_date': invoice.due_date.isoformat(),
            'status': invoice.status.value,
            'total_amount': float(invoice.total_amount.amount),
            'currency': invoice.total_amount.currency,
            'version': invoice.version
        }
        
        # Save main item
        self.table.put_item(Item=invoice_item)
        
        # Save line items
        for item in invoice.line_items:
            line_item = {
                'PK': f'INVOICE#{invoice.invoice_id}',
                'SK': f'LINEITEM#{item.line_item_id}',
                'description': item.description,
                'quantity': float(item.quantity),
                'unit_price': float(item.unit_price.amount),
                'currency': item.unit_price.currency
            }
            self.table.put_item(Item=line_item)
    
    def get_by_id(self, invoice_id: InvoiceId) -> Optional[InvoiceAggregate]:
        """Get invoice by ID - simplified implementation"""
        try:
            response = self.table.get_item(
                Key={
                    'PK': f'INVOICE#{invoice_id}',
                    'SK': 'METADATA'
                }
            )
            
            if 'Item' not in response:
                return None
            
            # For now, return None - full reconstruction would be complex
            # In production, you'd reconstruct the full aggregate here
            return None
            
        except Exception as e:
            print(f"Error getting invoice: {e}")
            return None
    
    def get_by_number(self, invoice_number: str) -> Optional[InvoiceAggregate]:
        """Get invoice by number - not implemented for simplicity"""
        return None
    
    def get_by_customer_id(self, customer_id: CustomerId) -> List[InvoiceAggregate]:
        """Get invoices by customer - not implemented for simplicity"""
        return []
    
    def get_by_status(self, status: InvoiceStatus) -> List[InvoiceAggregate]:
        """Get invoices by status - not implemented for simplicity"""
        return []
    
    def get_all(self) -> List[InvoiceAggregate]:
        """Get all invoices - not implemented for simplicity"""
        return []
    
    def delete(self, invoice_id: InvoiceId) -> bool:
        """Delete invoice - not implemented for simplicity"""
        return False