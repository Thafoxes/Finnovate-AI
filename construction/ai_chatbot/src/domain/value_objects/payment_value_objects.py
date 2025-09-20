"""
Domain Value Objects for Payment Intelligence Bounded Context

Value objects are immutable objects that represent descriptive aspects of the domain
with no conceptual identity. They are compared by their attributes rather than identity.
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


class ReminderLevel(Enum):
    """Enumeration for payment reminder escalation levels"""
    FIRST = "first"
    SECOND = "second" 
    THIRD = "third"
    ESCALATED = "escalated"
    
    def __str__(self) -> str:
        return self.value
    
    def next_level(self) -> Optional['ReminderLevel']:
        """Get the next escalation level"""
        levels = [ReminderLevel.FIRST, ReminderLevel.SECOND, ReminderLevel.THIRD, ReminderLevel.ESCALATED]
        try:
            current_index = levels.index(self)
            if current_index < len(levels) - 1:
                return levels[current_index + 1]
            return None
        except ValueError:
            return None
    
    def is_final_reminder(self) -> bool:
        """Check if this is the final automated reminder before escalation"""
        return self == ReminderLevel.THIRD


class PaymentStatus(Enum):
    """Enumeration for payment status tracking"""
    PENDING = "pending"
    OVERDUE = "overdue"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    IN_DEFAULT = "in_default"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"
    
    def __str__(self) -> str:
        return self.value
    
    def is_actionable(self) -> bool:
        """Check if this status requires payment collection action"""
        return self in [PaymentStatus.OVERDUE, PaymentStatus.PARTIALLY_PAID]
    
    def is_collectible(self) -> bool:
        """Check if payment can still be collected"""
        return self not in [PaymentStatus.PAID, PaymentStatus.CANCELLED, PaymentStatus.IN_DEFAULT]


class MessageIntent(Enum):
    """Enumeration for chatbot message intent classification"""
    PAYMENT_INQUIRY = "payment_inquiry"
    REMINDER_REQUEST = "reminder_request"
    ESCALATION_TRIGGER = "escalation_trigger"
    ALTERNATIVE_PAYMENT_REQUEST = "alternative_payment_request"
    PAYMENT_PLAN_INQUIRY = "payment_plan_inquiry"
    GENERAL_QUESTION = "general_question"
    COMPLAINT = "complaint"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    
    def __str__(self) -> str:
        return self.value
    
    def requires_immediate_action(self) -> bool:
        """Check if this intent requires immediate action"""
        return self in [
            MessageIntent.ESCALATION_TRIGGER,
            MessageIntent.COMPLAINT,
            MessageIntent.PAYMENT_CONFIRMATION
        ]


@dataclass(frozen=True)
class Money:
    """Value object representing monetary amounts"""
    amount: float
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency code is required")
        if len(self.currency) != 3:
            raise ValueError("Currency code must be 3 characters")
    
    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts (must be same currency)"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract two money amounts (must be same currency)"""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} and {other.currency}")
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Subtraction would result in negative amount")
        return Money(result_amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        """Multiply money by a factor"""
        if factor < 0:
            raise ValueError("Factor cannot be negative")
        return Money(self.amount * factor, self.currency)
    
    def is_zero(self) -> bool:
        """Check if amount is zero"""
        return abs(self.amount) < 0.01  # Account for floating point precision
    
    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"


@dataclass(frozen=True)
class ConversationContext:
    """Value object representing the current state of a conversation"""
    user_id: str
    session_id: str
    current_intent: Optional[MessageIntent]
    related_invoice_ids: List[str]
    customer_info: Optional[dict]
    conversation_stage: str
    last_action_timestamp: datetime
    sentiment_score: Optional[float] = None
    escalation_flags: List[str] = None
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("User ID is required")
        if not self.session_id:
            raise ValueError("Session ID is required")
        if not self.conversation_stage:
            raise ValueError("Conversation stage is required")
        
        # Set default empty list if None
        if self.escalation_flags is None:
            object.__setattr__(self, 'escalation_flags', [])
    
    def with_intent(self, intent: MessageIntent) -> 'ConversationContext':
        """Create new context with updated intent"""
        return ConversationContext(
            user_id=self.user_id,
            session_id=self.session_id,
            current_intent=intent,
            related_invoice_ids=self.related_invoice_ids,
            customer_info=self.customer_info,
            conversation_stage=self.conversation_stage,
            last_action_timestamp=datetime.now(),
            sentiment_score=self.sentiment_score,
            escalation_flags=self.escalation_flags
        )
    
    def add_invoice(self, invoice_id: str) -> 'ConversationContext':
        """Create new context with additional invoice"""
        new_invoice_ids = self.related_invoice_ids + [invoice_id]
        return ConversationContext(
            user_id=self.user_id,
            session_id=self.session_id,
            current_intent=self.current_intent,
            related_invoice_ids=new_invoice_ids,
            customer_info=self.customer_info,
            conversation_stage=self.conversation_stage,
            last_action_timestamp=self.last_action_timestamp,
            sentiment_score=self.sentiment_score,
            escalation_flags=self.escalation_flags
        )
    
    def requires_escalation(self) -> bool:
        """Check if conversation should be escalated"""
        return len(self.escalation_flags) > 0 or (
            self.sentiment_score is not None and self.sentiment_score < 0.3
        )


@dataclass(frozen=True)
class EmailTemplate:
    """Value object representing an AI-generated email template"""
    template_id: str
    subject: str
    body: str
    reminder_level: ReminderLevel
    tone: str  # "professional", "friendly", "urgent", "formal"
    personalization_tokens: List[str]
    created_at: datetime
    
    def __post_init__(self):
        if not self.template_id:
            raise ValueError("Template ID is required")
        if not self.subject:
            raise ValueError("Email subject is required")
        if not self.body:
            raise ValueError("Email body is required")
        if not self.tone:
            raise ValueError("Email tone is required")
        
        # Set default empty list if None
        if self.personalization_tokens is None:
            object.__setattr__(self, 'personalization_tokens', [])
    
    def is_escalated_template(self) -> bool:
        """Check if this is an escalated communication template"""
        return self.reminder_level == ReminderLevel.ESCALATED
    
    def get_estimated_length(self) -> int:
        """Get estimated character length of email"""
        return len(self.subject) + len(self.body)
    
    def requires_personalization(self) -> bool:
        """Check if template requires personalization"""
        return len(self.personalization_tokens) > 0


@dataclass(frozen=True)
class ContactInformation:
    """Value object for customer contact information"""
    email: str
    phone: Optional[str] = None
    preferred_contact_method: str = "email"
    
    def __post_init__(self):
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email format")
        if self.preferred_contact_method not in ["email", "phone", "both"]:
            raise ValueError("Invalid preferred contact method")
    
    def can_contact_via_email(self) -> bool:
        """Check if customer can be contacted via email"""
        return self.preferred_contact_method in ["email", "both"]
    
    def can_contact_via_phone(self) -> bool:
        """Check if customer can be contacted via phone"""
        return self.phone is not None and self.preferred_contact_method in ["phone", "both"]