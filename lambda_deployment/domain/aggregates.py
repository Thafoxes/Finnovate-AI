"""Domain Aggregates for Invoice Management"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from .entities import Invoice, Payment, InvoiceLineItem, PaymentAllocation
from .value_objects import (
    InvoiceId, InvoiceNumber, CustomerId, CustomerReference, PaymentId,
    Money, InvoiceStatus, PaymentMethod, ExternalReference, LineItemId
)
from .events import (
    DomainEvent, InvoiceCreated, InvoiceStatusChanged, InvoiceBecameOverdue,
    InvoicePaid, ManualReminderRequested, PaymentReceived, PaymentAllocated
)


@dataclass
class InvoiceAggregate:
    """Invoice Aggregate Root - manages invoice lifecycle and consistency"""
    invoice: Invoice
    _uncommitted_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    @classmethod
    def create(cls, invoice_number: InvoiceNumber, customer_reference: CustomerReference,
               issue_date: datetime, due_date: datetime, line_items_data: List[dict],
               created_by: str) -> 'InvoiceAggregate':
        """Create new invoice aggregate"""
        invoice_id = InvoiceId.generate()
        
        # Create line items
        line_items = []
        for item_data in line_items_data:
            line_item = InvoiceLineItem(
                line_item_id=LineItemId.generate(),
                description=item_data['description'],
                quantity=Decimal(str(item_data['quantity'])),
                unit_price=Money(Decimal(str(item_data['unit_price'])), item_data.get('currency', 'USD'))
            )
            line_items.append(line_item)
        
        # Create invoice
        invoice = Invoice(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            customer_reference=customer_reference,
            issue_date=issue_date,
            due_date=due_date,
            status=InvoiceStatus.DRAFT,
            line_items=line_items
        )
        
        aggregate = cls(invoice)
        
        # Raise domain event
        event = InvoiceCreated(
            event_id=None,  # Will be auto-generated
            occurred_at=None,  # Will be auto-generated
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            customer_id=customer_reference.customer_id,
            customer_name=customer_reference.cached_name,
            total_amount=invoice.total_amount,
            due_date=due_date,
            created_by=created_by
        )
        aggregate._add_event(event)
        
        return aggregate
    
    def change_status(self, new_status: InvoiceStatus, changed_by: str, reason: Optional[str] = None) -> None:
        """Change invoice status and raise appropriate events"""
        previous_status = self.invoice.status
        
        # Delegate to entity for validation and state change
        self.invoice.change_status(new_status, changed_by, reason)
        
        # Raise status changed event
        event = InvoiceStatusChanged(
            event_id=None,
            occurred_at=None,
            invoice_id=self.invoice.invoice_id,
            invoice_number=self.invoice.invoice_number,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        self._add_event(event)
        
        # Check for special status transitions
        if new_status == InvoiceStatus.OVERDUE:
            self._raise_overdue_event()
        elif new_status == InvoiceStatus.PAID:
            self._raise_paid_event()
    
    def mark_as_overdue(self, current_date: datetime) -> None:
        """Mark invoice as overdue if conditions are met"""
        if self.invoice.is_overdue(current_date) and self.invoice.status == InvoiceStatus.SENT:
            self.change_status(InvoiceStatus.OVERDUE, "system", "Due date passed")
    
    def request_manual_reminder(self, requested_by: str, custom_message: Optional[str] = None) -> None:
        """Request manual reminder for invoice"""
        if self.invoice.status in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]:
            raise ValueError("Cannot send reminder for paid or cancelled invoice")
        
        event = ManualReminderRequested(
            event_id=None,
            occurred_at=None,
            invoice_id=self.invoice.invoice_id,
            invoice_number=self.invoice.invoice_number,
            customer_id=self.invoice.customer_reference.customer_id,
            customer_name=self.invoice.customer_reference.cached_name,
            customer_email=self.invoice.customer_reference.cached_email,
            requested_by=requested_by,
            custom_message=custom_message
        )
        self._add_event(event)
    
    def apply_payment(self, payment_amount: Money) -> None:
        """Apply payment to invoice (simplified - assumes full or partial payment)"""
        if payment_amount.amount >= self.invoice.total_amount.amount:
            # Full payment
            self.change_status(InvoiceStatus.PAID, "system", "Payment received")
    
    def _raise_overdue_event(self) -> None:
        """Raise invoice became overdue event"""
        current_date = datetime.utcnow()
        event = InvoiceBecameOverdue(
            event_id=None,
            occurred_at=None,
            invoice_id=self.invoice.invoice_id,
            invoice_number=self.invoice.invoice_number,
            customer_id=self.invoice.customer_reference.customer_id,
            customer_name=self.invoice.customer_reference.cached_name,
            customer_email=self.invoice.customer_reference.cached_email,
            total_amount=self.invoice.total_amount,
            outstanding_amount=self.invoice.total_amount,  # Simplified
            due_date=self.invoice.due_date,
            days_overdue=self.invoice.days_overdue(current_date)
        )
        self._add_event(event)
    
    def _raise_paid_event(self) -> None:
        """Raise invoice paid event"""
        event = InvoicePaid(
            event_id=None,
            occurred_at=None,
            invoice_id=self.invoice.invoice_id,
            invoice_number=self.invoice.invoice_number,
            customer_id=self.invoice.customer_reference.customer_id,
            customer_name=self.invoice.customer_reference.cached_name,
            total_amount=self.invoice.total_amount,
            paid_amount=self.invoice.total_amount
        )
        self._add_event(event)
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add event to uncommitted events list"""
        self._uncommitted_events.append(event)
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get list of uncommitted events"""
        return self._uncommitted_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Clear uncommitted events after successful persistence"""
        self._uncommitted_events.clear()


@dataclass
class PaymentAggregate:
    """Payment Aggregate Root - manages payment allocation and consistency"""
    payment: Payment
    _uncommitted_events: List[DomainEvent] = field(default_factory=list, init=False)
    
    @classmethod
    def create_from_external(cls, amount: Money, payment_date: datetime,
                           payment_method: PaymentMethod, external_reference: ExternalReference,
                           invoice_id: InvoiceId) -> 'PaymentAggregate':
        """Create payment from external system (e.g., Stripe)"""
        payment_id = PaymentId.generate()
        
        payment = Payment(
            payment_id=payment_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method,
            external_reference=external_reference
        )
        
        aggregate = cls(payment)
        
        # Raise payment received event
        event = PaymentReceived(
            event_id=None,
            occurred_at=None,
            payment_id=payment_id,
            invoice_id=invoice_id,
            amount=amount,
            payment_date=payment_date,
            external_reference=external_reference
        )
        aggregate._add_event(event)
        
        return aggregate
    
    def allocate_to_invoice(self, invoice_id: InvoiceId, allocation_amount: Money,
                          remaining_invoice_balance: Money) -> None:
        """Allocate payment to specific invoice"""
        # Delegate to entity for validation and state change
        self.payment.allocate_to_invoice(invoice_id, allocation_amount)
        
        # Raise allocation event
        event = PaymentAllocated(
            event_id=None,
            occurred_at=None,
            payment_id=self.payment.payment_id,
            invoice_id=invoice_id,
            allocated_amount=allocation_amount,
            remaining_invoice_balance=remaining_invoice_balance
        )
        self._add_event(event)
    
    def _add_event(self, event: DomainEvent) -> None:
        """Add event to uncommitted events list"""
        self._uncommitted_events.append(event)
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get list of uncommitted events"""
        return self._uncommitted_events.copy()
    
    def mark_events_as_committed(self) -> None:
        """Clear uncommitted events after successful persistence"""
        self._uncommitted_events.clear()