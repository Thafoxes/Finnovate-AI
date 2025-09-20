"""
Conversation Aggregate Root for Payment Intelligence Domain

Handles AI chatbot interactions with users, maintains conversation context,
and coordinates with payment campaigns for payment-related actions.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
from enum import Enum
import uuid

from ..entities.base_entity import Entity, DomainEvent
from ..entities.message import Message, MessageType
from ..value_objects.payment_value_objects import (
    MessageIntent, ConversationContext, ContactInformation
)


class ConversationStatus(Enum):
    """Status of a conversation"""
    ACTIVE = "active"
    WAITING_FOR_USER = "waiting_for_user"
    WAITING_FOR_AI = "waiting_for_ai"
    ESCALATED = "escalated"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ConversationStartedEvent(DomainEvent):
    """Domain event raised when a conversation is started"""
    def __init__(self, conversation_id: str, user_id: str, initial_intent: Optional[MessageIntent]):
        super().__init__()
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.initial_intent = initial_intent


class ConversationEscalatedEvent(DomainEvent):
    """Domain event raised when a conversation is escalated to human agent"""
    def __init__(self, conversation_id: str, escalation_reason: str, escalation_triggers: List[str]):
        super().__init__()
        self.conversation_id = conversation_id
        self.escalation_reason = escalation_reason
        self.escalation_triggers = escalation_triggers


class ConversationCompletedEvent(DomainEvent):
    """Domain event raised when a conversation is completed"""
    def __init__(self, conversation_id: str, completion_reason: str, message_count: int, duration_minutes: int):
        super().__init__()
        self.conversation_id = conversation_id
        self.completion_reason = completion_reason
        self.message_count = message_count
        self.duration_minutes = duration_minutes


class Conversation(Entity):
    """
    Aggregate Root for AI Chatbot Conversations.
    
    Manages the complete conversation lifecycle including:
    - Message exchange between user and AI
    - Context maintenance and intent tracking
    - Escalation logic and triggers
    - Integration with payment campaigns
    """
    
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        session_id: str,
        contact_info: ContactInformation,
        initial_context: Optional[ConversationContext] = None
    ):
        super().__init__(conversation_id)
        
        if not user_id:
            raise ValueError("User ID is required")
        if not session_id:
            raise ValueError("Session ID is required")
        
        self._user_id = user_id
        self._session_id = session_id
        self._contact_info = contact_info
        self._start_time = datetime.utcnow()
        
        # Conversation state
        self._status = ConversationStatus.ACTIVE
        self._current_context = initial_context or self._create_initial_context()
        self._last_activity_time = datetime.utcnow()
        self._completion_time: Optional[datetime] = None
        
        # Message management
        self._messages: List[Message] = []
        self._current_topic: Optional[str] = None
        self._active_invoice_ids: Set[str] = set()
        
        # AI state
        self._ai_confidence_scores: List[float] = []
        self._failed_ai_responses = 0
        self._max_failed_responses = 3
        
        # Escalation tracking
        self._escalation_triggers: List[str] = []
        self._escalation_score = 0.0
        self._escalation_threshold = 0.8
        self._escalated = False
        self._escalation_time: Optional[datetime] = None
        
        # Performance metrics
        self._user_satisfaction_score: Optional[float] = None
        self._resolution_achieved = False
        self._actions_completed: List[str] = []
        
        # Business rules
        self._max_conversation_duration = timedelta(hours=2)
        self._inactivity_timeout = timedelta(minutes=30)
        
        # Raise domain event
        initial_intent = self._current_context.current_intent if self._current_context else None
        event = ConversationStartedEvent(
            conversation_id=self.id,
            user_id=self._user_id,
            initial_intent=initial_intent
        )
        self.add_domain_event(event)
    
    @property
    def user_id(self) -> str:
        return self._user_id
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    @property
    def status(self) -> ConversationStatus:
        return self._status
    
    @property
    def current_context(self) -> ConversationContext:
        return self._current_context
    
    @property
    def messages(self) -> List[Message]:
        return self._messages.copy()
    
    @property
    def active_invoice_ids(self) -> Set[str]:
        return self._active_invoice_ids.copy()
    
    @property
    def is_escalated(self) -> bool:
        return self._escalated
    
    @property
    def duration_minutes(self) -> int:
        end_time = self._completion_time or datetime.utcnow()
        return int((end_time - self._start_time).total_seconds() / 60)
    
    @property
    def message_count(self) -> int:
        return len(self._messages)
    
    def add_user_message(self, content: str, timestamp: Optional[datetime] = None) -> Message:
        """Add a user message to the conversation"""
        if self._status not in [ConversationStatus.ACTIVE, ConversationStatus.WAITING_FOR_AI]:
            raise ValueError(f"Cannot add user message. Conversation status: {self._status}")
        
        message_id = str(uuid.uuid4())
        message = Message(
            message_id=message_id,
            conversation_id=self.id,
            sender_id=self._user_id,
            content=content,
            message_type=MessageType.USER_MESSAGE,
            timestamp=timestamp
        )
        
        self._messages.append(message)
        self._last_activity_time = datetime.utcnow()
        self._status = ConversationStatus.WAITING_FOR_AI
        
        self.mark_as_modified()
        return message
    
    def add_ai_response(
        self,
        content: str,
        intent: MessageIntent,
        confidence: float,
        model_name: str,
        processing_duration: float,
        timestamp: Optional[datetime] = None
    ) -> Message:
        """Add an AI response to the conversation"""
        if self._status != ConversationStatus.WAITING_FOR_AI:
            raise ValueError(f"Cannot add AI response. Conversation status: {self._status}")
        
        message_id = str(uuid.uuid4())
        message = Message(
            message_id=message_id,
            conversation_id=self.id,
            sender_id="ai_assistant",
            content=content,
            message_type=MessageType.AI_RESPONSE,
            timestamp=timestamp
        )
        
        # Process AI metadata
        message.process_with_ai(
            intent=intent,
            confidence=confidence,
            model_name=model_name,
            processing_duration=processing_duration
        )
        
        self._messages.append(message)
        self._ai_confidence_scores.append(confidence)
        self._last_activity_time = datetime.utcnow()
        self._status = ConversationStatus.WAITING_FOR_USER
        
        # Update conversation context
        self._update_context_from_message(message)
        
        # Check for escalation triggers
        if confidence < 0.5:
            self._failed_ai_responses += 1
            if self._failed_ai_responses >= self._max_failed_responses:
                self._add_escalation_trigger("Multiple low-confidence AI responses")
        
        self.mark_as_modified()
        return message
    
    def add_system_message(self, content: str, timestamp: Optional[datetime] = None) -> Message:
        """Add a system message (notifications, status updates)"""
        message_id = str(uuid.uuid4())
        message = Message(
            message_id=message_id,
            conversation_id=self.id,
            sender_id="system",
            content=content,
            message_type=MessageType.SYSTEM_MESSAGE,
            timestamp=timestamp
        )
        
        self._messages.append(message)
        self._last_activity_time = datetime.utcnow()
        
        self.mark_as_modified()
        return message
    
    def process_user_message(
        self,
        message_id: str,
        intent: MessageIntent,
        confidence: float,
        sentiment_score: Optional[float] = None,
        extracted_entities: Optional[Dict[str, Any]] = None
    ) -> None:
        """Process a user message with AI analysis"""
        message = self._find_message(message_id)
        if not message:
            raise ValueError(f"Message {message_id} not found")
        
        if message.message_type != MessageType.USER_MESSAGE:
            raise ValueError("Can only process user messages")
        
        # Process the message
        message.process_with_ai(
            intent=intent,
            confidence=confidence,
            model_name="intent_classifier",
            processing_duration=0.1,  # Placeholder
            sentiment_score=sentiment_score,
            extracted_entities=extracted_entities
        )
        
        # Update conversation context
        self._update_context_from_message(message)
        
        # Handle payment-related intents
        if message.is_payment_related():
            self._handle_payment_intent(message)
        
        # Check for escalation triggers
        if message.requires_immediate_attention():
            self._handle_escalation_triggers(message)
        
        self.mark_as_modified()
    
    def add_invoice_to_context(self, invoice_id: str) -> None:
        """Add an invoice to the conversation context"""
        self._active_invoice_ids.add(invoice_id)
        
        # Update context
        new_related_invoices = list(self._current_context.related_invoice_ids)
        if invoice_id not in new_related_invoices:
            new_related_invoices.append(invoice_id)
            
        self._current_context = ConversationContext(
            user_id=self._current_context.user_id,
            session_id=self._current_context.session_id,
            current_intent=self._current_context.current_intent,
            related_invoice_ids=new_related_invoices,
            customer_info=self._current_context.customer_info,
            conversation_stage=self._current_context.conversation_stage,
            last_action_timestamp=datetime.utcnow(),
            sentiment_score=self._current_context.sentiment_score,
            escalation_flags=self._current_context.escalation_flags
        )
        
        self.mark_as_modified()
    
    def escalate_conversation(self, reason: str, escalation_triggers: Optional[List[str]] = None) -> None:
        """Escalate the conversation to a human agent"""
        if self._escalated:
            return
        
        self._escalated = True
        self._escalation_time = datetime.utcnow()
        self._status = ConversationStatus.ESCALATED
        
        escalation_triggers = escalation_triggers or self._escalation_triggers
        
        # Add system message about escalation
        self.add_system_message(f"Conversation escalated to human agent. Reason: {reason}")
        
        # Raise domain event
        event = ConversationEscalatedEvent(
            conversation_id=self.id,
            escalation_reason=reason,
            escalation_triggers=escalation_triggers
        )
        self.add_domain_event(event)
        
        self.mark_as_modified()
    
    def complete_conversation(self, completion_reason: str, resolution_achieved: bool = False) -> None:
        """Complete the conversation"""
        if self._status == ConversationStatus.COMPLETED:
            return
        
        self._status = ConversationStatus.COMPLETED
        self._completion_time = datetime.utcnow()
        self._resolution_achieved = resolution_achieved
        
        # Add system message about completion
        self.add_system_message(f"Conversation completed. Reason: {completion_reason}")
        
        # Raise domain event
        event = ConversationCompletedEvent(
            conversation_id=self.id,
            completion_reason=completion_reason,
            message_count=len(self._messages),
            duration_minutes=self.duration_minutes
        )
        self.add_domain_event(event)
        
        self.mark_as_modified()
    
    def set_user_satisfaction(self, satisfaction_score: float) -> None:
        """Set user satisfaction score (0.0 to 1.0)"""
        if not 0.0 <= satisfaction_score <= 1.0:
            raise ValueError("Satisfaction score must be between 0.0 and 1.0")
        
        self._user_satisfaction_score = satisfaction_score
        self.mark_as_modified()
    
    def record_action_completed(self, action: str) -> None:
        """Record that an action was completed during the conversation"""
        if action not in self._actions_completed:
            self._actions_completed.append(action)
            self.mark_as_modified()
    
    def is_inactive(self) -> bool:
        """Check if the conversation has been inactive too long"""
        return (
            datetime.utcnow() - self._last_activity_time > self._inactivity_timeout
        )
    
    def is_too_long(self) -> bool:
        """Check if the conversation has exceeded maximum duration"""
        return (
            datetime.utcnow() - self._start_time > self._max_conversation_duration
        )
    
    def should_escalate(self) -> bool:
        """Check if the conversation should be escalated"""
        return (
            not self._escalated and
            (self._escalation_score >= self._escalation_threshold or
             len(self._escalation_triggers) >= 3 or
             self.is_too_long())
        )
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation"""
        avg_confidence = (
            sum(self._ai_confidence_scores) / len(self._ai_confidence_scores)
            if self._ai_confidence_scores else 0.0
        )
        
        return {
            "conversation_id": self.id,
            "user_id": self._user_id,
            "status": self._status.value,
            "duration_minutes": self.duration_minutes,
            "message_count": len(self._messages),
            "escalated": self._escalated,
            "escalation_triggers": self._escalation_triggers,
            "resolution_achieved": self._resolution_achieved,
            "user_satisfaction": self._user_satisfaction_score,
            "avg_ai_confidence": avg_confidence,
            "active_invoices": list(self._active_invoice_ids),
            "actions_completed": self._actions_completed,
            "current_intent": self._current_context.current_intent.value if self._current_context.current_intent else None
        }
    
    def _create_initial_context(self) -> ConversationContext:
        """Create initial conversation context"""
        return ConversationContext(
            user_id=self._user_id,
            session_id=self._session_id,
            current_intent=None,
            related_invoice_ids=[],
            customer_info={"email": self._contact_info.email},
            conversation_stage="greeting",
            last_action_timestamp=datetime.utcnow()
        )
    
    def _find_message(self, message_id: str) -> Optional[Message]:
        """Find a message by ID"""
        return next((m for m in self._messages if m.id == message_id), None)
    
    def _update_context_from_message(self, message: Message) -> None:
        """Update conversation context based on message"""
        if message.recognized_intent:
            self._current_context = self._current_context.with_intent(message.recognized_intent)
        
        # Add related invoices from message
        for invoice_id in message.related_invoice_ids:
            self.add_invoice_to_context(invoice_id)
        
        # Update escalation flags
        for flag in message._escalation_flags:
            if flag not in self._current_context.escalation_flags:
                self._add_escalation_trigger(f"Message flag: {flag}")
    
    def _handle_payment_intent(self, message: Message) -> None:
        """Handle payment-related intents"""
        intent = message.recognized_intent
        
        if intent == MessageIntent.PAYMENT_INQUIRY:
            self._current_topic = "payment_inquiry"
        elif intent == MessageIntent.PAYMENT_PLAN_INQUIRY:
            self._current_topic = "payment_plan"
            self.record_action_completed("payment_plan_requested")
        elif intent == MessageIntent.PAYMENT_CONFIRMATION:
            self.record_action_completed("payment_confirmed")
        elif intent == MessageIntent.ESCALATION_TRIGGER:
            self._add_escalation_trigger("User requested escalation")
    
    def _handle_escalation_triggers(self, message: Message) -> None:
        """Handle escalation triggers from message analysis"""
        if message.has_negative_sentiment():
            self._add_escalation_trigger("Negative sentiment detected")
        
        if message.requires_immediate_attention():
            self._add_escalation_trigger("Message requires immediate attention")
        
        for flag in message._escalation_flags:
            self._add_escalation_trigger(f"Message flag: {flag}")
    
    def _add_escalation_trigger(self, trigger: str) -> None:
        """Add an escalation trigger and update score"""
        if trigger not in self._escalation_triggers:
            self._escalation_triggers.append(trigger)
            self._escalation_score += 0.2  # Increase escalation score
            
            # Check if escalation threshold is reached
            if self.should_escalate():
                self.escalate_conversation("Escalation threshold reached", self._escalation_triggers)
    
    def __str__(self) -> str:
        return f"Conversation(id={self.id}, user={self._user_id}, status={self._status.value}, messages={len(self._messages)})"