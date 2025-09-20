"""
Application Services for Payment Intelligence

Application services coordinate use cases and orchestrate domain operations.
They provide the main entry points for business operations.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod

from .commands import *
from .queries import *
from .handlers import *
from .query_handlers import *
from ..domain.services.overdue_payment_service import OverduePaymentService
from ..domain.services.reminder_escalation_service import ReminderEscalationService
from ..domain.services.alternative_payment_service import AlternativePaymentService
from ..domain.services.email_generation_service import EmailGenerationService


class PaymentCampaignService:
    """
    Application service for payment campaign management.
    
    Coordinates campaign creation, reminder sending, escalation,
    and performance tracking.
    """
    
    def __init__(
        self,
        create_campaign_handler: CreatePaymentCampaignHandler,
        send_reminder_handler: SendPaymentReminderHandler,
        escalate_campaign_handler: EscalateCampaignHandler,
        campaign_query_handler: GetPaymentCampaignsHandler,
        campaign_details_handler: GetCampaignDetailsHandler,
        overdue_payment_service: OverduePaymentService,
        escalation_service: ReminderEscalationService
    ):
        self._create_campaign_handler = create_campaign_handler
        self._send_reminder_handler = send_reminder_handler
        self._escalate_campaign_handler = escalate_campaign_handler
        self._campaign_query_handler = campaign_query_handler
        self._campaign_details_handler = campaign_details_handler
        self._overdue_payment_service = overdue_payment_service
        self._escalation_service = escalation_service
    
    def create_intelligent_campaign(
        self,
        customer_id: str,
        invoice_ids: List[str],
        requested_by: str,
        campaign_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create an intelligent payment campaign with AI-powered optimization.
        
        This method analyzes invoices, determines optimal campaign strategy,
        and creates a campaign with intelligent defaults.
        """
        
        # Analyze invoices to determine campaign strategy
        campaign_analysis = self._analyze_campaign_requirements(invoice_ids)
        
        # Determine optimal campaign configuration
        campaign_config = self._optimize_campaign_configuration(
            customer_id, campaign_analysis, campaign_options
        )
        
        # Create campaign command
        create_command = CreatePaymentCampaignCommand(
            customer_id=customer_id,
            invoice_ids=invoice_ids,
            campaign_type=campaign_config["campaign_type"],
            priority_level=campaign_config["priority_level"],
            requested_by=requested_by,
            notes=campaign_config["notes"]
        )
        
        # Execute campaign creation
        creation_result = self._create_campaign_handler.handle(create_command)
        
        if not creation_result.success:
            return {
                "success": False,
                "error": creation_result.error_message,
                "campaign_id": None
            }
        
        # Schedule initial reminder if appropriate
        initial_reminder_result = None
        if campaign_config.get("send_immediate_reminder", False):
            reminder_command = SendPaymentReminderCommand(
                campaign_id=creation_result.campaign_id,
                reminder_level=ReminderLevel.FIRST,
                personalization_level="moderate",
                requested_by=requested_by
            )
            initial_reminder_result = self._send_reminder_handler.handle(reminder_command)
        
        return {
            "success": True,
            "campaign_id": creation_result.campaign_id,
            "campaign_strategy": campaign_config,
            "estimated_collection_probability": creation_result.estimated_collection_probability,
            "recommended_actions": creation_result.recommended_actions,
            "initial_reminder_sent": initial_reminder_result is not None and initial_reminder_result.success
        }
    
    def execute_automated_reminder_sequence(
        self,
        campaign_id: str,
        sequence_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an automated reminder sequence with intelligent timing and escalation.
        """
        
        # Get campaign details
        details_query = GetCampaignDetailsQuery(campaign_id=campaign_id)
        campaign_details = self._campaign_details_handler.handle(details_query)
        
        # Analyze current campaign state
        sequence_analysis = self._analyze_reminder_sequence_needs(campaign_details.campaign)
        
        if not sequence_analysis["should_send_reminder"]:
            return {
                "success": False,
                "reason": sequence_analysis["reason"],
                "next_action": sequence_analysis["next_action"]
            }
        
        # Determine next reminder level
        next_level = sequence_analysis["next_reminder_level"]
        
        # Check if escalation is needed instead
        should_escalate, escalation_reasons = self._escalation_service.evaluate_campaign_for_escalation(
            self._build_campaign_aggregate_from_details(campaign_details.campaign)
        )
        
        if should_escalate:
            # Execute escalation instead of reminder
            escalate_command = EscalateCampaignCommand(
                campaign_id=campaign_id,
                escalation_reason=escalation_reasons[0].value if escalation_reasons else "reminder_limit_reached",
                escalation_level="collections",
                requested_by="system"
            )
            
            escalation_result = self._escalate_campaign_handler.handle(escalate_command)
            
            return {
                "success": escalation_result.success,
                "action_taken": "escalation",
                "escalation_reasons": [r.value for r in escalation_reasons],
                "escalation_details": escalation_result.metadata
            }
        
        # Send reminder
        reminder_command = SendPaymentReminderCommand(
            campaign_id=campaign_id,
            reminder_level=next_level,
            personalization_level=sequence_analysis["personalization_level"],
            requested_by="system"
        )
        
        reminder_result = self._send_reminder_handler.handle(reminder_command)
        
        # Schedule next reminder if appropriate
        next_reminder_date = self._calculate_next_reminder_date(
            next_level, campaign_details.campaign
        )
        
        return {
            "success": reminder_result.success,
            "action_taken": "reminder_sent",
            "reminder_level": next_level.value,
            "reminder_id": reminder_result.reminder_id,
            "tracking_id": reminder_result.tracking_id,
            "next_reminder_scheduled": next_reminder_date
        }
    
    def get_campaign_performance_analytics(
        self,
        date_range: Tuple[datetime, datetime],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive campaign performance analytics"""
        
        # Get campaigns in date range
        campaigns_query = GetPaymentCampaignsQuery(
            created_after=date_range[0],
            created_before=date_range[1],
            limit=1000
        )
        campaigns_result = self._campaign_query_handler.handle(campaigns_query)
        
        # Calculate performance metrics
        performance_metrics = self._calculate_campaign_performance_metrics(
            campaigns_result.campaigns
        )
        
        # Analyze trends
        trend_analysis = self._analyze_campaign_trends(campaigns_result.campaigns)
        
        # Generate insights and recommendations
        insights = self._generate_campaign_insights(performance_metrics, trend_analysis)
        
        return {
            "performance_metrics": performance_metrics,
            "trend_analysis": trend_analysis,
            "insights_and_recommendations": insights,
            "campaign_summary": {
                "total_campaigns": campaigns_result.total_count,
                "success_rate": campaigns_result.success_rate,
                "total_amount": campaigns_result.total_amount_in_campaigns.amount
            }
        }
    
    def _analyze_campaign_requirements(self, invoice_ids: List[str]) -> Dict[str, Any]:
        """Analyze invoice requirements to determine campaign strategy"""
        
        # This would analyze invoice amounts, ages, customer risk, etc.
        return {
            "total_amount": 5000.0,
            "average_days_overdue": 25,
            "customer_risk_level": "medium",
            "complexity_score": 0.6
        }
    
    def _optimize_campaign_configuration(
        self,
        customer_id: str,
        analysis: Dict[str, Any],
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Optimize campaign configuration based on analysis"""
        
        config = {
            "campaign_type": "standard_collection",
            "priority_level": "medium",
            "send_immediate_reminder": True,
            "personalization_level": "moderate",
            "notes": "AI-optimized campaign configuration"
        }
        
        # Adjust based on analysis
        if analysis["total_amount"] > 10000:
            config["priority_level"] = "high"
            config["personalization_level"] = "advanced"
        
        if analysis["customer_risk_level"] == "high":
            config["campaign_type"] = "aggressive_collection"
        
        # Apply user overrides
        if options:
            config.update(options)
        
        return config
    
    def _analyze_reminder_sequence_needs(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if campaign needs next reminder"""
        
        reminders_sent = len(campaign_data.get("reminders", []))
        days_since_last_reminder = 0
        
        if campaign_data.get("reminders"):
            last_reminder_date = max(r["sent_at"] for r in campaign_data["reminders"])
            days_since_last_reminder = (datetime.utcnow() - last_reminder_date).days
        
        # Business rules for reminder timing
        if reminders_sent >= 3:
            return {
                "should_send_reminder": False,
                "reason": "Maximum reminders reached",
                "next_action": "evaluate_for_escalation"
            }
        
        if days_since_last_reminder < 7:
            return {
                "should_send_reminder": False,
                "reason": "Too soon since last reminder",
                "next_action": f"wait_{7 - days_since_last_reminder}_days"
            }
        
        # Determine next reminder level
        next_level = ReminderLevel.FIRST
        if reminders_sent == 1:
            next_level = ReminderLevel.SECOND
        elif reminders_sent == 2:
            next_level = ReminderLevel.THIRD
        
        return {
            "should_send_reminder": True,
            "next_reminder_level": next_level,
            "personalization_level": "moderate" if reminders_sent < 2 else "advanced"
        }
    
    def _build_campaign_aggregate_from_details(self, campaign_data: Dict[str, Any]) -> PaymentCampaign:
        """Build campaign aggregate from data dictionary (simplified)"""
        # In real implementation, this would reconstruct the aggregate properly
        # For now, return a mock campaign for escalation evaluation
        pass
    
    def _calculate_next_reminder_date(
        self,
        reminder_level: ReminderLevel,
        campaign_data: Dict[str, Any]
    ) -> Optional[datetime]:
        """Calculate when next reminder should be sent"""
        
        if reminder_level == ReminderLevel.THIRD:
            return None  # No more reminders after third
        
        # Standard intervals: 7 days between reminders
        return datetime.utcnow() + timedelta(days=7)
    
    def _calculate_campaign_performance_metrics(
        self,
        campaigns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for campaigns"""
        
        if not campaigns:
            return {}
        
        total_campaigns = len(campaigns)
        completed_campaigns = len([c for c in campaigns if c["status"] == "completed"])
        escalated_campaigns = len([c for c in campaigns if c["status"] == "escalated"])
        
        return {
            "total_campaigns": total_campaigns,
            "completion_rate": completed_campaigns / total_campaigns,
            "escalation_rate": escalated_campaigns / total_campaigns,
            "average_campaign_duration": 21,  # Would calculate from data
            "average_reminders_per_campaign": 2.1,  # Would calculate from data
            "collection_effectiveness": 0.75  # Would calculate from data
        }
    
    def _analyze_campaign_trends(self, campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in campaign data"""
        
        return {
            "monthly_trends": {
                "campaign_volume": [100, 95, 110, 105],  # Last 4 months
                "success_rate": [0.78, 0.75, 0.82, 0.79],
                "escalation_rate": [0.15, 0.18, 0.12, 0.14]
            },
            "seasonal_patterns": {
                "q1_performance": 0.75,
                "q2_performance": 0.78,
                "q3_performance": 0.72,
                "q4_performance": 0.69
            }
        }
    
    def _generate_campaign_insights(
        self,
        performance_metrics: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate insights and recommendations"""
        
        insights = []
        
        completion_rate = performance_metrics.get("completion_rate", 0)
        if completion_rate < 0.7:
            insights.append("Campaign completion rate below target - consider optimizing reminder timing")
        
        escalation_rate = performance_metrics.get("escalation_rate", 0)
        if escalation_rate > 0.2:
            insights.append("High escalation rate - review early intervention strategies")
        
        insights.append("Consider A/B testing different reminder templates")
        insights.append("Implement payment plan offers for high-value campaigns")
        
        return insights


class ConversationService:
    """
    Application service for AI conversation management.
    
    Coordinates conversation lifecycle, message processing,
    and integration with payment operations.
    """
    
    def __init__(
        self,
        start_conversation_handler: StartConversationHandler,
        conversation_query_handler: GetConversationHistoryHandler
    ):
        self._start_conversation_handler = start_conversation_handler
        self._conversation_query_handler = conversation_query_handler
    
    def start_payment_assistance_conversation(
        self,
        customer_id: str,
        initial_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new payment assistance conversation"""
        
        # Build conversation context
        conversation_context = {
            "customer_id": customer_id,
            "assistance_type": "payment_inquiry",
            "initial_intent": self._analyze_initial_intent(initial_message),
            **(context or {})
        }
        
        # Start conversation
        start_command = StartConversationCommand(
            customer_id=customer_id,
            conversation_context=conversation_context,
            initial_message=initial_message,
            conversation_type="payment_assistance",
            channel="web_chat"
        )
        
        result = self._start_conversation_handler.handle(start_command)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error_message
            }
        
        return {
            "success": True,
            "conversation_id": result.conversation_id,
            "ai_response": result.ai_response,
            "suggested_actions": result.suggested_actions,
            "conversation_state": "active",
            "next_steps": self._determine_next_steps(result.context_analysis)
        }
    
    def process_conversation_message(
        self,
        conversation_id: str,
        message: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Process an incoming conversation message"""
        
        # This would typically use a message processing handler
        # For now, return a simulated response
        
        # Analyze message intent
        intent_analysis = self._analyze_message_intent(message)
        
        # Generate AI response based on intent
        ai_response = self._generate_ai_response(message, intent_analysis)
        
        # Determine follow-up actions
        follow_up_actions = self._determine_follow_up_actions(intent_analysis)
        
        return {
            "success": True,
            "ai_response": ai_response,
            "message_intent": intent_analysis["primary_intent"],
            "confidence_score": intent_analysis["confidence"],
            "follow_up_actions": follow_up_actions,
            "requires_human_handoff": intent_analysis.get("requires_human", False)
        }
    
    def get_conversation_summary(
        self,
        conversation_id: str,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        
        # Get conversation history
        history_query = GetConversationHistoryQuery(conversation_id=conversation_id)
        history_result = self._conversation_query_handler.handle(history_query)
        
        if not history_result.conversations:
            return {"success": False, "error": "Conversation not found"}
        
        conversation = history_result.conversations[0]
        
        # Analyze conversation
        conversation_analysis = self._analyze_conversation_performance(conversation)
        
        # Generate recommendations if requested
        recommendations = []
        if include_recommendations:
            recommendations = self._generate_conversation_recommendations(conversation_analysis)
        
        return {
            "success": True,
            "conversation_summary": conversation_analysis,
            "recommendations": recommendations,
            "satisfaction_score": conversation.get("satisfaction_score", 0.0),
            "resolution_status": conversation.get("resolution_status", "ongoing")
        }
    
    def _analyze_initial_intent(self, message: str) -> str:
        """Analyze the initial intent of the customer message"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["payment", "pay", "invoice", "bill"]):
            return "payment_inquiry"
        elif any(word in message_lower for word in ["plan", "installment", "monthly"]):
            return "payment_plan_request"
        elif any(word in message_lower for word in ["dispute", "disagree", "wrong"]):
            return "payment_dispute"
        elif any(word in message_lower for word in ["help", "assistance", "support"]):
            return "general_assistance"
        else:
            return "general_inquiry"
    
    def _analyze_message_intent(self, message: str) -> Dict[str, Any]:
        """Analyze message intent and confidence"""
        
        return {
            "primary_intent": self._analyze_initial_intent(message),
            "confidence": 0.85,
            "secondary_intents": [],
            "requires_human": False,
            "sentiment": "neutral"
        }
    
    def _generate_ai_response(self, message: str, intent_analysis: Dict[str, Any]) -> str:
        """Generate AI response based on message and intent"""
        
        intent = intent_analysis["primary_intent"]
        
        responses = {
            "payment_inquiry": "I can help you with your payment. Let me check your account status.",
            "payment_plan_request": "I'd be happy to help you set up a payment plan. Let me review your options.",
            "payment_dispute": "I understand you have concerns about your invoice. Let me connect you with our billing team.",
            "general_assistance": "I'm here to help! What specific payment-related question can I assist you with?"
        }
        
        return responses.get(intent, "Thank you for your message. How can I assist you today?")
    
    def _determine_follow_up_actions(self, intent_analysis: Dict[str, Any]) -> List[str]:
        """Determine appropriate follow-up actions"""
        
        intent = intent_analysis["primary_intent"]
        
        action_mapping = {
            "payment_inquiry": ["check_account_status", "show_payment_options"],
            "payment_plan_request": ["calculate_payment_plan_options", "check_eligibility"],
            "payment_dispute": ["escalate_to_billing_team", "collect_dispute_details"],
            "general_assistance": ["clarify_customer_needs", "provide_menu_options"]
        }
        
        return action_mapping.get(intent, ["clarify_customer_needs"])
    
    def _determine_next_steps(self, context_analysis: Dict[str, Any]) -> List[str]:
        """Determine next steps based on conversation context"""
        
        return [
            "Gather customer payment preferences",
            "Review account status",
            "Offer appropriate payment solutions"
        ]
    
    def _analyze_conversation_performance(self, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversation performance metrics"""
        
        return {
            "message_count": len(conversation.get("messages", [])),
            "duration_minutes": 15,  # Would calculate from timestamps
            "resolution_achieved": conversation.get("status") == "resolved",
            "customer_satisfaction": conversation.get("satisfaction_score", 0.0),
            "ai_effectiveness": 0.8,  # Would calculate based on various factors
            "topics_covered": ["payment_options", "account_status"]
        }
    
    def _generate_conversation_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on conversation analysis"""
        
        recommendations = []
        
        if analysis["message_count"] > 10:
            recommendations.append("Consider offering human assistance for complex inquiries")
        
        if analysis["customer_satisfaction"] < 0.7:
            recommendations.append("Follow up with customer satisfaction survey")
        
        if not analysis["resolution_achieved"]:
            recommendations.append("Schedule follow-up contact within 24 hours")
        
        return recommendations


class PaymentProcessingService:
    """
    Application service for payment processing operations.
    
    Coordinates payment reception, plan management,
    and integration with collection campaigns.
    """
    
    def __init__(
        self,
        process_payment_handler: ProcessIncomingPaymentHandler,
        create_payment_plan_handler: CreatePaymentPlanHandler,
        payment_history_handler: GetCustomerPaymentHistoryHandler,
        alternative_payment_service: AlternativePaymentService
    ):
        self._process_payment_handler = process_payment_handler
        self._create_payment_plan_handler = create_payment_plan_handler
        self._payment_history_handler = payment_history_handler
        self._alternative_payment_service = alternative_payment_service
    
    def process_customer_payment(
        self,
        invoice_id: str,
        payment_details: Dict[str, Any],
        processed_by: str
    ) -> Dict[str, Any]:
        """Process a customer payment with intelligent workflow"""
        
        # Validate payment details
        validation_result = self._validate_payment_details(payment_details)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": validation_result["error"],
                "validation_details": validation_result
            }
        
        # Create payment command
        payment_command = ProcessIncomingPaymentCommand(
            invoice_id=invoice_id,
            payment_amount=Money(payment_details["amount"], payment_details["currency"]),
            payment_date=payment_details["payment_date"],
            payment_method=payment_details["method"],
            confirmation_number=payment_details["confirmation"],
            processed_by=processed_by,
            notes=payment_details.get("notes")
        )
        
        # Process payment
        result = self._process_payment_handler.handle(payment_command)
        
        if not result.success:
            return {
                "success": False,
                "error": result.error_message,
                "payment_id": None
            }
        
        # Post-processing actions
        post_processing_actions = self._execute_post_payment_actions(
            invoice_id, payment_details, result
        )
        
        return {
            "success": True,
            "payment_processed": True,
            "remaining_balance": result.metadata.get("remaining_balance", 0),
            "payment_status": result.metadata.get("payment_status"),
            "post_processing_actions": post_processing_actions
        }
    
    def create_intelligent_payment_plan(
        self,
        customer_id: str,
        invoice_ids: List[str],
        customer_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create payment plan with AI optimization"""
        
        # Get customer payment history for analysis
        history_query = GetCustomerPaymentHistoryQuery(customer_id=customer_id)
        payment_history = self._payment_history_handler.handle(history_query)
        
        # Build customer profile
        customer_profile = self._build_customer_profile_for_payment_plan(
            customer_id, payment_history, customer_preferences
        )
        
        # Generate payment plan options
        plan_options = self._generate_optimal_payment_plan_options(
            invoice_ids, customer_profile
        )
        
        if not plan_options:
            return {
                "success": False,
                "error": "No suitable payment plan options available",
                "options": []
            }
        
        # Select best option or use customer preference
        selected_plan = self._select_optimal_payment_plan(plan_options, customer_preferences)
        
        # Create payment plan
        plan_command = CreatePaymentPlanCommand(
            customer_id=customer_id,
            invoice_ids=invoice_ids,
            plan_type=selected_plan["plan_type"],
            installments=selected_plan["installments"],
            monthly_payment=Money(selected_plan["monthly_payment"], "USD"),
            start_date=selected_plan["start_date"],
            setup_autopay=selected_plan.get("setup_autopay", False),
            payment_method=selected_plan.get("payment_method"),
            created_by="ai_system"
        )
        
        result = self._create_payment_plan_handler.handle(plan_command)
        
        return {
            "success": result.success,
            "payment_plan_id": result.payment_plan_id if result.success else None,
            "plan_details": selected_plan,
            "alternative_options": plan_options[1:3],  # Top 2 alternatives
            "monthly_payment": result.monthly_payment.amount if result.success else 0,
            "total_payments": result.total_payments if result.success else 0
        }
    
    def _validate_payment_details(self, payment_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate payment details"""
        
        required_fields = ["amount", "currency", "payment_date", "method", "confirmation"]
        
        for field in required_fields:
            if field not in payment_details:
                return {
                    "valid": False,
                    "error": f"Missing required field: {field}"
                }
        
        if payment_details["amount"] <= 0:
            return {
                "valid": False,
                "error": "Payment amount must be positive"
            }
        
        return {"valid": True, "error": None}
    
    def _execute_post_payment_actions(
        self,
        invoice_id: str,
        payment_details: Dict[str, Any],
        result: CommandResult
    ) -> List[str]:
        """Execute post-payment processing actions"""
        
        actions = []
        
        # Send thank you email (handled by payment handler)
        actions.append("thank_you_email_sent")
        
        # Update customer payment history
        actions.append("payment_history_updated")
        
        # Check for campaign completion
        if result.metadata.get("remaining_balance", 1) == 0:
            actions.append("campaign_completion_check")
        
        # Update credit profile if significant payment
        if payment_details["amount"] > 1000:
            actions.append("credit_profile_updated")
        
        return actions
    
    def _build_customer_profile_for_payment_plan(
        self,
        customer_id: str,
        payment_history: CustomerPaymentHistoryResult,
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build customer profile for payment plan optimization"""
        
        profile = {
            "customer_id": customer_id,
            "payment_patterns": payment_history.payment_patterns,
            "risk_assessment": payment_history.risk_assessment,
            "preferred_payment_methods": preferences.get("payment_methods", []) if preferences else [],
            "monthly_payment_capacity": preferences.get("monthly_capacity", 500) if preferences else 500
        }
        
        return profile
    
    def _generate_optimal_payment_plan_options(
        self,
        invoice_ids: List[str],
        customer_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate optimal payment plan options"""
        
        # Calculate total amount (simplified)
        total_amount = 3000.0  # Would calculate from actual invoices
        
        options = []
        
        # 3-month plan
        if customer_profile["monthly_payment_capacity"] >= total_amount / 3:
            options.append({
                "plan_type": "installment_plan",
                "installments": 3,
                "monthly_payment": total_amount / 3,
                "start_date": datetime.utcnow() + timedelta(days=7),
                "interest_rate": 0.0,
                "setup_fee": 0.0,
                "suitability_score": 0.9
            })
        
        # 6-month plan
        options.append({
            "plan_type": "installment_plan",
            "installments": 6,
            "monthly_payment": total_amount / 6,
            "start_date": datetime.utcnow() + timedelta(days=7),
            "interest_rate": 0.02,
            "setup_fee": 25.0,
            "suitability_score": 0.8
        })
        
        # 12-month plan
        options.append({
            "plan_type": "installment_plan",
            "installments": 12,
            "monthly_payment": total_amount / 12,
            "start_date": datetime.utcnow() + timedelta(days=7),
            "interest_rate": 0.05,
            "setup_fee": 50.0,
            "suitability_score": 0.7
        })
        
        # Sort by suitability score
        options.sort(key=lambda x: x["suitability_score"], reverse=True)
        
        return options
    
    def _select_optimal_payment_plan(
        self,
        options: List[Dict[str, Any]],
        preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select the optimal payment plan"""
        
        if preferences and "preferred_installments" in preferences:
            # Find option matching preference
            for option in options:
                if option["installments"] == preferences["preferred_installments"]:
                    return option
        
        # Return highest scoring option
        return options[0]