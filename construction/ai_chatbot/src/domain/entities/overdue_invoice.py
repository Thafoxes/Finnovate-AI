"""
Overdue Invoice Entity for Payment Intelligence Domain

Represents an invoice that requires payment collection with extended metadata.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from .base_entity import Entity, DomainEvent
from ..value_objects.payment_value_objects import PaymentStatus, Money, ReminderLevel


class PaymentPriority(Enum):
    """Priority levels for payment collection"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PaymentReceivedEvent(DomainEvent):
    """Domain event raised when payment is received for an invoice"""
    def __init__(self, invoice_id: str, amount_paid: Money, payment_method: str):
        super().__init__()
        self.invoice_id = invoice_id
        self.amount_paid = amount_paid
        self.payment_method = payment_method


class EscalationTriggeredEvent(DomainEvent):
    """Domain event raised when an invoice is escalated to collections"""
    def __init__(self, invoice_id: str, customer_id: str, reason: str):
        super().__init__()
        self.invoice_id = invoice_id
        self.customer_id = customer_id
        self.reason = reason


class OverdueInvoice(Entity):
    """
    Entity representing an overdue invoice with payment collection metadata.
    
    Extends basic invoice information with collection-specific data
    such as reminder history, escalation status, and payment attempts.
    """
    
    def __init__(
        self,
        invoice_id: str,
        customer_id: str,
        invoice_number: str,
        original_amount: Money,
        due_date: datetime,
        issue_date: datetime,
        description: str = ""
    ):
        super().__init__(invoice_id)
        
        if not customer_id:
            raise ValueError("Customer ID is required")
        if not invoice_number:
            raise ValueError("Invoice number is required")
        if due_date < issue_date:
            raise ValueError("Due date cannot be before issue date")
        
        self._customer_id = customer_id
        self._invoice_number = invoice_number
        self._original_amount = original_amount
        self._due_date = due_date
        self._issue_date = issue_date
        self._description = description
        
        # Payment tracking
        self._current_balance = original_amount
        self._payment_status = PaymentStatus.PENDING if due_date > datetime.utcnow() else PaymentStatus.OVERDUE
        self._payments_received: List[Dict[str, Any]] = []
        
        # Collection metadata
        self._reminder_count = 0
        self._last_reminder_date: Optional[datetime] = None
        self._current_reminder_level = ReminderLevel.FIRST
        self._escalation_date: Optional[datetime] = None
        self._priority = self._calculate_initial_priority()
        
        # Customer interaction
        self._payment_promises: List[Dict[str, Any]] = []
        self._disputes: List[Dict[str, Any]] = []
        self._collection_notes: List[str] = []
        self._last_contact_date: Optional[datetime] = None
        
        # AI/Automation metadata
        self._ai_risk_score: Optional[float] = None
        self._predicted_payment_date: Optional[datetime] = None
        self._recommended_actions: List[str] = []
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def invoice_number(self) -> str:
        return self._invoice_number
    
    @property
    def original_amount(self) -> Money:
        return self._original_amount
    
    @property
    def current_balance(self) -> Money:
        return self._current_balance
    
    @property
    def due_date(self) -> datetime:
        return self._due_date
    
    @property
    def issue_date(self) -> datetime:
        return self._issue_date
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def payment_status(self) -> PaymentStatus:
        return self._payment_status
    
    @property
    def reminder_count(self) -> int:
        return self._reminder_count
    
    @property
    def current_reminder_level(self) -> ReminderLevel:
        return self._current_reminder_level
    
    @property
    def priority(self) -> PaymentPriority:
        return self._priority
    
    @property
    def days_overdue(self) -> int:
        """Calculate number of days overdue"""
        if self._payment_status not in [PaymentStatus.OVERDUE, PaymentStatus.PARTIALLY_PAID]:
            return 0
        return max(0, (datetime.utcnow() - self._due_date).days)
    
    @property
    def ai_risk_score(self) -> Optional[float]:
        return self._ai_risk_score
    
    def record_payment(self, amount: Money, payment_method: str, payment_date: Optional[datetime] = None) -> None:
        """Record a payment received for this invoice"""
        if amount.currency != self._current_balance.currency:
            raise ValueError(f"Payment currency {amount.currency} doesn't match invoice currency {self._current_balance.currency}")
        
        if amount.amount <= 0:
            raise ValueError("Payment amount must be positive")
        
        if amount.amount > self._current_balance.amount:
            raise ValueError("Payment amount cannot exceed current balance")
        
        payment_date = payment_date or datetime.utcnow()
        
        payment_record = {
            "amount": amount,
            "payment_method": payment_method,
            "payment_date": payment_date,
            "recorded_at": datetime.utcnow()
        }
        
        self._payments_received.append(payment_record)
        self._current_balance = self._current_balance.subtract(amount)
        
        # Update payment status
        if self._current_balance.is_zero():
            self._payment_status = PaymentStatus.PAID
        elif self._payment_status == PaymentStatus.OVERDUE:
            self._payment_status = PaymentStatus.PARTIALLY_PAID
        
        self.mark_as_modified()
        
        # Raise domain event
        event = PaymentReceivedEvent(
            invoice_id=self.id,
            amount_paid=amount,
            payment_method=payment_method
        )
        self.add_domain_event(event)
    
    def record_reminder_sent(self, reminder_level: ReminderLevel, sent_date: Optional[datetime] = None) -> None:
        """Record that a payment reminder was sent"""
        sent_date = sent_date or datetime.utcnow()
        
        self._reminder_count += 1
        self._last_reminder_date = sent_date
        self._current_reminder_level = reminder_level
        self._last_contact_date = sent_date
        
        self.mark_as_modified()
    
    def escalate_to_collections(self, reason: str, escalation_date: Optional[datetime] = None) -> None:
        """Escalate the invoice to collections process"""
        if self._payment_status == PaymentStatus.PAID:
            raise ValueError("Cannot escalate paid invoice")
        
        escalation_date = escalation_date or datetime.utcnow()
        
        self._escalation_date = escalation_date
        self._current_reminder_level = ReminderLevel.ESCALATED
        self._priority = PaymentPriority.CRITICAL
        
        self.mark_as_modified()
        
        # Raise domain event
        event = EscalationTriggeredEvent(
            invoice_id=self.id,
            customer_id=self._customer_id,
            reason=reason
        )
        self.add_domain_event(event)
    
    def add_payment_promise(self, promised_amount: Money, promised_date: datetime, notes: str = "") -> None:
        """Record a customer's promise to pay"""
        promise = {
            "promised_amount": promised_amount,
            "promised_date": promised_date,
            "notes": notes,
            "recorded_at": datetime.utcnow(),
            "fulfilled": False
        }
        
        self._payment_promises.append(promise)
        self._last_contact_date = datetime.utcnow()
        self.mark_as_modified()
    
    def add_dispute(self, dispute_reason: str, disputed_amount: Money, notes: str = "") -> None:
        """Record a customer dispute"""
        dispute = {
            "reason": dispute_reason,
            "disputed_amount": disputed_amount,
            "notes": notes,
            "recorded_at": datetime.utcnow(),
            "resolved": False
        }
        
        self._disputes.append(dispute)
        self._payment_status = PaymentStatus.DISPUTED
        self._last_contact_date = datetime.utcnow()
        self.mark_as_modified()
    
    def add_collection_note(self, note: str) -> None:
        """Add a collection note"""
        if not note.strip():
            raise ValueError("Collection note cannot be empty")
        
        timestamped_note = f"[{datetime.utcnow().isoformat()}] {note}"
        self._collection_notes.append(timestamped_note)
        self.mark_as_modified()
    
    def update_ai_risk_score(self, risk_score: float) -> None:
        """Update the AI-calculated risk score (0.0 to 1.0)"""
        if not 0.0 <= risk_score <= 1.0:
            raise ValueError("Risk score must be between 0.0 and 1.0")
        
        self._ai_risk_score = risk_score
        self._priority = self._calculate_priority_from_risk(risk_score)
        self.mark_as_modified()
    
    def set_predicted_payment_date(self, predicted_date: datetime) -> None:
        """Set AI-predicted payment date"""
        if predicted_date < datetime.utcnow():
            raise ValueError("Predicted payment date cannot be in the past")
        
        self._predicted_payment_date = predicted_date
        self.mark_as_modified()
    
    def add_recommended_action(self, action: str) -> None:
        """Add an AI-recommended action"""
        if action not in self._recommended_actions:
            self._recommended_actions.append(action)
            self.mark_as_modified()
    
    def is_ready_for_next_reminder(self, min_days_between_reminders: int = 7) -> bool:
        """Check if enough time has passed for the next reminder"""
        if not self._last_reminder_date:
            return True
        
        days_since_last = (datetime.utcnow() - self._last_reminder_date).days
        return days_since_last >= min_days_between_reminders
    
    def requires_escalation(self) -> bool:
        """Check if the invoice should be escalated"""
        return (
            self._current_reminder_level == ReminderLevel.THIRD and
            self.days_overdue > 21 and
            not self._escalation_date
        )
    
    def is_high_risk(self) -> bool:
        """Check if this is a high-risk invoice"""
        return (
            self._ai_risk_score is not None and self._ai_risk_score > 0.7
        ) or (
            self.days_overdue > 30 and 
            self._current_balance.amount > 1000
        )
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get a summary of collection activities"""
        return {
            "invoice_id": self.id,
            "customer_id": self._customer_id,
            "original_amount": self._original_amount,
            "current_balance": self._current_balance,
            "days_overdue": self.days_overdue,
            "reminder_count": self._reminder_count,
            "current_level": self._current_reminder_level.value,
            "priority": self._priority.value,
            "payments_count": len(self._payments_received),
            "promises_count": len(self._payment_promises),
            "disputes_count": len(self._disputes),
            "ai_risk_score": self._ai_risk_score,
            "is_escalated": self._escalation_date is not None
        }
    
    def _calculate_initial_priority(self) -> PaymentPriority:
        """Calculate initial priority based on amount and customer history"""
        amount = self._original_amount.amount
        
        if amount >= 10000:
            return PaymentPriority.HIGH
        elif amount >= 5000:
            return PaymentPriority.MEDIUM
        else:
            return PaymentPriority.LOW
    
    def _calculate_priority_from_risk(self, risk_score: float) -> PaymentPriority:
        """Calculate priority based on AI risk score"""
        if risk_score >= 0.8:
            return PaymentPriority.CRITICAL
        elif risk_score >= 0.6:
            return PaymentPriority.HIGH
        elif risk_score >= 0.4:
            return PaymentPriority.MEDIUM
        else:
            return PaymentPriority.LOW
    
    def __str__(self) -> str:
        return f"OverdueInvoice(id={self.id}, number={self._invoice_number}, balance={self._current_balance}, days_overdue={self.days_overdue})"