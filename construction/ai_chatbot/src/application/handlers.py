"""
Command Handlers for Payment Intelligence Application

Command handlers orchestrate domain operations and coordinate
between domain services, aggregates, and infrastructure services.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

from .commands import *
from ..domain.aggregates.payment_campaign import PaymentCampaign
from ..domain.aggregates.conversation import Conversation
from ..domain.aggregates.chatbot_profile import ChatbotProfile
from ..domain.entities.overdue_invoice import OverdueInvoice
from ..domain.entities.payment_reminder import PaymentReminder
from ..domain.services.overdue_payment_service import OverduePaymentService
from ..domain.services.reminder_escalation_service import ReminderEscalationService
from ..domain.services.alternative_payment_service import AlternativePaymentService
from ..domain.services.email_generation_service import EmailGenerationService, EmailPersonalization
from ..domain.value_objects.payment_value_objects import *


# Repository Interfaces (Infrastructure concerns)

class IPaymentCampaignRepository(ABC):
    @abstractmethod
    def save(self, campaign: PaymentCampaign) -> None: pass
    
    @abstractmethod
    def find_by_id(self, campaign_id: str) -> Optional[PaymentCampaign]: pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: str) -> List[PaymentCampaign]: pass


class IConversationRepository(ABC):
    @abstractmethod
    def save(self, conversation: Conversation) -> None: pass
    
    @abstractmethod
    def find_by_id(self, conversation_id: str) -> Optional[Conversation]: pass


class IOverdueInvoiceRepository(ABC):
    @abstractmethod
    def find_by_id(self, invoice_id: str) -> Optional[OverdueInvoice]: pass
    
    @abstractmethod
    def save(self, invoice: OverdueInvoice) -> None: pass


class IChatbotProfileRepository(ABC):
    @abstractmethod
    def save(self, profile: ChatbotProfile) -> None: pass
    
    @abstractmethod
    def find_by_id(self, profile_id: str) -> Optional[ChatbotProfile]: pass


# Infrastructure Services Interfaces

class IEmailService(ABC):
    @abstractmethod
    def send_email(self, template: EmailTemplate, recipient: str) -> str: pass


class INotificationService(ABC):
    @abstractmethod
    def notify_escalation(self, campaign_id: str, details: Dict[str, Any]) -> None: pass


class IPaymentProcessingService(ABC):
    @abstractmethod
    def process_payment(self, payment_details: Dict[str, Any]) -> Dict[str, Any]: pass


# Command Handlers

class CreatePaymentCampaignHandler:
    """Handles creation of new payment campaigns"""
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        invoice_repository: IOverdueInvoiceRepository,
        overdue_payment_service: OverduePaymentService
    ):
        self._campaign_repository = campaign_repository
        self._invoice_repository = invoice_repository
        self._overdue_payment_service = overdue_payment_service
    
    def handle(self, command: CreatePaymentCampaignCommand) -> CampaignCreatedResult:
        """Handle campaign creation command"""
        
        # Get invoices for the campaign
        invoices = []
        for invoice_id in command.invoice_ids:
            invoice = self._invoice_repository.find_by_id(invoice_id)
            if invoice:
                invoices.append(invoice)
        
        if not invoices:
            return CampaignCreatedResult(
                success=False,
                error_message="No valid invoices found for campaign",
                campaign_id="",
                invoices_included=[],
                estimated_collection_probability=0.0,
                recommended_actions=[]
            )
        
        # Calculate total amount
        total_amount = Money(
            sum(inv.current_balance.amount for inv in invoices),
            invoices[0].current_balance.currency
        )
        
        # Determine initial reminder level
        initial_level = ReminderLevel.FIRST
        
        # Create campaign
        campaign = PaymentCampaign.create_campaign(
            customer_id=command.customer_id,
            invoices=invoices,
            total_amount=total_amount,
            initial_reminder_level=initial_level,
            priority_level=command.priority_level
        )
        
        # Add creation notes if provided
        if command.notes:
            campaign.add_collection_note(
                content=command.notes,
                note_type="campaign_creation",
                created_by=command.requested_by
            )
        
        # Get AI recommendations
        prioritized_invoices = self._overdue_payment_service.prioritize_overdue_invoices(invoices)
        recommended_actions = []
        
        for invoice in prioritized_invoices[:3]:  # Top 3 recommendations
            recommendations = self._overdue_payment_service.get_collection_recommendations(invoice)
            recommended_actions.extend(recommendations[:2])  # Top 2 per invoice
        
        # Calculate collection probability
        collection_probability = sum(
            self._overdue_payment_service.estimate_collection_probability(inv) 
            for inv in invoices
        ) / len(invoices)
        
        # Save campaign
        self._campaign_repository.save(campaign)
        
        return CampaignCreatedResult(
            success=True,
            campaign_id=campaign.campaign_id,
            invoices_included=command.invoice_ids,
            estimated_collection_probability=collection_probability,
            recommended_actions=list(set(recommended_actions))  # Remove duplicates
        )


class SendPaymentReminderHandler:
    """Handles sending payment reminders"""
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        email_generation_service: EmailGenerationService,
        email_service: IEmailService
    ):
        self._campaign_repository = campaign_repository
        self._email_generation_service = email_generation_service
        self._email_service = email_service
    
    def handle(self, command: SendPaymentReminderCommand) -> ReminderSentResult:
        """Handle payment reminder sending"""
        
        # Get campaign
        campaign = self._campaign_repository.find_by_id(command.campaign_id)
        if not campaign:
            return ReminderSentResult(
                success=False,
                error_message="Campaign not found",
                reminder_id="",
                delivery_status="failed"
            )
        
        # Get primary invoice for email generation
        primary_invoice = campaign.get_highest_priority_invoice()
        if not primary_invoice:
            return ReminderSentResult(
                success=False,
                error_message="No invoices found in campaign",
                reminder_id="",
                delivery_status="failed"
            )
        
        # Create customer profile from campaign data
        customer_profile = self._build_customer_profile(campaign)
        
        # Generate personalized email
        email_template = self._email_generation_service.generate_payment_reminder_email(
            invoice=primary_invoice,
            reminder_level=command.reminder_level,
            customer_profile=customer_profile,
            personalization_level=EmailPersonalization(command.personalization_level)
        )
        
        # Create reminder
        reminder = PaymentReminder.create_reminder(
            campaign_id=campaign.campaign_id,
            reminder_level=command.reminder_level,
            email_template=email_template,
            scheduled_send_time=command.scheduled_send_time
        )
        
        # Send email
        recipient_email = customer_profile.get("email", "customer@example.com")
        tracking_id = self._email_service.send_email(email_template, recipient_email)
        
        # Mark reminder as sent
        reminder.mark_as_sent(tracking_id)
        
        # Add reminder to campaign
        campaign.add_reminder(reminder)
        
        # Save campaign
        self._campaign_repository.save(campaign)
        
        return ReminderSentResult(
            success=True,
            reminder_id=reminder.reminder_id,
            delivery_status="sent",
            tracking_id=tracking_id,
            estimated_open_rate=0.65  # Industry average estimate
        )
    
    def _build_customer_profile(self, campaign: PaymentCampaign) -> Dict[str, Any]:
        """Build customer profile for email generation"""
        return {
            "customer_id": campaign.customer_id,
            "name": "Valued Customer",  # Would come from customer service
            "company_name": "",  # Would come from customer service
            "email": "customer@example.com",  # Would come from customer service
            "payment_history_summary": "good",
            "communication_preferences": {
                "preferred_tone": "professional",
                "prefers_brief_communication": False
            }
        }


class ProcessIncomingPaymentHandler:
    """Handles processing of incoming payments"""
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        invoice_repository: IOverdueInvoiceRepository,
        payment_processing_service: IPaymentProcessingService,
        email_generation_service: EmailGenerationService,
        email_service: IEmailService
    ):
        self._campaign_repository = campaign_repository
        self._invoice_repository = invoice_repository
        self._payment_processing_service = payment_processing_service
        self._email_generation_service = email_generation_service
        self._email_service = email_service
    
    def handle(self, command: ProcessIncomingPaymentCommand) -> CommandResult:
        """Handle incoming payment processing"""
        
        # Get invoice
        invoice = self._invoice_repository.find_by_id(command.invoice_id)
        if not invoice:
            return CommandResult(
                success=False,
                error_message="Invoice not found"
            )
        
        # Process payment on invoice
        payment_result = invoice.record_payment(
            amount=command.payment_amount,
            payment_date=command.payment_date,
            payment_method=command.payment_method,
            confirmation_number=command.confirmation_number
        )
        
        if not payment_result["success"]:
            return CommandResult(
                success=False,
                error_message=payment_result["error"]
            )
        
        # Update invoice
        self._invoice_repository.save(invoice)
        
        # Find and update related campaigns
        campaigns = self._campaign_repository.find_by_customer(invoice.customer_id)
        for campaign in campaigns:
            if campaign.has_invoice(command.invoice_id):
                campaign.record_payment(
                    invoice_id=command.invoice_id,
                    payment_amount=command.payment_amount,
                    payment_date=command.payment_date
                )
                
                # Check if campaign should be completed
                if campaign.all_invoices_paid():
                    campaign.complete_campaign("all_invoices_paid")
                
                self._campaign_repository.save(campaign)
        
        # Send thank you email if payment is substantial
        if command.payment_amount.amount >= 100:  # Configurable threshold
            self._send_thank_you_email(invoice, command)
        
        return CommandResult(
            success=True,
            entity_id=command.invoice_id,
            metadata={
                "payment_amount": command.payment_amount.amount,
                "remaining_balance": invoice.current_balance.amount,
                "payment_status": invoice.payment_status.value
            }
        )
    
    def _send_thank_you_email(self, invoice: OverdueInvoice, command: ProcessIncomingPaymentCommand):
        """Send thank you email for payment"""
        try:
            customer_profile = {
                "customer_id": invoice.customer_id,
                "name": "Valued Customer",
                "email": "customer@example.com"
            }
            
            payment_details = {
                "amount": command.payment_amount,
                "payment_date": command.payment_date,
                "payment_method": command.payment_method,
                "confirmation_number": command.confirmation_number
            }
            
            thank_you_email = self._email_generation_service.generate_thank_you_email(
                invoice, payment_details, customer_profile
            )
            
            self._email_service.send_email(thank_you_email, customer_profile["email"])
            
        except Exception as e:
            # Log error but don't fail the payment processing
            print(f"Failed to send thank you email: {e}")


class EscalateCampaignHandler:
    """Handles campaign escalation"""
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        escalation_service: ReminderEscalationService,
        notification_service: INotificationService
    ):
        self._campaign_repository = campaign_repository
        self._escalation_service = escalation_service
        self._notification_service = notification_service
    
    def handle(self, command: EscalateCampaignCommand) -> CommandResult:
        """Handle campaign escalation"""
        
        # Get campaign
        campaign = self._campaign_repository.find_by_id(command.campaign_id)
        if not campaign:
            return CommandResult(
                success=False,
                error_message="Campaign not found"
            )
        
        # Evaluate escalation
        should_escalate, reasons = self._escalation_service.evaluate_campaign_for_escalation(campaign)
        
        if not should_escalate and command.escalation_reason != "manual_escalation_request":
            return CommandResult(
                success=False,
                error_message="Campaign does not meet escalation criteria"
            )
        
        # Determine escalation actions
        escalation_reasons = [ReminderEscalationService.EscalationReason(command.escalation_reason)]
        escalation_actions = self._escalation_service.determine_escalation_actions(
            campaign, escalation_reasons
        )
        
        # Execute escalation
        escalation_result = self._escalation_service.execute_escalation(
            campaign, escalation_reasons, escalation_actions
        )
        
        # Update campaign status
        campaign.escalate_campaign(
            escalation_reason=command.escalation_reason,
            escalated_by=command.requested_by,
            escalation_notes=command.escalation_notes
        )
        
        # Save campaign
        self._campaign_repository.save(campaign)
        
        # Send notifications
        self._notification_service.notify_escalation(
            command.campaign_id,
            escalation_result
        )
        
        return CommandResult(
            success=True,
            entity_id=command.campaign_id,
            metadata=escalation_result
        )


class StartConversationHandler:
    """Handles starting new AI conversations"""
    
    def __init__(
        self,
        conversation_repository: IConversationRepository,
        chatbot_repository: IChatbotProfileRepository
    ):
        self._conversation_repository = conversation_repository
        self._chatbot_repository = chatbot_repository
    
    def handle(self, command: StartConversationCommand) -> ConversationStartedResult:
        """Handle conversation start"""
        
        # Get chatbot profile
        chatbot_profile = self._chatbot_repository.find_by_id("default_payment_assistant")
        if not chatbot_profile:
            return ConversationStartedResult(
                success=False,
                error_message="Chatbot profile not found",
                conversation_id="",
                ai_response="",
                suggested_actions=[],
                context_analysis={}
            )
        
        # Create conversation context
        context = ConversationContext(
            customer_id=command.customer_id,
            conversation_type=command.conversation_type,
            channel=command.channel,
            context_data=command.conversation_context
        )
        
        # Start conversation
        conversation = Conversation.start_conversation(
            customer_id=command.customer_id,
            chatbot_profile=chatbot_profile,
            initial_context=context,
            channel=command.channel
        )
        
        # Process initial message
        response = conversation.process_message(
            content=command.initial_message,
            sender="customer",
            message_type="text"
        )
        
        # Save conversation
        self._conversation_repository.save(conversation)
        
        # Extract AI response and suggestions
        ai_response = response.get("ai_response", "Hello! How can I help you with your payment today?")
        suggested_actions = response.get("suggested_actions", [
            "check_payment_status",
            "setup_payment_plan",
            "make_payment"
        ])
        
        return ConversationStartedResult(
            success=True,
            conversation_id=conversation.conversation_id,
            ai_response=ai_response,
            suggested_actions=suggested_actions,
            context_analysis=response.get("context_analysis", {})
        )


class CreatePaymentPlanHandler:
    """Handles creation of payment plans"""
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        invoice_repository: IOverdueInvoiceRepository,
        alternative_payment_service: AlternativePaymentService
    ):
        self._campaign_repository = campaign_repository
        self._invoice_repository = invoice_repository
        self._alternative_payment_service = alternative_payment_service
    
    def handle(self, command: CreatePaymentPlanCommand) -> PaymentPlanCreatedResult:
        """Handle payment plan creation"""
        
        # Get invoices
        invoices = []
        total_amount = Money(0.0, "USD")
        
        for invoice_id in command.invoice_ids:
            invoice = self._invoice_repository.find_by_id(invoice_id)
            if invoice:
                invoices.append(invoice)
                total_amount = Money(
                    total_amount.amount + invoice.current_balance.amount,
                    invoice.current_balance.currency
                )
        
        if not invoices:
            return PaymentPlanCreatedResult(
                success=False,
                error_message="No valid invoices found",
                payment_plan_id="",
                monthly_payment=Money(0, "USD"),
                total_payments=0,
                first_payment_due=datetime.utcnow(),
                autopay_configured=False
            )
        
        # Create payment plan details
        plan_details = {
            "installments": command.installments,
            "monthly_payment": command.monthly_payment.amount,
            "start_date": command.start_date,
            "setup_autopay": command.setup_autopay,
            "payment_method": command.payment_method,
            "requires_approval": command.installments > 6 or total_amount.amount > 10000
        }
        
        # Create payment plan using domain service
        primary_invoice = invoices[0]  # Use first invoice as primary
        plan_result = self._alternative_payment_service.create_payment_plan(
            invoice=primary_invoice,
            plan_type=AlternativePaymentService.PaymentPlanType(command.plan_type),
            plan_details=plan_details
        )
        
        if not plan_result["success"]:
            return PaymentPlanCreatedResult(
                success=False,
                error_message=plan_result["error"],
                payment_plan_id="",
                monthly_payment=Money(0, "USD"),
                total_payments=0,
                first_payment_due=datetime.utcnow(),
                autopay_configured=False
            )
        
        # Update related campaigns
        campaigns = self._campaign_repository.find_by_customer(command.customer_id)
        for campaign in campaigns:
            for invoice_id in command.invoice_ids:
                if campaign.has_invoice(invoice_id):
                    campaign.add_collection_note(
                        content=f"Payment plan created: {plan_result['plan_id']}",
                        note_type="payment_plan_created",
                        created_by=command.created_by
                    )
                    self._campaign_repository.save(campaign)
        
        return PaymentPlanCreatedResult(
            success=True,
            payment_plan_id=plan_result["plan_id"],
            monthly_payment=plan_result["monthly_payment"],
            total_payments=len(plan_result["payment_schedule"]),
            first_payment_due=plan_result["payment_schedule"][0]["due_date"],
            autopay_configured=plan_result.get("recurring_payment_id") is not None
        )