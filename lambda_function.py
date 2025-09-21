import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = 'InvoiceManagementTable'
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Lambda function for Bedrock Agent actions
    Handles invoice management operations for the PaymentIntelligenceAgent
    """
    print(f"Function called with event: {json.dumps(event)}")
    
    try:
        # Parse the incoming request
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', 'GET')
        parameters = event.get('parameters', [])
        
        print(f"Action Group: {action_group}")
        print(f"API Path: {api_path}")
        print(f"HTTP Method: {http_method}")
        print(f"Parameters: {parameters}")
        
        # Handle different API paths
        if api_path == '/get_overdue_invoices' and http_method == 'GET':
            return get_overdue_invoices()
        elif api_path == '/get_all_invoices' and http_method == 'GET':
            return get_all_invoices()
        elif api_path == '/get_customer_statistics' and http_method == 'GET':
            return get_customer_statistics()
        else:
            return {
                'messageVersion': '1.0',
                'response': {
                    'actionGroup': action_group,
                    'apiPath': api_path,
                    'httpMethod': http_method,
                    'httpStatusCode': 400,
                    'responseBody': {
                        'application/json': {
                            'body': json.dumps({
                                'error': f'Unsupported API path: {api_path}',
                                'supported_paths': ['/get_overdue_invoices', '/get_all_invoices', '/get_customer_statistics']
                            })
                        }
                    }
                }
            }
            
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': f'Internal server error: {str(e)}'
                        })
                    }
                }
            }
        }

def get_overdue_invoices():
    """Get all overdue invoices from DynamoDB"""
    try:
        # Scan for all invoices that are overdue
        current_date = datetime.now().isoformat()
        
        response = table.scan(
            FilterExpression=Attr('SK').eq('METADATA') & 
                           (Attr('status').eq('OVERDUE') | 
                            (Attr('due_date').lt(current_date) & Attr('status').ne('PAID')))
        )
        
        invoices = response.get('Items', [])
        
        # Calculate summary statistics
        total_overdue_amount = sum(float(inv.get('remaining_balance', 0)) for inv in invoices)
        overdue_count = len(invoices)
        
        # Format invoices for response
        formatted_invoices = []
        for invoice in invoices:
            formatted_invoices.append({
                'invoice_id': invoice.get('invoice_id', ''),
                'invoice_number': invoice.get('invoice_number', ''),
                'customer_name': invoice.get('customer_name', ''),
                'customer_email': invoice.get('customer_email', ''),
                'total_amount': float(invoice.get('total_amount', 0)),
                'remaining_balance': float(invoice.get('remaining_balance', 0)),
                'due_date': invoice.get('due_date', ''),
                'days_overdue': calculate_days_overdue(invoice.get('due_date', '')),
                'status': invoice.get('status', '')
            })
        
        result = {
            'summary': {
                'total_overdue_invoices': overdue_count,
                'total_overdue_amount': total_overdue_amount,
                'average_overdue_amount': total_overdue_amount / max(overdue_count, 1)
            },
            'overdue_invoices': formatted_invoices
        }
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'InvoiceManagement',
                'apiPath': '/get_overdue_invoices',
                'httpMethod': 'GET',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error getting overdue invoices: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'InvoiceManagement',
                'apiPath': '/get_overdue_invoices',
                'httpMethod': 'GET',
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': f'Failed to retrieve overdue invoices: {str(e)}'
                        })
                    }
                }
            }
        }

def get_all_invoices():
    """Get all invoices from DynamoDB"""
    try:
        response = table.scan(
            FilterExpression=Attr('SK').eq('METADATA')
        )
        
        invoices = response.get('Items', [])
        
        # Calculate statistics
        total_invoices = len(invoices)
        total_amount = sum(float(inv.get('total_amount', 0)) for inv in invoices)
        paid_invoices = len([inv for inv in invoices if inv.get('status') == 'PAID'])
        overdue_invoices = len([inv for inv in invoices if inv.get('status') == 'OVERDUE'])
        
        result = {
            'summary': {
                'total_invoices': total_invoices,
                'total_amount': total_amount,
                'paid_invoices': paid_invoices,
                'overdue_invoices': overdue_invoices,
                'collection_rate': (paid_invoices / max(total_invoices, 1)) * 100
            },
            'invoices': [format_invoice(inv) for inv in invoices[:20]]  # Limit to 20 for response size
        }
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'InvoiceManagement',
                'apiPath': '/get_all_invoices',
                'httpMethod': 'GET',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error getting all invoices: {str(e)}")
        return error_response('InvoiceManagement', '/get_all_invoices', 'GET', str(e))

def get_customer_statistics():
    """Get customer payment statistics"""
    try:
        # Get all invoices
        response = table.scan(
            FilterExpression=Attr('SK').eq('METADATA')
        )
        
        invoices = response.get('Items', [])
        
        # Group by customer
        customers = {}
        for invoice in invoices:
            customer_id = invoice.get('customer_id', 'unknown')
            if customer_id not in customers:
                customers[customer_id] = {
                    'customer_name': invoice.get('customer_name', 'Unknown'),
                    'customer_email': invoice.get('customer_email', ''),
                    'total_invoices': 0,
                    'total_amount': 0,
                    'paid_amount': 0,
                    'overdue_amount': 0,
                    'overdue_count': 0
                }
            
            customers[customer_id]['total_invoices'] += 1
            customers[customer_id]['total_amount'] += float(invoice.get('total_amount', 0))
            customers[customer_id]['paid_amount'] += float(invoice.get('paid_amount', 0))
            
            if invoice.get('status') == 'OVERDUE':
                customers[customer_id]['overdue_amount'] += float(invoice.get('remaining_balance', 0))
                customers[customer_id]['overdue_count'] += 1
        
        # Convert to list and sort by risk (overdue amount)
        customer_stats = []
        for customer_id, stats in customers.items():
            customer_stats.append({
                'customer_id': customer_id,
                'customer_name': stats['customer_name'],
                'customer_email': stats['customer_email'],
                'total_invoices': stats['total_invoices'],
                'total_amount': stats['total_amount'],
                'paid_amount': stats['paid_amount'],
                'overdue_amount': stats['overdue_amount'],
                'overdue_count': stats['overdue_count'],
                'payment_rate': (stats['paid_amount'] / max(stats['total_amount'], 1)) * 100,
                'risk_level': 'High' if stats['overdue_amount'] > 1000 else 'Medium' if stats['overdue_amount'] > 100 else 'Low'
            })
        
        # Sort by overdue amount (highest risk first)
        customer_stats.sort(key=lambda x: x['overdue_amount'], reverse=True)
        
        result = {
            'summary': {
                'total_customers': len(customer_stats),
                'high_risk_customers': len([c for c in customer_stats if c['risk_level'] == 'High']),
                'total_overdue_across_customers': sum(c['overdue_amount'] for c in customer_stats)
            },
            'customers': customer_stats[:15]  # Top 15 customers by risk
        }
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'InvoiceManagement',
                'apiPath': '/get_customer_statistics',
                'httpMethod': 'GET',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        print(f"Error getting customer statistics: {str(e)}")
        return error_response('InvoiceManagement', '/get_customer_statistics', 'GET', str(e))

def format_invoice(invoice):
    """Format invoice for API response"""
    return {
        'invoice_id': invoice.get('invoice_id', ''),
        'invoice_number': invoice.get('invoice_number', ''),
        'customer_name': invoice.get('customer_name', ''),
        'total_amount': float(invoice.get('total_amount', 0)),
        'remaining_balance': float(invoice.get('remaining_balance', 0)),
        'status': invoice.get('status', ''),
        'due_date': invoice.get('due_date', ''),
        'issue_date': invoice.get('issue_date', '')
    }

def calculate_days_overdue(due_date_str):
    """Calculate days overdue from due date string"""
    try:
        if not due_date_str:
            return 0
        due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
        current_date = datetime.now(due_date.tzinfo)
        if current_date > due_date:
            return (current_date - due_date).days
        return 0
    except:
        return 0

def error_response(action_group, api_path, http_method, error_message):
    """Generate standardized error response"""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 500,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'error': error_message
                    })
                }
            }
        }
    }