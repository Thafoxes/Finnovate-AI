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


# In-Memory Implementations

class InMemoryInvoiceRepository(IInvoiceRepository):
    """In-memory implementation of invoice repository"""
    
    def __init__(self):
        self._invoices: Dict[str, InvoiceAggregate] = {}
    
    def save(self, invoice_aggregate: InvoiceAggregate) -> None:
        """Save invoice aggregate"""
        invoice_id = str(invoice_aggregate.invoice.invoice_id)
        self._invoices[invoice_id] = invoice_aggregate
    
    def get_by_id(self, invoice_id: InvoiceId) -> Optional[InvoiceAggregate]:
        """Get invoice by ID"""
        return self._invoices.get(str(invoice_id))
    
    def get_by_number(self, invoice_number: str) -> Optional[InvoiceAggregate]:
        """Get invoice by number"""
        for invoice_aggregate in self._invoices.values():
            if str(invoice_aggregate.invoice.invoice_number) == invoice_number:
                return invoice_aggregate
        return None
    
    def get_by_customer_id(self, customer_id: CustomerId) -> List[InvoiceAggregate]:
        """Get invoices by customer ID"""
        result = []
        for invoice_aggregate in self._invoices.values():
            if invoice_aggregate.invoice.customer_reference.customer_id == customer_id:
                result.append(invoice_aggregate)
        return result
    
    def get_by_status(self, status: InvoiceStatus) -> List[InvoiceAggregate]:
        """Get invoices by status"""
        result = []
        for invoice_aggregate in self._invoices.values():
            if invoice_aggregate.invoice.status == status:
                result.append(invoice_aggregate)
        return result
    
    def get_all(self) -> List[InvoiceAggregate]:
        """Get all invoices"""
        return list(self._invoices.values())
    
    def delete(self, invoice_id: InvoiceId) -> bool:
        """Delete invoice by ID"""
        invoice_id_str = str(invoice_id)
        if invoice_id_str in self._invoices:
            del self._invoices[invoice_id_str]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all invoices (for testing)"""
        self._invoices.clear()
    
    def count(self) -> int:
        """Get count of invoices"""
        return len(self._invoices)


class InMemoryPaymentRepository(IPaymentRepository):
    """In-memory implementation of payment repository"""
    
    def __init__(self):
        self._payments: Dict[str, PaymentAggregate] = {}
    
    def save(self, payment_aggregate: PaymentAggregate) -> None:
        """Save payment aggregate"""
        payment_id = str(payment_aggregate.payment.payment_id)
        self._payments[payment_id] = payment_aggregate
    
    def get_by_id(self, payment_id: PaymentId) -> Optional[PaymentAggregate]:
        """Get payment by ID"""
        return self._payments.get(str(payment_id))
    
    def get_by_invoice_id(self, invoice_id: InvoiceId) -> List[PaymentAggregate]:
        """Get payments by invoice ID"""
        result = []
        for payment_aggregate in self._payments.values():
            for allocation in payment_aggregate.payment.allocations:
                if allocation.invoice_id == invoice_id:
                    result.append(payment_aggregate)
                    break
        return result
    
    def get_all(self) -> List[PaymentAggregate]:
        """Get all payments"""
        return list(self._payments.values())
    
    def clear(self) -> None:
        """Clear all payments (for testing)"""
        self._payments.clear()
    
    def count(self) -> int:
        """Get count of payments"""
        return len(self._payments)


# Mock Customer Management Client

class MockCustomerManagementClient:
    """Mock client for Customer Management service"""
    
    def __init__(self):
        # Mock customer data
        self._customers = {
            "customer-1": {"name": "Acme Corp", "email": "billing@acme.com", "active": True},
            "customer-2": {"name": "TechStart Inc", "email": "finance@techstart.com", "active": True},
            "customer-3": {"name": "Global Solutions", "email": "accounts@global.com", "active": True}
        }
    
    def validate_customer(self, customer_id: str) -> bool:
        """Validate if customer exists and is active"""
        customer = self._customers.get(customer_id)
        return customer is not None and customer.get("active", False)
    
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer information"""
        return self._customers.get(customer_id)
    
    def add_customer(self, customer_id: str, name: str, email: str) -> None:
        """Add customer for testing"""
        self._customers[customer_id] = {"name": name, "email": email, "active": True}


# Repository Factory

class RepositoryFactory:
    """Factory for creating repository instances"""
    
    @staticmethod
    def create_invoice_repository() -> IInvoiceRepository:
        """Create invoice repository instance"""
        return InMemoryInvoiceRepository()
    
    @staticmethod
    def create_payment_repository() -> IPaymentRepository:
        """Create payment repository instance"""
        return InMemoryPaymentRepository()
    
    @staticmethod
    def create_customer_client() -> MockCustomerManagementClient:
        """Create customer management client"""
        return MockCustomerManagementClient()


# Repository Manager (for demo purposes)

class RepositoryManager:
    """Manager for repository instances (singleton pattern for demo)"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._invoice_repository = InMemoryInvoiceRepository()
            self._payment_repository = InMemoryPaymentRepository()
            self._customer_client = MockCustomerManagementClient()
            self._initialized = True
    
    @property
    def invoice_repository(self) -> IInvoiceRepository:
        return self._invoice_repository
    
    @property
    def payment_repository(self) -> IPaymentRepository:
        return self._payment_repository
    
    @property
    def customer_client(self) -> MockCustomerManagementClient:
        return self._customer_client
    
    def reset(self) -> None:
        """Reset all repositories (for testing)"""
        self._invoice_repository.clear()
        self._payment_repository.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get repository statistics"""
        return {
            "invoices": self._invoice_repository.count(),
            "payments": self._payment_repository.count()
        }