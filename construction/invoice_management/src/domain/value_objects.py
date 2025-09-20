"""Domain Value Objects for Invoice Management"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
import uuid
from datetime import datetime


class InvoiceStatus(Enum):
    """Invoice status enumeration with transition rules"""
    DRAFT = "DRAFT"
    SENT = "SENT"
    OVERDUE = "OVERDUE"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"
    
    def can_transition_to(self, new_status: 'InvoiceStatus') -> bool:
        """Check if transition to new status is valid"""
        valid_transitions = {
            InvoiceStatus.DRAFT: [InvoiceStatus.SENT, InvoiceStatus.CANCELLED],
            InvoiceStatus.SENT: [InvoiceStatus.OVERDUE, InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DISPUTED],
            InvoiceStatus.OVERDUE: [InvoiceStatus.PAID, InvoiceStatus.CANCELLED, InvoiceStatus.DISPUTED],
            InvoiceStatus.PAID: [],  # Terminal state
            InvoiceStatus.CANCELLED: [],  # Terminal state
            InvoiceStatus.DISPUTED: [InvoiceStatus.PAID, InvoiceStatus.CANCELLED]
        }
        return new_status in valid_transitions.get(self, [])


@dataclass(frozen=True)
class InvoiceId:
    """Invoice unique identifier"""
    value: str
    
    @classmethod
    def generate(cls) -> 'InvoiceId':
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class InvoiceNumber:
    """Invoice business identifier with format validation"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('INV-'):
            raise ValueError("Invoice number must start with 'INV-'")
    
    @classmethod
    def generate(cls, year: int, sequence: int) -> 'InvoiceNumber':
        return cls(f"INV-{year}-{sequence:06d}")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    """Money value object with currency"""
    amount: Decimal
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be 3 characters")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Result cannot be negative")
        return Money(result_amount, self.currency)
    
    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclass(frozen=True)
class CustomerId:
    """Customer unique identifier"""
    value: str
    
    @classmethod
    def generate(cls) -> 'CustomerId':
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CustomerReference:
    """Customer reference with cached data"""
    customer_id: CustomerId
    cached_name: str
    cached_email: str
    
    def update_cache(self, name: str, email: str) -> 'CustomerReference':
        return CustomerReference(self.customer_id, name, email)


@dataclass(frozen=True)
class PaymentId:
    """Payment unique identifier"""
    value: str
    
    @classmethod
    def generate(cls) -> 'PaymentId':
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


class PaymentMethod(Enum):
    """Payment method enumeration"""
    CREDIT_CARD = "CREDIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    STRIPE = "STRIPE"
    CASH = "CASH"


@dataclass(frozen=True)
class LineItemId:
    """Line item unique identifier"""
    value: str
    
    @classmethod
    def generate(cls) -> 'LineItemId':
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EventId:
    """Event unique identifier"""
    value: str
    
    @classmethod
    def generate(cls) -> 'EventId':
        return cls(str(uuid.uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ExternalReference:
    """External system reference"""
    system: str
    reference_id: str
    
    def __str__(self) -> str:
        return f"{self.system}:{self.reference_id}"