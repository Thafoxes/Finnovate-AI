"""
Queries for Payment Intelligence Application

Queries represent requests to retrieve information from the system.
They follow the CQRS pattern and are handled by query handlers.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..domain.value_objects.payment_value_objects import Money


@dataclass(frozen=True)
class GetOverdueInvoicesQuery:
    """Query to get overdue invoices with optional filtering"""
    customer_id: Optional[str] = None
    minimum_amount: Optional[Money] = None
    days_overdue_min: Optional[int] = None
    days_overdue_max: Optional[int] = None
    payment_status: Optional[str] = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True)
class GetPaymentCampaignsQuery:
    """Query to get payment campaigns with filtering"""
    customer_id: Optional[str] = None
    campaign_status: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    assigned_to: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetCampaignDetailsQuery:
    """Query to get detailed information about a specific campaign"""
    campaign_id: str
    include_reminders: bool = True
    include_payments: bool = True
    include_notes: bool = True


@dataclass(frozen=True)
class GetCustomerPaymentHistoryQuery:
    """Query to get customer payment history and analytics"""
    customer_id: str
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    include_disputes: bool = True
    include_payment_plans: bool = True


@dataclass(frozen=True)
class GetConversationHistoryQuery:
    """Query to get conversation history for a customer"""
    customer_id: Optional[str] = None
    conversation_id: Optional[str] = None
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    conversation_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetActiveConversationsQuery:
    """Query to get currently active conversations"""
    assigned_to: Optional[str] = None
    conversation_status: Optional[str] = None
    priority_level: Optional[str] = None
    escalation_required: bool = False
    limit: int = 25


@dataclass(frozen=True)
class GetPaymentRecommendationsQuery:
    """Query to get AI-powered payment recommendations"""
    customer_id: Optional[str] = None
    invoice_id: Optional[str] = None
    recommendation_type: Optional[str] = None  # "payment_plan", "settlement", "escalation"
    include_probability_scores: bool = True


@dataclass(frozen=True)
class GetCollectionMetricsQuery:
    """Query to get collection performance metrics"""
    date_range_start: datetime
    date_range_end: datetime
    group_by: str = "month"  # "day", "week", "month", "quarter"
    metric_types: List[str] = None  # ["collection_rate", "response_rate", "escalation_rate"]
    customer_segment: Optional[str] = None


@dataclass(frozen=True)
class GetEscalatedCasesQuery:
    """Query to get escalated payment cases"""
    escalation_level: Optional[str] = None
    assigned_to: Optional[str] = None
    escalation_reason: Optional[str] = None
    date_escalated_after: Optional[datetime] = None
    requires_action: bool = False
    limit: int = 50


@dataclass(frozen=True)
class GetSettlementOffersQuery:
    """Query to get settlement offers with filtering"""
    customer_id: Optional[str] = None
    offer_status: Optional[str] = None  # "pending", "accepted", "rejected", "expired"
    created_after: Optional[datetime] = None
    minimum_discount: Optional[float] = None
    requires_approval: Optional[bool] = None
    limit: int = 50


@dataclass(frozen=True)
class GetPaymentPlansQuery:
    """Query to get payment plans with filtering"""
    customer_id: Optional[str] = None
    plan_status: Optional[str] = None  # "active", "completed", "defaulted", "cancelled"
    created_after: Optional[datetime] = None
    past_due_only: bool = False
    auto_pay_enabled: Optional[bool] = None
    limit: int = 50


@dataclass(frozen=True)
class GetCustomerInsightsQuery:
    """Query to get AI-generated customer insights"""
    customer_id: str
    insight_types: List[str] = None  # ["payment_behavior", "communication_preferences", "risk_assessment"]
    include_predictions: bool = True
    historical_analysis_months: int = 12


@dataclass(frozen=True)
class GetReminderEffectivenessQuery:
    """Query to analyze reminder effectiveness"""
    date_range_start: datetime
    date_range_end: datetime
    reminder_level: Optional[str] = None
    customer_segment: Optional[str] = None
    email_template: Optional[str] = None
    group_by: str = "reminder_level"


@dataclass(frozen=True)
class GetConversationAnalyticsQuery:
    """Query to get conversation analytics and AI performance"""
    date_range_start: datetime
    date_range_end: datetime
    conversation_type: Optional[str] = None
    resolution_status: Optional[str] = None
    ai_confidence_threshold: Optional[float] = None


@dataclass(frozen=True)
class GetUpcomingActionsQuery:
    """Query to get upcoming scheduled actions"""
    assigned_to: Optional[str] = None
    action_type: Optional[str] = None
    due_date_start: Optional[datetime] = None
    due_date_end: Optional[datetime] = None
    priority_level: Optional[str] = None
    overdue_only: bool = False
    limit: int = 50


@dataclass(frozen=True)
class GetDashboardSummaryQuery:
    """Query to get dashboard summary data"""
    user_id: str
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    include_trends: bool = True
    include_alerts: bool = True


@dataclass(frozen=True)
class SearchCustomersQuery:
    """Query to search customers with various criteria"""
    search_term: Optional[str] = None
    customer_status: Optional[str] = None
    has_overdue_invoices: Optional[bool] = None
    payment_risk_level: Optional[str] = None
    relationship_manager: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetAIPerformanceMetricsQuery:
    """Query to get AI system performance metrics"""
    date_range_start: datetime
    date_range_end: datetime
    metric_types: List[str] = None  # ["accuracy", "response_time", "user_satisfaction"]
    model_version: Optional[str] = None


@dataclass(frozen=True)
class GetComplianceReportQuery:
    """Query to get compliance and audit report data"""
    report_type: str  # "escalation_audit", "settlement_approvals", "payment_plan_compliance"
    date_range_start: datetime
    date_range_end: datetime
    include_supporting_documents: bool = False


# Query Result Types

@dataclass(frozen=True)
class OverdueInvoicesResult:
    """Result containing overdue invoices data"""
    invoices: List[Dict[str, Any]]
    total_count: int
    total_amount: Money
    average_days_overdue: float
    priority_breakdown: Dict[str, int]


@dataclass(frozen=True)
class PaymentCampaignsResult:
    """Result containing payment campaigns data"""
    campaigns: List[Dict[str, Any]]
    total_count: int
    status_breakdown: Dict[str, int]
    total_amount_in_campaigns: Money
    success_rate: float


@dataclass(frozen=True)
class CampaignDetailsResult:
    """Result containing detailed campaign information"""
    campaign: Dict[str, Any]
    reminders: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    notes: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    ai_recommendations: List[str]


@dataclass(frozen=True)
class CustomerPaymentHistoryResult:
    """Result containing customer payment history"""
    customer_id: str
    payment_summary: Dict[str, Any]
    payment_timeline: List[Dict[str, Any]]
    payment_patterns: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    dispute_history: List[Dict[str, Any]]


@dataclass(frozen=True)
class ConversationHistoryResult:
    """Result containing conversation history"""
    conversations: List[Dict[str, Any]]
    total_count: int
    satisfaction_scores: Dict[str, float]
    common_topics: List[str]
    resolution_rates: Dict[str, float]


@dataclass(frozen=True)
class PaymentRecommendationsResult:
    """Result containing AI payment recommendations"""
    recommendations: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    expected_outcomes: Dict[str, Any]
    alternative_strategies: List[Dict[str, Any]]


@dataclass(frozen=True)
class CollectionMetricsResult:
    """Result containing collection performance metrics"""
    metrics_by_period: List[Dict[str, Any]]
    overall_statistics: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    benchmark_comparison: Dict[str, Any]


@dataclass(frozen=True)
class CustomerInsightsResult:
    """Result containing AI-generated customer insights"""
    customer_id: str
    behavioral_insights: Dict[str, Any]
    communication_preferences: Dict[str, Any]
    risk_factors: List[str]
    success_predictors: List[str]
    recommended_strategies: List[str]


@dataclass(frozen=True)
class DashboardSummaryResult:
    """Result containing dashboard summary data"""
    key_metrics: Dict[str, Any]
    recent_activities: List[Dict[str, Any]]
    alerts_and_notifications: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    upcoming_tasks: List[Dict[str, Any]]


@dataclass(frozen=True)
class SearchResult:
    """Generic search result container"""
    results: List[Dict[str, Any]]
    total_count: int
    search_metadata: Dict[str, Any]
    facets: Dict[str, List[Dict[str, Any]]]


@dataclass(frozen=True)
class AIPerformanceResult:
    """Result containing AI performance metrics"""
    accuracy_metrics: Dict[str, float]
    performance_trends: List[Dict[str, Any]]
    model_comparisons: Dict[str, Any]
    improvement_recommendations: List[str]