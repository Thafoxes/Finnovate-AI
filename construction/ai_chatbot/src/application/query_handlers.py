"""
Query Handlers for Payment Intelligence Application

Query handlers retrieve and aggregate data from repositories
and domain services to fulfill information requests.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .queries import *
from ..domain.services.overdue_payment_service import OverduePaymentService
from ..domain.services.alternative_payment_service import AlternativePaymentService


# Read Model Interfaces (Infrastructure concerns)

class IPaymentCampaignReadRepository:
    def get_campaigns(
        self, 
        customer_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]: pass
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]: pass


class IOverdueInvoiceReadRepository:
    def get_overdue_invoices(
        self,
        customer_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]: pass


class IConversationReadRepository:
    def get_conversations(
        self,
        customer_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]: pass


class ICustomerDataService:
    def get_customer_profile(self, customer_id: str) -> Dict[str, Any]: pass
    
    def get_payment_history(self, customer_id: str) -> Dict[str, Any]: pass


class IAnalyticsService:
    def get_collection_metrics(
        self,
        date_range: tuple,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]: pass


# Query Handlers

class GetOverdueInvoicesHandler:
    """Handles queries for overdue invoices"""
    
    def __init__(
        self,
        invoice_read_repository: IOverdueInvoiceReadRepository,
        overdue_payment_service: OverduePaymentService
    ):
        self._invoice_repository = invoice_read_repository
        self._overdue_payment_service = overdue_payment_service
    
    def handle(self, query: GetOverdueInvoicesQuery) -> OverdueInvoicesResult:
        """Handle overdue invoices query"""
        
        # Build filters
        filters = {}
        if query.minimum_amount:
            filters["minimum_amount"] = query.minimum_amount.amount
        if query.days_overdue_min:
            filters["days_overdue_min"] = query.days_overdue_min
        if query.days_overdue_max:
            filters["days_overdue_max"] = query.days_overdue_max
        if query.payment_status:
            filters["payment_status"] = query.payment_status
        
        # Get invoices from repository
        invoices_data = self._invoice_repository.get_overdue_invoices(
            customer_id=query.customer_id,
            filters=filters,
            limit=query.limit,
            offset=query.offset
        )
        
        # Calculate aggregated metrics
        total_amount = sum(inv["current_balance"] for inv in invoices_data)
        total_count = len(invoices_data)
        average_days_overdue = (
            sum(inv["days_overdue"] for inv in invoices_data) / total_count
            if total_count > 0 else 0
        )
        
        # Priority breakdown
        priority_breakdown = {"high": 0, "medium": 0, "low": 0}
        for invoice_data in invoices_data:
            priority = invoice_data.get("priority", "medium")
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
        
        return OverdueInvoicesResult(
            invoices=invoices_data,
            total_count=total_count,
            total_amount=Money(total_amount, "USD"),
            average_days_overdue=average_days_overdue,
            priority_breakdown=priority_breakdown
        )


class GetPaymentCampaignsHandler:
    """Handles queries for payment campaigns"""
    
    def __init__(self, campaign_read_repository: IPaymentCampaignReadRepository):
        self._campaign_repository = campaign_read_repository
    
    def handle(self, query: GetPaymentCampaignsQuery) -> PaymentCampaignsResult:
        """Handle payment campaigns query"""
        
        # Get campaigns from repository
        campaigns_data = self._campaign_repository.get_campaigns(
            customer_id=query.customer_id,
            status=query.campaign_status,
            limit=query.limit,
            offset=query.offset
        )
        
        # Calculate aggregated metrics
        total_count = len(campaigns_data)
        total_amount = sum(camp["total_amount"] for camp in campaigns_data)
        
        # Status breakdown
        status_breakdown = {}
        for campaign in campaigns_data:
            status = campaign["status"]
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Calculate success rate
        completed_campaigns = status_breakdown.get("completed", 0)
        success_rate = completed_campaigns / total_count if total_count > 0 else 0.0
        
        return PaymentCampaignsResult(
            campaigns=campaigns_data,
            total_count=total_count,
            status_breakdown=status_breakdown,
            total_amount_in_campaigns=Money(total_amount, "USD"),
            success_rate=success_rate
        )


class GetCampaignDetailsHandler:
    """Handles detailed campaign information queries"""
    
    def __init__(
        self,
        campaign_read_repository: IPaymentCampaignReadRepository,
        overdue_payment_service: OverduePaymentService
    ):
        self._campaign_repository = campaign_read_repository
        self._overdue_payment_service = overdue_payment_service
    
    def handle(self, query: GetCampaignDetailsQuery) -> CampaignDetailsResult:
        """Handle campaign details query"""
        
        # Get campaign details
        campaign_data = self._campaign_repository.get_campaign_details(query.campaign_id)
        if not campaign_data:
            raise ValueError(f"Campaign {query.campaign_id} not found")
        
        # Get related data based on query flags
        reminders = campaign_data.get("reminders", []) if query.include_reminders else []
        payments = campaign_data.get("payments", []) if query.include_payments else []
        notes = campaign_data.get("notes", []) if query.include_notes else []
        
        # Build timeline
        timeline = self._build_campaign_timeline(campaign_data, reminders, payments, notes)
        
        # Generate AI recommendations
        ai_recommendations = self._generate_campaign_recommendations(campaign_data)
        
        return CampaignDetailsResult(
            campaign=campaign_data,
            reminders=reminders,
            payments=payments,
            notes=notes,
            timeline=timeline,
            ai_recommendations=ai_recommendations
        )
    
    def _build_campaign_timeline(
        self,
        campaign: Dict[str, Any],
        reminders: List[Dict[str, Any]],
        payments: List[Dict[str, Any]],
        notes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build chronological timeline of campaign events"""
        
        timeline_events = []
        
        # Add campaign creation
        timeline_events.append({
            "date": campaign["created_at"],
            "type": "campaign_created",
            "description": f"Campaign created for {len(campaign.get('invoice_ids', []))} invoices",
            "details": {"total_amount": campaign["total_amount"]}
        })
        
        # Add reminders
        for reminder in reminders:
            timeline_events.append({
                "date": reminder["sent_at"],
                "type": "reminder_sent",
                "description": f"{reminder['reminder_level']} reminder sent",
                "details": reminder
            })
        
        # Add payments
        for payment in payments:
            timeline_events.append({
                "date": payment["payment_date"],
                "type": "payment_received",
                "description": f"Payment of {payment['amount']} received",
                "details": payment
            })
        
        # Add notes
        for note in notes:
            timeline_events.append({
                "date": note["created_at"],
                "type": "note_added",
                "description": f"Note: {note['content'][:50]}...",
                "details": note
            })
        
        # Sort by date
        timeline_events.sort(key=lambda x: x["date"])
        
        return timeline_events
    
    def _generate_campaign_recommendations(self, campaign_data: Dict[str, Any]) -> List[str]:
        """Generate AI recommendations for campaign"""
        
        recommendations = []
        
        # Analyze campaign status
        status = campaign_data.get("status", "active")
        days_active = (datetime.utcnow() - campaign_data["created_at"]).days
        reminder_count = len(campaign_data.get("reminders", []))
        
        if status == "active" and days_active > 14 and reminder_count < 2:
            recommendations.append("Consider sending follow-up reminder")
        
        if status == "active" and days_active > 30:
            recommendations.append("Evaluate for escalation to collections")
        
        if reminder_count > 2 and not campaign_data.get("payments"):
            recommendations.append("Consider alternative payment options or settlement offer")
        
        total_amount = campaign_data.get("total_amount", 0)
        if total_amount > 5000:
            recommendations.append("High-value campaign - consider personal outreach")
        
        return recommendations


class GetCustomerPaymentHistoryHandler:
    """Handles customer payment history queries"""
    
    def __init__(
        self,
        customer_data_service: ICustomerDataService,
        overdue_payment_service: OverduePaymentService
    ):
        self._customer_data_service = customer_data_service
        self._overdue_payment_service = overdue_payment_service
    
    def handle(self, query: GetCustomerPaymentHistoryQuery) -> CustomerPaymentHistoryResult:
        """Handle customer payment history query"""
        
        # Get customer profile and payment history
        customer_profile = self._customer_data_service.get_customer_profile(query.customer_id)
        payment_history = self._customer_data_service.get_payment_history(query.customer_id)
        
        # Analyze payment patterns
        payment_patterns = self._analyze_payment_patterns(payment_history)
        
        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(customer_profile, payment_history)
        
        # Get dispute history if requested
        dispute_history = []
        if query.include_disputes:
            dispute_history = payment_history.get("disputes", [])
        
        return CustomerPaymentHistoryResult(
            customer_id=query.customer_id,
            payment_summary=payment_history.get("summary", {}),
            payment_timeline=payment_history.get("timeline", []),
            payment_patterns=payment_patterns,
            risk_assessment=risk_assessment,
            dispute_history=dispute_history
        )
    
    def _analyze_payment_patterns(self, payment_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze customer payment patterns"""
        
        payments = payment_history.get("payments", [])
        if not payments:
            return {"insufficient_data": True}
        
        # Calculate average payment time
        payment_delays = []
        for payment in payments:
            if payment.get("due_date") and payment.get("payment_date"):
                delay = (payment["payment_date"] - payment["due_date"]).days
                payment_delays.append(delay)
        
        avg_delay = sum(payment_delays) / len(payment_delays) if payment_delays else 0
        
        # Analyze payment methods
        payment_methods = {}
        for payment in payments:
            method = payment.get("payment_method", "unknown")
            payment_methods[method] = payment_methods.get(method, 0) + 1
        
        # Analyze payment amounts
        avg_payment = sum(p.get("amount", 0) for p in payments) / len(payments)
        
        return {
            "average_payment_delay_days": avg_delay,
            "on_time_payment_rate": len([d for d in payment_delays if d <= 0]) / len(payment_delays) if payment_delays else 0,
            "preferred_payment_methods": payment_methods,
            "average_payment_amount": avg_payment,
            "payment_frequency": len(payments) / 12,  # payments per month over last year
            "typically_pays_late": avg_delay > 5,
            "reliable_payer": avg_delay <= 5 and len(payment_delays) > 3
        }
    
    def _generate_risk_assessment(
        self,
        customer_profile: Dict[str, Any],
        payment_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customer risk assessment"""
        
        risk_score = 0.5  # Base risk score
        risk_factors = []
        
        # Analyze payment history
        patterns = self._analyze_payment_patterns(payment_history)
        
        if patterns.get("typically_pays_late", False):
            risk_score += 0.2
            risk_factors.append("Typically pays late")
        
        if patterns.get("on_time_payment_rate", 1.0) < 0.7:
            risk_score += 0.15
            risk_factors.append("Low on-time payment rate")
        
        # Analyze business factors
        if customer_profile.get("credit_score", 700) < 600:
            risk_score += 0.2
            risk_factors.append("Low credit score")
        
        if customer_profile.get("financial_hardship", False):
            risk_score += 0.25
            risk_factors.append("Reported financial hardship")
        
        # Cap risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "high"
        elif risk_score >= 0.6:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "credit_limit_recommendation": self._calculate_credit_limit(risk_score, customer_profile),
            "collection_probability": 1.0 - risk_score,
            "recommended_payment_terms": self._recommend_payment_terms(risk_score)
        }
    
    def _calculate_credit_limit(self, risk_score: float, customer_profile: Dict[str, Any]) -> float:
        """Calculate recommended credit limit"""
        base_limit = customer_profile.get("annual_revenue", 100000) * 0.1
        risk_adjustment = 1.0 - (risk_score * 0.5)  # Reduce by up to 50% based on risk
        return base_limit * risk_adjustment
    
    def _recommend_payment_terms(self, risk_score: float) -> str:
        """Recommend payment terms based on risk"""
        if risk_score >= 0.8:
            return "Cash on delivery or prepayment required"
        elif risk_score >= 0.6:
            return "Net 15 days with credit application"
        elif risk_score >= 0.4:
            return "Net 30 days standard terms"
        else:
            return "Net 30-45 days extended terms available"


class GetPaymentRecommendationsHandler:
    """Handles AI payment recommendation queries"""
    
    def __init__(
        self,
        alternative_payment_service: AlternativePaymentService,
        customer_data_service: ICustomerDataService
    ):
        self._alternative_payment_service = alternative_payment_service
        self._customer_data_service = customer_data_service
    
    def handle(self, query: GetPaymentRecommendationsQuery) -> PaymentRecommendationsResult:
        """Handle payment recommendations query"""
        
        recommendations = []
        confidence_scores = {}
        
        if query.invoice_id:
            # Get specific invoice recommendations
            invoice_recs = self._get_invoice_recommendations(query.invoice_id, query)
            recommendations.extend(invoice_recs["recommendations"])
            confidence_scores.update(invoice_recs["confidence_scores"])
        
        elif query.customer_id:
            # Get customer-level recommendations
            customer_recs = self._get_customer_recommendations(query.customer_id, query)
            recommendations.extend(customer_recs["recommendations"])
            confidence_scores.update(customer_recs["confidence_scores"])
        
        # Generate expected outcomes
        expected_outcomes = self._calculate_expected_outcomes(recommendations)
        
        # Generate alternative strategies
        alternative_strategies = self._generate_alternative_strategies(recommendations)
        
        return PaymentRecommendationsResult(
            recommendations=recommendations,
            confidence_scores=confidence_scores,
            expected_outcomes=expected_outcomes,
            alternative_strategies=alternative_strategies
        )
    
    def _get_invoice_recommendations(
        self,
        invoice_id: str,
        query: GetPaymentRecommendationsQuery
    ) -> Dict[str, Any]:
        """Get recommendations for specific invoice"""
        
        # This would typically load the invoice and generate recommendations
        # Simplified implementation
        recommendations = [
            {
                "type": "payment_plan",
                "description": "6-month installment plan",
                "parameters": {"installments": 6, "monthly_payment": 500},
                "expected_success_rate": 0.75
            },
            {
                "type": "settlement_discount",
                "description": "10% early payment discount",
                "parameters": {"discount_rate": 0.10, "deadline_days": 14},
                "expected_success_rate": 0.65
            }
        ]
        
        confidence_scores = {
            "payment_plan": 0.8,
            "settlement_discount": 0.7
        }
        
        return {
            "recommendations": recommendations,
            "confidence_scores": confidence_scores
        }
    
    def _get_customer_recommendations(
        self,
        customer_id: str,
        query: GetPaymentRecommendationsQuery
    ) -> Dict[str, Any]:
        """Get recommendations for customer overall"""
        
        customer_profile = self._customer_data_service.get_customer_profile(customer_id)
        
        recommendations = [
            {
                "type": "account_review",
                "description": "Schedule account review meeting",
                "parameters": {"urgency": "medium", "recommended_by": "ai_system"},
                "expected_success_rate": 0.85
            }
        ]
        
        confidence_scores = {"account_review": 0.9}
        
        return {
            "recommendations": recommendations,
            "confidence_scores": confidence_scores
        }
    
    def _calculate_expected_outcomes(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate expected outcomes for recommendations"""
        
        if not recommendations:
            return {}
        
        avg_success_rate = sum(r.get("expected_success_rate", 0.5) for r in recommendations) / len(recommendations)
        
        return {
            "average_success_rate": avg_success_rate,
            "recommended_approach": recommendations[0]["type"] if recommendations else None,
            "estimated_collection_improvement": avg_success_rate * 0.2,  # 20% improvement estimate
            "time_to_resolution_days": 30  # Average estimate
        }
    
    def _generate_alternative_strategies(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate alternative strategies"""
        
        alternatives = [
            {
                "strategy": "escalation_path",
                "description": "Escalate to collections if no response in 14 days",
                "conditions": ["no_customer_response", "amount_over_threshold"]
            },
            {
                "strategy": "relationship_management",
                "description": "Engage customer relationship manager for personal outreach",
                "conditions": ["high_value_customer", "long_term_relationship"]
            }
        ]
        
        return alternatives


class GetDashboardSummaryHandler:
    """Handles dashboard summary queries"""
    
    def __init__(
        self,
        campaign_read_repository: IPaymentCampaignReadRepository,
        invoice_read_repository: IOverdueInvoiceReadRepository,
        analytics_service: IAnalyticsService
    ):
        self._campaign_repository = campaign_read_repository
        self._invoice_repository = invoice_read_repository
        self._analytics_service = analytics_service
    
    def handle(self, query: GetDashboardSummaryQuery) -> DashboardSummaryResult:
        """Handle dashboard summary query"""
        
        # Date range for analysis
        end_date = query.date_range_end or datetime.utcnow()
        start_date = query.date_range_start or (end_date - timedelta(days=30))
        
        # Get key metrics
        key_metrics = self._get_key_metrics(start_date, end_date)
        
        # Get recent activities
        recent_activities = self._get_recent_activities(query.user_id)
        
        # Get alerts and notifications
        alerts = self._get_alerts_and_notifications(query.user_id) if query.include_alerts else []
        
        # Get performance trends
        trends = self._get_performance_trends(start_date, end_date) if query.include_trends else {}
        
        # Get upcoming tasks
        upcoming_tasks = self._get_upcoming_tasks(query.user_id)
        
        return DashboardSummaryResult(
            key_metrics=key_metrics,
            recent_activities=recent_activities,
            alerts_and_notifications=alerts,
            performance_trends=trends,
            upcoming_tasks=upcoming_tasks
        )
    
    def _get_key_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get key performance metrics"""
        
        # Get overdue invoices
        overdue_invoices = self._invoice_repository.get_overdue_invoices(limit=1000)
        total_overdue = sum(inv["current_balance"] for inv in overdue_invoices)
        
        # Get active campaigns
        active_campaigns = self._campaign_repository.get_campaigns(status="active", limit=1000)
        
        # Get collection metrics
        collection_metrics = self._analytics_service.get_collection_metrics(
            (start_date, end_date)
        )
        
        return {
            "total_overdue_amount": total_overdue,
            "overdue_invoice_count": len(overdue_invoices),
            "active_campaigns": len(active_campaigns),
            "collection_rate": collection_metrics.get("collection_rate", 0.0),
            "average_days_to_collection": collection_metrics.get("avg_collection_days", 0),
            "escalation_rate": collection_metrics.get("escalation_rate", 0.0)
        }
    
    def _get_recent_activities(self, user_id: str) -> List[Dict[str, Any]]:
        """Get recent user activities"""
        
        # This would typically query activity logs
        return [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "activity": "Campaign created for Customer ABC Corp",
                "type": "campaign_created",
                "entity_id": "camp_123"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(hours=4),
                "activity": "Payment received for Invoice #INV-456",
                "type": "payment_received",
                "entity_id": "inv_456"
            }
        ]
    
    def _get_alerts_and_notifications(self, user_id: str) -> List[Dict[str, Any]]:
        """Get alerts and notifications"""
        
        return [
            {
                "id": "alert_1",
                "type": "escalation_required",
                "message": "Campaign CAMP-789 requires escalation review",
                "priority": "high",
                "created_at": datetime.utcnow() - timedelta(hours=1)
            }
        ]
    
    def _get_performance_trends(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance trend data"""
        
        return {
            "collection_rate_trend": [
                {"date": start_date + timedelta(days=i), "value": 0.75 + (i * 0.01)}
                for i in range(0, (end_date - start_date).days, 7)
            ],
            "overdue_amount_trend": [
                {"date": start_date + timedelta(days=i), "value": 50000 - (i * 1000)}
                for i in range(0, (end_date - start_date).days, 7)
            ]
        }
    
    def _get_upcoming_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get upcoming tasks for user"""
        
        return [
            {
                "id": "task_1",
                "type": "follow_up_call",
                "description": "Follow up with Customer XYZ Corp on payment plan",
                "due_date": datetime.utcnow() + timedelta(days=1),
                "priority": "medium"
            }
        ]