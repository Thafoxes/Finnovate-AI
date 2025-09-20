"""
Reminder Escalation Service for Payment Intelligence Domain

Domain service responsible for managing the escalation process for
payment reminders and campaigns.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from abc import ABC, abstractmethod

from ..aggregates.payment_campaign import PaymentCampaign
from ..entities.payment_reminder import PaymentReminder
from ..entities.overdue_invoice import OverdueInvoice
from ..value_objects.payment_value_objects import ReminderLevel, PaymentStatus
from ..events.domain_events import (
    EscalationTriggered,
    CampaignEscalated,
    ManualInterventionRequired
)


class EscalationReason(Enum):
    """Reasons for escalating a payment campaign"""
    REMINDER_LIMIT_REACHED = "reminder_limit_reached"
    CUSTOMER_NON_RESPONSIVE = "customer_non_responsive"
    HIGH_RISK_CUSTOMER = "high_risk_customer"
    LARGE_AMOUNT_OVERDUE = "large_amount_overdue"
    MULTIPLE_INVOICES_OVERDUE = "multiple_invoices_overdue"
    PAYMENT_DISPUTES = "payment_disputes"
    MANUAL_ESCALATION_REQUEST = "manual_escalation_request"
    COLLECTION_PROBABILITY_LOW = "collection_probability_low"


class EscalationAction(Enum):
    """Actions to take when escalating"""
    COLLECTIONS_HANDOFF = "collections_handoff"
    MANAGER_REVIEW = "manager_review"
    LEGAL_REVIEW = "legal_review"
    PAYMENT_PLAN_NEGOTIATION = "payment_plan_negotiation"
    CUSTOMER_RELATIONSHIP_INTERVENTION = "customer_relationship_intervention"
    CREDIT_HOLD = "credit_hold"
    ACCOUNT_SUSPENSION = "account_suspension"


class IPaymentCampaignRepository(ABC):
    """Interface for payment campaign repository"""
    
    @abstractmethod
    def find_active_campaigns_by_customer(self, customer_id: str) -> List[PaymentCampaign]:
        pass
    
    @abstractmethod
    def find_escalated_campaigns(self) -> List[PaymentCampaign]:
        pass


class ICollectionsService(ABC):
    """Interface for collections service integration"""
    
    @abstractmethod
    def create_collections_case(self, campaign: PaymentCampaign, reason: EscalationReason) -> str:
        pass
    
    @abstractmethod
    def transfer_campaign_data(self, campaign: PaymentCampaign, case_id: str) -> bool:
        pass


class ReminderEscalationService:
    """
    Domain service for managing reminder escalation logic and processes.
    
    Handles the complex business rules around when and how to escalate
    payment campaigns beyond automated reminders.
    """
    
    def __init__(
        self,
        campaign_repository: IPaymentCampaignRepository,
        collections_service: ICollectionsService
    ):
        self._campaign_repository = campaign_repository
        self._collections_service = collections_service
        
        # Business configuration
        self._max_reminder_attempts = 3
        self._escalation_amount_threshold = 5000.0
        self._non_responsive_days = 14
        self._high_risk_threshold = 0.75
        self._multiple_invoices_threshold = 3
    
    def evaluate_campaign_for_escalation(self, campaign: PaymentCampaign) -> Tuple[bool, List[EscalationReason]]:
        """
        Evaluate if a payment campaign should be escalated and why.
        
        Returns:
            Tuple of (should_escalate: bool, reasons: List[EscalationReason])
        """
        escalation_reasons = []
        
        # Check reminder limit
        if self._check_reminder_limit_reached(campaign):
            escalation_reasons.append(EscalationReason.REMINDER_LIMIT_REACHED)
        
        # Check customer responsiveness
        if self._check_customer_non_responsive(campaign):
            escalation_reasons.append(EscalationReason.CUSTOMER_NON_RESPONSIVE)
        
        # Check customer risk profile
        if self._check_high_risk_customer(campaign):
            escalation_reasons.append(EscalationReason.HIGH_RISK_CUSTOMER)
        
        # Check amount threshold
        if self._check_large_amount_overdue(campaign):
            escalation_reasons.append(EscalationReason.LARGE_AMOUNT_OVERDUE)
        
        # Check multiple invoices
        if self._check_multiple_invoices_overdue(campaign):
            escalation_reasons.append(EscalationReason.MULTIPLE_INVOICES_OVERDUE)
        
        # Check collection probability
        if self._check_low_collection_probability(campaign):
            escalation_reasons.append(EscalationReason.COLLECTION_PROBABILITY_LOW)
        
        # Check for payment disputes
        if self._check_payment_disputes(campaign):
            escalation_reasons.append(EscalationReason.PAYMENT_DISPUTES)
        
        should_escalate = len(escalation_reasons) > 0
        
        return should_escalate, escalation_reasons
    
    def determine_escalation_actions(
        self,
        campaign: PaymentCampaign,
        reasons: List[EscalationReason]
    ) -> List[EscalationAction]:
        """Determine what actions to take based on escalation reasons"""
        actions = []
        
        # Map reasons to actions
        for reason in reasons:
            if reason == EscalationReason.REMINDER_LIMIT_REACHED:
                actions.append(EscalationAction.COLLECTIONS_HANDOFF)
            
            elif reason == EscalationReason.CUSTOMER_NON_RESPONSIVE:
                actions.append(EscalationAction.MANAGER_REVIEW)
                actions.append(EscalationAction.CUSTOMER_RELATIONSHIP_INTERVENTION)
            
            elif reason == EscalationReason.HIGH_RISK_CUSTOMER:
                actions.append(EscalationAction.CREDIT_HOLD)
                actions.append(EscalationAction.COLLECTIONS_HANDOFF)
            
            elif reason == EscalationReason.LARGE_AMOUNT_OVERDUE:
                actions.append(EscalationAction.MANAGER_REVIEW)
                actions.append(EscalationAction.LEGAL_REVIEW)
            
            elif reason == EscalationReason.MULTIPLE_INVOICES_OVERDUE:
                actions.append(EscalationAction.CREDIT_HOLD)
                actions.append(EscalationAction.PAYMENT_PLAN_NEGOTIATION)
            
            elif reason == EscalationReason.PAYMENT_DISPUTES:
                actions.append(EscalationAction.CUSTOMER_RELATIONSHIP_INTERVENTION)
                actions.append(EscalationAction.MANAGER_REVIEW)
            
            elif reason == EscalationReason.COLLECTION_PROBABILITY_LOW:
                actions.append(EscalationAction.COLLECTIONS_HANDOFF)
                actions.append(EscalationAction.LEGAL_REVIEW)
        
        # Remove duplicates while preserving order
        unique_actions = []
        for action in actions:
            if action not in unique_actions:
                unique_actions.append(action)
        
        return unique_actions
    
    def execute_escalation(
        self,
        campaign: PaymentCampaign,
        reasons: List[EscalationReason],
        actions: List[EscalationAction]
    ) -> Dict[str, Any]:
        """Execute the escalation process for a campaign"""
        escalation_results = {
            "campaign_id": campaign.campaign_id,
            "escalation_timestamp": datetime.utcnow(),
            "reasons": [reason.value for reason in reasons],
            "actions_taken": [],
            "collections_case_id": None,
            "requires_manual_intervention": False,
            "next_review_date": None
        }
        
        # Execute each escalation action
        for action in actions:
            try:
                result = self._execute_escalation_action(campaign, action, reasons)
                escalation_results["actions_taken"].append({
                    "action": action.value,
                    "status": "completed",
                    "result": result
                })
                
                # Store important results
                if action == EscalationAction.COLLECTIONS_HANDOFF:
                    escalation_results["collections_case_id"] = result.get("case_id")
                
            except Exception as e:
                escalation_results["actions_taken"].append({
                    "action": action.value,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Determine if manual intervention is required
        escalation_results["requires_manual_intervention"] = self._requires_manual_intervention(
            campaign, reasons, actions
        )
        
        # Set next review date
        escalation_results["next_review_date"] = self._calculate_next_review_date(
            campaign, actions
        )
        
        # Publish escalation event
        escalation_event = CampaignEscalated(
            campaign_id=campaign.campaign_id,
            customer_id=campaign.customer_id,
            escalation_reasons=reasons,
            escalation_actions=actions,
            escalation_timestamp=escalation_results["escalation_timestamp"],
            collections_case_id=escalation_results["collections_case_id"],
            requires_manual_intervention=escalation_results["requires_manual_intervention"]
        )
        
        # Add event to campaign
        campaign.add_domain_event(escalation_event)
        
        return escalation_results
    
    def get_escalation_metrics(self, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Get escalation metrics for analysis"""
        start_date, end_date = date_range
        escalated_campaigns = self._campaign_repository.find_escalated_campaigns()
        
        # Filter by date range
        filtered_campaigns = [
            campaign for campaign in escalated_campaigns
            if start_date <= campaign.created_at <= end_date
        ]
        
        # Calculate metrics
        total_escalations = len(filtered_campaigns)
        
        # Group by escalation reasons
        reason_counts = {}
        action_counts = {}
        
        for campaign in filtered_campaigns:
            # This would require storing escalation history in the campaign
            # For now, we'll simulate based on campaign state
            if campaign.status.value == "escalated":
                reason_counts["reminder_limit_reached"] = reason_counts.get("reminder_limit_reached", 0) + 1
        
        # Calculate success rates
        successful_escalations = len([
            c for c in filtered_campaigns
            if c.status.value in ["completed", "resolved"]
        ])
        
        success_rate = successful_escalations / total_escalations if total_escalations > 0 else 0.0
        
        return {
            "total_escalations": total_escalations,
            "escalation_reasons": reason_counts,
            "escalation_actions": action_counts,
            "success_rate": success_rate,
            "average_time_to_escalation": self._calculate_average_escalation_time(filtered_campaigns),
            "collections_handoff_rate": self._calculate_collections_handoff_rate(filtered_campaigns)
        }
    
    def recommend_escalation_prevention(self, campaign: PaymentCampaign) -> List[str]:
        """Recommend actions to prevent escalation"""
        recommendations = []
        
        # Analyze campaign risk factors
        should_escalate, reasons = self.evaluate_campaign_for_escalation(campaign)
        
        if not should_escalate:
            return ["No escalation prevention needed - campaign is on track"]
        
        # Provide targeted recommendations based on risk factors
        for reason in reasons:
            if reason == EscalationReason.CUSTOMER_NON_RESPONSIVE:
                recommendations.extend([
                    "Try alternative contact methods (phone, email, SMS)",
                    "Update contact information",
                    "Engage customer relationship manager"
                ])
            
            elif reason == EscalationReason.LARGE_AMOUNT_OVERDUE:
                recommendations.extend([
                    "Offer payment plan immediately",
                    "Provide early payment discount",
                    "Schedule payment negotiation call"
                ])
            
            elif reason == EscalationReason.HIGH_RISK_CUSTOMER:
                recommendations.extend([
                    "Require payment guarantee or collateral",
                    "Implement stricter payment terms",
                    "Consider credit insurance"
                ])
        
        return list(set(recommendations))  # Remove duplicates
    
    # Private helper methods
    
    def _check_reminder_limit_reached(self, campaign: PaymentCampaign) -> bool:
        """Check if reminder limit has been reached"""
        return campaign.reminder_count >= self._max_reminder_attempts
    
    def _check_customer_non_responsive(self, campaign: PaymentCampaign) -> bool:
        """Check if customer has been non-responsive"""
        if not campaign.reminders:
            return False
        
        last_reminder = max(campaign.reminders, key=lambda r: r.sent_at)
        days_since_last = (datetime.utcnow() - last_reminder.sent_at).days
        
        return days_since_last >= self._non_responsive_days and not last_reminder.was_opened
    
    def _check_high_risk_customer(self, campaign: PaymentCampaign) -> bool:
        """Check if customer is high risk"""
        # This would integrate with customer risk assessment
        # For now, simulate based on campaign characteristics
        return (campaign.total_amount.amount > 10000 and 
                campaign.reminder_count > 1 and
                len([r for r in campaign.reminders if r.was_opened]) == 0)
    
    def _check_large_amount_overdue(self, campaign: PaymentCampaign) -> bool:
        """Check if large amount is overdue"""
        return campaign.total_amount.amount >= self._escalation_amount_threshold
    
    def _check_multiple_invoices_overdue(self, campaign: PaymentCampaign) -> bool:
        """Check if multiple invoices are overdue for same customer"""
        customer_campaigns = self._campaign_repository.find_active_campaigns_by_customer(
            campaign.customer_id
        )
        return len(customer_campaigns) >= self._multiple_invoices_threshold
    
    def _check_low_collection_probability(self, campaign: PaymentCampaign) -> bool:
        """Check if collection probability is low"""
        # Simplified probability calculation
        base_prob = 0.8
        days_penalty = min(campaign.days_active * 0.01, 0.3)
        reminder_penalty = campaign.reminder_count * 0.1
        
        probability = base_prob - days_penalty - reminder_penalty
        
        return probability < 0.4
    
    def _check_payment_disputes(self, campaign: PaymentCampaign) -> bool:
        """Check if there are payment disputes"""
        # This would check for dispute flags in the campaign
        return any(note.content.lower().find("dispute") >= 0 for note in campaign.collection_notes)
    
    def _execute_escalation_action(
        self,
        campaign: PaymentCampaign,
        action: EscalationAction,
        reasons: List[EscalationReason]
    ) -> Dict[str, Any]:
        """Execute a specific escalation action"""
        
        if action == EscalationAction.COLLECTIONS_HANDOFF:
            # Create collections case
            primary_reason = reasons[0] if reasons else EscalationReason.REMINDER_LIMIT_REACHED
            case_id = self._collections_service.create_collections_case(campaign, primary_reason)
            
            # Transfer campaign data
            success = self._collections_service.transfer_campaign_data(campaign, case_id)
            
            return {
                "case_id": case_id,
                "transfer_success": success,
                "handoff_timestamp": datetime.utcnow()
            }
        
        elif action == EscalationAction.MANAGER_REVIEW:
            return {
                "review_assigned": True,
                "priority": "high" if EscalationReason.LARGE_AMOUNT_OVERDUE in reasons else "medium",
                "review_deadline": datetime.utcnow() + timedelta(days=2)
            }
        
        elif action == EscalationAction.CREDIT_HOLD:
            return {
                "credit_hold_applied": True,
                "hold_timestamp": datetime.utcnow(),
                "hold_reason": "overdue_payments"
            }
        
        # Add other action implementations as needed
        return {"action_completed": True}
    
    def _requires_manual_intervention(
        self,
        campaign: PaymentCampaign,
        reasons: List[EscalationReason],
        actions: List[EscalationAction]
    ) -> bool:
        """Determine if manual intervention is required"""
        manual_reasons = [
            EscalationReason.PAYMENT_DISPUTES,
            EscalationReason.HIGH_RISK_CUSTOMER,
            EscalationReason.LARGE_AMOUNT_OVERDUE
        ]
        
        manual_actions = [
            EscalationAction.LEGAL_REVIEW,
            EscalationAction.CUSTOMER_RELATIONSHIP_INTERVENTION,
            EscalationAction.PAYMENT_PLAN_NEGOTIATION
        ]
        
        return (any(reason in manual_reasons for reason in reasons) or
                any(action in manual_actions for action in actions))
    
    def _calculate_next_review_date(
        self,
        campaign: PaymentCampaign,
        actions: List[EscalationAction]
    ) -> datetime:
        """Calculate when to next review the escalated campaign"""
        base_days = 7  # Default weekly review
        
        if EscalationAction.LEGAL_REVIEW in actions:
            base_days = 14  # Legal reviews take longer
        elif EscalationAction.COLLECTIONS_HANDOFF in actions:
            base_days = 30  # Collections process takes time
        elif EscalationAction.MANAGER_REVIEW in actions:
            base_days = 3   # Manager reviews are urgent
        
        return datetime.utcnow() + timedelta(days=base_days)
    
    def _calculate_average_escalation_time(self, campaigns: List[PaymentCampaign]) -> float:
        """Calculate average time from campaign start to escalation"""
        if not campaigns:
            return 0.0
        
        total_days = sum(campaign.days_active for campaign in campaigns)
        return total_days / len(campaigns)
    
    def _calculate_collections_handoff_rate(self, campaigns: List[PaymentCampaign]) -> float:
        """Calculate percentage of escalations that go to collections"""
        if not campaigns:
            return 0.0
        
        # This would require tracking escalation actions in campaign history
        # For now, estimate based on campaign characteristics
        collections_handoffs = len([
            c for c in campaigns
            if c.status.value == "escalated" and c.total_amount.amount > 5000
        ])
        
        return collections_handoffs / len(campaigns)