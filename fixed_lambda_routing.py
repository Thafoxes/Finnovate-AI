"""Fixed Lambda routing for proper GET/POST handling"""

# Add this to your existing Lambda code - replace the lambda_handler function

def lambda_handler(event, context):
    """Fixed Lambda handler with proper routing"""
    
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Initialize services
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('InvoiceManagementTable')
        invoice_service = InvoiceApplicationService(table)
        
        # Get routing information
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        path_params = event.get('pathParameters') or {}
        
        print(f"Method: {http_method}, Path: {path}")
        print(f"Query params: {query_params}")
        print(f"Path params: {path_params}")
        
        # Route based on method and path
        if http_method == 'POST' and path == '/invoices':
            return handle_create_invoice(event, invoice_service)
            
        elif http_method == 'GET' and path == '/invoices':
            # Check if specific invoice requested via query parameter
            invoice_id = query_params.get('invoice_id')
            if invoice_id:
                return handle_get_specific_invoice(invoice_id, invoice_service)
            else:
                return handle_get_all_invoices(table)
                
        elif http_method == 'GET' and '/invoices/' in path:
            # Handle /invoices/{invoice_id} path parameter
            invoice_id = path_params.get('invoice_id')
            if invoice_id:
                return handle_get_specific_invoice(invoice_id, invoice_service)
            else:
                return error_response(400, "Invoice ID is required")
                
        elif http_method == 'PUT' and '/invoices/' in path:
            return handle_update_invoice(event, invoice_service)
            
        elif http_method == 'DELETE' and '/invoices/' in path:
            return handle_delete_invoice(event, invoice_service)
            
        elif http_method == 'POST' and path == '/payments':
            return handle_process_payment(event, invoice_service)
            
        elif http_method == 'POST' and path == '/overdue-check':
            return handle_overdue_check(invoice_service)
            
        else:
            return error_response(404, f"Endpoint not found: {http_method} {path}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, f"Internal server error: {str(e)}")

def handle_get_specific_invoice(invoice_id, invoice_service):
    """Handle getting a specific invoice"""
    try:
        invoice = invoice_service._get_invoice_by_id(invoice_id)
        if not invoice:
            return error_response(404, "Invoice not found")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'invoice': {
                    'invoice_id': invoice.invoice_id,
                    'invoice_number': invoice.invoice_number,
                    'customer_name': invoice.customer_name,
                    'customer_email': invoice.customer_email,
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
        
    except Exception as e:
        return error_response(400, f"Failed to get invoice: {str(e)}")

def handle_get_all_invoices(table):
    """Handle getting all invoices"""
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
        return error_response(400, f"Failed to get invoices: {str(e)}")

def error_response(status_code, message):
    """Helper function for error responses"""
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'error': message})
    }

# Also fix the create_invoice method in InvoiceApplicationService
def create_invoice_fixed(self, command_data: dict) -> Invoice:
    """Fixed create_invoice method"""
    # Create line items - FIX: Handle empty line_items
    line_items = []
    for item_data in command_data.get('line_items', []):
        print(f"Processing line item: {item_data}")  # Debug log
        line_item = InvoiceLineItem(
            description=item_data['description'],
            quantity=Decimal(str(item_data['quantity'])),
            unit_price=Money(Decimal(str(item_data['unit_price'])), 
                           item_data.get('currency', 'USD'))
        )
        line_items.append(line_item)
    
    print(f"Created {len(line_items)} line items")  # Debug log
    
    # Create invoice
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
    
    print(f"Invoice total: {invoice.total_amount.amount}")  # Debug log
    
    # Save to DynamoDB
    self._save_invoice(invoice)
    
    return invoice