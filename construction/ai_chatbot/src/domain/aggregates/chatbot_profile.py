"""
Chatbot Profile Aggregate Root for Payment Intelligence Domain

Defines AI assistant capabilities, personality, and domain-specific knowledge
for financial communications and payment collection scenarios.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from ..entities.base_entity import Entity, DomainEvent
from ..value_objects.payment_value_objects import ReminderLevel, EmailTemplate


class ChatbotPersonality(Enum):
    """Personality types for the chatbot"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    EMPATHETIC = "empathetic"
    AUTHORITATIVE = "authoritative"
    HELPFUL = "helpful"


class ChatbotCapability(Enum):
    """Capabilities that the chatbot can perform"""
    PAYMENT_INQUIRY_HANDLING = "payment_inquiry_handling"
    EMAIL_GENERATION = "email_generation"
    REMINDER_SCHEDULING = "reminder_scheduling"
    ALTERNATIVE_PAYMENT_OFFERING = "alternative_payment_offering"
    ESCALATION_MANAGEMENT = "escalation_management"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    INVOICE_LOOKUP = "invoice_lookup"
    CUSTOMER_COMMUNICATION = "customer_communication"


class ChatbotProfileUpdatedEvent(DomainEvent):
    """Domain event raised when chatbot profile is updated"""
    def __init__(self, profile_id: str, updated_capabilities: List[str], version: int):
        super().__init__()
        self.profile_id = profile_id
        self.updated_capabilities = updated_capabilities
        self.version = version


class ChatbotProfile(Entity):
    """
    Aggregate Root for AI Chatbot Configuration and Capabilities.
    
    Manages the AI assistant's behavior, knowledge base, and capabilities
    for handling payment collection conversations and tasks.
    """
    
    def __init__(
        self,
        profile_id: str,
        name: str,
        personality: ChatbotPersonality,
        domain_focus: str = "payment_collection"
    ):
        super().__init__(profile_id)
        
        if not name:
            raise ValueError("Chatbot name is required")
        
        self._name = name
        self._personality = personality
        self._domain_focus = domain_focus
        self._version = 1
        
        # Capabilities and configuration
        self._enabled_capabilities: List[ChatbotCapability] = []
        self._conversation_starters: List[str] = []
        self._response_templates: Dict[str, str] = {}
        self._escalation_phrases: List[str] = []
        
        # Email generation
        self._email_templates: Dict[ReminderLevel, EmailTemplate] = {}
        self._email_tone_preferences: Dict[str, str] = {}
        
        # AI model configuration
        self._ai_model_settings: Dict[str, Any] = {
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0
        }
        
        # Business rules and constraints
        self._max_conversation_turns = 20
        self._escalation_triggers: List[str] = []
        self._prohibited_actions: List[str] = []
        self._required_disclaimers: List[str] = []
        
        # Performance and analytics
        self._total_conversations = 0
        self._successful_resolutions = 0
        self._escalation_rate = 0.0
        self._average_satisfaction_score = 0.0
        self._last_performance_update: Optional[datetime] = None
        
        # Knowledge base
        self._knowledge_base: Dict[str, Any] = {}
        self._faq_responses: Dict[str, str] = {}
        
        # Initialize with default configuration
        self._initialize_default_configuration()
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def personality(self) -> ChatbotPersonality:
        return self._personality
    
    @property
    def version(self) -> int:
        return self._version
    
    @property
    def enabled_capabilities(self) -> List[ChatbotCapability]:
        return self._enabled_capabilities.copy()
    
    @property
    def email_templates(self) -> Dict[ReminderLevel, EmailTemplate]:
        return self._email_templates.copy()
    
    @property
    def ai_model_settings(self) -> Dict[str, Any]:
        return self._ai_model_settings.copy()
    
    @property
    def escalation_rate(self) -> float:
        return self._escalation_rate
    
    def enable_capability(self, capability: ChatbotCapability) -> None:
        """Enable a chatbot capability"""
        if capability not in self._enabled_capabilities:
            self._enabled_capabilities.append(capability)
            self._increment_version()
            self.mark_as_modified()
    
    def disable_capability(self, capability: ChatbotCapability) -> None:
        """Disable a chatbot capability"""
        if capability in self._enabled_capabilities:
            self._enabled_capabilities.remove(capability)
            self._increment_version()
            self.mark_as_modified()
    
    def has_capability(self, capability: ChatbotCapability) -> bool:
        """Check if chatbot has a specific capability"""
        return capability in self._enabled_capabilities
    
    def add_email_template(self, reminder_level: ReminderLevel, template: EmailTemplate) -> None:
        """Add an email template for a specific reminder level"""
        if template.reminder_level != reminder_level:
            raise ValueError("Template reminder level must match the provided level")
        
        self._email_templates[reminder_level] = template
        self._increment_version()
        self.mark_as_modified()
    
    def get_email_template(self, reminder_level: ReminderLevel) -> Optional[EmailTemplate]:
        """Get email template for a specific reminder level"""
        return self._email_templates.get(reminder_level)
    
    def update_ai_model_setting(self, setting_name: str, value: Any) -> None:
        """Update AI model configuration"""
        valid_settings = ["temperature", "max_tokens", "top_p", "presence_penalty", "frequency_penalty"]
        
        if setting_name not in valid_settings:
            raise ValueError(f"Invalid setting name. Must be one of: {valid_settings}")
        
        # Validate setting values
        if setting_name == "temperature" and not 0.0 <= value <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        elif setting_name == "max_tokens" and not 1 <= value <= 4000:
            raise ValueError("Max tokens must be between 1 and 4000")
        elif setting_name in ["top_p"] and not 0.0 <= value <= 1.0:
            raise ValueError(f"{setting_name} must be between 0.0 and 1.0")
        elif setting_name in ["presence_penalty", "frequency_penalty"] and not -2.0 <= value <= 2.0:
            raise ValueError(f"{setting_name} must be between -2.0 and 2.0")
        
        self._ai_model_settings[setting_name] = value
        self._increment_version()
        self.mark_as_modified()
    
    def add_conversation_starter(self, starter: str) -> None:
        """Add a conversation starter phrase"""
        if starter and starter not in self._conversation_starters:
            self._conversation_starters.append(starter)
            self.mark_as_modified()
    
    def add_response_template(self, intent: str, template: str) -> None:
        """Add a response template for a specific intent"""
        if not intent or not template:
            raise ValueError("Intent and template are required")
        
        self._response_templates[intent] = template
        self.mark_as_modified()
    
    def get_response_template(self, intent: str) -> Optional[str]:
        """Get response template for a specific intent"""
        return self._response_templates.get(intent)
    
    def add_escalation_trigger(self, trigger: str) -> None:
        """Add an escalation trigger phrase"""
        if trigger and trigger not in self._escalation_triggers:
            self._escalation_triggers.append(trigger)
            self.mark_as_modified()
    
    def should_escalate_for_phrase(self, phrase: str) -> bool:
        """Check if a phrase should trigger escalation"""
        phrase_lower = phrase.lower()
        return any(trigger.lower() in phrase_lower for trigger in self._escalation_triggers)
    
    def add_prohibited_action(self, action: str) -> None:
        """Add a prohibited action"""
        if action and action not in self._prohibited_actions:
            self._prohibited_actions.append(action)
            self.mark_as_modified()
    
    def is_action_prohibited(self, action: str) -> bool:
        """Check if an action is prohibited"""
        return action in self._prohibited_actions
    
    def add_knowledge_base_entry(self, topic: str, content: Any) -> None:
        """Add an entry to the knowledge base"""
        if not topic:
            raise ValueError("Topic is required")
        
        self._knowledge_base[topic] = content
        self.mark_as_modified()
    
    def get_knowledge_base_entry(self, topic: str) -> Optional[Any]:
        """Get knowledge base entry for a topic"""
        return self._knowledge_base.get(topic)
    
    def add_faq_response(self, question: str, answer: str) -> None:
        """Add a FAQ response"""
        if not question or not answer:
            raise ValueError("Question and answer are required")
        
        self._faq_responses[question.lower()] = answer
        self.mark_as_modified()
    
    def get_faq_response(self, question: str) -> Optional[str]:
        """Get FAQ response for a question"""
        return self._faq_responses.get(question.lower())
    
    def update_performance_metrics(
        self,
        total_conversations: int,
        successful_resolutions: int,
        escalation_count: int,
        average_satisfaction: float
    ) -> None:
        """Update performance metrics"""
        if total_conversations < 0 or successful_resolutions < 0 or escalation_count < 0:
            raise ValueError("Metrics cannot be negative")
        
        if not 0.0 <= average_satisfaction <= 1.0:
            raise ValueError("Average satisfaction must be between 0.0 and 1.0")
        
        self._total_conversations = total_conversations
        self._successful_resolutions = successful_resolutions
        self._escalation_rate = escalation_count / total_conversations if total_conversations > 0 else 0.0
        self._average_satisfaction_score = average_satisfaction
        self._last_performance_update = datetime.utcnow()
        
        self.mark_as_modified()
    
    def get_success_rate(self) -> float:
        """Calculate success rate based on resolutions"""
        if self._total_conversations == 0:
            return 0.0
        return self._successful_resolutions / self._total_conversations
    
    def needs_performance_review(self) -> bool:
        """Check if chatbot needs performance review"""
        return (
            self._escalation_rate > 0.3 or  # High escalation rate
            self._average_satisfaction_score < 0.6 or  # Low satisfaction
            self.get_success_rate() < 0.7  # Low success rate
        )
    
    def generate_conversation_starter(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a conversation starter based on context"""
        if not self._conversation_starters:
            return "Hello! I'm here to help you with your payment inquiries. How can I assist you today?"
        
        # For MVP, return first starter
        # In production, this could be context-aware
        return self._conversation_starters[0]
    
    def get_recommended_email_tone(self, reminder_level: ReminderLevel, customer_history: Optional[Dict] = None) -> str:
        """Get recommended email tone based on reminder level and customer history"""
        tone_mapping = {
            ReminderLevel.FIRST: "friendly",
            ReminderLevel.SECOND: "professional", 
            ReminderLevel.THIRD: "urgent",
            ReminderLevel.ESCALATED: "formal"
        }
        
        base_tone = tone_mapping.get(reminder_level, "professional")
        
        # Adjust based on customer history if available
        if customer_history:
            if customer_history.get("has_disputes", False):
                return "empathetic"
            elif customer_history.get("payment_history") == "excellent":
                return "friendly"
        
        return base_tone
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the chatbot profile"""
        return {
            "profile_id": self.id,
            "name": self._name,
            "personality": self._personality.value,
            "version": self._version,
            "domain_focus": self._domain_focus,
            "capabilities_count": len(self._enabled_capabilities),
            "email_templates_count": len(self._email_templates),
            "knowledge_base_entries": len(self._knowledge_base),
            "faq_responses": len(self._faq_responses),
            "total_conversations": self._total_conversations,
            "success_rate": self.get_success_rate(),
            "escalation_rate": self._escalation_rate,
            "satisfaction_score": self._average_satisfaction_score,
            "needs_review": self.needs_performance_review(),
            "last_updated": self.updated_at
        }
    
    def _initialize_default_configuration(self) -> None:
        """Initialize with default configuration for payment collection"""
        # Enable core capabilities
        default_capabilities = [
            ChatbotCapability.PAYMENT_INQUIRY_HANDLING,
            ChatbotCapability.EMAIL_GENERATION,
            ChatbotCapability.REMINDER_SCHEDULING,
            ChatbotCapability.SENTIMENT_ANALYSIS,
            ChatbotCapability.INVOICE_LOOKUP
        ]
        
        for capability in default_capabilities:
            self.enable_capability(capability)
        
        # Add default conversation starters
        default_starters = [
            "Hello! I'm your payment assistant. I can help you with invoice inquiries, payment reminders, and payment options. How can I assist you today?",
            "Hi there! I'm here to help you manage your payments and resolve any invoice questions. What can I help you with?",
            "Welcome! I can assist you with overdue payments, payment plans, and invoice inquiries. How may I help you?"
        ]
        
        for starter in default_starters:
            self.add_conversation_starter(starter)
        
        # Add default response templates
        default_templates = {
            "payment_inquiry": "I can help you check your payment status. Let me look up your invoice information.",
            "reminder_request": "I'll help you set up payment reminders. When would you like to be reminded?",
            "escalation_trigger": "I understand your concern. Let me connect you with a specialist who can help you better.",
            "payment_plan_inquiry": "I can help you explore payment plan options. Let me review what's available for your situation."
        }
        
        for intent, template in default_templates.items():
            self.add_response_template(intent, template)
        
        # Add default escalation triggers
        escalation_triggers = [
            "speak to manager", "this is ridiculous", "file complaint",
            "legal action", "dispute this", "cancel account", "terrible service"
        ]
        
        for trigger in escalation_triggers:
            self.add_escalation_trigger(trigger)
        
        # Add prohibited actions
        prohibited_actions = [
            "delete_invoice", "modify_amount", "cancel_debt",
            "provide_legal_advice", "make_promises", "access_other_accounts"
        ]
        
        for action in prohibited_actions:
            self.add_prohibited_action(action)
        
        # Add basic knowledge base entries
        self.add_knowledge_base_entry("payment_methods", [
            "Credit Card", "Bank Transfer", "Check", "Online Payment", "Payment Plan"
        ])
        
        self.add_knowledge_base_entry("reminder_schedule", {
            "first_reminder": "7 days after due date",
            "second_reminder": "14 days after due date", 
            "third_reminder": "21 days after due date",
            "escalation": "30 days after due date"
        })
        
        # Add default FAQs
        default_faqs = {
            "how do i pay my invoice": "You can pay your invoice online through our payment portal, by bank transfer, or by calling our payment line.",
            "why am i getting reminders": "You're receiving reminders because we show an outstanding balance on your account. Please check your payment status.",
            "can i set up a payment plan": "Yes, we offer flexible payment plans. I can help you explore options that work for your situation.",
            "how do i dispute an invoice": "If you believe there's an error, I can help you start the dispute process or connect you with our billing team."
        }
        
        for question, answer in default_faqs.items():
            self.add_faq_response(question, answer)
    
    def _increment_version(self) -> None:
        """Increment profile version and raise update event"""
        self._version += 1
        
        # Raise domain event
        event = ChatbotProfileUpdatedEvent(
            profile_id=self.id,
            updated_capabilities=[cap.value for cap in self._enabled_capabilities],
            version=self._version
        )
        self.add_domain_event(event)
    
    def __str__(self) -> str:
        return f"ChatbotProfile(id={self.id}, name={self._name}, version={self._version}, personality={self._personality.value})"