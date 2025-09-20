"""Application Services for Invoice Management"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from domain.aggregates import InvoiceAggregate, PaymentAggregate
from domain.value_objects import (
    InvoiceId, CustomerId, CustomerReference, InvoiceStatus, 
    PaymentMethod, ExternalReference, Money
)
from domain.services import (
    InvoiceNumberGenerationService, InvoiceStatusTransitionService,
    OverdueInvoiceDetectionService, PaymentAllocationService,
    CustomerCacheService, InvoiceValidationService
)
from .commands import (
    CreateInvoiceCommand, UpdateInvoiceStatusCommand, SendManualReminderCommand,
    ProcessPaymentCommand, ProcessOverdueInvoicesCommand, UpdateCustomerCacheCommand,
    GetInvoiceListQuery, GetInvoiceDetailsQuery, SearchInvoicesQuery, GetOverdueInvoicesQuery,
    InvoiceCreatedResult, StatusUpdateResult, ReminderRequestResult, PaymentProcessedResult,
    InvoiceListItem, InvoiceDetails, PagedResult, ValidationError, BusinessRuleError, NotFoundError
)


class InvoiceApplicationService:
    """Application service for invoice write operations"""
    
    def __init__(self, invoice_repository, payment_repository, event_publisher,
                 customer_client=None):
        # Repositories (will be injected)
        self._invoice_repository = invoice_repository
        self._payment_repository = payment_repository
        self._event_publisher = event_publisher
        self._customer_client = customer_client
        
        # Domain services
        self._number_service = InvoiceNumberGenerationService()
        self._status_service = InvoiceStatusTransitionService()
        self._overdue_service = OverdueInvoiceDetectionService()
        self._payment_service = PaymentAllocationService()
        self._cache_service = CustomerCacheService()
        self._validation_service = InvoiceValidationService()
    
    def create_invoice(self, command: CreateInvoiceCommand) -> InvoiceCreatedResult:
        """Create new invoice"""
        try:
            # Validate command
            self._validate_create_command(command)
            
            # Validate customer (simplified - in real implementation would call external service)
            if self._customer_client:
                customer_exists = self._customer_client.validate_customer(command.customer_id)
                if not customer_exists:
                    raise ValidationError(f"Customer {command.customer_id} not found", "customer_id")
            
            # Generate invoice number
            invoice_number = self._number_service.generate_next_number()
            
            # Create customer reference
            customer_ref = CustomerReference(
                customer_id=CustomerId(command.customer_id),
                cached_name=command.customer_name,
                cached_email=command.customer_email
            )
            
            # Create invoice aggregate
            invoice_aggregate = InvoiceAggregate.create(
                invoice_number=invoice_number,
                customer_reference=customer_ref,
                issue_date=command.issue_date,
                due_date=command.due_date,
                line_items_data=command.line_items,
                created_by=command.created_by
            )
            
            # Save aggregate
            self._invoice_repository.save(invoice_aggregate)
            
            # Publish events
            self._publish_events(invoice_aggregate)
            
            return InvoiceCreatedResult(
                invoice_id=str(invoice_aggregate.invoice.invoice_id),
                invoice_number=str(invoice_aggregate.invoice.invoice_number),
                total_amount=invoice_aggregate.invoice.total_amount.amount,
                currency=invoice_aggregate.invoice.total_amount.currency,
                status=invoice_aggregate.invoice.status.value,
                created_at=invoice_aggregate.invoice.issue_date
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, BusinessRuleError)):
                raise
            raise BusinessRuleError(f"Failed to create invoice: {str(e)}")
    
    def update_invoice_status(self, command: UpdateInvoiceStatusCommand) -> StatusUpdateResult:
        """Update invoice status"""
        try:
            # Load invoice
            invoice_aggregate = self._invoice_repository.get_by_id(InvoiceId(command.invoice_id))
            if not invoice_aggregate:
                raise NotFoundError("Invoice", command.invoice_id)
            
            # Convert status
            new_status = InvoiceStatus(command.new_status)
            previous_status = invoice_aggregate.invoice.status
            
            # Execute transition
            self._status_service.execute_transition(
                invoice_aggregate, new_status, command.changed_by, command.reason
            )
            
            # Save aggregate
            self._invoice_repository.save(invoice_aggregate)
            
            # Publish events
            self._publish_events(invoice_aggregate)
            
            return StatusUpdateResult(
                invoice_id=command.invoice_id,
                previous_status=previous_status.value,
                new_status=new_status.value,
                changed_at=datetime.utcnow(),
                success=True
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, BusinessRuleError, NotFoundError)):
                raise
            raise BusinessRuleError(f"Failed to update status: {str(e)}")
    
    def send_manual_reminder(self, command: SendManualReminderCommand) -> ReminderRequestResult:
        """Send manual reminder"""
        try:
            # Load invoice
            invoice_aggregate = self._invoice_repository.get_by_id(InvoiceId(command.invoice_id))
            if not invoice_aggregate:
                raise NotFoundError("Invoice", command.invoice_id)
            
            # Request reminder
            invoice_aggregate.request_manual_reminder(command.requested_by, command.custom_message)
            
            # Save aggregate
            self._invoice_repository.save(invoice_aggregate)
            
            # Publish events
            self._publish_events(invoice_aggregate)
            
            return ReminderRequestResult(
                invoice_id=command.invoice_id,
                requested_at=datetime.utcnow(),
                success=True,
                message="Reminder request submitted successfully"
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, BusinessRuleError, NotFoundError)):
                raise
            raise BusinessRuleError(f"Failed to send reminder: {str(e)}")
    
    def process_payment(self, command: ProcessPaymentCommand) -> PaymentProcessedResult:
        """Process payment from external system"""
        try:
            # Load invoice
            invoice_aggregate = self._invoice_repository.get_by_id(InvoiceId(command.invoice_id))
            if not invoice_aggregate:
                raise NotFoundError("Invoice", command.invoice_id)
            
            # Create payment aggregate
            payment_amount = Money(command.payment_amount, command.currency)
            payment_method = PaymentMethod(command.payment_method)
            external_ref = None
            
            if command.external_system and command.external_reference_id:
                external_ref = ExternalReference(command.external_system, command.external_reference_id)
            
            payment_aggregate = PaymentAggregate.create_from_external(
                amount=payment_amount,
                payment_date=command.payment_date,
                payment_method=payment_method,
                external_reference=external_ref,
                invoice_id=InvoiceId(command.invoice_id)
            )
            
            # Allocate payment to invoice
            allocations = self._payment_service.allocate_payment(payment_aggregate, [invoice_aggregate])
            
            # Save aggregates
            self._payment_repository.save(payment_aggregate)
            self._invoice_repository.save(invoice_aggregate)
            
            # Publish events
            self._publish_events(payment_aggregate)
            self._publish_events(invoice_aggregate)
            
            return PaymentProcessedResult(
                payment_id=str(payment_aggregate.payment.payment_id),
                invoice_id=command.invoice_id,
                allocated_amount=payment_amount.amount,
                currency=payment_amount.currency,
                invoice_status=invoice_aggregate.invoice.status.value,
                success=True,
                message="Payment processed successfully"
            )
            
        except Exception as e:
            if isinstance(e, (ValidationError, BusinessRuleError, NotFoundError)):
                raise
            raise BusinessRuleError(f"Failed to process payment: {str(e)}")
    
    def process_overdue_invoices(self, command: ProcessOverdueInvoicesCommand) -> List[str]:
        """Process overdue invoices (scheduled operation)"""
        try:
            as_of_date = command.as_of_date or datetime.utcnow()
            
            # Get all sent invoices
            all_invoices = self._invoice_repository.get_by_status(InvoiceStatus.SENT)
            
            # Process overdue invoices
            processed_invoices = self._overdue_service.process_overdue_invoices(all_invoices, as_of_date)
            
            # Save and publish events
            processed_ids = []
            for invoice_aggregate in processed_invoices:
                self._invoice_repository.save(invoice_aggregate)
                self._publish_events(invoice_aggregate)
                processed_ids.append(str(invoice_aggregate.invoice.invoice_id))
            
            return processed_ids
            
        except Exception as e:
            raise BusinessRuleError(f"Failed to process overdue invoices: {str(e)}")
    
    def update_customer_cache(self, command: UpdateCustomerCacheCommand) -> int:
        """Update customer cache in invoices"""
        try:
            customer_id = CustomerId(command.customer_id)
            
            # Get all invoices for customer
            customer_invoices = self._invoice_repository.get_by_customer_id(customer_id)
            
            # Update cache
            updated_invoices = self._cache_service.update_customer_cache(
                customer_invoices, customer_id, command.customer_name, command.customer_email
            )
            
            # Save updated invoices
            for invoice_aggregate in updated_invoices:
                self._invoice_repository.save(invoice_aggregate)
            
            return len(updated_invoices)
            
        except Exception as e:
            raise BusinessRuleError(f"Failed to update customer cache: {str(e)}")
    
    def _validate_create_command(self, command: CreateInvoiceCommand) -> None:
        """Validate create invoice command"""
        if not command.customer_id:
            raise ValidationError("Customer ID is required", "customer_id")
        
        if not command.customer_name.strip():
            raise ValidationError("Customer name is required", "customer_name")
        
        if not command.customer_email or '@' not in command.customer_email:
            raise ValidationError("Valid customer email is required", "customer_email")
        
        if not command.line_items:
            raise ValidationError("At least one line item is required", "line_items")
        
        if command.due_date <= command.issue_date:
            raise ValidationError("Due date must be after issue date", "due_date")
    
    def _publish_events(self, aggregate) -> None:
        """Publish uncommitted events"""
        events = aggregate.get_uncommitted_events()
        for event in events:
            self._event_publisher.publish(event)
        aggregate.mark_events_as_committed()


class InvoiceQueryService:
    """Application service for invoice read operations"""
    
    def __init__(self, invoice_repository, payment_repository):
        self._invoice_repository = invoice_repository
        self._payment_repository = payment_repository
    
    def get_invoice_list(self, query: GetInvoiceListQuery) -> PagedResult:
        """Get paginated list of invoices"""
        try:
            # Apply filters
            invoices = self._invoice_repository.get_all()
            
            if query.status_filter:
                status = InvoiceStatus(query.status_filter)
                invoices = [inv for inv in invoices if inv.invoice.status == status]
            
            if query.customer_id_filter:
                customer_id = CustomerId(query.customer_id_filter)
                invoices = [inv for inv in invoices 
                           if inv.invoice.customer_reference.customer_id == customer_id]
            
            if query.date_from:
                invoices = [inv for inv in invoices if inv.invoice.issue_date >= query.date_from]
            
            if query.date_to:
                invoices = [inv for inv in invoices if inv.invoice.issue_date <= query.date_to]
            
            # Sort by issue date (newest first)
            invoices.sort(key=lambda inv: inv.invoice.issue_date, reverse=True)
            
            # Pagination
            total_count = len(invoices)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            page_invoices = invoices[start_idx:end_idx]
            
            # Convert to list items
            items = []
            for inv_agg in page_invoices:
                inv = inv_agg.invoice
                current_date = datetime.utcnow()
                
                item = InvoiceListItem(
                    invoice_id=str(inv.invoice_id),
                    invoice_number=str(inv.invoice_number),
                    customer_name=inv.customer_reference.cached_name,
                    customer_email=inv.customer_reference.cached_email,
                    issue_date=inv.issue_date,
                    due_date=inv.due_date,
                    total_amount=inv.total_amount.amount,
                    currency=inv.total_amount.currency,
                    status=inv.status.value,
                    days_overdue=inv.days_overdue(current_date)
                )
                items.append(item)
            
            return PagedResult(
                items=items,
                total_count=total_count,
                page=query.page,
                page_size=query.page_size,
                has_next=end_idx < total_count,
                has_previous=query.page > 1
            )
            
        except Exception as e:
            raise BusinessRuleError(f"Failed to get invoice list: {str(e)}")
    
    def get_invoice_details(self, query: GetInvoiceDetailsQuery) -> InvoiceDetails:
        """Get detailed invoice information"""
        try:
            invoice_aggregate = self._invoice_repository.get_by_id(InvoiceId(query.invoice_id))
            if not invoice_aggregate:
                raise NotFoundError("Invoice", query.invoice_id)
            
            inv = invoice_aggregate.invoice
            
            # Convert line items
            line_items = []
            for item in inv.line_items:
                line_items.append({
                    "line_item_id": str(item.line_item_id),
                    "description": item.description,
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price.amount),
                    "currency": item.unit_price.currency,
                    "line_total": float(item.line_total.amount)
                })
            
            # Convert status history
            status_history = []
            for history in inv.status_history:
                status_history.append({
                    "previous_status": history.previous_status.value,
                    "new_status": history.new_status.value,
                    "changed_at": history.changed_at.isoformat(),
                    "changed_by": history.changed_by,
                    "reason": history.reason
                })
            
            return InvoiceDetails(
                invoice_id=str(inv.invoice_id),
                invoice_number=str(inv.invoice_number),
                customer_id=str(inv.customer_reference.customer_id),
                customer_name=inv.customer_reference.cached_name,
                customer_email=inv.customer_reference.cached_email,
                issue_date=inv.issue_date,
                due_date=inv.due_date,
                status=inv.status.value,
                total_amount=inv.total_amount.amount,
                currency=inv.total_amount.currency,
                line_items=line_items,
                status_history=status_history,
                version=inv.version
            )
            
        except Exception as e:
            if isinstance(e, NotFoundError):
                raise
            raise BusinessRuleError(f"Failed to get invoice details: {str(e)}")
    
    def search_invoices(self, query: SearchInvoicesQuery) -> List[InvoiceListItem]:
        """Search invoices by term"""
        try:
            all_invoices = self._invoice_repository.get_all()
            matching_invoices = []
            
            search_term = query.search_term.lower()
            
            for inv_agg in all_invoices:
                inv = inv_agg.invoice
                
                # Search in invoice number, customer name, customer email
                if (search_term in str(inv.invoice_number).lower() or
                    search_term in inv.customer_reference.cached_name.lower() or
                    search_term in inv.customer_reference.cached_email.lower()):
                    
                    # Apply additional filters
                    if query.status_filter and inv.status.value != query.status_filter:
                        continue
                    
                    if (query.customer_filter and 
                        query.customer_filter.lower() not in inv.customer_reference.cached_name.lower()):
                        continue
                    
                    current_date = datetime.utcnow()
                    item = InvoiceListItem(
                        invoice_id=str(inv.invoice_id),
                        invoice_number=str(inv.invoice_number),
                        customer_name=inv.customer_reference.cached_name,
                        customer_email=inv.customer_reference.cached_email,
                        issue_date=inv.issue_date,
                        due_date=inv.due_date,
                        total_amount=inv.total_amount.amount,
                        currency=inv.total_amount.currency,
                        status=inv.status.value,
                        days_overdue=inv.days_overdue(current_date)
                    )
                    matching_invoices.append(item)
            
            return matching_invoices
            
        except Exception as e:
            raise BusinessRuleError(f"Failed to search invoices: {str(e)}")
    
    def get_overdue_invoices(self, query: GetOverdueInvoicesQuery) -> List[InvoiceListItem]:
        """Get overdue invoices"""
        try:
            as_of_date = query.as_of_date or datetime.utcnow()
            all_invoices = self._invoice_repository.get_all()
            overdue_invoices = []
            
            for inv_agg in all_invoices:
                inv = inv_agg.invoice
                days_overdue = inv.days_overdue(as_of_date)
                
                if days_overdue >= query.days_overdue_threshold:
                    item = InvoiceListItem(
                        invoice_id=str(inv.invoice_id),
                        invoice_number=str(inv.invoice_number),
                        customer_name=inv.customer_reference.cached_name,
                        customer_email=inv.customer_reference.cached_email,
                        issue_date=inv.issue_date,
                        due_date=inv.due_date,
                        total_amount=inv.total_amount.amount,
                        currency=inv.total_amount.currency,
                        status=inv.status.value,
                        days_overdue=days_overdue
                    )
                    overdue_invoices.append(item)
            
            # Sort by days overdue (most overdue first)
            overdue_invoices.sort(key=lambda x: x.days_overdue, reverse=True)
            return overdue_invoices
            
        except Exception as e:
            raise BusinessRuleError(f"Failed to get overdue invoices: {str(e)}")