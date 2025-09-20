"""Application Commands and Queries for Invoice Management"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from domain.value_objects import InvoiceId, CustomerId, InvoiceStatus, PaymentMethod, ExternalReference


# Commands (Write Operations)

@dataclass(frozen=True)
class CreateInvoiceCommand:
    """Command to create a new invoice"""
    customer_id: str
    customer_name: str
    customer_email: str
    issue_date: datetime
    due_date: datetime
    line_items: List[Dict[str, Any]]  # [{"description": str, "quantity": float, "unit_price": float, "currency": str}]
    created_by: str


@dataclass(frozen=True)
class UpdateInvoiceStatusCommand:
    """Command to update invoice status"""
    invoice_id: str
    new_status: str  # Will be converted to InvoiceStatus enum
    changed_by: str
    reason: Optional[str] = None


@dataclass(frozen=True)
class SendManualReminderCommand:
    """Command to send manual reminder"""
    invoice_id: str
    requested_by: str
    custom_message: Optional[str] = None


@dataclass(frozen=True)
class ProcessPaymentCommand:
    """Command to process payment from external system"""
    invoice_id: str
    payment_amount: Decimal
    currency: str
    payment_date: datetime
    payment_method: str  # Will be converted to PaymentMethod enum
    external_system: Optional[str] = None
    external_reference_id: Optional[str] = None


# Queries (Read Operations)

@dataclass(frozen=True)
class GetInvoiceListQuery:
    """Query to get list of invoices with filters"""
    status_filter: Optional[str] = None
    customer_id_filter: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class GetInvoiceDetailsQuery:
    """Query to get detailed invoice information"""
    invoice_id: str


@dataclass(frozen=True)
class SearchInvoicesQuery:
    """Query to search invoices by various criteria"""
    search_term: str
    status_filter: Optional[str] = None
    customer_filter: Optional[str] = None


@dataclass(frozen=True)
class GetOverdueInvoicesQuery:
    """Query to get overdue invoices"""
    as_of_date: Optional[datetime] = None
    days_overdue_threshold: int = 0


# Events (for event handlers)

@dataclass(frozen=True)
class ProcessOverdueInvoicesCommand:
    """Command to process overdue invoices (scheduled)"""
    as_of_date: Optional[datetime] = None


@dataclass(frozen=True)
class UpdateCustomerCacheCommand:
    """Command to update customer cache in invoices"""
    customer_id: str
    customer_name: str
    customer_email: str


# Results (Response objects)

@dataclass(frozen=True)
class InvoiceCreatedResult:
    """Result of invoice creation"""
    invoice_id: str
    invoice_number: str
    total_amount: Decimal
    currency: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class StatusUpdateResult:
    """Result of status update"""
    invoice_id: str
    previous_status: str
    new_status: str
    changed_at: datetime
    success: bool
    message: Optional[str] = None


@dataclass(frozen=True)
class ReminderRequestResult:
    """Result of reminder request"""
    invoice_id: str
    requested_at: datetime
    success: bool
    message: Optional[str] = None


@dataclass(frozen=True)
class PaymentProcessedResult:
    """Result of payment processing"""
    payment_id: str
    invoice_id: str
    allocated_amount: Decimal
    currency: str
    invoice_status: str
    success: bool
    message: Optional[str] = None


@dataclass(frozen=True)
class InvoiceListItem:
    """Invoice list item for query results"""
    invoice_id: str
    invoice_number: str
    customer_name: str
    customer_email: str
    issue_date: datetime
    due_date: datetime
    total_amount: Decimal
    currency: str
    status: str
    days_overdue: int = 0


@dataclass(frozen=True)
class InvoiceDetails:
    """Detailed invoice information"""
    invoice_id: str
    invoice_number: str
    customer_id: str
    customer_name: str
    customer_email: str
    issue_date: datetime
    due_date: datetime
    status: str
    total_amount: Decimal
    currency: str
    line_items: List[Dict[str, Any]]
    status_history: List[Dict[str, Any]]
    version: int


@dataclass(frozen=True)
class PagedResult:
    """Paged query result"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# Validation Errors

class ValidationError(Exception):
    """Validation error for commands"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleError(Exception):
    """Business rule violation error"""
    def __init__(self, message: str, rule: Optional[str] = None):
        self.message = message
        self.rule = rule
        super().__init__(message)


class NotFoundError(Exception):
    """Entity not found error"""
    def __init__(self, entity_type: str, entity_id: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        message = f"{entity_type} with ID {entity_id} not found"
        super().__init__(message)