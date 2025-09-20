"""Simple Lambda handler for Invoice Management"""

import json
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

def lambda_handler(event, context):
    """Simple Lambda handler for creating invoices"""
    
    try:
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        table_name = 'InvoiceManagementTable'  # Will be set via environment variable
        table = dynamodb.Table(table_name)
        
        # Parse request
        if event.get('httpMethod') == 'POST':
            return handle_create_invoice(event, table)
        elif event.get('httpMethod') == 'GET':
            return handle_get_invoices(event, table)
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
            'body': json.dumps({'error': 'Internal server error'})
        }

def handle_create_invoice(event, table):
    """Handle invoice creation"""
    try:
        # Parse request body
        request_body = json.loads(event['body'])
        
        # Generate invoice data
        invoice_id = str(uuid.uuid4())
        invoice_number = f"INV-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"
        
        # Calculate total
        total_amount = 0
        for item in request_body['line_items']:
            total_amount += float(item['quantity']) * float(item['unit_price'])
        
        # Create invoice item
        invoice_item = {
            'PK': f'INVOICE#{invoice_id}',
            'SK': 'METADATA',
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'customer_id': request_body['customer_id'],
            'customer_name': request_body['customer_name'],
            'customer_email': request_body['customer_email'],
            'issue_date': request_body['issue_date'],
            'due_date': request_body['due_date'],
            'status': 'DRAFT',
            'total_amount': Decimal(str(total_amount)),
            'currency': request_body['line_items'][0].get('currency', 'USD'),
            'created_by': request_body['created_by'],
            'created_at': datetime.utcnow().isoformat(),
            'version': 1
        }
        
        # Save to DynamoDB
        table.put_item(Item=invoice_item)
        
        # Save line items
        for i, item in enumerate(request_body['line_items']):
            line_item = {
                'PK': f'INVOICE#{invoice_id}',
                'SK': f'LINEITEM#{i+1:03d}',
                'description': item['description'],
                'quantity': Decimal(str(item['quantity'])),
                'unit_price': Decimal(str(item['unit_price'])),
                'currency': item.get('currency', 'USD'),
                'line_total': Decimal(str(float(item['quantity']) * float(item['unit_price'])))
            }
            table.put_item(Item=line_item)
        
        # Return success response
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'invoice_id': invoice_id,
                'invoice_number': invoice_number,
                'total_amount': float(total_amount),
                'currency': request_body['line_items'][0].get('currency', 'USD'),
                'status': 'DRAFT',
                'created_at': datetime.utcnow().isoformat()
            }, default=str)
        }
        
    except Exception as e:
        print(f"Create invoice error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }

def handle_get_invoices(event, table):
    """Handle get invoices"""
    try:
        # Simple scan for all invoices (metadata only)
        response = table.scan(
            FilterExpression='SK = :sk',
            ExpressionAttributeValues={':sk': 'METADATA'}
        )
        
        invoices = []
        for item in response['Items']:
            invoices.append({
                'invoice_id': item['invoice_id'],
                'invoice_number': item['invoice_number'],
                'customer_name': item['customer_name'],
                'total_amount': float(item['total_amount']),
                'currency': item['currency'],
                'status': item['status'],
                'created_at': item['created_at']
            })
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'invoices': invoices,
                'count': len(invoices)
            }, default=str)
        }
        
    except Exception as e:
        print(f"Get invoices error: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)})
        }