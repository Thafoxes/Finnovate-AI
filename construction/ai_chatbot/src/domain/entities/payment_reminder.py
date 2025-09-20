"""
Payment Reminder Entity for Payment Intelligence Domain

Represents individual payment reminder instances with delivery status and metadata.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from .base_entity import Entity, DomainEvent
from ..value_objects.payment_value_objects import ReminderLevel, Money, ContactInformation


class ReminderStatus(Enum):
    """Status of a payment reminder"""
    SCHEDULED = "scheduled"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    REPLIED = "replied"
    FAILED = "failed"
    BOUNCED = "bounced"


class PaymentReminderSentEvent(DomainEvent):
    """Domain event raised when a payment reminder is sent"""
    def __init__(self, reminder_id: str, customer_id: str, invoice_id: str, reminder_level: ReminderLevel):
        super().__init__()
        self.reminder_id = reminder_id
        self.customer_id = customer_id
        self.invoice_id = invoice_id
        self.reminder_level = reminder_level


class PaymentReminderFailedEvent(DomainEvent):
    """Domain event raised when a payment reminder fails to send"""
    def __init__(self, reminder_id: str, customer_id: str, failure_reason: str):
        super().__init__()
        self.reminder_id = reminder_id
        self.customer_id = customer_id
        self.failure_reason = failure_reason


class PaymentReminder(Entity):
    """
    Entity representing a payment reminder sent to a customer.
    
    This entity tracks the lifecycle of individual payment reminders,
    including their status, delivery information, and response tracking.
    """
    
    def __init__(
        self,
        reminder_id: str,
        invoice_id: str,
        customer_id: str,
        reminder_level: ReminderLevel,
        amount_due: Money,
        contact_info: ContactInformation,
        scheduled_date: datetime,
        template_id: str
    ):
        super().__init__(reminder_id)
        
        if not invoice_id:
            raise ValueError("Invoice ID is required")
        if not customer_id:
            raise ValueError("Customer ID is required")
        if not template_id:
            raise ValueError("Template ID is required")
        if scheduled_date < datetime.utcnow() - timedelta(days=1):
            raise ValueError("Scheduled date cannot be more than 1 day in the past")
        
        self._invoice_id = invoice_id
        self._customer_id = customer_id
        self._reminder_level = reminder_level
        self._amount_due = amount_due
        self._contact_info = contact_info
        self._scheduled_date = scheduled_date
        self._template_id = template_id
        
        # Status tracking
        self._status = ReminderStatus.SCHEDULED
        self._sent_date: Optional[datetime] = None
        self._delivery_date: Optional[datetime] = None
        self._last_opened_date: Optional[datetime] = None
        self._response_received: bool = False
        self._failure_reason: Optional[str] = None
        
        # Metadata
        self._delivery_metadata: Dict[str, Any] = {}
        self._retry_count: int = 0
        self._max_retries: int = 3
    
    @property
    def invoice_id(self) -> str:
        return self._invoice_id
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def reminder_level(self) -> ReminderLevel:
        return self._reminder_level
    
    @property
    def amount_due(self) -> Money:
        return self._amount_due
    
    @property
    def contact_info(self) -> ContactInformation:
        return self._contact_info
    
    @property
    def scheduled_date(self) -> datetime:
        return self._scheduled_date
    
    @property
    def template_id(self) -> str:
        return self._template_id
    
    @property
    def status(self) -> ReminderStatus:
        return self._status
    
    @property
    def sent_date(self) -> Optional[datetime]:
        return self._sent_date
    
    @property
    def delivery_date(self) -> Optional[datetime]:
        return self._delivery_date
    
    @property
    def retry_count(self) -> int:
        return self._retry_count
    
    @property
    def response_received(self) -> bool:
        return self._response_received
    
    def mark_as_sent(self, sent_date: Optional[datetime] = None) -> None:
        """Mark the reminder as sent"""
        if self._status != ReminderStatus.SCHEDULED:
            raise ValueError(f"Cannot mark reminder as sent. Current status: {self._status}")
        
        self._sent_date = sent_date or datetime.utcnow()
        self._status = ReminderStatus.SENT
        self.mark_as_modified()
        
        # Raise domain event
        event = PaymentReminderSentEvent(
            reminder_id=self.id,
            customer_id=self._customer_id,
            invoice_id=self._invoice_id,
            reminder_level=self._reminder_level
        )
        self.add_domain_event(event)
    
    def mark_as_delivered(self, delivery_date: Optional[datetime] = None) -> None:
        """Mark the reminder as delivered"""
        if self._status not in [ReminderStatus.SENT, ReminderStatus.DELIVERED]:
            raise ValueError(f"Cannot mark reminder as delivered. Current status: {self._status}")
        
        self._delivery_date = delivery_date or datetime.utcnow()
        self._status = ReminderStatus.DELIVERED
        self.mark_as_modified()
    
    def mark_as_opened(self, opened_date: Optional[datetime] = None) -> None:
        """Mark the reminder as opened by recipient"""
        if self._status not in [ReminderStatus.DELIVERED, ReminderStatus.OPENED]:
            raise ValueError(f"Cannot mark reminder as opened. Current status: {self._status}")
        
        self._last_opened_date = opened_date or datetime.utcnow()
        self._status = ReminderStatus.OPENED
        self.mark_as_modified()
    
    def mark_as_clicked(self) -> None:
        """Mark that recipient clicked links in the reminder"""
        if self._status not in [ReminderStatus.OPENED, ReminderStatus.CLICKED]:
            raise ValueError(f"Cannot mark reminder as clicked. Current status: {self._status}")
        
        self._status = ReminderStatus.CLICKED
        self.mark_as_modified()
    
    def mark_as_replied(self) -> None:
        """Mark that recipient replied to the reminder"""
        self._response_received = True
        self._status = ReminderStatus.REPLIED
        self.mark_as_modified()
    
    def mark_as_failed(self, failure_reason: str, can_retry: bool = True) -> None:
        """Mark the reminder as failed to send"""
        if not failure_reason:
            raise ValueError("Failure reason is required")
        
        self._failure_reason = failure_reason
        self._status = ReminderStatus.FAILED
        self.mark_as_modified()
        
        # Raise domain event
        event = PaymentReminderFailedEvent(
            reminder_id=self.id,
            customer_id=self._customer_id,
            failure_reason=failure_reason
        )
        self.add_domain_event(event)
        
        # Increment retry count if retryable
        if can_retry:
            self._retry_count += 1
    
    def can_retry(self) -> bool:
        """Check if the reminder can be retried"""
        return (
            self._status == ReminderStatus.FAILED and
            self._retry_count < self._max_retries
        )
    
    def is_overdue_for_sending(self) -> bool:
        """Check if the reminder is overdue for sending"""
        return (
            self._status == ReminderStatus.SCHEDULED and
            datetime.utcnow() > self._scheduled_date
        )
    
    def is_successful(self) -> bool:
        """Check if the reminder was successful (delivered and potentially opened)"""
        return self._status in [
            ReminderStatus.DELIVERED,
            ReminderStatus.OPENED,
            ReminderStatus.CLICKED,
            ReminderStatus.REPLIED
        ]
    
    def is_final_level(self) -> bool:
        """Check if this is the final reminder level"""
        return self._reminder_level.is_final_reminder()
    
    def add_delivery_metadata(self, key: str, value: Any) -> None:
        """Add delivery metadata (e.g., email provider response)"""
        self._delivery_metadata[key] = value
        self.mark_as_modified()
    
    def get_delivery_metadata(self) -> Dict[str, Any]:
        """Get delivery metadata"""
        return self._delivery_metadata.copy()
    
    def reschedule(self, new_date: datetime) -> None:
        """Reschedule the reminder to a new date"""
        if self._status != ReminderStatus.SCHEDULED:
            raise ValueError(f"Cannot reschedule reminder. Current status: {self._status}")
        
        if new_date <= datetime.utcnow():
            raise ValueError("New scheduled date must be in the future")
        
        self._scheduled_date = new_date
        self.mark_as_modified()
    
    def get_days_since_scheduled(self) -> int:
        """Get the number of days since the reminder was scheduled"""
        return (datetime.utcnow() - self._scheduled_date).days
    
    def __str__(self) -> str:
        return f"PaymentReminder(id={self.id}, level={self._reminder_level.value}, status={self._status.value})"