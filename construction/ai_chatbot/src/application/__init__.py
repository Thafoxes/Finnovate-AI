"""
Application Layer for Payment Intelligence

This module provides the application layer that coordinates domain operations
and orchestrates use cases for the AI-powered payment collection system.

The application layer includes:
- Commands and Queries (CQRS pattern)
- Command and Query Handlers
- Application Services for high-level use cases
"""

from .commands import *
from .queries import *
from .handlers import *
from .query_handlers import *
from .services import *

__all__ = [
    # Commands
    "CreatePaymentCampaignCommand",
    "SendPaymentReminderCommand", 
    "ProcessIncomingPaymentCommand",
    "EscalateCampaignCommand",
    "CreatePaymentPlanCommand",
    "GenerateSettlementOfferCommand",
    "StartConversationCommand",
    "ProcessConversationMessageCommand",
    "ConfigureChatbotProfileCommand",
    "GenerateAIEmailCommand",
    
    # Command Results
    "CommandResult",
    "CampaignCreatedResult",
    "ReminderSentResult",
    "ConversationStartedResult",
    "SettlementGeneratedResult",
    "PaymentPlanCreatedResult",
    
    # Queries
    "GetOverdueInvoicesQuery",
    "GetPaymentCampaignsQuery",
    "GetCampaignDetailsQuery",
    "GetCustomerPaymentHistoryQuery",
    "GetConversationHistoryQuery",
    "GetPaymentRecommendationsQuery",
    "GetCollectionMetricsQuery",
    "GetDashboardSummaryQuery",
    
    # Query Results
    "OverdueInvoicesResult",
    "PaymentCampaignsResult",
    "CampaignDetailsResult",
    "CustomerPaymentHistoryResult",
    "ConversationHistoryResult",
    "PaymentRecommendationsResult",
    "CollectionMetricsResult",
    "DashboardSummaryResult",
    
    # Command Handlers
    "CreatePaymentCampaignHandler",
    "SendPaymentReminderHandler",
    "ProcessIncomingPaymentHandler",
    "EscalateCampaignHandler",
    "StartConversationHandler",
    "CreatePaymentPlanHandler",
    
    # Query Handlers
    "GetOverdueInvoicesHandler",
    "GetPaymentCampaignsHandler",
    "GetCampaignDetailsHandler",
    "GetCustomerPaymentHistoryHandler",
    "GetPaymentRecommendationsHandler",
    "GetDashboardSummaryHandler",
    
    # Application Services
    "PaymentCampaignService",
    "ConversationService", 
    "PaymentProcessingService"
]

# Application Layer Architecture:
#
# Commands & Queries:
#   - CQRS pattern separating write and read operations
#   - Commands represent state-changing operations
#   - Queries represent data retrieval operations
#
# Handlers:
#   - Command handlers orchestrate domain operations
#   - Query handlers aggregate data from read models
#   - Follow single responsibility principle
#
# Application Services:
#   - High-level use case coordination
#   - Business workflow orchestration
#   - Cross-aggregate operation management
#
# Integration Points:
#   - Domain services for business logic
#   - Infrastructure services for external concerns
#   - Repository interfaces for data persistence