"""Domain Services for Invoice Management"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from .aggregates import InvoiceAggregate, PaymentAggregate
from .value_objects import InvoiceNumber, Money, InvoiceStatus, CustomerId
from .entities import Invoice


class InvoiceNumberGenerationService:
    """Service for generating unique invoice numbers"""
    
    def __init__(self):
        self._current_sequence = 0
    
    def generate_next_number(self, year: Optional[int] = None) -> InvoiceNumber:
        """Generate next sequential invoice number"""
        if year is None:
            year = datetime.now().year
        
        self._current_sequence += 1
        return InvoiceNumber.generate(year, self._current_sequence)
    
    def validate_number(self, invoice_number: InvoiceNumber) -> bool:
        """Validate invoice number format"""
        try:
            parts = invoice_number.value.split('-')
            return (len(parts) == 3 and 
                   parts[0] == 'INV' and 
                   len(parts[1]) == 4 and 
                   len(parts[2]) == 6 and
                   parts[1].isdigit() and 
                   parts[2].isdigit())
        except:
            return False


class InvoiceStatusTransitionService:
    """Service for managing complex invoice status transitions"""
    
    def can_transition(self, current_status: InvoiceStatus, new_status: InvoiceStatus) -> bool:
        """Check if status transition is valid"""
        return current_status.can_transition_to(new_status)
    
    def validate_transition(self, invoice: Invoice, new_status: InvoiceStatus) -> tuple[bool, Optional[str]]:
        """Validate status transition with detailed reason"""
        if not self.can_transition(invoice.status, new_status):
            return False, f"Invalid transition from {invoice.status.value} to {new_status.value}"
        
        # Additional business rule validations
        if new_status == InvoiceStatus.SENT and not invoice.line_items:
            return False, "Cannot send invoice without line items"
        
        if new_status == InvoiceStatus.PAID and invoice.total_amount.amount == 0:
            return False, "Cannot mark zero-amount invoice as paid"
        
        return True, None
    
    def execute_transition(self, invoice_aggregate: InvoiceAggregate, new_status: InvoiceStatus, 
                          changed_by: str, reason: Optional[str] = None) -> bool:
        """Execute status transition with validation"""
        is_valid, error_message = self.validate_transition(invoice_aggregate.invoice, new_status)
        
        if not is_valid:
            raise ValueError(error_message)
        
        invoice_aggregate.change_status(new_status, changed_by, reason)
        return True


class OverdueInvoiceDetectionService:
    """Service for detecting and processing overdue invoices"""
    
    def detect_overdue_invoices(self, invoices: List[InvoiceAggregate], 
                               as_of_date: Optional[datetime] = None) -> List[InvoiceAggregate]:
        """Detect invoices that have become overdue"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()
        
        overdue_invoices = []
        for invoice_aggregate in invoices:
            if self.should_mark_overdue(invoice_aggregate.invoice, as_of_date):
                overdue_invoices.append(invoice_aggregate)
        
        return overdue_invoices
    
    def should_mark_overdue(self, invoice: Invoice, current_date: datetime) -> bool:
        """Check if invoice should be marked as overdue"""
        return (invoice.status == InvoiceStatus.SENT and 
                invoice.is_overdue(current_date))
    
    def calculate_days_overdue(self, invoice: Invoice, as_of_date: datetime) -> int:
        """Calculate number of days invoice is overdue"""
        return invoice.days_overdue(as_of_date)
    
    def process_overdue_invoices(self, invoices: List[InvoiceAggregate], 
                               as_of_date: Optional[datetime] = None) -> List[InvoiceAggregate]:
        """Process all overdue invoices and mark them as overdue"""
        if as_of_date is None:
            as_of_date = datetime.utcnow()
        
        processed_invoices = []
        overdue_invoices = self.detect_overdue_invoices(invoices, as_of_date)
        
        for invoice_aggregate in overdue_invoices:
            invoice_aggregate.mark_as_overdue(as_of_date)
            processed_invoices.append(invoice_aggregate)
        
        return processed_invoices


class PaymentAllocationService:
    """Service for handling payment allocation across invoices"""
    
    def allocate_payment(self, payment_aggregate: PaymentAggregate, 
                        target_invoices: List[InvoiceAggregate]) -> List[tuple[InvoiceAggregate, Money]]:
        """Allocate payment to invoices using FIFO strategy"""
        if not target_invoices:
            raise ValueError("No target invoices provided")
        
        remaining_payment = payment_aggregate.payment.remaining_amount
        allocations = []
        
        # Sort invoices by due date (FIFO - oldest first)
        sorted_invoices = sorted(target_invoices, key=lambda inv: inv.invoice.due_date)
        
        for invoice_aggregate in sorted_invoices:
            if remaining_payment.amount <= 0:
                break
            
            invoice_balance = invoice_aggregate.invoice.total_amount
            allocation_amount = min(remaining_payment.amount, invoice_balance.amount)
            
            if allocation_amount > 0:
                allocation_money = Money(Decimal(str(allocation_amount)), remaining_payment.currency)
                
                # Allocate to payment
                remaining_balance = invoice_balance.subtract(allocation_money)
                payment_aggregate.allocate_to_invoice(
                    invoice_aggregate.invoice.invoice_id, 
                    allocation_money,
                    remaining_balance
                )
                
                # Apply payment to invoice
                invoice_aggregate.apply_payment(allocation_money)
                
                allocations.append((invoice_aggregate, allocation_money))
                remaining_payment = remaining_payment.subtract(allocation_money)
        
        return allocations
    
    def calculate_remaining_balance(self, invoice: Invoice, allocated_payments: List[Money]) -> Money:
        """Calculate remaining balance after payments"""
        total_allocated = Money(Decimal('0'), invoice.total_amount.currency)
        
        for payment in allocated_payments:
            total_allocated = total_allocated.add(payment)
        
        return invoice.total_amount.subtract(total_allocated)
    
    def validate_allocation(self, payment_aggregate: PaymentAggregate, 
                          allocation_amount: Money) -> tuple[bool, Optional[str]]:
        """Validate payment allocation"""
        if allocation_amount.amount <= 0:
            return False, "Allocation amount must be positive"
        
        if allocation_amount.currency != payment_aggregate.payment.amount.currency:
            return False, "Allocation currency must match payment currency"
        
        remaining = payment_aggregate.payment.remaining_amount
        if allocation_amount.amount > remaining.amount:
            return False, "Cannot allocate more than remaining payment amount"
        
        return True, None


class CustomerCacheService:
    """Service for managing customer data cache in invoices"""
    
    def update_customer_cache(self, invoices: List[InvoiceAggregate], 
                            customer_id: CustomerId, name: str, email: str) -> List[InvoiceAggregate]:
        """Update cached customer data in affected invoices"""
        updated_invoices = []
        
        for invoice_aggregate in invoices:
            if invoice_aggregate.invoice.customer_reference.customer_id == customer_id:
                # Update customer reference
                updated_reference = invoice_aggregate.invoice.customer_reference.update_cache(name, email)
                invoice_aggregate.invoice.customer_reference = updated_reference
                invoice_aggregate.invoice.version += 1
                updated_invoices.append(invoice_aggregate)
        
        return updated_invoices
    
    def validate_customer_reference(self, customer_id: CustomerId, name: str, email: str) -> tuple[bool, Optional[str]]:
        """Validate customer reference data"""
        if not name or not name.strip():
            return False, "Customer name cannot be empty"
        
        if not email or '@' not in email:
            return False, "Invalid customer email format"
        
        return True, None


class InvoiceValidationService:
    """Service for validating invoice business rules"""
    
    def validate_invoice_creation(self, customer_id: CustomerId, line_items_data: List[dict],
                                due_date: datetime, issue_date: datetime) -> tuple[bool, Optional[str]]:
        """Validate invoice creation data"""
        if not line_items_data:
            return False, "Invoice must have at least one line item"
        
        if due_date <= issue_date:
            return False, "Due date must be after issue date"
        
        # Validate line items
        for item in line_items_data:
            if not item.get('description', '').strip():
                return False, "Line item description cannot be empty"
            
            try:
                quantity = Decimal(str(item['quantity']))
                if quantity <= 0:
                    return False, "Line item quantity must be positive"
            except:
                return False, "Invalid line item quantity"
            
            try:
                unit_price = Decimal(str(item['unit_price']))
                if unit_price < 0:
                    return False, "Line item unit price cannot be negative"
            except:
                return False, "Invalid line item unit price"
        
        return True, None
    
    def validate_business_rules(self, invoice_aggregate: InvoiceAggregate) -> tuple[bool, Optional[str]]:
        """Validate general business rules for invoice"""
        invoice = invoice_aggregate.invoice
        
        if invoice.total_amount.amount <= 0:
            return False, "Invoice total amount must be positive"
        
        if not invoice.line_items:
            return False, "Invoice must have line items"
        
        return True, None