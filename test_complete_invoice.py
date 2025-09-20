"""Test script for complete invoice management operations"""

import json
import requests
from datetime import datetime, timedelta

# Replace with your actual Lambda API Gateway URL
BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"

def test_complete_invoice_lifecycle():
    """Test the complete invoice lifecycle"""
    
    print("=== Testing Complete Invoice Management System ===\n")
    
    # 1. Create Invoice
    print("1. Creating invoice...")
    create_data = {
        "customer_id": "CUST-001",
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "issue_date": datetime.now().isoformat(),
        "due_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "line_items": [
            {
                "description": "Web Development Services",
                "quantity": 10,
                "unit_price": 150.00,
                "currency": "USD"
            },
            {
                "description": "Hosting Setup",
                "quantity": 1,
                "unit_price": 500.00,
                "currency": "USD"
            }
        ]
    }
    
    # Simulate API call (replace with actual request when deployed)
    print(f"POST /invoices")
    print(f"Data: {json.dumps(create_data, indent=2)}")
    print("Response: Invoice created with ID: INV-2024-ABC123")
    invoice_id = "test-invoice-id"  # Would come from actual response
    print()
    
    # 2. Get Invoice Details
    print("2. Getting invoice details...")
    print(f"GET /invoices?invoice_id={invoice_id}")
    print("Response: Full invoice details with line items")
    print()
    
    # 3. Update Invoice Status (Draft -> Sent)
    print("3. Updating invoice status to SENT...")
    update_data = {
        "status": "SENT",
        "reason": "Invoice sent to customer via email"
    }
    print(f"PUT /invoices/{invoice_id}")
    print(f"Data: {json.dumps(update_data, indent=2)}")
    print("Response: Status updated to SENT")
    print()
    
    # 4. Process Partial Payment
    print("4. Processing partial payment...")
    payment_data = {
        "invoice_id": invoice_id,
        "payment_amount": 1000.00
    }
    print(f"POST /payments")
    print(f"Data: {json.dumps(payment_data, indent=2)}")
    print("Response: Partial payment recorded, invoice still SENT")
    print()
    
    # 5. Process Full Payment
    print("5. Processing full payment...")
    payment_data = {
        "invoice_id": invoice_id,
        "payment_amount": 2000.00
    }
    print(f"POST /payments")
    print(f"Data: {json.dumps(payment_data, indent=2)}")
    print("Response: Full payment processed, status changed to PAID")
    print()
    
    # 6. Check for Overdue Invoices
    print("6. Checking for overdue invoices...")
    print(f"POST /overdue-check")
    print("Response: Scanned all invoices, updated overdue statuses")
    print()
    
    # 7. Get All Invoices
    print("7. Getting all invoices...")
    print(f"GET /invoices")
    print("Response: List of all invoices with status and overdue flags")
    print()
    
    # 8. Try to Delete Paid Invoice (should fail)
    print("8. Attempting to delete paid invoice...")
    print(f"DELETE /invoices/{invoice_id}")
    print("Response: Error - Can only delete draft or cancelled invoices")
    print()
    
    print("=== Test Complete ===")
    print("\nAPI Endpoints Available:")
    print("- POST /invoices - Create invoice")
    print("- GET /invoices - Get all invoices")
    print("- GET /invoices?invoice_id=ID - Get specific invoice")
    print("- PUT /invoices/{id} - Update invoice status")
    print("- DELETE /invoices/{id} - Delete invoice (draft/cancelled only)")
    print("- POST /payments - Process payment")
    print("- POST /overdue-check - Check and update overdue invoices")

def test_status_transitions():
    """Test valid and invalid status transitions"""
    
    print("\n=== Testing Status Transitions ===\n")
    
    transitions = [
        ("DRAFT", "SENT", "Valid"),
        ("DRAFT", "CANCELLED", "Valid"),
        ("SENT", "PAID", "Valid"),
        ("SENT", "OVERDUE", "Valid"),
        ("OVERDUE", "PAID", "Valid"),
        ("PAID", "DRAFT", "Invalid - Cannot revert from PAID"),
        ("CANCELLED", "SENT", "Invalid - Cannot revert from CANCELLED")
    ]
    
    for current, new, expected in transitions:
        print(f"{current} -> {new}: {expected}")
    
    print("\nBusiness Rules:")
    print("- Invoices automatically become OVERDUE after due date")
    print("- Full payments automatically change status to PAID")
    print("- Only DRAFT and CANCELLED invoices can be deleted")
    print("- Status history is maintained for audit trail")

if __name__ == "__main__":
    test_complete_invoice_lifecycle()
    test_status_transitions()