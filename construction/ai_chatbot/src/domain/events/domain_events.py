"""
Domain Events for Payment Intelligence Bounded Context

This module provides access to all domain events used throughout the system.
Domain events represent business-significant occurrences in the domain.
"""

# Base event classes
from ..entities.base_entity import DomainEvent

# Payment Campaign Events
from ..aggregates.payment_campaign import (
    PaymentCampaignStartedEvent,
    PaymentCampaignCompletedEvent,
    PaymentCampaignEscalatedEvent
)

# Payment Reminder Events  
from ..entities.payment_reminder import (
    PaymentReminderSentEvent,
    PaymentReminderFailedEvent
)

# Invoice Events
from ..entities.overdue_invoice import (
    PaymentReceivedEvent,
    EscalationTriggeredEvent
)

# Conversation Events
from ..aggregates.conversation import (
    ConversationStartedEvent,
    ConversationEscalatedEvent,
    ConversationCompletedEvent
)

# Message Events
from ..entities.message import (
    MessageProcessedEvent
)

# Chatbot Profile Events
from ..aggregates.chatbot_profile import (
    ChatbotProfileUpdatedEvent
)

# Export all events
__all__ = [
    # Base
    "DomainEvent",
    
    # Payment Campaign
    "PaymentCampaignStartedEvent",
    "PaymentCampaignCompletedEvent", 
    "PaymentCampaignEscalatedEvent",
    
    # Payment Reminder
    "PaymentReminderSentEvent",
    "PaymentReminderFailedEvent",
    
    # Invoice
    "PaymentReceivedEvent",
    "EscalationTriggeredEvent",
    
    # Conversation
    "ConversationStartedEvent",
    "ConversationEscalatedEvent",
    "ConversationCompletedEvent",
    
    # Message
    "MessageProcessedEvent",
    
    # Chatbot Profile
    "ChatbotProfileUpdatedEvent"
]


def get_all_event_types() -> list:
    """Get list of all available domain event types"""
    return [
        PaymentCampaignStartedEvent,
        PaymentCampaignCompletedEvent,
        PaymentCampaignEscalatedEvent,
        PaymentReminderSentEvent,
        PaymentReminderFailedEvent,
        PaymentReceivedEvent,
        EscalationTriggeredEvent,
        ConversationStartedEvent,
        ConversationEscalatedEvent,
        ConversationCompletedEvent,
        MessageProcessedEvent,
        ChatbotProfileUpdatedEvent
    ]


def is_payment_related_event(event: DomainEvent) -> bool:
    """Check if event is related to payment processing"""
    payment_events = [
        PaymentReceivedEvent,
        PaymentReminderSentEvent,
        PaymentReminderFailedEvent,
        PaymentCampaignStartedEvent,
        PaymentCampaignCompletedEvent,
        PaymentCampaignEscalatedEvent,
        EscalationTriggeredEvent
    ]
    return type(event) in payment_events


def is_conversation_related_event(event: DomainEvent) -> bool:
    """Check if event is related to conversation processing"""
    conversation_events = [
        ConversationStartedEvent,
        ConversationEscalatedEvent,
        ConversationCompletedEvent,
        MessageProcessedEvent
    ]
    return type(event) in conversation_events


def is_system_related_event(event: DomainEvent) -> bool:
    """Check if event is related to system configuration"""
    system_events = [
        ChatbotProfileUpdatedEvent
    ]
    return type(event) in system_events