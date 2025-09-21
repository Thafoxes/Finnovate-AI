"""
InnovateAI-Customer Lambda Function
Domain: Customer Management with DDD patterns
Handles: Customer CRUD, risk analysis, customer statistics
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

# Environment variables
CUSTOMER_TABLE_NAME = os.environ.get('CUSTOMER_TABLE_NAME', 'InvoiceManagementTable')

# Domain Models (DDD)
class CustomerRiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Customer:
    customer_id: str
    name: str
    email: str
    phone: str
    address: str
    risk_score: float
    total_invoices: int
    total_amount: float
    overdue_count: int
    created_date: str
    
    def get_risk_level(self) -> CustomerRiskLevel:
        """Domain logic: Determine risk level based on score"""
        if self.risk_score >= 80:
            return CustomerRiskLevel.CRITICAL
        elif self.risk_score >= 60:
            return CustomerRiskLevel.HIGH
        elif self.risk_score >= 30:
            return CustomerRiskLevel.MEDIUM
        else:
            return CustomerRiskLevel.LOW
    
    def calculate_risk_score(self, invoices: List[dict]) -> float:
        """Domain logic: Calculate customer risk score"""
        if not invoices:
            return 0.0
        
        total_invoices = len(invoices)
        overdue_invoices = len([inv for inv in invoices if inv.get('status') == 'OVERDUE'])
        total_amount = sum(float(inv.get('total_amount', 0)) for inv in invoices)
        overdue_amount = sum(float(inv.get('total_amount', 0)) for inv in invoices if inv.get('status') == 'OVERDUE')
        
        # Risk factors
        overdue_ratio = overdue_invoices / total_invoices if total_invoices > 0 else 0
        amount_at_risk = overdue_amount / total_amount if total_amount > 0 else 0
        
        # Calculate weighted risk score (0-100)
        risk_score = (overdue_ratio * 50) + (amount_at_risk * 30) + (min(overdue_invoices, 10) * 2)
        
        return min(risk_score, 100.0)

class CustomerRepository:
    """Repository pattern for Customer data access"""
    
    def __init__(self, table_name: str):
        self.table = dynamodb.Table(table_name)
    
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            response = self.table.get_item(
                Key={'PK': f'CUSTOMER#{customer_id}', 'SK': 'METADATA'}
            )
            if 'Item' in response:
                return self._item_to_customer(response['Item'])
            return None
        except Exception as e:
            print(f"Error getting customer {customer_id}: {e}")
            return None
    
    def get_all(self) -> List[Customer]:
        """Get all customers"""
        try:
            response = self.table.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk',
                ExpressionAttributeValues={
                    ':pk': 'CUSTOMER#',
                    ':sk': 'METADATA'
                }
            )
            return [self._item_to_customer(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error getting all customers: {e}")
            return []
    
    def get_high_risk_customers(self, risk_threshold: float = 60.0) -> List[Customer]:
        """Get customers with high risk scores"""
        try:
            response = self.table.scan(
                FilterExpression='begins_with(PK, :pk) AND SK = :sk AND risk_score >= :threshold',
                ExpressionAttributeValues={
                    ':pk': 'CUSTOMER#',
                    ':sk': 'METADATA',
                    ':threshold': risk_threshold
                }
            )
            return [self._item_to_customer(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"Error getting high risk customers: {e}")
            return []
    
    def save(self, customer: Customer) -> bool:
        """Save customer to database"""
        try:
            item = self._customer_to_item(customer)
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            print(f"Error saving customer: {e}")
            return False
    
    def update_risk_score(self, customer_id: str, risk_score: float) -> bool:
        """Update customer risk score"""
        try:
            self.table.update_item(
                Key={'PK': f'CUSTOMER#{customer_id}', 'SK': 'METADATA'},
                UpdateExpression='SET risk_score = :score, updated_date = :updated',
                ExpressionAttributeValues={
                    ':score': Decimal(str(risk_score)),
                    ':updated': datetime.now().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error updating customer risk score: {e}")
            return False
    
    def _item_to_customer(self, item: dict) -> Customer:
        """Convert DynamoDB item to Customer domain object"""
        return Customer(
            customer_id=item.get('customer_id', ''),
            name=item.get('name', ''),
            email=item.get('email', ''),
            phone=item.get('phone', ''),
            address=item.get('address', ''),
            risk_score=float(item.get('risk_score', 0)),
            total_invoices=int(item.get('total_invoices', 0)),
            total_amount=float(item.get('total_amount', 0)),
            overdue_count=int(item.get('overdue_count', 0)),
            created_date=item.get('created_date', '')
        )
    
    def _customer_to_item(self, customer: Customer) -> dict:
        """Convert Customer domain object to DynamoDB item"""
        return {
            'PK': f'CUSTOMER#{customer.customer_id}',
            'SK': 'METADATA',
            'customer_id': customer.customer_id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'risk_score': Decimal(str(customer.risk_score)),
            'total_invoices': customer.total_invoices,
            'total_amount': Decimal(str(customer.total_amount)),
            'overdue_count': customer.overdue_count,
            'created_date': customer.created_date,
            'updated_date': datetime.now().isoformat()
        }

class CustomerDomainService:
    """Domain service for Customer business logic"""
    
    def __init__(self, repository: CustomerRepository):
        self.repository = repository
    
    def get_customer_statistics(self) -> dict:
        """Get comprehensive customer statistics"""
        customers = self.repository.get_all()
        
        if not customers:
            return {
                'total_customers': 0,
                'high_risk_customers': 0,
                'average_risk_score': 0,
                'total_customer_value': 0,
                'risk_distribution': {
                    'LOW': 0,
                    'MEDIUM': 0, 
                    'HIGH': 0,
                    'CRITICAL': 0
                }
            }
        
        total_customers = len(customers)
        total_value = sum(c.total_amount for c in customers)
        average_risk = sum(c.risk_score for c in customers) / total_customers
        
        # Risk distribution
        risk_distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        for customer in customers:
            risk_level = customer.get_risk_level()
            risk_distribution[risk_level.value] += 1
        
        high_risk_count = risk_distribution['HIGH'] + risk_distribution['CRITICAL']
        
        return {
            'total_customers': total_customers,
            'high_risk_customers': high_risk_count,
            'average_risk_score': round(average_risk, 2),
            'total_customer_value': total_value,
            'risk_distribution': risk_distribution,
            'average_customer_value': total_value / total_customers if total_customers > 0 else 0
        }
    
    def get_risk_analysis(self) -> dict:
        """Get detailed risk analysis"""
        customers = self.repository.get_all()
        high_risk_customers = [c for c in customers if c.get_risk_level() in [CustomerRiskLevel.HIGH, CustomerRiskLevel.CRITICAL]]
        
        if not high_risk_customers:
            return {
                'high_risk_count': 0,
                'critical_customers': [],
                'total_at_risk_amount': 0,
                'recommendations': ['No high-risk customers identified']
            }
        
        critical_customers = [c for c in high_risk_customers if c.get_risk_level() == CustomerRiskLevel.CRITICAL]
        total_at_risk = sum(c.total_amount for c in high_risk_customers)
        
        # Generate recommendations
        recommendations = []
        if len(critical_customers) > 0:
            recommendations.append(f"Immediate attention needed for {len(critical_customers)} critical customers")
        if total_at_risk > 10000:
            recommendations.append(f"${total_at_risk:,.2f} total amount at risk - consider payment plans")
        if len(high_risk_customers) > len(customers) * 0.3:
            recommendations.append("High percentage of risky customers - review credit policies")
        
        return {
            'high_risk_count': len(high_risk_customers),
            'critical_customers': [
                {
                    'customer_id': c.customer_id,
                    'name': c.name,
                    'risk_score': c.risk_score,
                    'total_amount': c.total_amount,
                    'overdue_count': c.overdue_count
                } for c in critical_customers[:10]  # Limit to top 10
            ],
            'total_at_risk_amount': total_at_risk,
            'recommendations': recommendations
        }

# Lambda Handler Functions
def handle_get_customer_statistics(domain_service: CustomerDomainService):
    """Handle get customer statistics request"""
    try:
        stats = domain_service.get_customer_statistics()
        return success_response(stats)
    except Exception as e:
        return error_response(f"Error getting customer statistics: {str(e)}")

def handle_get_customer_by_id(repository: CustomerRepository, params: dict):
    """Handle get customer by ID request"""
    try:
        customer_id = params.get('customer_id')
        if not customer_id:
            return error_response("customer_id is required", 400)
        
        customer = repository.get_by_id(customer_id)
        if not customer:
            return error_response(f"Customer {customer_id} not found", 404)
        
        return success_response({
            'customer_id': customer.customer_id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone,
            'address': customer.address,
            'risk_score': customer.risk_score,
            'risk_level': customer.get_risk_level().value,
            'total_invoices': customer.total_invoices,
            'total_amount': customer.total_amount,
            'overdue_count': customer.overdue_count,
            'created_date': customer.created_date
        })
    except Exception as e:
        return error_response(f"Error getting customer: {str(e)}")

def handle_get_all_customers(repository: CustomerRepository, params: dict):
    """Handle get all customers request"""
    try:
        customers = repository.get_all()
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'customer_id': customer.customer_id,
                'name': customer.name,
                'email': customer.email,
                'risk_score': customer.risk_score,
                'risk_level': customer.get_risk_level().value,
                'total_invoices': customer.total_invoices,
                'total_amount': customer.total_amount,
                'overdue_count': customer.overdue_count
            })
        
        return success_response({
            'customers': customer_data,
            'total_count': len(customer_data)
        })
    except Exception as e:
        return error_response(f"Error getting customers: {str(e)}")

def handle_get_high_risk_customers(repository: CustomerRepository, params: dict):
    """Handle get high risk customers request"""
    try:
        risk_threshold = float(params.get('risk_threshold', 60.0))
        customers = repository.get_high_risk_customers(risk_threshold)
        
        customer_data = []
        for customer in customers:
            customer_data.append({
                'customer_id': customer.customer_id,
                'name': customer.name,
                'email': customer.email,
                'risk_score': customer.risk_score,
                'risk_level': customer.get_risk_level().value,
                'total_amount': customer.total_amount,
                'overdue_count': customer.overdue_count
            })
        
        return success_response({
            'high_risk_customers': customer_data,
            'total_count': len(customer_data),
            'risk_threshold': risk_threshold
        })
    except Exception as e:
        return error_response(f"Error getting high risk customers: {str(e)}")

def handle_get_risk_analysis(domain_service: CustomerDomainService):
    """Handle get risk analysis request"""
    try:
        analysis = domain_service.get_risk_analysis()
        return success_response(analysis)
    except Exception as e:
        return error_response(f"Error getting risk analysis: {str(e)}")

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
    Customer Lambda Handler - Routes internal service calls
    Designed to be called by other Lambdas, not directly from API Gateway
    """
    try:
        print(f"=== CUSTOMER LAMBDA HANDLER ===")
        print(f"Event: {json.dumps(event)}")
        
        # Initialize repository and services
        repository = CustomerRepository(CUSTOMER_TABLE_NAME)
        domain_service = CustomerDomainService(repository)
        
        # Get action and parameters from event
        action = event.get('action', '')
        params = event.get('params', {})
        
        print(f"Action: {action}, Params: {params}")
        
        # Route based on action
        if action == 'get_customer_statistics':
            return handle_get_customer_statistics(domain_service)
        elif action == 'get_customer_by_id':
            return handle_get_customer_by_id(repository, params)
        elif action == 'get_all_customers':
            return handle_get_all_customers(repository, params)
        elif action == 'get_high_risk_customers':
            return handle_get_high_risk_customers(repository, params)
        elif action == 'get_risk_analysis':
            return handle_get_risk_analysis(domain_service)
        else:
            return error_response(f"Unknown action: {action}", 400)
            
    except Exception as e:
        print(f"Customer Lambda error: {e}")
        return error_response(f"Internal server error: {str(e)}")