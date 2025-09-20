"""
Overdue Payment Service for Payment Intelligence Domain

Domain service responsible for identifying, prioritizing, and managing
overdue invoices for payment collection campaigns.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from ..entities.overdue_invoice import OverdueInvoice, PaymentPriority
from ..value_objects.payment_value_objects import PaymentStatus, Money, ReminderLevel


class IInvoiceRepository(ABC):
    """Interface for invoice repository"""
    
    @abstractmethod
    def find_overdue_invoices(self, customer_id: Optional[str] = None) -> List[OverdueInvoice]:
        pass
    
    @abstractmethod
    def find_by_id(self, invoice_id: str) -> Optional[OverdueInvoice]:
        pass


class ICustomerRepository(ABC):
    """Interface for customer repository"""
    
    @abstractmethod
    def get_customer_payment_history(self, customer_id: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def get_customer_risk_profile(self, customer_id: str) -> Dict[str, Any]:
        pass


class OverduePaymentService:
    """
    Domain service for managing overdue payment detection and prioritization.
    
    This service contains business logic that spans multiple aggregates and
    doesn't belong to any single aggregate root.
    """
    
    def __init__(self, invoice_repository: IInvoiceRepository, customer_repository: ICustomerRepository):
        self._invoice_repository = invoice_repository
        self._customer_repository = customer_repository
        
        # Business rules configuration
        self._high_priority_threshold = Money(5000.0, "USD")
        self._critical_days_overdue = 30
        self._risk_score_threshold = 0.7
        self._vip_customer_threshold = Money(100000.0, "USD")  # Annual volume
    
    def identify_overdue_invoices(self, customer_id: Optional[str] = None) -> List[OverdueInvoice]:
        """Identify all overdue invoices, optionally filtered by customer"""
        all_overdue = self._invoice_repository.find_overdue_invoices(customer_id)
        
        # Filter to only actionable overdue invoices
        actionable_invoices = [
            invoice for invoice in all_overdue
            if invoice.payment_status.is_actionable() and invoice.payment_status.is_collectible()
        ]
        
        return actionable_invoices
    
    def prioritize_overdue_invoices(self, invoices: List[OverdueInvoice]) -> List[OverdueInvoice]:
        """Prioritize overdue invoices based on business rules"""
        prioritized_invoices = []
        
        for invoice in invoices:
            # Calculate priority score
            priority_score = self._calculate_priority_score(invoice)
            
            # Store priority score in invoice for sorting
            invoice._priority_score = priority_score
            prioritized_invoices.append(invoice)
        
        # Sort by priority score (highest first)
        prioritized_invoices.sort(key=lambda inv: inv._priority_score, reverse=True)
        
        return prioritized_invoices
    
    def get_collection_recommendations(self, invoice: OverdueInvoice) -> List[str]:
        """Get AI-powered collection recommendations for an invoice"""
        recommendations = []
        
        # Get customer history
        customer_history = self._customer_repository.get_customer_payment_history(invoice.customer_id)
        customer_risk = self._customer_repository.get_customer_risk_profile(invoice.customer_id)
        
        # Days overdue analysis
        days_overdue = invoice.days_overdue
        
        if days_overdue <= 7:
            recommendations.extend(self._get_early_stage_recommendations(invoice, customer_history))
        elif days_overdue <= 14:
            recommendations.extend(self._get_middle_stage_recommendations(invoice, customer_history))
        elif days_overdue <= 30:
            recommendations.extend(self._get_late_stage_recommendations(invoice, customer_history))
        else:
            recommendations.extend(self._get_critical_stage_recommendations(invoice, customer_history))
        
        # Amount-based recommendations
        if invoice.current_balance.amount >= self._high_priority_threshold.amount:
            recommendations.append("high_value_escalation")
            recommendations.append("manager_review_required")
        
        # Customer risk-based recommendations
        if customer_risk.get("risk_score", 0.0) > self._risk_score_threshold:
            recommendations.append("high_risk_customer_protocol")
            recommendations.append("require_payment_guarantee")
        
        # Payment history analysis
        payment_patterns = customer_history.get("payment_patterns", {})
        
        if payment_patterns.get("typically_pays_late", False):
            recommendations.append("schedule_follow_up_reminders")
        
        if payment_patterns.get("responds_to_phone_calls", False):
            recommendations.append("phone_contact_preferred")
        
        if payment_patterns.get("prefers_payment_plans", False):
            recommendations.append("offer_payment_plan_early")
        
        # Remove duplicates and return
        return list(set(recommendations))
    
    def calculate_collection_urgency(self, invoice: OverdueInvoice) -> Tuple[str, float]:
        """Calculate urgency level and score for collection efforts"""
        urgency_score = 0.0
        
        # Days overdue factor (0-40 points)
        days_factor = min(invoice.days_overdue / 30.0, 1.0) * 40
        urgency_score += days_factor
        
        # Amount factor (0-30 points)
        amount_factor = min(invoice.current_balance.amount / 10000.0, 1.0) * 30
        urgency_score += amount_factor
        
        # Customer risk factor (0-20 points)
        customer_risk = self._customer_repository.get_customer_risk_profile(invoice.customer_id)
        risk_factor = customer_risk.get("risk_score", 0.0) * 20
        urgency_score += risk_factor
        
        # Reminder attempts factor (0-10 points)
        reminder_factor = min(invoice.reminder_count / 3.0, 1.0) * 10
        urgency_score += reminder_factor
        
        # Determine urgency level
        if urgency_score >= 80:
            urgency_level = "critical"
        elif urgency_score >= 60:
            urgency_level = "high"
        elif urgency_score >= 40:
            urgency_level = "medium"
        else:
            urgency_level = "low"
        
        return urgency_level, urgency_score
    
    def should_escalate_to_collections(self, invoice: OverdueInvoice) -> bool:
        """Determine if an invoice should be escalated to collections"""
        # Check basic escalation criteria
        if invoice.requires_escalation():
            return True
        
        # Check if customer is high risk
        customer_risk = self._customer_repository.get_customer_risk_profile(invoice.customer_id)
        if customer_risk.get("risk_score", 0.0) > 0.8:
            return True
        
        # Check if multiple invoices are overdue for same customer
        customer_overdue = self._invoice_repository.find_overdue_invoices(invoice.customer_id)
        if len(customer_overdue) >= 3:
            return True
        
        # Check if amount is significant and overdue for too long
        if (invoice.current_balance.amount >= 5000 and 
            invoice.days_overdue >= 21):
            return True
        
        return False
    
    def get_next_reminder_level(self, invoice: OverdueInvoice) -> Optional[ReminderLevel]:
        """Determine the next appropriate reminder level"""
        current_level = invoice.current_reminder_level
        
        # Check if we should escalate instead
        if self.should_escalate_to_collections(invoice):
            return ReminderLevel.ESCALATED
        
        # Get next level in sequence
        next_level = current_level.next_level()
        
        # Business rule: VIP customers get extra reminder before escalation
        customer_history = self._customer_repository.get_customer_payment_history(invoice.customer_id)
        annual_volume = customer_history.get("annual_volume", Money(0.0, "USD"))
        
        if (annual_volume.amount >= self._vip_customer_threshold.amount and
            current_level == ReminderLevel.THIRD):
            # Give VIP customer additional time before escalation
            return None  # Don't escalate immediately
        
        return next_level
    
    def estimate_collection_probability(self, invoice: OverdueInvoice) -> float:
        """Estimate probability of successful collection (0.0 to 1.0)"""
        base_probability = 0.8  # Start with 80% base probability
        
        # Adjust based on days overdue
        days_penalty = min(invoice.days_overdue * 0.01, 0.3)  # Max 30% penalty
        base_probability -= days_penalty
        
        # Adjust based on customer payment history
        customer_history = self._customer_repository.get_customer_payment_history(invoice.customer_id)
        payment_rate = customer_history.get("on_time_payment_rate", 0.7)
        base_probability = (base_probability + payment_rate) / 2
        
        # Adjust based on reminder responses
        if invoice.reminder_count > 0:
            # If reminders haven't been effective, reduce probability
            response_rate = customer_history.get("reminder_response_rate", 0.5)
            base_probability *= (0.8 + response_rate * 0.2)
        
        # Adjust based on amount (larger amounts may be harder to collect)
        if invoice.current_balance.amount > 10000:
            base_probability *= 0.9
        elif invoice.current_balance.amount > 50000:
            base_probability *= 0.8
        
        # Ensure probability is within valid range
        return max(0.0, min(1.0, base_probability))
    
    def _calculate_priority_score(self, invoice: OverdueInvoice) -> float:
        """Calculate priority score for invoice ranking"""
        score = 0.0
        
        # Amount weight (40% of score)
        amount_score = min(invoice.current_balance.amount / 10000.0, 1.0) * 40
        score += amount_score
        
        # Days overdue weight (30% of score)
        days_score = min(invoice.days_overdue / 30.0, 1.0) * 30
        score += days_score
        
        # Customer risk weight (20% of score)
        customer_risk = self._customer_repository.get_customer_risk_profile(invoice.customer_id)
        risk_score = customer_risk.get("risk_score", 0.0) * 20
        score += risk_score
        
        # Collection probability weight (10% of score)
        collection_prob = self.estimate_collection_probability(invoice)
        prob_score = collection_prob * 10
        score += prob_score
        
        return score
    
    def _get_early_stage_recommendations(self, invoice: OverdueInvoice, customer_history: Dict) -> List[str]:
        """Get recommendations for early stage collection (1-7 days overdue)"""
        return [
            "send_friendly_reminder",
            "check_payment_processing_delays",
            "verify_contact_information",
            "offer_automatic_payment_setup"
        ]
    
    def _get_middle_stage_recommendations(self, invoice: OverdueInvoice, customer_history: Dict) -> List[str]:
        """Get recommendations for middle stage collection (8-14 days overdue)"""
        return [
            "send_second_reminder",
            "include_payment_options",
            "offer_payment_plan",
            "request_payment_commitment_date"
        ]
    
    def _get_late_stage_recommendations(self, invoice: OverdueInvoice, customer_history: Dict) -> List[str]:
        """Get recommendations for late stage collection (15-30 days overdue)"""
        return [
            "send_urgent_reminder",
            "request_immediate_payment",
            "offer_settlement_discount",
            "schedule_payment_plan_call",
            "document_collection_efforts"
        ]
    
    def _get_critical_stage_recommendations(self, invoice: OverdueInvoice, customer_history: Dict) -> List[str]:
        """Get recommendations for critical stage collection (30+ days overdue)"""
        return [
            "prepare_escalation_documentation",
            "final_demand_notice",
            "legal_review_recommended",
            "consider_collection_agency",
            "account_hold_procedures"
        ]