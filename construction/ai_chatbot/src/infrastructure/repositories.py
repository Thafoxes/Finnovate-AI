"""
Infrastructure layer repository implementations.

This module provides concrete implementations of repository interfaces
defined in the domain layer, following the Repository pattern.
For MVP scope, using in-memory storage with thread-safe operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from threading import Lock
import uuid

from ..domain.value_objects import (
    CustomerId, InvoiceId, ConversationId, CampaignId, MessageId
)
from ..domain.entities import (
    Customer, OverdueInvoice, ConversationMessage, PaymentReminder
)
from ..domain.aggregates import PaymentCampaign, Conversation
from ..domain.repositories import (
    CustomerRepository, InvoiceRepository, PaymentCampaignRepository,
    ConversationRepository
)


class InMemoryCustomerRepository(CustomerRepository):
    """In-memory implementation of CustomerRepository for MVP."""
    
    def __init__(self):
        self._customers: Dict[str, Customer] = {}
        self._lock = Lock()
    
    async def find_by_id(self, customer_id: CustomerId) -> Optional[Customer]:
        """Find customer by ID."""
        with self._lock:
            return self._customers.get(customer_id.value)
    
    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Find customer by email address."""
        with self._lock:
            for customer in self._customers.values():
                if customer.email == email:
                    return customer
            return None
    
    async def find_by_company_name(self, company_name: str) -> List[Customer]:
        """Find customers by company name."""
        with self._lock:
            return [
                customer for customer in self._customers.values()
                if customer.company_name and company_name.lower() in customer.company_name.lower()
            ]
    
    async def find_customers_with_overdue_invoices(self) -> List[Customer]:
        """Find customers who have overdue invoices."""
        # Note: This would typically join with invoice repository
        # For MVP, returning all customers for simplicity
        with self._lock:
            return list(self._customers.values())
    
    async def save(self, customer: Customer) -> None:
        """Save customer to repository."""
        with self._lock:
            self._customers[customer.customer_id.value] = customer
    
    async def delete(self, customer_id: CustomerId) -> None:
        """Delete customer from repository."""
        with self._lock:
            self._customers.pop(customer_id.value, None)


class InMemoryInvoiceRepository(InvoiceRepository):
    """In-memory implementation of InvoiceRepository for MVP."""
    
    def __init__(self):
        self._invoices: Dict[str, OverdueInvoice] = {}
        self._lock = Lock()
    
    async def find_by_id(self, invoice_id: InvoiceId) -> Optional[OverdueInvoice]:
        """Find invoice by ID."""
        with self._lock:
            return self._invoices.get(invoice_id.value)
    
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[OverdueInvoice]:
        """Find all overdue invoices for a customer."""
        with self._lock:
            return [
                invoice for invoice in self._invoices.values()
                if invoice.customer_id == customer_id
            ]
    
    async def find_overdue_invoices(
        self, 
        days_overdue: Optional[int] = None,
        min_amount: Optional[float] = None
    ) -> List[OverdueInvoice]:
        """Find overdue invoices with optional filters."""
        with self._lock:
            invoices = list(self._invoices.values())
            
            if days_overdue is not None:
                invoices = [
                    inv for inv in invoices 
                    if inv.days_overdue >= days_overdue
                ]
            
            if min_amount is not None:
                invoices = [
                    inv for inv in invoices 
                    if inv.amount_due >= min_amount
                ]
            
            return invoices
    
    async def find_by_priority(self, priority: str) -> List[OverdueInvoice]:
        """Find invoices by priority level."""
        with self._lock:
            return [
                invoice for invoice in self._invoices.values()
                if invoice.priority.lower() == priority.lower()
            ]
    
    async def save(self, invoice: OverdueInvoice) -> None:
        """Save invoice to repository."""
        with self._lock:
            self._invoices[invoice.invoice_id.value] = invoice
    
    async def delete(self, invoice_id: InvoiceId) -> None:
        """Delete invoice from repository."""
        with self._lock:
            self._invoices.pop(invoice_id.value, None)
    
    async def update_payment_status(self, invoice_id: InvoiceId, status: str) -> None:
        """Update payment status of an invoice."""
        with self._lock:
            if invoice_id.value in self._invoices:
                invoice = self._invoices[invoice_id.value]
                # Create updated invoice with new status
                updated_invoice = OverdueInvoice(
                    invoice_id=invoice.invoice_id,
                    customer_id=invoice.customer_id,
                    amount_due=invoice.amount_due,
                    due_date=invoice.due_date,
                    currency=invoice.currency,
                    description=invoice.description,
                    priority=invoice.priority,
                    payment_terms=invoice.payment_terms
                )
                # Note: In real implementation, would have status field
                self._invoices[invoice_id.value] = updated_invoice


class InMemoryPaymentCampaignRepository(PaymentCampaignRepository):
    """In-memory implementation of PaymentCampaignRepository for MVP."""
    
    def __init__(self):
        self._campaigns: Dict[str, PaymentCampaign] = {}
        self._lock = Lock()
    
    async def find_by_id(self, campaign_id: CampaignId) -> Optional[PaymentCampaign]:
        """Find campaign by ID."""
        with self._lock:
            return self._campaigns.get(campaign_id.value)
    
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[PaymentCampaign]:
        """Find all campaigns for a customer."""
        with self._lock:
            return [
                campaign for campaign in self._campaigns.values()
                if campaign.customer_id == customer_id
            ]
    
    async def find_active_campaigns(self) -> List[PaymentCampaign]:
        """Find all active payment campaigns."""
        with self._lock:
            return [
                campaign for campaign in self._campaigns.values()
                if campaign.is_active()
            ]
    
    async def find_campaigns_needing_escalation(self) -> List[PaymentCampaign]:
        """Find campaigns that need escalation."""
        with self._lock:
            return [
                campaign for campaign in self._campaigns.values()
                if campaign.should_escalate()
            ]
    
    async def find_by_status(self, status: str) -> List[PaymentCampaign]:
        """Find campaigns by status."""
        with self._lock:
            return [
                campaign for campaign in self._campaigns.values()
                if campaign.status.lower() == status.lower()
            ]
    
    async def save(self, campaign: PaymentCampaign) -> None:
        """Save campaign to repository."""
        with self._lock:
            self._campaigns[campaign.campaign_id.value] = campaign
    
    async def delete(self, campaign_id: CampaignId) -> None:
        """Delete campaign from repository."""
        with self._lock:
            self._campaigns.pop(campaign_id.value, None)


class InMemoryConversationRepository(ConversationRepository):
    """In-memory implementation of ConversationRepository for MVP."""
    
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
        self._lock = Lock()
    
    async def find_by_id(self, conversation_id: ConversationId) -> Optional[Conversation]:
        """Find conversation by ID."""
        with self._lock:
            return self._conversations.get(conversation_id.value)
    
    async def find_by_customer_id(self, customer_id: CustomerId) -> List[Conversation]:
        """Find all conversations for a customer."""
        with self._lock:
            return [
                conversation for conversation in self._conversations.values()
                if conversation.customer_id == customer_id
            ]
    
    async def find_by_campaign_id(self, campaign_id: CampaignId) -> List[Conversation]:
        """Find conversations for a specific campaign."""
        with self._lock:
            return [
                conversation for conversation in self._conversations.values()
                if conversation.campaign_id == campaign_id
            ]
    
    async def find_active_conversations(self) -> List[Conversation]:
        """Find all active conversations."""
        with self._lock:
            return [
                conversation for conversation in self._conversations.values()
                if conversation.is_active()
            ]
    
    async def find_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """Find most recent conversations."""
        with self._lock:
            conversations = list(self._conversations.values())
            # Sort by last message timestamp (assuming we have this)
            conversations.sort(
                key=lambda c: c.started_at, 
                reverse=True
            )
            return conversations[:limit]
    
    async def save(self, conversation: Conversation) -> None:
        """Save conversation to repository."""
        with self._lock:
            self._conversations[conversation.conversation_id.value] = conversation
    
    async def delete(self, conversation_id: ConversationId) -> None:
        """Delete conversation from repository."""
        with self._lock:
            self._conversations.pop(conversation_id.value, None)


# Repository factory for dependency injection
class RepositoryFactory:
    """Factory for creating repository instances."""
    
    @staticmethod
    def create_customer_repository() -> CustomerRepository:
        """Create customer repository instance."""
        return InMemoryCustomerRepository()
    
    @staticmethod
    def create_invoice_repository() -> InvoiceRepository:
        """Create invoice repository instance."""
        return InMemoryInvoiceRepository()
    
    @staticmethod
    def create_payment_campaign_repository() -> PaymentCampaignRepository:
        """Create payment campaign repository instance."""
        return InMemoryPaymentCampaignRepository()
    
    @staticmethod
    def create_conversation_repository() -> ConversationRepository:
        """Create conversation repository instance."""
        return InMemoryConversationRepository()


# Singleton instances for MVP (in production, use proper DI container)
_customer_repo = None
_invoice_repo = None
_campaign_repo = None
_conversation_repo = None


def get_customer_repository() -> CustomerRepository:
    """Get singleton customer repository instance."""
    global _customer_repo
    if _customer_repo is None:
        _customer_repo = RepositoryFactory.create_customer_repository()
    return _customer_repo


def get_invoice_repository() -> InvoiceRepository:
    """Get singleton invoice repository instance."""
    global _invoice_repo
    if _invoice_repo is None:
        _invoice_repo = RepositoryFactory.create_invoice_repository()
    return _invoice_repo


def get_payment_campaign_repository() -> PaymentCampaignRepository:
    """Get singleton payment campaign repository instance."""
    global _campaign_repo
    if _campaign_repo is None:
        _campaign_repo = RepositoryFactory.create_payment_campaign_repository()
    return _campaign_repo


def get_conversation_repository() -> ConversationRepository:
    """Get singleton conversation repository instance."""
    global _conversation_repo
    if _conversation_repo is None:
        _conversation_repo = RepositoryFactory.create_conversation_repository()
    return _conversation_repo