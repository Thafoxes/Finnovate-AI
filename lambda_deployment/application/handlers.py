"""Command and Query Handlers for Invoice Management"""

from typing import Any, Dict, List
from .commands import (
    CreateInvoiceCommand, UpdateInvoiceStatusCommand, SendManualReminderCommand,
    ProcessPaymentCommand, ProcessOverdueInvoicesCommand, UpdateCustomerCacheCommand,
    GetInvoiceListQuery, GetInvoiceDetailsQuery, SearchInvoicesQuery, GetOverdueInvoicesQuery,
    InvoiceCreatedResult, StatusUpdateResult, ReminderRequestResult, PaymentProcessedResult,
    InvoiceListItem, InvoiceDetails, PagedResult
)
from .services import InvoiceApplicationService, InvoiceQueryService


class CreateInvoiceHandler:
    """Handler for creating invoices"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: CreateInvoiceCommand) -> InvoiceCreatedResult:
        """Handle invoice creation command"""
        return self._service.create_invoice(command)


class UpdateInvoiceStatusHandler:
    """Handler for updating invoice status"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: UpdateInvoiceStatusCommand) -> StatusUpdateResult:
        """Handle status update command"""
        return self._service.update_invoice_status(command)


class SendManualReminderHandler:
    """Handler for sending manual reminders"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: SendManualReminderCommand) -> ReminderRequestResult:
        """Handle manual reminder command"""
        return self._service.send_manual_reminder(command)


class ProcessPaymentHandler:
    """Handler for processing payments"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: ProcessPaymentCommand) -> PaymentProcessedResult:
        """Handle payment processing command"""
        return self._service.process_payment(command)


class ProcessOverdueInvoicesHandler:
    """Handler for processing overdue invoices (scheduled)"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: ProcessOverdueInvoicesCommand) -> Dict[str, Any]:
        """Handle overdue processing command"""
        processed_ids = self._service.process_overdue_invoices(command)
        return {
            "processed_count": len(processed_ids),
            "processed_invoice_ids": processed_ids,
            "success": True
        }


class UpdateCustomerCacheHandler:
    """Handler for updating customer cache"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, command: UpdateCustomerCacheCommand) -> Dict[str, Any]:
        """Handle customer cache update command"""
        updated_count = self._service.update_customer_cache(command)
        return {
            "updated_count": updated_count,
            "customer_id": command.customer_id,
            "success": True
        }


class GetInvoiceListHandler:
    """Handler for getting invoice list"""
    
    def __init__(self, query_service: InvoiceQueryService):
        self._service = query_service
    
    def handle(self, query: GetInvoiceListQuery) -> PagedResult:
        """Handle invoice list query"""
        return self._service.get_invoice_list(query)


class GetInvoiceDetailsHandler:
    """Handler for getting invoice details"""
    
    def __init__(self, query_service: InvoiceQueryService):
        self._service = query_service
    
    def handle(self, query: GetInvoiceDetailsQuery) -> InvoiceDetails:
        """Handle invoice details query"""
        return self._service.get_invoice_details(query)


class SearchInvoicesHandler:
    """Handler for searching invoices"""
    
    def __init__(self, query_service: InvoiceQueryService):
        self._service = query_service
    
    def handle(self, query: SearchInvoicesQuery) -> List[InvoiceListItem]:
        """Handle invoice search query"""
        return self._service.search_invoices(query)


class GetOverdueInvoicesHandler:
    """Handler for getting overdue invoices"""
    
    def __init__(self, query_service: InvoiceQueryService):
        self._service = query_service
    
    def handle(self, query: GetOverdueInvoicesQuery) -> List[InvoiceListItem]:
        """Handle overdue invoices query"""
        return self._service.get_overdue_invoices(query)


# Event Handlers (for domain events from other contexts)

class PaymentReceivedEventHandler:
    """Handler for PaymentReceived events from external systems"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle PaymentReceived event"""
        # Convert event data to command
        command = ProcessPaymentCommand(
            invoice_id=event_data['invoice_id'],
            payment_amount=event_data['amount']['amount'],
            currency=event_data['amount']['currency'],
            payment_date=event_data['payment_date'],
            payment_method=event_data.get('payment_method', 'STRIPE'),
            external_system=event_data.get('external_reference', {}).get('system'),
            external_reference_id=event_data.get('external_reference', {}).get('reference_id')
        )
        
        # Process payment
        self._service.process_payment(command)


class CustomerUpdatedEventHandler:
    """Handler for CustomerUpdated events from Customer Management"""
    
    def __init__(self, application_service: InvoiceApplicationService):
        self._service = application_service
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Handle CustomerUpdated event"""
        # Convert event data to command
        command = UpdateCustomerCacheCommand(
            customer_id=event_data['customer_id'],
            customer_name=event_data['name'],
            customer_email=event_data['email']
        )
        
        # Update customer cache
        self._service.update_customer_cache(command)


# Handler Registry for easy lookup

class HandlerRegistry:
    """Registry for all command and query handlers"""
    
    def __init__(self, application_service: InvoiceApplicationService, 
                 query_service: InvoiceQueryService):
        # Command handlers
        self._command_handlers = {
            'CreateInvoice': CreateInvoiceHandler(application_service),
            'UpdateInvoiceStatus': UpdateInvoiceStatusHandler(application_service),
            'SendManualReminder': SendManualReminderHandler(application_service),
            'ProcessPayment': ProcessPaymentHandler(application_service),
            'ProcessOverdueInvoices': ProcessOverdueInvoicesHandler(application_service),
            'UpdateCustomerCache': UpdateCustomerCacheHandler(application_service)
        }
        
        # Query handlers
        self._query_handlers = {
            'GetInvoiceList': GetInvoiceListHandler(query_service),
            'GetInvoiceDetails': GetInvoiceDetailsHandler(query_service),
            'SearchInvoices': SearchInvoicesHandler(query_service),
            'GetOverdueInvoices': GetOverdueInvoicesHandler(query_service)
        }
        
        # Event handlers
        self._event_handlers = {
            'PaymentReceived': PaymentReceivedEventHandler(application_service),
            'CustomerUpdated': CustomerUpdatedEventHandler(application_service)
        }
    
    def get_command_handler(self, command_type: str):
        """Get command handler by type"""
        return self._command_handlers.get(command_type)
    
    def get_query_handler(self, query_type: str):
        """Get query handler by type"""
        return self._query_handlers.get(query_type)
    
    def get_event_handler(self, event_type: str):
        """Get event handler by type"""
        return self._event_handlers.get(event_type)
    
    def handle_command(self, command_type: str, command) -> Any:
        """Handle command by type"""
        handler = self.get_command_handler(command_type)
        if not handler:
            raise ValueError(f"No handler found for command type: {command_type}")
        return handler.handle(command)
    
    def handle_query(self, query_type: str, query) -> Any:
        """Handle query by type"""
        handler = self.get_query_handler(query_type)
        if not handler:
            raise ValueError(f"No handler found for query type: {query_type}")
        return handler.handle(query)
    
    def handle_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle event by type"""
        handler = self.get_event_handler(event_type)
        if not handler:
            raise ValueError(f"No handler found for event type: {event_type}")
        handler.handle(event_data)


# Simplified API for Lambda functions

class InvoiceManagementAPI:
    """Simplified API interface for Lambda functions"""
    
    def __init__(self, handler_registry: HandlerRegistry):
        self._registry = handler_registry
    
    def create_invoice(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create invoice API endpoint"""
        command = CreateInvoiceCommand(**request_data)
        result = self._registry.handle_command('CreateInvoice', command)
        return {
            'invoice_id': result.invoice_id,
            'invoice_number': result.invoice_number,
            'total_amount': float(result.total_amount),
            'currency': result.currency,
            'status': result.status,
            'created_at': result.created_at.isoformat()
        }
    
    def update_invoice_status(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update invoice status API endpoint"""
        command = UpdateInvoiceStatusCommand(**request_data)
        result = self._registry.handle_command('UpdateInvoiceStatus', command)
        return {
            'invoice_id': result.invoice_id,
            'previous_status': result.previous_status,
            'new_status': result.new_status,
            'changed_at': result.changed_at.isoformat(),
            'success': result.success
        }
    
    def send_reminder(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send manual reminder API endpoint"""
        command = SendManualReminderCommand(**request_data)
        result = self._registry.handle_command('SendManualReminder', command)
        return {
            'invoice_id': result.invoice_id,
            'requested_at': result.requested_at.isoformat(),
            'success': result.success,
            'message': result.message
        }
    
    def get_invoice_list(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get invoice list API endpoint"""
        query = GetInvoiceListQuery(**request_data)
        result = self._registry.handle_query('GetInvoiceList', query)
        
        return {
            'items': [
                {
                    'invoice_id': item.invoice_id,
                    'invoice_number': item.invoice_number,
                    'customer_name': item.customer_name,
                    'customer_email': item.customer_email,
                    'issue_date': item.issue_date.isoformat(),
                    'due_date': item.due_date.isoformat(),
                    'total_amount': float(item.total_amount),
                    'currency': item.currency,
                    'status': item.status,
                    'days_overdue': item.days_overdue
                }
                for item in result.items
            ],
            'pagination': {
                'total_count': result.total_count,
                'page': result.page,
                'page_size': result.page_size,
                'has_next': result.has_next,
                'has_previous': result.has_previous
            }
        }
    
    def get_invoice_details(self, invoice_id: str) -> Dict[str, Any]:
        """Get invoice details API endpoint"""
        query = GetInvoiceDetailsQuery(invoice_id=invoice_id)
        result = self._registry.handle_query('GetInvoiceDetails', query)
        
        return {
            'invoice_id': result.invoice_id,
            'invoice_number': result.invoice_number,
            'customer_id': result.customer_id,
            'customer_name': result.customer_name,
            'customer_email': result.customer_email,
            'issue_date': result.issue_date.isoformat(),
            'due_date': result.due_date.isoformat(),
            'status': result.status,
            'total_amount': float(result.total_amount),
            'currency': result.currency,
            'line_items': result.line_items,
            'status_history': result.status_history,
            'version': result.version
        }
    
    def process_overdue_invoices(self) -> Dict[str, Any]:
        """Process overdue invoices API endpoint (scheduled)"""
        command = ProcessOverdueInvoicesCommand()
        return self._registry.handle_command('ProcessOverdueInvoices', command)
    
    def handle_payment_received_event(self, event_data: Dict[str, Any]) -> None:
        """Handle PaymentReceived event"""
        self._registry.handle_event('PaymentReceived', event_data)
    
    def handle_customer_updated_event(self, event_data: Dict[str, Any]) -> None:
        """Handle CustomerUpdated event"""
        self._registry.handle_event('CustomerUpdated', event_data)