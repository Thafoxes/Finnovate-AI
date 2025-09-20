"""Domain Events for Invoice Management"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .value_objects import (
    EventId, InvoiceId, InvoiceNumber, CustomerId, PaymentId, 
    Money, InvoiceStatus, ExternalReference
)


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events"""
    event_id: EventId
    occurred_at: datetime
    
    def __post_init__(self):
        if not self.event_id:
            object.__setattr__(self, 'event_id', EventId.generate())
        if not self.occurred_at:
            object.__setattr__(self, 'occurred_at', datetime.utcnow())


@dataclass(frozen=True)
class InvoiceCreated(DomainEvent):
    """Event published when an invoice is created"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    customer_id: CustomerId
    customer_name: str
    total_amount: Money
    due_date: datetime
    created_by: str
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class InvoiceStatusChanged(DomainEvent):
    """Event published when invoice status changes"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    previous_status: InvoiceStatus
    new_status: InvoiceStatus
    changed_by: str
    reason: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class InvoiceBecameOverdue(DomainEvent):
    """Event published when invoice becomes overdue"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    customer_id: CustomerId
    customer_name: str
    customer_email: str
    total_amount: Money
    outstanding_amount: Money
    due_date: datetime
    days_overdue: int
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class InvoicePaid(DomainEvent):
    """Event published when invoice is fully paid"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    customer_id: CustomerId
    customer_name: str
    total_amount: Money
    paid_amount: Money
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class ManualReminderRequested(DomainEvent):
    """Event published when manual reminder is requested"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    customer_id: CustomerId
    customer_name: str
    customer_email: str
    requested_by: str
    custom_message: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class PaymentReceived(DomainEvent):
    """Event published when payment is received (from external systems)"""
    payment_id: PaymentId
    invoice_id: InvoiceId
    amount: Money
    payment_date: datetime
    external_reference: Optional[ExternalReference] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class PaymentAllocated(DomainEvent):
    """Event published when payment is allocated to invoice"""
    payment_id: PaymentId
    invoice_id: InvoiceId
    allocated_amount: Money
    remaining_invoice_balance: Money
    
    def __post_init__(self):
        super().__post_init__()