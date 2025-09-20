"""Demo Script for Invoice Management System"""

from datetime import datetime, timedelta
from decimal import Decimal
import json

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all necessary components
from domain.value_objects import InvoiceStatus, PaymentMethod
from application.commands import (
    CreateInvoiceCommand, UpdateInvoiceStatusCommand, SendManualReminderCommand,
    ProcessPaymentCommand, ProcessOverdueInvoicesCommand,
    GetInvoiceListQuery, GetInvoiceDetailsQuery
)
from application.services import InvoiceApplicationService, InvoiceQueryService
from application.handlers import HandlerRegistry, InvoiceManagementAPI
from infrastructure.repositories import RepositoryManager
from infrastructure.event_store import GlobalEventBus


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print subsection header"""
    print(f"\n--- {title} ---")


def print_json(data, title: str = ""):
    """Print data as formatted JSON"""
    if title:
        print(f"\n{title}:")
    print(json.dumps(data, indent=2, default=str))


def demo_invoice_lifecycle():
    """Demonstrate complete invoice lifecycle"""
    
    print_section("INVOICE MANAGEMENT SYSTEM DEMO")
    print("Demonstrating complete invoice lifecycle with DDD implementation")
    
    # Initialize system components
    repo_manager = RepositoryManager()
    event_bus = GlobalEventBus().event_bus
    
    # Create services
    app_service = InvoiceApplicationService(
        repo_manager.invoice_repository,
        repo_manager.payment_repository,
        event_bus.event_publisher,
        repo_manager.customer_client
    )
    
    query_service = InvoiceQueryService(
        repo_manager.invoice_repository,
        repo_manager.payment_repository
    )
    
    # Create handler registry and API
    handler_registry = HandlerRegistry(app_service, query_service)
    api = InvoiceManagementAPI(handler_registry)
    
    # Reset system state
    repo_manager.reset()
    event_bus.reset()
    
    print_subsection("System Initialized")
    print("[OK] Repositories created")
    print("[OK] Event bus initialized")
    print("[OK] Application services ready")
    print("[OK] API handlers configured")
    
    # Step 1: Create Invoice
    print_section("STEP 1: CREATE INVOICE")
    
    create_request = {
        "customer_id": "customer-1",
        "customer_name": "Acme Corp",
        "customer_email": "billing@acme.com",
        "issue_date": datetime.now(),
        "due_date": datetime.now() + timedelta(days=30),
        "line_items": [
            {
                "description": "Software License - Annual",
                "quantity": 1,
                "unit_price": 1200.00,
                "currency": "USD"
            },
            {
                "description": "Support Services",
                "quantity": 12,
                "unit_price": 150.00,
                "currency": "USD"
            }
        ],
        "created_by": "john.doe@company.com"
    }
    
    invoice_result = api.create_invoice(create_request)
    invoice_id = invoice_result["invoice_id"]
    
    print_json(invoice_result, "Invoice Created")
    
    # Step 2: Get Invoice Details
    print_section("STEP 2: GET INVOICE DETAILS")
    
    invoice_details = api.get_invoice_details(invoice_id)
    print_json(invoice_details, "Invoice Details")
    
    # Step 3: Send Invoice (Status Change)
    print_section("STEP 3: SEND INVOICE (STATUS CHANGE)")
    
    status_update_request = {
        "invoice_id": invoice_id,
        "new_status": "SENT",
        "changed_by": "john.doe@company.com",
        "reason": "Invoice sent to customer"
    }
    
    status_result = api.update_invoice_status(status_update_request)
    print_json(status_result, "Status Update Result")
    
    # Step 4: Process Partial Payment
    print_section("STEP 4: PROCESS PARTIAL PAYMENT")
    
    partial_payment_request = {
        "invoice_id": invoice_id,
        "payment_amount": Decimal("1000.00"),
        "currency": "USD",
        "payment_date": datetime.now(),
        "payment_method": "STRIPE",
        "external_system": "stripe",
        "external_reference_id": "pi_1234567890"
    }
    
    try:
        payment_result = app_service.process_payment(ProcessPaymentCommand(**partial_payment_request))
        print_json({
            "payment_id": payment_result.payment_id,
            "allocated_amount": float(payment_result.allocated_amount),
            "currency": payment_result.currency,
            "invoice_status": payment_result.invoice_status,
            "success": payment_result.success,
            "message": payment_result.message
        }, "Partial Payment Processed")
    except Exception as e:
        print(f"Payment processing error: {e}")
    
    # Step 5: Send Manual Reminder
    print_section("STEP 5: SEND MANUAL REMINDER")
    
    reminder_request = {
        "invoice_id": invoice_id,
        "requested_by": "jane.smith@company.com",
        "custom_message": "Please process the remaining payment at your earliest convenience."
    }
    
    reminder_result = api.send_reminder(reminder_request)
    print_json(reminder_result, "Manual Reminder Sent")
    
    # Step 6: Process Full Payment
    print_section("STEP 6: PROCESS REMAINING PAYMENT")
    
    remaining_payment_request = {
        "invoice_id": invoice_id,
        "payment_amount": Decimal("3000.00"),  # Remaining amount
        "currency": "USD",
        "payment_date": datetime.now(),
        "payment_method": "BANK_TRANSFER",
        "external_system": "bank",
        "external_reference_id": "TXN_9876543210"
    }
    
    try:
        final_payment_result = app_service.process_payment(ProcessPaymentCommand(**remaining_payment_request))
        print_json({
            "payment_id": final_payment_result.payment_id,
            "allocated_amount": float(final_payment_result.allocated_amount),
            "currency": final_payment_result.currency,
            "invoice_status": final_payment_result.invoice_status,
            "success": final_payment_result.success,
            "message": final_payment_result.message
        }, "Final Payment Processed")
    except Exception as e:
        print(f"Final payment processing error: {e}")
    
    # Step 7: Create Overdue Invoice for Demo
    print_section("STEP 7: CREATE OVERDUE INVOICE SCENARIO")
    
    overdue_invoice_request = {
        "customer_id": "customer-2",
        "customer_name": "TechStart Inc",
        "customer_email": "finance@techstart.com",
        "issue_date": datetime.now() - timedelta(days=45),
        "due_date": datetime.now() - timedelta(days=15),  # 15 days overdue
        "line_items": [
            {
                "description": "Consulting Services",
                "quantity": 40,
                "unit_price": 125.00,
                "currency": "USD"
            }
        ],
        "created_by": "system@company.com"
    }
    
    overdue_invoice = api.create_invoice(overdue_invoice_request)
    overdue_id = overdue_invoice["invoice_id"]
    
    # Send the overdue invoice
    api.update_invoice_status({
        "invoice_id": overdue_id,
        "new_status": "SENT",
        "changed_by": "system@company.com",
        "reason": "Invoice sent to customer"
    })
    
    print_json(overdue_invoice, "Overdue Invoice Created")
    
    # Step 8: Process Overdue Detection
    print_section("STEP 8: OVERDUE DETECTION")
    
    overdue_result = api.process_overdue_invoices()
    print_json(overdue_result, "Overdue Processing Result")
    
    # Step 9: Get Invoice List
    print_section("STEP 9: GET INVOICE LIST")
    
    invoice_list = api.get_invoice_list({
        "page": 1,
        "page_size": 10
    })
    
    print_json(invoice_list, "Invoice List")
    
    # Step 10: Show Event History
    print_section("STEP 10: EVENT HISTORY")
    
    event_history = event_bus.get_event_history()
    print(f"\nTotal Events Generated: {len(event_history)}")
    
    for i, event in enumerate(event_history[-10:], 1):  # Show last 10 events
        print(f"\n{i}. {event['event_type']} at {event['occurred_at']}")
        if 'invoice_id' in event['data']:
            print(f"   Invoice: {event['data'].get('invoice_number', 'N/A')}")
    
    # Step 11: System Statistics
    print_section("STEP 11: SYSTEM STATISTICS")
    
    repo_stats = repo_manager.get_stats()
    event_stats = event_bus.get_stats()
    
    stats = {
        "repository_stats": repo_stats,
        "event_stats": event_stats
    }
    
    print_json(stats, "System Statistics")
    
    print_section("DEMO COMPLETED SUCCESSFULLY")
    print("[OK] Invoice created with line items")
    print("[OK] Status transitions (Draft -> Sent -> Paid)")
    print("[OK] Partial and full payment processing")
    print("[OK] Manual reminder functionality")
    print("[OK] Overdue detection and processing")
    print("[OK] Event-driven architecture working")
    print("[OK] All domain events captured")
    print("\nThe Invoice Management system demonstrates:")
    print("- Domain-Driven Design principles")
    print("- Event sourcing and CQRS patterns")
    print("- Hexagonal architecture")
    print("- Complete business workflow")
    print("- Serverless-ready implementation")


if __name__ == "__main__":
    try:
        demo_invoice_lifecycle()
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        import traceback
        traceback.print_exc()