"""Domain Entities for Invoice Management"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from .value_objects import (
    InvoiceId, InvoiceNumber, CustomerId, CustomerReference, PaymentId,
    LineItemId, Money, InvoiceStatus, PaymentMethod, ExternalReference
)


@dataclass
class InvoiceLineItem:
    """Invoice line item entity"""
    line_item_id: LineItemId
    description: str
    quantity: Decimal
    unit_price: Money
    
    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.unit_price.amount < 0:
            raise ValueError("Unit price cannot be negative")
    
    @property
    def line_total(self) -> Money:
        """Calculate line total"""
        total_amount = self.unit_price.amount * self.quantity
        return Money(total_amount, self.unit_price.currency)


@dataclass
class InvoiceStatusHistory:
    """Invoice status change history entity"""
    previous_status: InvoiceStatus
    new_status: InvoiceStatus
    changed_at: datetime
    changed_by: str
    reason: Optional[str] = None
    
    @classmethod
    def create(cls, previous_status: InvoiceStatus, new_status: InvoiceStatus, 
               changed_by: str, reason: Optional[str] = None) -> 'InvoiceStatusHistory':
        return cls(
            previous_status=previous_status,
            new_status=new_status,
            changed_at=datetime.utcnow(),
            changed_by=changed_by,
            reason=reason
        )


@dataclass
class Invoice:
    """Invoice entity (will be aggregate root)"""
    invoice_id: InvoiceId
    invoice_number: InvoiceNumber
    customer_reference: CustomerReference
    issue_date: datetime
    due_date: datetime
    status: InvoiceStatus
    line_items: List[InvoiceLineItem] = field(default_factory=list)
    status_history: List[InvoiceStatusHistory] = field(default_factory=list)
    version: int = 1
    
    def __post_init__(self):
        if self.due_date <= self.issue_date:
            raise ValueError("Due date must be after issue date")
        if not self.line_items:
            raise ValueError("Invoice must have at least one line item")
    
    @property
    def total_amount(self) -> Money:
        """Calculate total invoice amount"""
        if not self.line_items:
            return Money(Decimal('0'))
        
        total = self.line_items[0].line_total
        for item in self.line_items[1:]:
            total = total.add(item.line_total)
        return total
    
    def add_line_item(self, description: str, quantity: Decimal, unit_price: Money) -> None:
        """Add line item to invoice"""
        line_item = InvoiceLineItem(
            line_item_id=LineItemId.generate(),
            description=description,
            quantity=quantity,
            unit_price=unit_price
        )
        self.line_items.append(line_item)
    
    def change_status(self, new_status: InvoiceStatus, changed_by: str, reason: Optional[str] = None) -> bool:
        """Change invoice status with validation"""
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status.value} to {new_status.value}")
        
        # Record status change
        history_entry = InvoiceStatusHistory.create(
            previous_status=self.status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        self.status_history.append(history_entry)
        self.status = new_status
        self.version += 1
        return True
    
    def is_overdue(self, current_date: datetime) -> bool:
        """Check if invoice is overdue"""
        return (self.status == InvoiceStatus.SENT and 
                current_date.date() > self.due_date.date())
    
    def days_overdue(self, current_date: datetime) -> int:
        """Calculate days overdue"""
        if not self.is_overdue(current_date):
            return 0
        return (current_date.date() - self.due_date.date()).days


@dataclass
class PaymentAllocation:
    """Payment allocation to invoice entity"""
    invoice_id: InvoiceId
    allocated_amount: Money
    allocation_date: datetime
    
    @classmethod
    def create(cls, invoice_id: InvoiceId, allocated_amount: Money) -> 'PaymentAllocation':
        return cls(
            invoice_id=invoice_id,
            allocated_amount=allocated_amount,
            allocation_date=datetime.utcnow()
        )


@dataclass
class Payment:
    """Payment entity (will be aggregate root)"""
    payment_id: PaymentId
    amount: Money
    payment_date: datetime
    payment_method: PaymentMethod
    external_reference: Optional[ExternalReference] = None
    allocations: List[PaymentAllocation] = field(default_factory=list)
    
    def __post_init__(self):
        if self.amount.amount <= 0:
            raise ValueError("Payment amount must be positive")
    
    @property
    def allocated_amount(self) -> Money:
        """Calculate total allocated amount"""
        if not self.allocations:
            return Money(Decimal('0'), self.amount.currency)
        
        total = self.allocations[0].allocated_amount
        for allocation in self.allocations[1:]:
            total = total.add(allocation.allocated_amount)
        return total
    
    @property
    def remaining_amount(self) -> Money:
        """Calculate remaining unallocated amount"""
        return self.amount.subtract(self.allocated_amount)
    
    def allocate_to_invoice(self, invoice_id: InvoiceId, amount: Money) -> None:
        """Allocate payment amount to specific invoice"""
        if amount.amount <= 0:
            raise ValueError("Allocation amount must be positive")
        
        if amount.currency != self.amount.currency:
            raise ValueError("Allocation currency must match payment currency")
        
        remaining = self.remaining_amount
        if amount.amount > remaining.amount:
            raise ValueError("Cannot allocate more than remaining amount")
        
        allocation = PaymentAllocation.create(invoice_id, amount)
        self.allocations.append(allocation)
    
    def is_fully_allocated(self) -> bool:
        """Check if payment is fully allocated"""
        return self.remaining_amount.amount == 0