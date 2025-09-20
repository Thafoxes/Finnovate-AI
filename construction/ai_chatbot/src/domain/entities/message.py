"""
Message Entity for Payment Intelligence Domain

Represents individual chat messages in conversations with context and intent.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from .base_entity import Entity, DomainEvent
from ..value_objects.payment_value_objects import MessageIntent


class MessageType(Enum):
    """Types of messages in conversations"""
    USER_MESSAGE = "user_message"
    AI_RESPONSE = "ai_response"
    SYSTEM_MESSAGE = "system_message"
    NOTIFICATION = "notification"


class MessageProcessedEvent(DomainEvent):
    """Domain event raised when a message is processed by AI"""
    def __init__(self, message_id: str, conversation_id: str, intent: MessageIntent, confidence: float):
        super().__init__()
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.intent = intent
        self.confidence = confidence


class Message(Entity):
    """
    Entity representing a single message in a conversation.
    
    Contains the message content, metadata about intent recognition,
    and processing information for AI responses.
    """
    
    def __init__(
        self,
        message_id: str,
        conversation_id: str,
        sender_id: str,
        content: str,
        message_type: MessageType,
        timestamp: Optional[datetime] = None
    ):
        super().__init__(message_id)
        
        if not conversation_id:
            raise ValueError("Conversation ID is required")
        if not sender_id:
            raise ValueError("Sender ID is required")
        if not content.strip():
            raise ValueError("Message content cannot be empty")
        
        self._conversation_id = conversation_id
        self._sender_id = sender_id
        self._content = content.strip()
        self._message_type = message_type
        self._timestamp = timestamp or datetime.utcnow()
        
        # Intent recognition
        self._recognized_intent: Optional[MessageIntent] = None
        self._intent_confidence: Optional[float] = None
        self._extracted_entities: Dict[str, Any] = {}
        
        # AI processing metadata
        self._ai_processed = False
        self._ai_processing_duration: Optional[float] = None
        self._ai_model_used: Optional[str] = None
        self._sentiment_score: Optional[float] = None
        
        # Response handling
        self._requires_response = message_type == MessageType.USER_MESSAGE
        self._response_generated = False
        self._response_message_id: Optional[str] = None
        
        # Context and actions
        self._related_invoice_ids: List[str] = []
        self._suggested_actions: List[str] = []
        self._escalation_flags: List[str] = []
    
    @property
    def conversation_id(self) -> str:
        return self._conversation_id
    
    @property
    def sender_id(self) -> str:
        return self._sender_id
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def message_type(self) -> MessageType:
        return self._message_type
    
    @property
    def timestamp(self) -> datetime:
        return self._timestamp
    
    @property
    def recognized_intent(self) -> Optional[MessageIntent]:
        return self._recognized_intent
    
    @property
    def intent_confidence(self) -> Optional[float]:
        return self._intent_confidence
    
    @property
    def sentiment_score(self) -> Optional[float]:
        return self._sentiment_score
    
    @property
    def requires_response(self) -> bool:
        return self._requires_response
    
    @property
    def response_generated(self) -> bool:
        return self._response_generated
    
    @property
    def related_invoice_ids(self) -> List[str]:
        return self._related_invoice_ids.copy()
    
    def process_with_ai(
        self,
        intent: MessageIntent,
        confidence: float,
        model_name: str,
        processing_duration: float,
        sentiment_score: Optional[float] = None,
        extracted_entities: Optional[Dict[str, Any]] = None
    ) -> None:
        """Process the message with AI intent recognition and sentiment analysis"""
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        if sentiment_score is not None and not -1.0 <= sentiment_score <= 1.0:
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        
        self._recognized_intent = intent
        self._intent_confidence = confidence
        self._ai_processed = True
        self._ai_processing_duration = processing_duration
        self._ai_model_used = model_name
        self._sentiment_score = sentiment_score
        
        if extracted_entities:
            self._extracted_entities = extracted_entities.copy()
        
        self.mark_as_modified()
        
        # Raise domain event
        event = MessageProcessedEvent(
            message_id=self.id,
            conversation_id=self._conversation_id,
            intent=intent,
            confidence=confidence
        )
        self.add_domain_event(event)
    
    def add_related_invoice(self, invoice_id: str) -> None:
        """Add a related invoice ID to this message"""
        if invoice_id not in self._related_invoice_ids:
            self._related_invoice_ids.append(invoice_id)
            self.mark_as_modified()
    
    def add_suggested_action(self, action: str) -> None:
        """Add a suggested action based on message content"""
        if action not in self._suggested_actions:
            self._suggested_actions.append(action)
            self.mark_as_modified()
    
    def add_escalation_flag(self, flag: str) -> None:
        """Add an escalation flag (e.g., 'complaint', 'threat', 'dispute')"""
        if flag not in self._escalation_flags:
            self._escalation_flags.append(flag)
            self.mark_as_modified()
    
    def mark_response_generated(self, response_message_id: str) -> None:
        """Mark that a response has been generated for this message"""
        self._response_generated = True
        self._response_message_id = response_message_id
        self.mark_as_modified()
    
    def set_extracted_entity(self, entity_type: str, entity_value: Any) -> None:
        """Set an extracted entity (e.g., 'amount', 'date', 'invoice_number')"""
        self._extracted_entities[entity_type] = entity_value
        self.mark_as_modified()
    
    def get_extracted_entity(self, entity_type: str) -> Optional[Any]:
        """Get an extracted entity value"""
        return self._extracted_entities.get(entity_type)
    
    def has_negative_sentiment(self) -> bool:
        """Check if the message has negative sentiment"""
        return self._sentiment_score is not None and self._sentiment_score < -0.3
    
    def requires_immediate_attention(self) -> bool:
        """Check if the message requires immediate attention"""
        return (
            len(self._escalation_flags) > 0 or
            self.has_negative_sentiment() or
            (self._recognized_intent and self._recognized_intent.requires_immediate_action())
        )
    
    def is_payment_related(self) -> bool:
        """Check if the message is related to payments"""
        payment_intents = [
            MessageIntent.PAYMENT_INQUIRY,
            MessageIntent.PAYMENT_PLAN_INQUIRY,
            MessageIntent.PAYMENT_CONFIRMATION,
            MessageIntent.ALTERNATIVE_PAYMENT_REQUEST
        ]
        return self._recognized_intent in payment_intents
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of AI processing results"""
        return {
            "message_id": self.id,
            "ai_processed": self._ai_processed,
            "intent": self._recognized_intent.value if self._recognized_intent else None,
            "confidence": self._intent_confidence,
            "sentiment": self._sentiment_score,
            "model_used": self._ai_model_used,
            "processing_duration": self._ai_processing_duration,
            "entities_count": len(self._extracted_entities),
            "escalation_flags": self._escalation_flags,
            "requires_attention": self.requires_immediate_attention()
        }
    
    def __str__(self) -> str:
        return f"Message(id={self.id}, type={self._message_type.value}, intent={self._recognized_intent})"


class AlternativePaymentOption(Entity):
    """
    Entity representing alternative payment options offered to customers.
    
    Includes payment plans, installments, and alternative payment methods
    that can be offered after standard reminders fail.
    """
    
    def __init__(
        self,
        option_id: str,
        invoice_id: str,
        customer_id: str,
        option_type: str,
        description: str,
        terms: Dict[str, Any]
    ):
        super().__init__(option_id)
        
        if not invoice_id:
            raise ValueError("Invoice ID is required")
        if not customer_id:
            raise ValueError("Customer ID is required")
        if not option_type:
            raise ValueError("Option type is required")
        if not description:
            raise ValueError("Description is required")
        
        self._invoice_id = invoice_id
        self._customer_id = customer_id
        self._option_type = option_type  # "payment_plan", "discount", "alternative_method"
        self._description = description
        self._terms = terms.copy()
        
        # Status tracking
        self._offered_date = datetime.utcnow()
        self._accepted = False
        self._accepted_date: Optional[datetime] = None
        self._declined = False
        self._declined_date: Optional[datetime] = None
        self._expiry_date: Optional[datetime] = None
        
        # Implementation tracking
        self._implemented = False
        self._implementation_notes: List[str] = []
    
    @property
    def invoice_id(self) -> str:
        return self._invoice_id
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def option_type(self) -> str:
        return self._option_type
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def terms(self) -> Dict[str, Any]:
        return self._terms.copy()
    
    @property
    def offered_date(self) -> datetime:
        return self._offered_date
    
    @property
    def is_accepted(self) -> bool:
        return self._accepted
    
    @property
    def is_declined(self) -> bool:
        return self._declined
    
    @property
    def is_expired(self) -> bool:
        return (
            self._expiry_date is not None and 
            datetime.utcnow() > self._expiry_date
        )
    
    @property
    def is_pending(self) -> bool:
        return not self._accepted and not self._declined and not self.is_expired
    
    def accept_option(self, acceptance_date: Optional[datetime] = None) -> None:
        """Mark the payment option as accepted by customer"""
        if self._accepted:
            raise ValueError("Option is already accepted")
        if self._declined:
            raise ValueError("Cannot accept a declined option")
        if self.is_expired:
            raise ValueError("Cannot accept an expired option")
        
        self._accepted = True
        self._accepted_date = acceptance_date or datetime.utcnow()
        self.mark_as_modified()
    
    def decline_option(self, decline_date: Optional[datetime] = None) -> None:
        """Mark the payment option as declined by customer"""
        if self._declined:
            raise ValueError("Option is already declined")
        if self._accepted:
            raise ValueError("Cannot decline an accepted option")
        
        self._declined = True
        self._declined_date = decline_date or datetime.utcnow()
        self.mark_as_modified()
    
    def set_expiry_date(self, expiry_date: datetime) -> None:
        """Set expiration date for the payment option"""
        if expiry_date <= datetime.utcnow():
            raise ValueError("Expiry date must be in the future")
        
        self._expiry_date = expiry_date
        self.mark_as_modified()
    
    def implement_option(self, implementation_notes: str = "") -> None:
        """Mark the payment option as implemented"""
        if not self._accepted:
            raise ValueError("Option must be accepted before implementation")
        
        self._implemented = True
        if implementation_notes:
            self._implementation_notes.append(f"[{datetime.utcnow().isoformat()}] {implementation_notes}")
        
        self.mark_as_modified()
    
    def add_implementation_note(self, note: str) -> None:
        """Add an implementation note"""
        if note.strip():
            timestamped_note = f"[{datetime.utcnow().isoformat()}] {note.strip()}"
            self._implementation_notes.append(timestamped_note)
            self.mark_as_modified()
    
    def update_terms(self, new_terms: Dict[str, Any]) -> None:
        """Update the terms of the payment option"""
        if self._accepted:
            raise ValueError("Cannot update terms of accepted option")
        
        self._terms.update(new_terms)
        self.mark_as_modified()
    
    def get_term(self, key: str) -> Any:
        """Get a specific term value"""
        return self._terms.get(key)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of the option status"""
        return {
            "option_id": self.id,
            "type": self._option_type,
            "status": self._get_status_string(),
            "offered_date": self._offered_date,
            "accepted_date": self._accepted_date,
            "declined_date": self._declined_date,
            "expiry_date": self._expiry_date,
            "implemented": self._implemented,
            "days_since_offered": (datetime.utcnow() - self._offered_date).days
        }
    
    def _get_status_string(self) -> str:
        """Get status as string"""
        if self._accepted:
            return "accepted"
        elif self._declined:
            return "declined"
        elif self.is_expired:
            return "expired"
        else:
            return "pending"
    
    def __str__(self) -> str:
        return f"AlternativePaymentOption(id={self.id}, type={self._option_type}, status={self._get_status_string()})"