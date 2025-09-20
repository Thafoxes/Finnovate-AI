"""Repository Interfaces and In-Memory Implementations"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime
from domain.aggregates import InvoiceAggregate, PaymentAggregate
from domain.value_objects import InvoiceId, PaymentId, CustomerId, InvoiceStatus


# Repository Interfaces

class IInvoiceRepository(ABC):
    """Interface for invoice repository"""
    
    @abstractmethod
    def save(self, invoice_aggregate: InvoiceAggregate) -> None:
        """Save invoice aggregate"""
        pass
    
    @abstractmethod
    def get_by_id(self, invoice_id: InvoiceId) -> Optional[InvoiceAggregate]:
        """Get invoice by ID"""
        pass
    
    @abstractmethod
    def get_by_number(self, invoice_number: str) -> Optional[InvoiceAggregate]:
        """Get invoice by number"""
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: CustomerId) -> List[InvoiceAggregate]:
        """Get invoices by customer ID"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: InvoiceStatus) -> List[InvoiceAggregate]:
        """Get invoices by status"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[InvoiceAggregate]:
        """Get all invoices"""
        pass
    
    @abstractmethod
    def delete(self, invoice_id: InvoiceId) -> bool:
        """Delete invoice by ID"""
        pass


class IPaymentRepository(ABC):
    """Interface for payment repository"""
    
    @abstractmethod
    def save(self, payment_aggregate: PaymentAggregate) -> None:
        """Save payment aggregate"""
        pass
    
    @abstractmethod
    def get_by_id(self, payment_id: PaymentId) -> Optional[PaymentAggregate]:
        """Get payment by ID"""
        pass
    
    @abstractmethod
    def get_by_invoice_id(self, invoice_id: InvoiceId) -> List[PaymentAggregate]:
        """Get payments by invoice ID"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[PaymentAggregate]:
        """Get all payments"""
        pass