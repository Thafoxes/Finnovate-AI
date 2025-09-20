"""
Payment Campaign Aggregate Root for Payment Intelligence Domain

Manages the entire lifecycle of payment collection for an invoice including
reminders, escalation logic, and alternative payment options.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from ..entities.base_entity import Entity, DomainEvent
from ..entities.payment_reminder import PaymentReminder, ReminderStatus
from ..entities.overdue_invoice import OverdueInvoice, PaymentPriority
from ..entities.message import AlternativePaymentOption
from ..value_objects.payment_value_objects import ReminderLevel, PaymentStatus, Money


class CampaignStatus(Enum):
    """Status of a payment campaign"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class PaymentCampaignStartedEvent(DomainEvent):
    """Domain event raised when a payment campaign is started"""
    def __init__(self, campaign_id: str, invoice_id: str, customer_id: str):
        super().__init__()
        self.campaign_id = campaign_id
        self.invoice_id = invoice_id
        self.customer_id = customer_id


class PaymentCampaignCompletedEvent(DomainEvent):
    """Domain event raised when a payment campaign is completed"""
    def __init__(self, campaign_id: str, completion_reason: str, total_reminders_sent: int):
        super().__init__()
        self.campaign_id = campaign_id
        self.completion_reason = completion_reason
        self.total_reminders_sent = total_reminders_sent


class PaymentCampaignEscalatedEvent(DomainEvent):
    """Domain event raised when a payment campaign is escalated"""
    def __init__(self, campaign_id: str, escalation_reason: str, final_amount: Money):
        super().__init__()
        self.campaign_id = campaign_id
        self.escalation_reason = escalation_reason
        self.final_amount = final_amount


class PaymentCampaign(Entity):
    """
    Aggregate Root for Payment Collection Campaigns.
    
    Orchestrates the entire payment collection process including:
    - Automated reminder scheduling and sending
    - Escalation logic based on business rules
    - Alternative payment option management
    - Campaign performance tracking
    """
    
    def __init__(
        self,
        campaign_id: str,
        invoice: OverdueInvoice,
        customer_id: str,
        start_date: Optional[datetime] = None
    ):
        super().__init__(campaign_id)
        
        if not customer_id:
            raise ValueError("Customer ID is required")
        if invoice.payment_status == PaymentStatus.PAID:
            raise ValueError("Cannot create campaign for paid invoice")
        
        self._invoice = invoice
        self._customer_id = customer_id
        self._start_date = start_date or datetime.utcnow()
        
        # Campaign status
        self._status = CampaignStatus.ACTIVE
        self._completion_date: Optional[datetime] = None
        self._completion_reason: Optional[str] = None
        
        # Reminder management
        self._reminders: List[PaymentReminder] = []
        self._current_reminder_level = ReminderLevel.FIRST
        self._last_reminder_date: Optional[datetime] = None
        self._next_reminder_date: Optional[datetime] = None
        
        # Alternative payment options
        self._alternative_options: List[AlternativePaymentOption] = []
        self._escalation_triggered = False
        self._escalation_date: Optional[datetime] = None
        
        # Campaign configuration
        self._max_reminder_attempts = 3
        self._days_between_reminders = 7
        self._auto_escalation_days = 21
        
        # Performance metrics
        self._total_contact_attempts = 0
        self._successful_deliveries = 0
        self._customer_responses = 0
        
        # Business rules
        self._pause_on_customer_contact = True
        self._auto_pause_on_dispute = True
        
        # Calculate initial next reminder date
        self._calculate_next_reminder_date()
        
        # Raise domain event
        event = PaymentCampaignStartedEvent(
            campaign_id=self.id,
            invoice_id=self._invoice.id,
            customer_id=self._customer_id
        )
        self.add_domain_event(event)
    
    @property
    def invoice(self) -> OverdueInvoice:
        return self._invoice
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def status(self) -> CampaignStatus:
        return self._status
    
    @property
    def current_reminder_level(self) -> ReminderLevel:
        return self._current_reminder_level
    
    @property
    def reminders(self) -> List[PaymentReminder]:
        return self._reminders.copy()
    
    @property
    def alternative_options(self) -> List[AlternativePaymentOption]:
        return self._alternative_options.copy()
    
    @property
    def next_reminder_date(self) -> Optional[datetime]:
        return self._next_reminder_date
    
    @property
    def is_escalated(self) -> bool:
        return self._escalation_triggered
    
    @property
    def days_since_start(self) -> int:
        return (datetime.utcnow() - self._start_date).days
    
    def schedule_reminder(
        self,
        reminder: PaymentReminder,
        scheduled_date: Optional[datetime] = None
    ) -> None:
        """Schedule a new payment reminder"""
        if self._status != CampaignStatus.ACTIVE:
            raise ValueError(f"Cannot schedule reminder. Campaign status: {self._status}")
        
        if reminder.invoice_id != self._invoice.id:
            raise ValueError("Reminder invoice ID must match campaign invoice ID")
        
        if reminder.customer_id != self._customer_id:
            raise ValueError("Reminder customer ID must match campaign customer ID")
        
        # Validate reminder level progression
        if len(self._reminders) > 0:
            last_level = self._reminders[-1].reminder_level
            if not self._is_valid_reminder_progression(last_level, reminder.reminder_level):
                raise ValueError(f"Invalid reminder level progression from {last_level} to {reminder.reminder_level}")
        
        self._reminders.append(reminder)
        self._current_reminder_level = reminder.reminder_level
        
        if scheduled_date:
            self._next_reminder_date = scheduled_date
        
        self.mark_as_modified()
    
    def send_reminder(self, reminder_id: str, sent_date: Optional[datetime] = None) -> None:
        """Mark a reminder as sent and update campaign state"""
        reminder = self._find_reminder(reminder_id)
        if not reminder:
            raise ValueError(f"Reminder {reminder_id} not found in campaign")
        
        sent_date = sent_date or datetime.utcnow()
        reminder.mark_as_sent(sent_date)
        
        self._last_reminder_date = sent_date
        self._total_contact_attempts += 1
        
        # Update invoice reminder tracking
        self._invoice.record_reminder_sent(reminder.reminder_level, sent_date)
        
        # Calculate next reminder date
        self._calculate_next_reminder_date()
        
        self.mark_as_modified()
    
    def mark_reminder_delivered(self, reminder_id: str, delivery_date: Optional[datetime] = None) -> None:
        """Mark a reminder as delivered"""
        reminder = self._find_reminder(reminder_id)
        if reminder:
            reminder.mark_as_delivered(delivery_date)
            self._successful_deliveries += 1
            self.mark_as_modified()
    
    def mark_reminder_failed(self, reminder_id: str, failure_reason: str) -> None:
        """Mark a reminder as failed and handle retry logic"""
        reminder = self._find_reminder(reminder_id)
        if not reminder:
            return
        
        reminder.mark_as_failed(failure_reason)
        
        # If all retry attempts exhausted, move to next level or escalate
        if not reminder.can_retry():
            self._handle_reminder_failure()
        
        self.mark_as_modified()
    
    def record_customer_response(self, reminder_id: str) -> None:
        """Record that customer responded to a reminder"""
        reminder = self._find_reminder(reminder_id)
        if reminder:
            reminder.mark_as_replied()
            self._customer_responses += 1
            
            # Pause campaign for manual review
            if self._pause_on_customer_contact:
                self.pause_campaign("Customer responded to reminder")
            
            self.mark_as_modified()
    
    def add_alternative_payment_option(self, option: AlternativePaymentOption) -> None:
        """Add an alternative payment option to the campaign"""
        if option.invoice_id != self._invoice.id:
            raise ValueError("Option invoice ID must match campaign invoice ID")
        
        if option.customer_id != self._customer_id:
            raise ValueError("Option customer ID must match campaign customer ID")
        
        self._alternative_options.append(option)
        self.mark_as_modified()
    
    def accept_payment_option(self, option_id: str) -> None:
        """Accept a payment option and modify campaign accordingly"""
        option = self._find_alternative_option(option_id)
        if not option:
            raise ValueError(f"Payment option {option_id} not found")
        
        option.accept_option()
        
        # Pause campaign while alternative payment is being implemented
        self.pause_campaign(f"Alternative payment option {option_id} accepted")
        
        self.mark_as_modified()
    
    def record_payment(self, amount: Money, payment_method: str) -> None:
        """Record a payment received for the campaign invoice"""
        self._invoice.record_payment(amount, payment_method)
        
        # Check if invoice is fully paid
        if self._invoice.payment_status == PaymentStatus.PAID:
            self.complete_campaign("Payment received - invoice fully paid")
        elif self._invoice.payment_status == PaymentStatus.PARTIALLY_PAID:
            # Restart campaign for remaining balance
            self.resume_campaign("Partial payment received - continuing for remaining balance")
        
        self.mark_as_modified()
    
    def escalate_campaign(self, escalation_reason: str) -> None:
        """Escalate the campaign to collections or legal action"""
        if self._status == CampaignStatus.ESCALATED:
            raise ValueError("Campaign is already escalated")
        
        self._escalation_triggered = True
        self._escalation_date = datetime.utcnow()
        self._status = CampaignStatus.ESCALATED
        
        # Update invoice status
        self._invoice.escalate_to_collections(escalation_reason, self._escalation_date)
        
        # Raise domain event
        event = PaymentCampaignEscalatedEvent(
            campaign_id=self.id,
            escalation_reason=escalation_reason,
            final_amount=self._invoice.current_balance
        )
        self.add_domain_event(event)
        
        self.mark_as_modified()
    
    def pause_campaign(self, reason: str) -> None:
        """Pause the campaign"""
        if self._status == CampaignStatus.ACTIVE:
            self._status = CampaignStatus.PAUSED
            self._invoice.add_collection_note(f"Campaign paused: {reason}")
            self.mark_as_modified()
    
    def resume_campaign(self, reason: str = "") -> None:
        """Resume a paused campaign"""
        if self._status == CampaignStatus.PAUSED:
            self._status = CampaignStatus.ACTIVE
            self._calculate_next_reminder_date()
            if reason:
                self._invoice.add_collection_note(f"Campaign resumed: {reason}")
            self.mark_as_modified()
    
    def complete_campaign(self, completion_reason: str) -> None:
        """Complete the campaign"""
        if self._status in [CampaignStatus.COMPLETED, CampaignStatus.CANCELLED]:
            return
        
        self._status = CampaignStatus.COMPLETED
        self._completion_date = datetime.utcnow()
        self._completion_reason = completion_reason
        
        # Raise domain event
        event = PaymentCampaignCompletedEvent(
            campaign_id=self.id,
            completion_reason=completion_reason,
            total_reminders_sent=self._total_contact_attempts
        )
        self.add_domain_event(event)
        
        self.mark_as_modified()
    
    def cancel_campaign(self, cancellation_reason: str) -> None:
        """Cancel the campaign"""
        self._status = CampaignStatus.CANCELLED
        self._completion_date = datetime.utcnow()
        self._completion_reason = f"Cancelled: {cancellation_reason}"
        
        self._invoice.add_collection_note(f"Campaign cancelled: {cancellation_reason}")
        
        self.mark_as_modified()
    
    def is_ready_for_next_reminder(self) -> bool:
        """Check if the campaign is ready for the next reminder"""
        if self._status != CampaignStatus.ACTIVE:
            return False
        
        if not self._next_reminder_date:
            return False
        
        return datetime.utcnow() >= self._next_reminder_date
    
    def should_auto_escalate(self) -> bool:
        """Check if the campaign should be automatically escalated"""
        return (
            self._status == CampaignStatus.ACTIVE and
            not self._escalation_triggered and
            self.days_since_start >= self._auto_escalation_days and
            self._current_reminder_level == ReminderLevel.THIRD
        )
    
    def get_campaign_metrics(self) -> Dict[str, Any]:
        """Get campaign performance metrics"""
        delivery_rate = (
            self._successful_deliveries / self._total_contact_attempts
            if self._total_contact_attempts > 0 else 0
        )
        
        response_rate = (
            self._customer_responses / self._successful_deliveries
            if self._successful_deliveries > 0 else 0
        )
        
        return {
            "campaign_id": self.id,
            "status": self._status.value,
            "days_active": self.days_since_start,
            "total_attempts": self._total_contact_attempts,
            "successful_deliveries": self._successful_deliveries,
            "customer_responses": self._customer_responses,
            "delivery_rate": delivery_rate,
            "response_rate": response_rate,
            "current_level": self._current_reminder_level.value,
            "alternative_options": len(self._alternative_options),
            "is_escalated": self._escalation_triggered,
            "invoice_balance": self._invoice.current_balance.amount
        }
    
    def _find_reminder(self, reminder_id: str) -> Optional[PaymentReminder]:
        """Find a reminder by ID"""
        return next((r for r in self._reminders if r.id == reminder_id), None)
    
    def _find_alternative_option(self, option_id: str) -> Optional[AlternativePaymentOption]:
        """Find an alternative payment option by ID"""
        return next((o for o in self._alternative_options if o.id == option_id), None)
    
    def _is_valid_reminder_progression(self, current: ReminderLevel, next_level: ReminderLevel) -> bool:
        """Validate reminder level progression"""
        valid_progressions = {
            ReminderLevel.FIRST: [ReminderLevel.SECOND],
            ReminderLevel.SECOND: [ReminderLevel.THIRD],
            ReminderLevel.THIRD: [ReminderLevel.ESCALATED],
            ReminderLevel.ESCALATED: []
        }
        return next_level in valid_progressions.get(current, [])
    
    def _calculate_next_reminder_date(self) -> None:
        """Calculate the next reminder date based on business rules"""
        if self._current_reminder_level == ReminderLevel.ESCALATED:
            self._next_reminder_date = None
            return
        
        if self._last_reminder_date:
            self._next_reminder_date = self._last_reminder_date + timedelta(days=self._days_between_reminders)
        else:
            # First reminder - schedule immediately if overdue, or on due date
            if self._invoice.payment_status == PaymentStatus.OVERDUE:
                self._next_reminder_date = datetime.utcnow()
            else:
                self._next_reminder_date = self._invoice.due_date
    
    def _handle_reminder_failure(self) -> None:
        """Handle permanent reminder failure"""
        next_level = self._current_reminder_level.next_level()
        
        if next_level is None or next_level == ReminderLevel.ESCALATED:
            # No more reminder levels - escalate
            self.escalate_campaign("All reminder attempts failed")
        else:
            # Move to next reminder level
            self._current_reminder_level = next_level
            self._calculate_next_reminder_date()
    
    def __str__(self) -> str:
        return f"PaymentCampaign(id={self.id}, status={self._status.value}, level={self._current_reminder_level.value})"