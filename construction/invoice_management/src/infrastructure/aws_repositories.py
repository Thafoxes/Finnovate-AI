import boto3
import json
from decimal import Decimal
from typing import List, Optional
from domain.aggregates import InvoiceAggregate
from domain.value_objects import InvoiceId, CustomerId, InvoiceStatus
from domain.entities import Invoice, InvoiceLineItem, InvoiceStatusHistory
from infrastructure.repositories import IInvoiceRepository

class DynamoDbInvoiceRepository(IInvoiceRepository):
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def save(self, invoice_aggregate: InvoiceAggregate) -> None:
        # Convert aggregate to DynamoDB format
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
        
        # Use batch writer for consistency
        with self.table.batch_writer() as batch:
            batch.put_item(Item=invoice_item)
            
            # Add line items
            for item in invoice.line_items:
                line_item = {
                    'PK': f'INVOICE#{invoice.invoice_id}',
                    'SK': f'LINEITEM#{item.line_item_id}',
                    'description': item.description,
                    'quantity': float(item.quantity),
                    'unit_price': float(item.unit_price.amount),
                    'currency': item.unit_price.currency
                }
                batch.put_item(Item=line_item)
    
    def get_by_id(self, invoice_id: InvoiceId) -> Optional[InvoiceAggregate]:
        # Query all items for this invoice
        response = self.table.query(
            KeyConditionExpression='PK = :pk',
            ExpressionAttributeValues={':pk': f'INVOICE#{invoice_id}'}
        )
        
        if not response['Items']:
            return None
        
        # Reconstruct invoice aggregate from DynamoDB items
        # (Implementation details for reconstruction)
        return self._reconstruct_invoice(response['Items'])
    
    def get_all(self) -> List[InvoiceAggregate]:
        # Scan table for all invoices (simplified)
        response = self.table.scan()
        # Group and reconstruct invoices
        return self._reconstruct_invoices(response['Items'])
    
    def _reconstruct_invoice(self, items) -> InvoiceAggregate:
        # Implementation to rebuild aggregate from DynamoDB items
        pass