"""Test data generator for Invoice Management System"""

import boto3
import json
from datetime import datetime, timedelta
import uuid

def generate_test_data():
    """Generate sample invoices for testing"""
    
    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('InvoiceManagementTable')
    
    # Sample customers
    customers = [
        {"id": "CUST001", "name": "Acme Corporation", "email": "billing@acme.com"},
        {"id": "CUST002", "name": "TechStart Inc", "email": "finance@techstart.com"},
        {"id": "CUST003", "name": "Global Solutions", "email": "accounts@globalsol.com"},
        {"id": "CUST004", "name": "Innovation Labs", "email": "billing@innovlabs.com"},
        {"id": "CUST005", "name": "Future Systems", "email": "payments@futuresys.com"}
    ]
    
    # Generate invoices
    invoices = []
    statuses = ['DRAFT', 'SENT', 'PAID', 'OVERDUE']
    
    for i in range(20):  # Generate 20 test invoices
        customer = customers[i % len(customers)]
        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-2024-{str(i+1).zfill(3)}"
        
        # Random amounts
        amounts = [1500, 2500, 3200, 4800, 1200, 6500, 2800, 3900, 5200, 1800]
        total_amount = amounts[i % len(amounts)]
        
        # Status distribution
        status = statuses[i % len(statuses)]
        
        # Calculate paid amount based on status
        if status == 'PAID':
            paid_amount = total_amount
            remaining_balance = 0
        elif status == 'OVERDUE':
            paid_amount = total_amount * 0.3  # 30% paid
            remaining_balance = total_amount - paid_amount
        elif status == 'SENT':
            paid_amount = 0
            remaining_balance = total_amount
        else:  # DRAFT
            paid_amount = 0
            remaining_balance = total_amount
        
        # Dates
        issue_date = datetime.now() - timedelta(days=30-i)
        due_date = issue_date + timedelta(days=30)
        
        invoice_item = {
            'PK': f'INVOICE#{invoice_id}',
            'SK': 'METADATA',
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'customer_id': customer['id'],
            'customer_name': customer['name'],
            'customer_email': customer['email'],
            'issue_date': issue_date.isoformat(),
            'due_date': due_date.isoformat(),
            'status': status,
            'total_amount': total_amount,
            'paid_amount': paid_amount,
            'remaining_balance': remaining_balance,
            'currency': 'USD',
            'version': 1,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        invoices.append(invoice_item)
        
        # Add line item
        line_item = {
            'PK': f'INVOICE#{invoice_id}',
            'SK': 'LINEITEM#001',
            'description': f'Professional Services - Project {i+1}',
            'quantity': 1,
            'unit_price': total_amount,
            'currency': 'USD',
            'line_total': total_amount
        }
        
        invoices.append(line_item)
    
    # Batch write to DynamoDB
    print(f"Writing {len(invoices)} items to DynamoDB...")
    
    # Write in batches of 25 (DynamoDB limit)
    batch_size = 25
    for i in range(0, len(invoices), batch_size):
        batch = invoices[i:i + batch_size]
        
        with table.batch_writer() as batch_writer:
            for item in batch:
                batch_writer.put_item(Item=item)
        
        print(f"Written batch {i//batch_size + 1}")
    
    print("Test data generation completed!")
    
    # Verify data
    response = table.scan(
        FilterExpression='SK = :sk',
        ExpressionAttributeValues={':sk': 'METADATA'}
    )
    
    print(f"Total invoices in database: {len(response['Items'])}")
    
    # Show sample data
    for item in response['Items'][:3]:
        print(f"Sample: {item['invoice_number']} - {item['customer_name']} - ${item['total_amount']} - {item['status']}")

if __name__ == "__main__":
    generate_test_data()