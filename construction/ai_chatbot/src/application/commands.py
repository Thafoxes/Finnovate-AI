"""
Commands for Payment Intelligence Application

Commands represent requests to change the state of the system.
They follow the Command pattern and are handled by command handlers.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..domain.value_objects.payment_value_objects import Money, ReminderLevel


@dataclass(frozen=True)
class CreatePaymentCampaignCommand:
    """Command to create a new payment campaign for overdue invoices"""
    customer_id: str
    invoice_ids: List[str]
    campaign_type: str
    priority_level: str
    requested_by: str
    due_date_override: Optional[datetime] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class SendPaymentReminderCommand:
    """Command to send a payment reminder"""
    campaign_id: str
    reminder_level: ReminderLevel
    template_id: Optional[str] = None
    personalization_level: str = "moderate"
    scheduled_send_time: Optional[datetime] = None
    requested_by: str = "system"


@dataclass(frozen=True)
class ProcessIncomingPaymentCommand:
    """Command to process an incoming payment"""
    invoice_id: str
    payment_amount: Money
    payment_date: datetime
    payment_method: str
    confirmation_number: str
    processed_by: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class EscalateCampaignCommand:
    """Command to escalate a payment campaign"""
    campaign_id: str
    escalation_reason: str
    escalation_level: str
    assigned_to: Optional[str] = None
    escalation_notes: Optional[str] = None
    requested_by: str = "system"


@dataclass(frozen=True)
class CreatePaymentPlanCommand:
    """Command to create a payment plan for a customer"""
    customer_id: str
    invoice_ids: List[str]
    plan_type: str
    installments: int
    monthly_payment: Money
    start_date: datetime
    setup_autopay: bool = False
    payment_method: Optional[str] = None
    created_by: str = "system"


@dataclass(frozen=True)
class GenerateSettlementOfferCommand:
    """Command to generate a settlement offer"""
    invoice_id: str
    discount_percentage: float
    settlement_deadline: datetime
    offer_terms: Dict[str, Any]
    created_by: str
    requires_approval: bool = True


@dataclass(frozen=True)
class StartConversationCommand:
    """Command to start a new AI conversation"""
    customer_id: str
    conversation_context: Dict[str, Any]
    initial_message: str
    conversation_type: str = "payment_inquiry"
    channel: str = "web_chat"


@dataclass(frozen=True)
class ProcessConversationMessageCommand:
    """Command to process a message in an ongoing conversation"""
    conversation_id: str
    message_content: str
    message_type: str
    sender: str  # "customer" or "ai_assistant"
    attachments: Optional[List[Dict[str, Any]]] = None


@dataclass(frozen=True)
class UpdateCustomerContactCommand:
    """Command to update customer contact information"""
    customer_id: str
    contact_updates: Dict[str, Any]
    updated_by: str
    update_reason: str
    verify_contact: bool = True


@dataclass(frozen=True)
class RecordPaymentPromiseCommand:
    """Command to record a customer payment promise"""
    customer_id: str
    invoice_ids: List[str]
    promised_amount: Money
    promised_date: datetime
    promise_type: str  # "full_payment", "partial_payment", "payment_plan"
    recorded_by: str
    conversation_id: Optional[str] = None


@dataclass(frozen=True)
class ApproveSettlementCommand:
    """Command to approve a settlement offer"""
    settlement_id: str
    approved_by: str
    approval_notes: Optional[str] = None
    auto_process_payment: bool = True


@dataclass(frozen=True)
class RejectSettlementCommand:
    """Command to reject a settlement offer"""
    settlement_id: str
    rejected_by: str
    rejection_reason: str
    alternative_offer: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ConfigureChatbotProfileCommand:
    """Command to configure or update chatbot profile"""
    profile_id: str
    personality_settings: Dict[str, Any]
    capability_updates: Dict[str, Any]
    email_template_updates: Optional[Dict[str, Any]] = None
    knowledge_base_updates: Optional[Dict[str, Any]] = None
    updated_by: str


@dataclass(frozen=True)
class GenerateAIEmailCommand:
    """Command to generate AI-powered email content"""
    invoice_id: str
    email_type: str  # "reminder", "settlement", "payment_plan", "escalation"
    customer_profile: Dict[str, Any]
    tone: str = "professional"
    personalization_level: str = "moderate"
    template_overrides: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ScheduleFollowUpCommand:
    """Command to schedule a follow-up action"""
    entity_id: str  # campaign_id, conversation_id, etc.
    entity_type: str  # "campaign", "conversation", "settlement"
    follow_up_type: str
    scheduled_date: datetime
    follow_up_action: str
    assigned_to: Optional[str] = None
    scheduled_by: str = "system"


@dataclass(frozen=True)
class UpdateCampaignStatusCommand:
    """Command to update payment campaign status"""
    campaign_id: str
    new_status: str
    status_reason: str
    updated_by: str
    completion_notes: Optional[str] = None


@dataclass(frozen=True)
class RecordCustomerInteractionCommand:
    """Command to record customer interaction details"""
    customer_id: str
    interaction_type: str
    interaction_channel: str
    interaction_summary: str
    interaction_outcome: str
    recorded_by: str
    conversation_id: Optional[str] = None
    follow_up_required: bool = False


@dataclass(frozen=True)
class ProcessPaymentPlanPaymentCommand:
    """Command to process a payment plan installment payment"""
    payment_plan_id: str
    installment_number: int
    payment_amount: Money
    payment_date: datetime
    payment_method: str
    processed_by: str


@dataclass(frozen=True)
class HandlePaymentDisputeCommand:
    """Command to handle a payment dispute"""
    invoice_id: str
    dispute_reason: str
    dispute_amount: Money
    customer_evidence: Optional[List[Dict[str, Any]]] = None
    assigned_to: str
    priority_level: str = "high"


# Command Result Types

@dataclass(frozen=True)
class CommandResult:
    """Base result type for command execution"""
    success: bool
    entity_id: Optional[str] = None
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class CampaignCreatedResult(CommandResult):
    """Result of creating a payment campaign"""
    campaign_id: str
    invoices_included: List[str]
    estimated_collection_probability: float
    recommended_actions: List[str]


@dataclass(frozen=True)
class ReminderSentResult(CommandResult):
    """Result of sending a payment reminder"""
    reminder_id: str
    delivery_status: str
    tracking_id: Optional[str] = None
    estimated_open_rate: float = 0.0


@dataclass(frozen=True)
class ConversationStartedResult(CommandResult):
    """Result of starting a conversation"""
    conversation_id: str
    ai_response: str
    suggested_actions: List[str]
    context_analysis: Dict[str, Any]


@dataclass(frozen=True)
class SettlementGeneratedResult(CommandResult):
    """Result of generating settlement offer"""
    settlement_id: str
    settlement_amount: Money
    discount_percentage: float
    approval_required: bool
    estimated_acceptance_rate: float


@dataclass(frozen=True)
class PaymentPlanCreatedResult(CommandResult):
    """Result of creating payment plan"""
    payment_plan_id: str
    monthly_payment: Money
    total_payments: int
    first_payment_due: datetime
    autopay_configured: bool